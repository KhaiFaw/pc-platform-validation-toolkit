[CmdletBinding()]
param(
    [string]$PythonPath = 'python',
    [string]$NativeProbePath,
    [ValidateRange(5, 60)]
    [int]$PauseSeconds = 15,
    [string]$OutputDirectory,
    [string]$BackgroundContext = 'Normal interactive desktop; other applications were not closed; no load was deliberately injected.'
)

$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path -Parent $PSScriptRoot
$captureId = [guid]::NewGuid().ToString()
$runtimeDirectory = Join-Path $projectRoot ".platval\sessions\$captureId"
if (-not $OutputDirectory) {
    $OutputDirectory = Join-Path $projectRoot ".tmp\session-evidence\$captureId"
}
$OutputDirectory = [System.IO.Path]::GetFullPath($OutputDirectory)
if (Test-Path -LiteralPath $OutputDirectory) {
    throw 'The evidence output directory already exists. Choose a new directory; captures are never overwritten.'
}
if ($BackgroundContext.Length -gt 500) {
    throw 'Background context must be 500 characters or fewer. Do not include personal information.'
}
$nativeArguments = @()
$nativeBinarySha256 = $null
if ($NativeProbePath) {
    $NativeProbePath = [System.IO.Path]::GetFullPath($NativeProbePath)
    if (-not (Test-Path -LiteralPath $NativeProbePath -PathType Leaf)) {
        throw 'The explicitly requested native probe does not exist.'
    }
    $nativeArguments = @('--native-probe', [System.IO.Path]::GetFullPath($NativeProbePath))
    $nativeBinarySha256 = (Get-FileHash -LiteralPath $NativeProbePath -Algorithm SHA256).Hash.ToLowerInvariant()
}

# This snapshot intentionally records no process names, command lines or filesystem paths.
$contextCode = @'
import json
import time
from datetime import UTC, datetime
import psutil
battery = psutil.sensors_battery()
print(json.dumps({
    "sampled_at_utc": datetime.now(UTC).isoformat(),
    "cpu_sampling_seconds": 2,
    "system_cpu_percent_before_run": psutil.cpu_percent(interval=2),
    "available_memory_bytes_before_run": psutil.virtual_memory().available,
    "process_count_before_run": len(psutil.pids()),
    "power_plugged": battery.power_plugged if battery is not None else None,
    "battery_percent": battery.percent if battery is not None else None,
    "battery_context": "observed" if battery is not None else "unavailable",
    "measurement_clock": vars(time.get_clock_info("perf_counter")),
    "deadline_clock": vars(time.get_clock_info("monotonic")),
}))
'@

