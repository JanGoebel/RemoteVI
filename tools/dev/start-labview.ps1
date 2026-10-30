# Start LabVIEW (64-bit, default 2020, the version the repository is saved in) outside this shell's job (WMI)
# and wait until its main window is up. Another LabVIEW version may run at the same time.
#   powershell -File tools\dev\start-labview.ps1 [-Version 2026]
param([string]$Version = '2020')
$exe = "C:\Program Files\National Instruments\LabVIEW $Version\LabVIEW.exe"
if (-not (Test-Path $exe)) { throw "LabVIEW $Version (64-bit) is not installed: $exe" }
$running = Get-CimInstance Win32_Process -Filter "Name='LabVIEW.exe'" | Where-Object { $_.ExecutablePath -eq $exe }
if ($running) { "already running: $($running.ProcessId)"; exit }
$r = Invoke-CimMethod -ClassName Win32_Process -MethodName Create -Arguments @{ CommandLine = "`"$exe`""; CurrentDirectory = (Split-Path $exe) }
"started $($r.ProcessId)"
for ($i = 0; $i -lt 60; $i++) {
  Start-Sleep 2
  $p = Get-Process -Id $r.ProcessId -ErrorAction SilentlyContinue
  if (-not $p) { "process gone"; exit 1 }
  if ($p.MainWindowHandle -ne 0) { "window after $(2*$i+2) s"; break }
}
Start-Sleep 15
"ready"
