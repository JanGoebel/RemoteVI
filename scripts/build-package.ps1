<#
.SYNOPSIS
    Builds the RemoteVI VI package (jgoebel_lib_remotevi-X.Y.Z.B.vip) into builds\.

.DESCRIPTION
    1. Builds the example executables with LabVIEW 2020 (build specifications "RemoteVI Demo" and
       "RemoteVI Server" in RemoteVI.lvproj), through tools\dev\Build Spec.vi over LabVIEW's ActiveX
       server. The run-time engine of the LabVIEW that builds them is what they need, so they are
       built by the version the package is saved for. -SkipExecutables reuses builds\ as it is.
    2. Copies them to examples\Executables\<name>\ (git-ignored), from where the package installs
       them with the examples.
    3. Runs `vipm build build\RemoteVI.vipb` with the version number.
    4. Checks the package: the files it must contain, and none of the repository's development files.

    Same script locally and in CI (.github/workflows/package.yml). Requirements: LabVIEW 2020 (64-bit)
    with Application Builder, VIPM 2026 or newer (CLI `vipm`), and the packages of vipm.toml
    installed for LabVIEW 2020 (`vipm install`).

.EXAMPLE
    .\scripts\build-package.ps1
    .\scripts\build-package.ps1 -Version 1.2.3 -BuildNumber 42
    .\scripts\build-package.ps1 -SkipExecutables
#>
[CmdletBinding()]
param(
    # X.Y.Z; default: [project] version in vipm.toml
    [string]$Version,
    [int]$BuildNumber = 0,
    [string]$LabVIEWVersion = '2020',
    [ValidateSet('64')][string]$Bitness = '64',
    [switch]$SkipExecutables
)

$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
$project = Join-Path $root 'RemoteVI.lvproj'
$vipb = Join-Path $root 'build\RemoteVI.vipb'
$builds = Join-Path $root 'builds'
$staging = Join-Path $root 'examples\Executables'
$executables = @('RemoteVI Demo', 'RemoteVI Server')

if (-not $Version) {
    $toml = Get-Content -Raw (Join-Path $root 'vipm.toml')
    $m = [regex]::Match($toml, '(?m)^\s*version\s*=\s*"([^"]+)"')
    if (-not $m.Success) { throw 'No [project] version in vipm.toml; pass -Version.' }
    $Version = $m.Groups[1].Value
}
if ($Version -notmatch '^\d+\.\d+\.\d+$') { throw "Version must be X.Y.Z, not '$Version'." }
$fullVersion = "$Version.$BuildNumber"

$vipm = (Get-Command vipm -ErrorAction SilentlyContinue).Source
if (-not $vipm) {
    $vipm = Join-Path $env:ProgramFiles 'JKI\VI Package Manager\support\vipm.exe'
    if (-not (Test-Path $vipm)) { throw 'vipm not found: install VIPM 2026 or newer, or put its CLI on PATH.' }
}

function Invoke-BuildSpec([string]$Spec) {
    # LabVIEW.Application is the LabVIEW registered last as ActiveX server; refuse any other version,
    # because the executables would then need another run-time engine than the package states.
    try { $lv = [System.Runtime.InteropServices.Marshal]::GetActiveObject('LabVIEW.Application') }
    catch { $lv = New-Object -ComObject 'LabVIEW.Application' }
    $lvVersion = [string]$lv.Version
    if (-not $lvVersion.StartsWith(($LabVIEWVersion -replace '^20', '') + '.')) {
        throw "LabVIEW's ActiveX server is LabVIEW $lvVersion, not $LabVIEWVersion. Register LabVIEW $LabVIEWVersion (run it once as administrator) or close the other version."
    }
    $helper = Join-Path $root 'tools\dev\Build Spec.vi'
    $vi = $null
    # GetVIReference's arity differs between LabVIEW versions
    foreach ($a in @(@($helper), @($helper, ''), @($helper, '', $false))) {
        try { $vi = $lv.GetVIReference.Invoke($a); if ($vi) { break } } catch { }
    }
    if (-not $vi) { throw "Cannot open $helper over LabVIEW's ActiveX server." }
    $vi.SetControlValue('project', $project)
    $vi.SetControlValue('spec', $Spec)
    Write-Host "Building '$Spec' with LabVIEW $lvVersion..."
    $vi.Run($false)
    $err = $vi.GetControlValue('error out')
    if ($err[0]) { throw "Building '$Spec' failed: error $($err[1]) $($err[2])" }
    foreach ($f in $vi.GetControlValue('files')) { Write-Host "  $f" }
}

# 1. Executables
if (-not $SkipExecutables) {
    foreach ($spec in $executables) { Invoke-BuildSpec $spec }
}

# 2. Stage them next to the examples
foreach ($spec in $executables) {
    $src = Join-Path $builds $spec
    $exe = Join-Path $src "$spec.exe"
    if (-not (Test-Path $exe)) { throw "$exe is missing; build without -SkipExecutables." }
    $dst = Join-Path $staging $spec
    if (Test-Path $dst) { Remove-Item -Recurse -Force $dst }
    New-Item -ItemType Directory -Force $dst | Out-Null
    Copy-Item $exe, (Join-Path $src "$spec.ini") $dst
    Write-Host ("Staged {0} ({1:yyyy-MM-dd HH:mm})" -f $exe, (Get-Item $exe).LastWriteTime)
}

# 3. Package
$before = Get-Date
Write-Host "Building the VI package $fullVersion with VIPM for LabVIEW $LabVIEWVersion ($Bitness-bit)..."
& $vipm --labview-version $LabVIEWVersion --labview-bitness $Bitness build $vipb --version-number $Version --build-number $BuildNumber
if ($LASTEXITCODE -ne 0) { throw "vipm build failed (exit code $LASTEXITCODE)." }
$vip = Get-ChildItem $builds -Filter "jgoebel_lib_remotevi-$fullVersion.vip" | Where-Object LastWriteTime -ge $before.AddSeconds(-5)
if (-not $vip) { throw "vipm build reported success but builds\jgoebel_lib_remotevi-$fullVersion.vip was not written." }

# 4. Check what the package carries
Add-Type -AssemblyName System.IO.Compression.FileSystem
$zip = [System.IO.Compression.ZipFile]::OpenRead($vip.FullName)
try { $entries = @($zip.Entries | ForEach-Object { $_.FullName -replace '\\', '/' }) } finally { $zip.Dispose() }
$required = @(
    'RemoteVI.lvlib', 'API/RemoteVI Start.vi', 'API/RemoteVI Stop.vi', 'Share in Browser.vi',
    'RemoteVI Demo.vi', 'RemoteVI Demo/RemoteVI Demo.exe', 'RemoteVI Server/RemoteVI Server.exe', '.mnu'
)
$missing = @($required | Where-Object { $r = $_; -not ($entries | Where-Object { $_.EndsWith($r) }) })
$forbidden = @($entries | Where-Object { $_ -match '(^|/)(\.git|\.github|\.claude|CLAUDE\.md|tests|tools|spikes|scripts|docs|web|aixml|node_modules|\.RemoteVI\.UserState)(/|$)|\.lvproj$|\.aliases$|\.lvlps$' })
if ($missing -or $forbidden) {
    $missing | ForEach-Object { Write-Warning "missing in the package: $_" }
    $forbidden | ForEach-Object { Write-Warning "development file in the package: $_" }
    throw "The package content check failed: $($vip.FullName)"
}
Write-Host ("Built {0} ({1:N0} kB, {2} files)" -f $vip.FullName, ($vip.Length / 1kB), $entries.Count)
$vip.FullName
