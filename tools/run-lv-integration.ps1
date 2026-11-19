<#
.SYNOPSIS
  Runs the LabVIEW integration suite (tests/lv) against tests/fixtures/RemoteVI Fixture.vi.

.DESCRIPTION
  1. Starts the fixture in LabVIEW with NI's LabVIEW CLI (RunVI on tests/fixtures/Launch Fixture.vi, over
     VI Server TCP; tools/labview-cli.ps1). The launcher opens the fixture's front panel, runs it without
     waiting (RemoteVI streams a 0x0 frame from a VI without an open panel) and returns the link of its
     share on port 8089, with the access token, which becomes RVI_URL for the suite. The fixture logs to
     %TEMP%\RemoteVI Fixture.log.
  2. Waits for the fixture's `ready` line, then runs `npm run test:lv` with RVI_LV=1 and writes the TAP
     output to reports/lv-integration.tap.
  3. Stops the fixture with its own Stop button (through the server, like a browser), then closes its
     front panel (RunVI on tests/fixtures/Close Fixture.vi), so the fixture and the RemoteVI VIs it calls
     leave memory: VIPM does not build the package while they are open.

  Port 8089 must be free in that LabVIEW: stop another share on it first.

.PARAMETER LabVIEWVersion
  LabVIEW year, default 2020 (the version the repository is saved for).

.PARAMETER ReadyTimeoutSeconds
  How long to wait for the fixture's `ready` line.
#>
param(
  [string]$LabVIEWVersion = '2020',
  [int]$ReadyTimeoutSeconds = 120
)

$ErrorActionPreference = 'Stop'

. (Join-Path $PSScriptRoot 'labview-cli.ps1')
$root = Split-Path -Parent $PSScriptRoot
if (-not $root) { $root = (Get-Location).Path }

$log = Join-Path $env:TEMP 'RemoteVI Fixture.log'
if (Test-Path $log) { Remove-Item $log }
New-Item -ItemType Directory -Force (Join-Path $root 'reports') | Out-Null

$launcher = Join-Path $root 'tests\fixtures\Launch Fixture.vi'
if (-not (Test-Path $launcher)) { throw "Missing $launcher" }

Write-Host "Starting the fixture in LabVIEW $LabVIEWVersion (LabVIEW CLI)..."
$r = Invoke-LabVIEWCli $LabVIEWVersion @('-OperationName', 'RunVI', '-VIPath', $launcher)
$url = ($r.Output | Select-String -Pattern 'http://\S+:8089/\S*' | Select-Object -First 1).Matches.Value
if ($r.ExitCode -ne 0 -or -not $url) { throw "Starting the fixture failed (LabVIEW CLI exit code $($r.ExitCode)): $($r.Output -join ' | ')" }
Write-Host "Fixture shared at $url"
$env:RVI_URL = $url

$deadline = (Get-Date).AddSeconds($ReadyTimeoutSeconds)
while (-not ((Test-Path $log) -and (Select-String -Path $log -Pattern '^ready' -Quiet))) {
  if ((Get-Date) -gt $deadline) { throw "The fixture did not report ready within $ReadyTimeoutSeconds s" }
  Start-Sleep -Milliseconds 500
}

$failed = $false
Push-Location $root
try {
  # Windows PowerShell turns a native program's stderr into errors; let npm and node write to it
  $ErrorActionPreference = 'Continue'
  $env:RVI_LV = '1'
  & npm run test:lv 2>&1 | Tee-Object -FilePath (Join-Path $root 'reports\lv-integration.tap')
  $failed = $LASTEXITCODE -ne 0
} finally {
  Write-Host 'Stopping the fixture...'
  & node -e "import('./tests/lv/harness.mjs').then(async (h) => { const c = await h.connect(); const r = h.layout(c).get('Stop'); await h.click(c, r.cx, r.cy, { settle: 1500 }); process.exit(0); }).catch((e) => { console.error(e.message); process.exit(1); });"
  # Unload the fixture and the RemoteVI VIs it calls: VIPM (the package job next) refuses to build while they are open
  $c = Invoke-LabVIEWCli $LabVIEWVersion @('-OperationName', 'RunVI', '-VIPath', (Join-Path $root 'tests\fixtures\Close Fixture.vi'))
  if ($c.ExitCode -ne 0) { Write-Warning "Closing the fixture failed (LabVIEW CLI exit code $($c.ExitCode)): $($c.Output -join ' | ')" }
  Pop-Location
}
if ($failed) { throw 'LabVIEW integration suite failed' }
Write-Host 'LabVIEW integration suite passed.'
