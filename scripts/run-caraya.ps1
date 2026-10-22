<#
.SYNOPSIS
    Runs the RemoteVI Caraya test suite headless via G-CLI and writes a JUnit report.

.EXAMPLE
    .\scripts\run-caraya.ps1 -LabVIEWVersion 2020 -Bitness 64
#>
[CmdletBinding()]
param(
    [string]$LabVIEWVersion = '2020',
    [ValidateSet('32', '64')][string]$Bitness = '64',
    [string]$TestPath = (Join-Path $PSScriptRoot '..\tests\caraya'),
    [string]$Report = (Join-Path $PSScriptRoot '..\reports\caraya.xml')
)

$ErrorActionPreference = 'Stop'

if (-not (Get-Command g-cli -ErrorAction SilentlyContinue)) {
    throw 'g-cli not found. Install G-CLI from VIPM (wiresmith_technology_lib_g_cli) and make sure it is on PATH.'
}

$TestPath = (Resolve-Path $TestPath).Path
New-Item -ItemType Directory -Force -Path (Split-Path $Report) | Out-Null

Write-Host "Running Caraya tests in $TestPath with LabVIEW $LabVIEWVersion ($Bitness-bit)"
& g-cli --lv-ver $LabVIEWVersion --arch $Bitness caraya -- -s "$TestPath" -x "$Report"
$code = $LASTEXITCODE

& g-cli --lv-ver $LabVIEWVersion --arch $Bitness QuitLabVIEW | Out-Null

if ($code -ne 0) {
    Write-Error "Caraya reported failures (exit code $code). See $Report"
}
Write-Host "All Caraya tests passed. Report: $Report"
