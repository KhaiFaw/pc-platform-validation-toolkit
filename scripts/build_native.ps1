[CmdletBinding()]
param(
    [ValidateSet('Debug', 'Release')]
    [string]$Configuration = 'Release'
)

$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path -Parent $PSScriptRoot
$sourceDirectory = Join-Path $projectRoot 'cpp\cpuid_probe'
$buildDirectory = Join-Path $sourceDirectory 'build'
$cmake = Get-Command cmake -ErrorAction SilentlyContinue

if (-not $cmake) {
    throw 'CMake is required to build cpuid_probe but was not found on PATH.'
}

& $cmake.Source -S $sourceDirectory -B $buildDirectory
if ($LASTEXITCODE -ne 0) { throw 'CMake configuration failed.' }

& $cmake.Source --build $buildDirectory --config $Configuration
if ($LASTEXITCODE -ne 0) { throw 'Native probe build failed.' }

$ctestPath = Join-Path (Split-Path -Parent $cmake.Source) 'ctest.exe'
if (-not (Test-Path -LiteralPath $ctestPath)) {
    throw 'ctest.exe was not found beside cmake.exe.'
}

& $ctestPath --test-dir $buildDirectory -C $Configuration --output-on-failure
if ($LASTEXITCODE -ne 0) { throw 'Native probe tests failed.' }
