[CmdletBinding()]
param(
    [ValidateSet('Debug', 'Release')]
    [string]$Configuration = 'Release',
    [string]$Generator,
    [string]$CxxCompiler,
    [string]$MakeProgram
)

$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path -Parent $PSScriptRoot
$sourceDirectory = Join-Path $projectRoot 'cpp\cpuid_probe'
$buildDirectory = Join-Path $sourceDirectory 'build'
$cmake = Get-Command cmake -ErrorAction SilentlyContinue

if (-not $cmake) {
    throw 'CMake is required to build cpuid_probe but was not found on PATH.'
}

$configureArguments = @('-S', $sourceDirectory, '-B', $buildDirectory, "-DCMAKE_BUILD_TYPE=$Configuration")
if ($Generator) { $configureArguments += @('-G', $Generator) }
foreach ($tool in @(@('CMAKE_CXX_COMPILER', $CxxCompiler), @('CMAKE_MAKE_PROGRAM', $MakeProgram))) {
    if ($tool[1]) {
        if (-not (Test-Path -LiteralPath $tool[1] -PathType Leaf)) {
            throw "The requested $($tool[0]) executable does not exist."
        }
        $resolvedTool = [System.IO.Path]::GetFullPath($tool[1]).Replace('\', '/')
        $configureArguments += "-D$($tool[0])=$resolvedTool"
    }
}
& $cmake.Source @configureArguments
if ($LASTEXITCODE -ne 0) { throw 'CMake configuration failed.' }

& $cmake.Source --build $buildDirectory --config $Configuration
if ($LASTEXITCODE -ne 0) { throw 'Native probe build failed.' }

$ctestPath = Join-Path (Split-Path -Parent $cmake.Source) 'ctest.exe'
if (-not (Test-Path -LiteralPath $ctestPath)) {
    throw 'ctest.exe was not found beside cmake.exe.'
}

& $ctestPath --test-dir $buildDirectory -C $Configuration --output-on-failure
if ($LASTEXITCODE -ne 0) { throw 'Native probe tests failed.' }
