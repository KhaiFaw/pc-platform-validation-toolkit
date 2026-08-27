[CmdletBinding()]
param(
    [switch]$UseExistingEnvironment,
    [switch]$SkipNative,
    [string]$PythonPath = 'python'
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
        $python = Join-Path $projectRoot '.venv\Scripts\python.exe'
        if (-not (Test-Path -LiteralPath $python)) {
            throw 'The project .venv is missing. Run the documented setup first.'
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
        } else {
            Write-Warning 'CMake is unavailable; native build verification was skipped.'
        }
    }

    Push-Location $projectRoot
    try {
        Write-Host 'Checking environment capabilities...'
        & $python -m platval.cli doctor --runtime-dir $runtimeDirectory
        if ($LASTEXITCODE -ne 0) { throw 'Capability diagnostics failed.' }

        Write-Host 'Running the bounded quick plan...'
        $runOutput = & $python -m platval.cli run --plan configs/quick.yaml --runtime-dir $runtimeDirectory --json
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

        Write-Host 'Creating and comparing an immutable baseline...'
        & $python -m platval.cli baseline create --from-run $runId --name verification-known-good --runtime-dir $runtimeDirectory --json | Out-Null
        if ($LASTEXITCODE -ne 0) { throw 'Baseline creation failed.' }
        & $python -m platval.cli compare --baseline verification-known-good --run $runId --runtime-dir $runtimeDirectory --json | Out-Null
        if ($LASTEXITCODE -ne 0) { throw 'Baseline comparison failed.' }

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
