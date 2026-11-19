# NI's LabVIEW CLI, shared by tools\build-package.ps1 and tools\run-lv-integration.ps1 (dot-source it).
# The CLI ships with LabVIEW (2018 or newer) and talks to LabVIEW over VI Server TCP, so it reaches a
# LabVIEW that VIPM or G-CLI started as well as one it starts itself - ActiveX does neither reliably.

function Get-LabVIEWExe([string]$Version) {
    $exe = Join-Path $env:ProgramFiles "National Instruments\LabVIEW $Version\LabVIEW.exe"
    if (-not (Test-Path $exe)) { throw "LabVIEW $Version (64-bit) not found: $exe" }
    $exe
}

function Get-VIServerPort([string]$Exe) {
    # LabVIEW CLI needs VI Server TCP: Tools > Options > VI Server > TCP/IP, saved in LabVIEW.ini
    $ini = Join-Path (Split-Path $Exe) 'LabVIEW.ini'
    $text = if (Test-Path $ini) { Get-Content -Raw $ini } else { '' }
    if ($text -notmatch '(?im)^server\.tcp\.enabled\s*=\s*"?true') {
        throw "VI Server TCP is off in $ini. Enable Tools > Options > VI Server > TCP/IP in that LabVIEW; LabVIEW CLI needs it."
    }
    $m = [regex]::Match($text, '(?im)^server\.tcp\.port\s*=\s*(\d+)')
    if ($m.Success) { [int]$m.Groups[1].Value } else { 3363 }
}

function Invoke-LabVIEWCli([string]$Version, [string[]]$Arguments) {
    $cli = Join-Path ${env:ProgramFiles(x86)} 'National Instruments\Shared\LabVIEW CLI\LabVIEWCLI.exe'
    if (-not (Test-Path $cli)) { throw "LabVIEW CLI not found: $cli (it is installed with LabVIEW 2018 or newer)" }
    $exe = Get-LabVIEWExe $Version
    $port = Get-VIServerPort $exe
    # Windows PowerShell turns a native program's stderr into errors; collect it as text instead
    $ErrorActionPreference = 'Continue'
    $out = & $cli @Arguments -LabVIEWPath $exe -PortNumber $port -LogToConsole true 2>&1 | ForEach-Object { "$_" }
    [pscustomobject]@{ ExitCode = $LASTEXITCODE; Output = @($out) }
}

function Close-LabVIEW([string]$Version, [int]$TimeoutSeconds = 120) {
    # CloseLabVIEW answers before the process has gone; a tool that starts LabVIEW meanwhile (VIPM) attaches to the dying one
    $r = Invoke-LabVIEWCli $Version @('-OperationName', 'CloseLabVIEW')
    if ($r.ExitCode -ne 0) { throw "Closing LabVIEW $Version failed (LabVIEW CLI exit code $($r.ExitCode)): $($r.Output -join ' | ')" }
    $exe = Get-LabVIEWExe $Version
    $deadline = (Get-Date).AddSeconds($TimeoutSeconds)
    while (Get-Process LabVIEW -ErrorAction SilentlyContinue | Where-Object { $_.Path -eq $exe }) {
        if ((Get-Date) -gt $deadline) { throw "LabVIEW $Version did not exit within $TimeoutSeconds s of CloseLabVIEW." }
        Start-Sleep -Seconds 1
    }
}

function Start-LabVIEW([string]$Version, [int]$TimeoutSeconds = 180) {
    # Starts that LabVIEW unless it runs, and waits until its VI Server answers, so that a tool expecting it (VIPM) finds it ready
    $exe = Get-LabVIEWExe $Version
    $port = Get-VIServerPort $exe
    if (-not (Get-Process LabVIEW -ErrorAction SilentlyContinue | Where-Object { $_.Path -eq $exe })) { Start-Process $exe | Out-Null }
    $deadline = (Get-Date).AddSeconds($TimeoutSeconds)
    while ($true) {
        $client = New-Object Net.Sockets.TcpClient
        try { $client.Connect('127.0.0.1', $port); return } catch { } finally { $client.Close() }
        if ((Get-Date) -gt $deadline) { throw "LabVIEW $Version did not open VI Server port $port within $TimeoutSeconds s." }
        Start-Sleep -Seconds 1
    }
}
