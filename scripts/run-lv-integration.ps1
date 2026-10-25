<#
.SYNOPSIS
  Runs the LabVIEW integration suite (tests/lv) against tests/fixtures/RemoteVI Fixture.vi.

.DESCRIPTION
  1. G-CLI runs tests/fixtures/Launch Fixture (CLI).vi, which starts the fixture detached and
     returns once it is running. The fixture serves on port 8089 and logs to the event log.
  2. Waits for the fixture's `ready` line, then runs `npm run test:lv` with RVI_LV=1 and writes
     the TAP output to reports/lv-integration.tap.
  3. Stops the fixture with its own Stop button (through the server, like a browser).

  Only one RemoteVI server can run per LabVIEW instance: stop any other one first.

.PARAMETER LabVIEWVersion
  LabVIEW year, default 2025.
#>
param(
  [string]$LabVIEWVersion = '2025',
  [ValidateSet('32', '64')][string]$Bitness = '64',
  [int]$ReadyTimeoutSeconds = 120
)

$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $PSScriptRoot
if (-not $root) { $root = (Get-Location).Path }
$gcliDir = 'C:\Program Files\G-CLI\bin'
if (Test-Path $gcliDir) { $env:Path = "$gcliDir;$env:Path" }

$log = Join-Path $env:TEMP 'RemoteVI Fixture.log'
if (Test-Path $log) { Remove-Item $log }
New-Item -ItemType Directory -Force (Join-Path $root 'reports') | Out-Null

$launcher = Join-Path $root 'tests\fixtures\Launch Fixture (CLI).vi'
if (-not (Test-Path $launcher)) { throw "Missing $launcher" }

Write-Host "Starting the fixture in LabVIEW $LabVIEWVersion ($Bitness-bit)..."
& g-cli --lv-ver $LabVIEWVersion --arch $Bitness $launcher
if ($LASTEXITCODE -ne 0) { throw "Launching the fixture failed (g-cli exit code $LASTEXITCODE)" }

$deadline = (Get-Date).AddSeconds($ReadyTimeoutSeconds)
while (-not ((Test-Path $log) -and (Select-String -Path $log -Pattern '^ready' -Quiet))) {
  if ((Get-Date) -gt $deadline) { throw "The fixture did not report ready within $ReadyTimeoutSeconds s" }
  Start-Sleep -Milliseconds 500
}

$failed = $false
Push-Location $root
try {
  $env:RVI_LV = '1'
  & npm run test:lv 2>&1 | Tee-Object -FilePath (Join-Path $root 'reports\lv-integration.tap')
  $failed = $LASTEXITCODE -ne 0
} finally {
  Write-Host 'Stopping the fixture...'
  & node -e "import('./tests/lv/harness.mjs').then(async (h) => { const c = await h.connect(); const r = h.layout(c).get('Stop'); await h.click(c, r.cx, r.cy, { settle: 1500 }); process.exit(0); }).catch((e) => { console.error(e.message); process.exit(1); });"
  Pop-Location
}
if ($failed) { throw 'LabVIEW integration suite failed' }
Write-Host 'LabVIEW integration suite passed.'
