[CmdletBinding()]
param(
    [switch]$UseExistingEnvironment,
    [switch]$SkipNative,
    [string]$PythonPath = 'python',
    [string]$NativeProbePath
)

$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path -Parent $PSScriptRoot
$temporaryRoot = [System.IO.Path]::GetFullPath((Join-Path $projectRoot '.tmp'))
$verificationRoot = [System.IO.Path]::GetFullPath((Join-Path $temporaryRoot 'verification'))
$runtimeDirectory = Join-Path $verificationRoot 'runtime'

if ([System.IO.Path]::GetDirectoryName($verificationRoot) -ne $temporaryRoot) {
    throw 'Resolved verification directory escaped the project temporary root.'
}

if (Test-Path -LiteralPath $verificationRoot) {
    throw "Verification directory already exists: $verificationRoot"
}

New-Item -ItemType Directory -Path $verificationRoot | Out-Null
try {
    if ($UseExistingEnvironment) {
        if ($PSBoundParameters.ContainsKey('PythonPath')) {
            $python = $PythonPath
        } else {
            $python = Join-Path $projectRoot '.venv\Scripts\python.exe'
            if (-not (Test-Path -LiteralPath $python)) {
                throw 'The project .venv is missing. Run the documented setup first.'
            }
        }
    } else {
        $venv = Join-Path $verificationRoot 'venv'
        & $PythonPath -m venv $venv
        if ($LASTEXITCODE -ne 0) { throw 'Virtual-environment creation failed.' }
        $python = Join-Path $venv 'Scripts\python.exe'
        & $python -m pip install -e "${projectRoot}[dev]"
        if ($LASTEXITCODE -ne 0) { throw 'Editable installation failed.' }
    }

    & $python -m ruff format --check "$projectRoot\src" "$projectRoot\tests"
    if ($LASTEXITCODE -ne 0) { throw 'Formatting check failed.' }
    & $python -m ruff check "$projectRoot\src" "$projectRoot\tests"
    if ($LASTEXITCODE -ne 0) { throw 'Lint check failed.' }
    & $python -m mypy "$projectRoot\src" "$projectRoot\tests"
    if ($LASTEXITCODE -ne 0) { throw 'Type check failed.' }
    & $python -m pytest "$projectRoot\tests" -m 'not hardware and not extended'
    if ($LASTEXITCODE -ne 0) { throw 'Automated tests failed.' }

    if (-not $SkipNative) {
        $cmake = Get-Command cmake -ErrorAction SilentlyContinue
        if ($cmake) {
            & "$projectRoot\scripts\build_native.ps1"
            if ($LASTEXITCODE -ne 0) { throw 'Native verification failed.' }
            if (-not $NativeProbePath) {
                $probeCandidates = @(
                    (Join-Path $projectRoot 'cpp\cpuid_probe\build\Release\cpuid_probe.exe'),
                    (Join-Path $projectRoot 'cpp\cpuid_probe\build\cpuid_probe.exe')
                )
                $NativeProbePath = $probeCandidates | Where-Object { Test-Path -LiteralPath $_ -PathType Leaf } | Select-Object -First 1
                if (-not $NativeProbePath) { throw 'The built native probe executable could not be located.' }
            }
        } else {
            Write-Warning 'CMake is unavailable; native build verification was skipped.'
        }
    }

    $nativeArguments = @()
    if ($NativeProbePath) {
        if (-not (Test-Path -LiteralPath $NativeProbePath -PathType Leaf)) {
            throw 'The explicitly requested native probe does not exist.'
        }
        $nativeArguments = @('--native-probe', [System.IO.Path]::GetFullPath($NativeProbePath))
    }

    Push-Location $projectRoot
    try {
        Write-Host 'Checking environment capabilities...'
        $doctorOutput = & $python -m platval.cli doctor --runtime-dir $runtimeDirectory @nativeArguments --json
        if ($LASTEXITCODE -ne 0) { throw 'Capability diagnostics failed.' }
        $doctor = $doctorOutput | ConvertFrom-Json
        Write-Host "Capability diagnostics: $($doctor.overall_status)"
        if ($NativeProbePath) {
            $nativeCheck = $doctor.checks | Where-Object { $_.name -eq 'native CPUID probe' }
            if ($nativeCheck.status -ne 'PASS') {
                throw 'The requested native probe did not pass schema/invocation validation.'
            }
        }

        Write-Host 'Running the bounded quick plan...'
        $runOutput = & $python -m platval.cli run --plan configs/quick.yaml --runtime-dir $runtimeDirectory @nativeArguments --json
        if ($LASTEXITCODE -ne 0) { throw 'Quick validation plan failed.' }
        $storedRun = $runOutput | ConvertFrom-Json
        $runId = $storedRun.execution.run.run_id
        if ([string]::IsNullOrWhiteSpace($runId)) { throw 'Quick run did not return a run identifier.' }

        Write-Host 'Generating JSON, Markdown, and HTML evidence...'
        foreach ($format in @('json', 'markdown', 'html')) {
            $reportOutput = & $python -m platval.cli report $runId --format $format --runtime-dir $runtimeDirectory --json
            if ($LASTEXITCODE -ne 0) { throw "$format report generation failed." }
            $report = $reportOutput | ConvertFrom-Json
            $reportPath = Join-Path $runtimeDirectory $report.artifact.relative_path
            if (-not (Test-Path -LiteralPath $reportPath -PathType Leaf)) {
                throw "$format report artifact is missing: $reportPath"
            }
        }

        $canonicalArtifact = Join-Path $runtimeDirectory $storedRun.artifacts[0].relative_path
        if (-not (Test-Path -LiteralPath $canonicalArtifact -PathType Leaf)) {
            throw "Canonical run artifact is missing: $canonicalArtifact"
        }

        Write-Host 'Creating an immutable baseline and executing a separate repeat run...'
        & $python -m platval.cli baseline create --from-run $runId --name verification-known-good --runtime-dir $runtimeDirectory --json | Out-Null
        if ($LASTEXITCODE -ne 0) { throw 'Baseline creation failed.' }
        $repeatOutput = & $python -m platval.cli run --plan configs/quick.yaml --runtime-dir $runtimeDirectory @nativeArguments --json
        if ($LASTEXITCODE -ne 0) { throw 'Repeated functional quick plan failed.' }
        $repeatRun = $repeatOutput | ConvertFrom-Json
        $repeatRunId = $repeatRun.execution.run.run_id
        if ([string]::IsNullOrWhiteSpace($repeatRunId) -or $repeatRunId -eq $runId) {
            throw 'The repeat plan did not return an independent run identifier.'
        }
        $comparisonOutput = & $python -m platval.cli compare --baseline verification-known-good --run $repeatRunId --runtime-dir $runtimeDirectory --json
        if ($LASTEXITCODE -notin @(0, 1)) { throw 'Baseline comparison execution failed.' }
        $comparison = $comparisonOutput | ConvertFrom-Json
        if (-not $comparison.platform_compatible -or -not $comparison.plan_compatible) {
            throw 'Independent verification runs are not compatible.'
        }
        Write-Host "Independent comparison: $($comparison.overall_status). Short-run timing classifications are evidence, not a quality-gate benchmark."

        Write-Host 'Producing the labelled synthetic failure demonstration...'
        $demoRuntimeDirectory = Join-Path $verificationRoot 'failure-demo'
        & $python -m platval.cli demo failure --runtime-dir $demoRuntimeDirectory
        if ($LASTEXITCODE -ne 0) { throw 'Synthetic failure demonstration failed.' }
    } finally {
        Pop-Location
    }
    Write-Host 'Verification completed successfully.'
} finally {
    if (Test-Path -LiteralPath $verificationRoot) {
        Remove-Item -LiteralPath $verificationRoot -Recurse -Force
    }
}
