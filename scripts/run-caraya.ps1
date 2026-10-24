<#
.SYNOPSIS
    Runs the RemoteVI Caraya unit tests headless via G-CLI and writes a JUnit report.

.DESCRIPTION
    The unit tests in tests\caraya\unit are generated from tests\vectors by tests\caraya\build.py
    (see docs\testing.md, "Caraya unit tests"). -Build regenerates them first, which is needed
    after a vector changed.

    Requirements: Caraya (VIPM package jki_lib_caraya) installed for the LabVIEW version used,
    G-CLI (wiresmith_technology_lib_g_cli) on PATH with its Caraya tool (lvos_lib_caraya_cli_extension).
    LabVIEW is left running unless -QuitLabVIEW is given.

.EXAMPLE
    .\scripts\run-caraya.ps1
    .\scripts\run-caraya.ps1 -Build -Report .\reports\caraya.xml -QuitLabVIEW
#>
[CmdletBinding()]
param(
    [string]$LabVIEWVersion = '2025',
    [ValidateSet('32', '64')][string]$Bitness = '64',
    [string]$TestPath,
    [string]$Report,
    [switch]$Build,
    [switch]$QuitLabVIEW
)

$ErrorActionPreference = 'Stop'
# $PSScriptRoot is empty inside param() defaults when Windows PowerShell 5.1 runs this with -File.
$root = Split-Path -Parent $MyInvocation.MyCommand.Path
if (-not $TestPath) { $TestPath = Join-Path $root '..\tests\caraya\unit' }
if (-not $Report) { $Report = Join-Path $root '..\reports\caraya.xml' }

$programFiles = if ($Bitness -eq '64') { $env:ProgramFiles } else { ${env:ProgramFiles(x86)} }
$caraya = Join-Path $programFiles "National Instruments\LabVIEW $LabVIEWVersion\vi.lib\addons\_JKI Toolkits\Caraya\Caraya.lvlib"
if (-not (Test-Path $caraya)) {
    throw "Caraya is not installed for LabVIEW $LabVIEWVersion ($Bitness-bit): $caraya is missing. Install jki_lib_caraya with VIPM for that LabVIEW, then run with -Build."
}

if ($Build) {
    $python = (Get-Command python -ErrorAction SilentlyContinue).Source
    if (-not $python) { throw 'python not found on PATH (needed by tests\caraya\build.py).' }
    & $python (Join-Path $root '..\tests\caraya\build.py')
    if ($LASTEXITCODE -ne 0) { throw "tests\caraya\build.py failed (exit code $LASTEXITCODE)." }
}

if (-not (Get-Command g-cli -ErrorAction SilentlyContinue)) {
    throw 'g-cli not found. Install G-CLI from VIPM (wiresmith_technology_lib_g_cli) and the Caraya CLI extension (lvos_lib_caraya_cli_extension), and make sure g-cli is on PATH.'
}

if (-not (Test-Path $TestPath)) { throw "No tests at $TestPath - run with -Build." }
$TestPath = (Resolve-Path $TestPath).Path
New-Item -ItemType Directory -Force -Path (Split-Path $Report) | Out-Null
$Report = [System.IO.Path]::GetFullPath($Report)

Write-Host "Running Caraya tests in $TestPath with LabVIEW $LabVIEWVersion ($Bitness-bit)"
& g-cli --lv-ver $LabVIEWVersion --arch $Bitness caraya -- -s "$TestPath" -x "$Report"
$code = $LASTEXITCODE

if ($QuitLabVIEW) { & g-cli --lv-ver $LabVIEWVersion --arch $Bitness QuitLabVIEW | Out-Null }

# The report is the verdict: Caraya's exit code says only that something failed.
if (Test-Path $Report) {
    [xml]$junit = Get-Content -Raw $Report
    foreach ($suite in $junit.SelectNodes('//testsuite')) {
        Write-Host ("{0}: {1} tests, {2} failures, {3} errors" -f $suite.name, $suite.tests, $suite.failures, $suite.errors)
        foreach ($case in $suite.SelectNodes('testcase[failure or error]')) { Write-Host "  FAIL $($case.name)" }
    }
} else {
    Write-Warning "No report was written at $Report."
}

if ($code -ne 0) {
    Write-Error "Caraya reported failures (exit code $code). See $Report"
}
Write-Host "All Caraya tests passed. Report: $Report"
