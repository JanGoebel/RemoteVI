# Prints the full link (with its ?t= access token) of the RemoteVI share on -Port in the running LabVIEW.
# Used by the LabVIEW integration tests (tests/lv/harness.mjs) to find the token of a fixture that was
# started with RemoteVI Start.vi and a random token. Reads source/API/RemoteVI Status.vi over LabVIEW's
# ActiveX server (main application instance), so LabVIEW must not show a modal dialog meanwhile.
#
#   powershell -File tools\lv-share-url.ps1 -Port 8089
param([int]$Port = 8089, [int]$TimeoutSeconds = 15)
$ErrorActionPreference = 'Stop'
$vi = Join-Path $PSScriptRoot '..\source\API\RemoteVI Status.vi' | Resolve-Path
$lv = New-Object -ComObject LabVIEW.Application
$deadline = (Get-Date).AddSeconds($TimeoutSeconds)
while ($true) {
  $r = $lv.GetVIReference([string]$vi, '', $false, 0)
  $r.Run($false)
  $text = [string]$r.GetControlValue('text')
  $m = [regex]::Match($text, "http://[^\s]+:$Port/\?t=[0-9A-Za-z]+")
  if ($m.Success) { $m.Value; exit 0 }
  if ((Get-Date) -gt $deadline) { throw "no RemoteVI share on port $Port in this LabVIEW (RemoteVI Status.vi):`n$text" }
  Start-Sleep -Milliseconds 500
}
