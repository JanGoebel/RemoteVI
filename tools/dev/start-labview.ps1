# Start LabVIEW 2025 64-bit outside this shell's job (WMI) and wait until its main window is up.
$exe = 'C:\Program Files\National Instruments\LabVIEW 2025\LabVIEW.exe'
$running = Get-Process LabVIEW -ErrorAction SilentlyContinue
if ($running) { "already running: $($running.Id)"; exit }
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