New-Item -ItemType Directory -Path $OutputDirectory | Out-Null
Push-Location $projectRoot
try {
    $provenanceCode = @'
import json
import platform
import sys
from pathlib import Path
import platval
print(json.dumps({
    "module_resolves_to_checkout": Path(platval.__file__).resolve().is_relative_to(Path(sys.argv[1]).resolve() / "src"),
    "python_version": platform.python_version(),
}))
'@
    $provenanceOutput = & $PythonPath -c $provenanceCode $projectRoot
    if ($LASTEXITCODE -ne 0) { throw 'Python package provenance check failed.' }
    $provenance = $provenanceOutput | ConvertFrom-Json
    if (-not $provenance.module_resolves_to_checkout) {
        throw 'The imported platval module is not from this checkout. Install this project into the requested Python environment.'
    }
    $sourceFiles = @(& git ls-files --cached --others --exclude-standard -- src cpp scripts configs)
    $sourceManifest = foreach ($sourceFile in $sourceFiles | Sort-Object -Unique) {
        [ordered]@{
            path = $sourceFile.Replace('\', '/')
            sha256 = (Get-FileHash -LiteralPath $sourceFile -Algorithm SHA256).Hash.ToLowerInvariant()
        }
    }
    [ordered]@{
        source_commit = (& git rev-parse HEAD).Trim()
        tracked_source_modified = [bool](& git status --porcelain --untracked-files=no)
        python_provenance = $provenance
        native_binary_sha256 = $nativeBinarySha256
        files = @($sourceManifest)
    } | ConvertTo-Json -Depth 5 | Set-Content -LiteralPath (Join-Path $OutputDirectory 'source-manifest.json') -Encoding utf8
    $doctorOutput = & $PythonPath -m platval.cli doctor --runtime-dir $runtimeDirectory @nativeArguments --json
    if ($LASTEXITCODE -ne 0) { throw 'Capability diagnostics failed.' }
    if ($NativeProbePath) {
        $doctor = $doctorOutput | ConvertFrom-Json
        $nativeCheck = $doctor.checks | Where-Object { $_.name -eq 'native CPUID probe' }
        if ($nativeCheck.status -ne 'PASS') {
            throw 'The explicitly requested native probe did not pass schema/invocation validation.'
        }
    }
    $doctorOutput | Set-Content -LiteralPath (Join-Path $OutputDirectory 'doctor.json') -Encoding utf8
    $sessions = @()
    foreach ($label in @('baseline-session', 'repeat-session')) {
        if ($label -eq 'repeat-session') {
            Write-Host "Waiting $PauseSeconds seconds between separate quick-plan processes..."
            Start-Sleep -Seconds $PauseSeconds
        }
        $contextOutput = & $PythonPath -c $contextCode
        if ($LASTEXITCODE -ne 0) { throw 'Context sampling failed.' }
        $context = $contextOutput | ConvertFrom-Json
        if ($context.sampled_at_utc -is [DateTime]) {
            $context.sampled_at_utc = $context.sampled_at_utc.ToUniversalTime().ToString('o')
        } else {
            $context.sampled_at_utc = [DateTimeOffset]::Parse(
                [string]$context.sampled_at_utc, [Globalization.CultureInfo]::InvariantCulture
            ).UtcDateTime.ToString('o')
        }
        $runOutput = & $PythonPath -m platval.cli run --plan configs/quick.yaml --runtime-dir $runtimeDirectory @nativeArguments --json
        if ($LASTEXITCODE -ne 0) { throw "$label did not complete a successful functional quick plan." }
        $stored = $runOutput | ConvertFrom-Json
        $runId = $stored.execution.run.run_id
        if ([string]::IsNullOrWhiteSpace($runId)) { throw 'A run UUID is missing.' }
        $sessionDirectory = Join-Path $OutputDirectory $label
        New-Item -ItemType Directory -Path $sessionDirectory | Out-Null
        foreach ($format in @('json', 'markdown', 'html')) {
            $reportOutput = & $PythonPath -m platval.cli report $runId --format $format --runtime-dir $runtimeDirectory --json
            if ($LASTEXITCODE -ne 0) { throw "$format report generation failed." }
            $report = $reportOutput | ConvertFrom-Json
            Copy-Item -LiteralPath (Join-Path $runtimeDirectory $report.artifact.relative_path) -Destination $sessionDirectory
        }
        $sessions += [ordered]@{
            label = $label
            run_id = $runId
            started_at_utc = $stored.execution.run.started_at
            overall_status = $stored.execution.run.overall_status
            plan_hash = $stored.execution.run.plan_hash
            platform_fingerprint = $stored.execution.run.platform_fingerprint
            power_plan_name = $stored.execution.platform.power_plan_name
            native_probe_version = $stored.execution.platform.native_probe_version
            background_context = $BackgroundContext
            pre_run_context = $context
        }
        Write-Host "$label completed: $runId ($($stored.execution.run.overall_status))"
    }
    if ($sessions[0].run_id -eq $sessions[1].run_id) { throw 'Independent sessions must have different run UUIDs.' }
    foreach ($sourceFile in $sourceManifest) {
        $currentHash = (Get-FileHash -LiteralPath $sourceFile.path -Algorithm SHA256).Hash.ToLowerInvariant()
        if ($currentHash -ne $sourceFile.sha256) {
            throw 'Source files changed during the capture. Retain the partial artifacts for diagnosis and capture again without editing sources.'
        }
    }
    if ($NativeProbePath -and
        (Get-FileHash -LiteralPath $NativeProbePath -Algorithm SHA256).Hash.ToLowerInvariant() -ne $nativeBinarySha256) {
        throw 'The native binary changed during the capture. Capture again without rebuilding it.'
    }
    $baselineOutput = & $PythonPath -m platval.cli baseline create --from-run $sessions[0].run_id --name independent-quick --runtime-dir $runtimeDirectory --json
    if ($LASTEXITCODE -ne 0) { throw 'Baseline creation failed.' }
    $baselineOutput | Set-Content -LiteralPath (Join-Path $OutputDirectory 'baseline.json') -Encoding utf8
    $comparisonOutput = & $PythonPath -m platval.cli compare --baseline independent-quick --run $sessions[1].run_id --runtime-dir $runtimeDirectory --json
    $comparisonExitCode = $LASTEXITCODE
    if ($comparisonExitCode -notin @(0, 1)) { throw 'Comparison execution failed.' }
    $comparison = $comparisonOutput | ConvertFrom-Json
    if (-not $comparison.platform_compatible -or -not $comparison.plan_compatible) {
        throw 'The two captures are incompatible; numeric conclusions cannot be used.'
    }
    $comparisonOutput | Set-Content -LiteralPath (Join-Path $OutputDirectory 'comparison.json') -Encoding utf8
    [ordered]@{
        schema_version = 1
        captured_at_utc = [DateTime]::UtcNow.ToString('o')
        separation_seconds = $PauseSeconds
        source_commit = (& git rev-parse HEAD).Trim()
        tracked_source_modified = [bool](& git status --porcelain --untracked-files=no)
        python_provenance = $provenance
        native_binary_sha256 = $nativeBinarySha256
        sessions = $sessions
        comparison_status = $comparison.overall_status
        comparison_exit_code = $comparisonExitCode
        interpretation = 'Two separately executed quick plans on the same host, not independent day-to-day sessions or hardware certification. Background load, cache state and temperature were not controlled. A short-run threshold crossing is retained as evidence, not a hardware-defect claim.'
    } | ConvertTo-Json -Depth 12 | Set-Content -LiteralPath (Join-Path $OutputDirectory 'context.json') -Encoding utf8
    Write-Host "Evidence saved: $OutputDirectory"
    Write-Host "Comparison status: $($comparison.overall_status). Review context and warnings before interpretation."
} finally {
    Pop-Location
}
