<#
.SYNOPSIS
  Runs the LabVIEW integration suite (tests/lv) against tests/fixtures/RemoteVI Fixture.vi.

.DESCRIPTION
  1. Opens the fixture's front panel and runs it without waiting, over LabVIEW's ActiveX server
     (like tools/dev/Launch Detached.vi; RemoteVI streams a 0x0 frame from a VI without an open
     panel). LabVIEW.Application starts the LabVIEW registered for ActiveX when none answers.
     The fixture shares itself on port 8089 and logs to %TEMP%\RemoteVI Fixture.log.
  2. Waits for the fixture's `ready` line, then runs `npm run test:lv` with RVI_LV=1 and writes
     the TAP output to reports/lv-integration.tap (the harness reads the link with its token
     through tools/lv-share-url.ps1).
  3. Stops the fixture with its own Stop button (through the server, like a browser).

  Port 8089 must be free in that LabVIEW: stop another share on it first.

.PARAMETER ReadyTimeoutSeconds
  How long to wait for the fixture's `ready` line.
#>
param(
  [int]$ReadyTimeoutSeconds = 120
)

$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $PSScriptRoot
if (-not $root) { $root = (Get-Location).Path }

$log = Join-Path $env:TEMP 'RemoteVI Fixture.log'
if (Test-Path $log) { Remove-Item $log }
New-Item -ItemType Directory -Force (Join-Path $root 'reports') | Out-Null

$fixture = Join-Path $root 'tests\fixtures\RemoteVI Fixture.vi'
if (-not (Test-Path $fixture)) { throw "Missing $fixture" }

Write-Host 'Starting the fixture over LabVIEW''s ActiveX server...'
try { $lv = [System.Runtime.InteropServices.Marshal]::GetActiveObject('LabVIEW.Application') }
catch {
  # A LabVIEW started without ActiveX (by VIPM or G-CLI) is not reachable here, and a new one cannot start beside it
  if (Get-Process LabVIEW -ErrorAction SilentlyContinue) { throw "LabVIEW runs but is not reachable over ActiveX (started by VIPM, G-CLI or by hand). Quit it and run this again." }
  $lv = New-Object -ComObject 'LabVIEW.Application'
}
# GetVIReference's arity differs between LabVIEW versions
$vi = $null
foreach ($a in @(@($fixture), @($fixture, ''), @($fixture, '', $false))) {
  try { $vi = $lv.GetVIReference.Invoke($a); if ($vi) { break } } catch { }
}
if (-not $vi) { throw "Cannot open $fixture over LabVIEW's ActiveX server" }
$vi.FPWinOpen = $true
$vi.Run($true)

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
