<#
.SYNOPSIS
    Lists the visible top-level windows of some processes and saves a picture of each (PrintWindow: the window
    itself, never the desktop). For CI diagnostics: what a tool waits for on the runner's desktop, e.g. a dialog.

.EXAMPLE
    .\tools\window-snapshot.ps1 -ProcessName 'VI Package Manager', 'LabVIEW' -OutDir builds\diag
#>
param(
    [string[]]$ProcessName = @('VI Package Manager', 'LabVIEW'),
    [string]$OutDir
)

Add-Type -ReferencedAssemblies System.Drawing -TypeDefinition @'
using System;
using System.Collections.Generic;
using System.Drawing;
using System.Runtime.InteropServices;
using System.Text;

public static class WindowSnapshot {
    delegate bool EnumProc(IntPtr hwnd, IntPtr lParam);
    [StructLayout(LayoutKind.Sequential)] public struct RECT { public int Left, Top, Right, Bottom; }
    [DllImport("user32.dll")] static extern bool EnumWindows(EnumProc cb, IntPtr lParam);
    [DllImport("user32.dll")] static extern uint GetWindowThreadProcessId(IntPtr hwnd, out uint pid);
    [DllImport("user32.dll")] static extern bool IsWindowVisible(IntPtr hwnd);
    [DllImport("user32.dll", CharSet = CharSet.Unicode)] static extern int GetWindowText(IntPtr hwnd, StringBuilder s, int n);
    [DllImport("user32.dll", CharSet = CharSet.Unicode)] static extern int GetClassName(IntPtr hwnd, StringBuilder s, int n);
    [DllImport("user32.dll")] static extern bool GetWindowRect(IntPtr hwnd, out RECT r);
    [DllImport("user32.dll")] static extern bool PrintWindow(IntPtr hwnd, IntPtr hdc, uint flags);

    public static List<object[]> List(uint[] pids) {
        var found = new List<object[]>();
        var set = new HashSet<uint>(pids);
        EnumWindows((h, l) => {
            uint pid; GetWindowThreadProcessId(h, out pid);
            if (set.Contains(pid) && IsWindowVisible(h)) {
                var t = new StringBuilder(512); GetWindowText(h, t, 512);
                var c = new StringBuilder(256); GetClassName(h, c, 256);
                RECT r; GetWindowRect(h, out r);
                found.Add(new object[] { h, pid, t.ToString(), c.ToString(), r.Left, r.Top, r.Right - r.Left, r.Bottom - r.Top });
            }
            return true;
        }, IntPtr.Zero);
        return found;
    }

    public static void Save(IntPtr hwnd, int w, int h, string path) {
        using (var bmp = new Bitmap(w, h))
        using (var g = Graphics.FromImage(bmp)) {
            IntPtr dc = g.GetHdc();
            PrintWindow(hwnd, dc, 2);  // PW_RENDERFULLCONTENT
            g.ReleaseHdc(dc);
            bmp.Save(path, System.Drawing.Imaging.ImageFormat.Png);
        }
    }
}
'@

$procs = @(Get-Process -Name $ProcessName -ErrorAction SilentlyContinue)
if (-not $procs) { Write-Host "No process named $($ProcessName -join ', ')."; return }
if ($OutDir) { New-Item -ItemType Directory -Force $OutDir | Out-Null }
$names = @{}; foreach ($p in $procs) { $names[[uint32]$p.Id] = $p.ProcessName }
$i = 0
foreach ($w in [WindowSnapshot]::List([uint32[]]$names.Keys)) {
    $i++
    $hwnd, $wpid, $title, $class, $x, $y, $width, $height = $w
    Write-Host ("{0} (pid {1}): '{2}' class {3} at {4},{5} size {6}x{7}" -f $names[$wpid], $wpid, $title, $class, $x, $y, $width, $height)
    if ($OutDir -and $width -gt 0 -and $height -gt 0) {
        $file = Join-Path $OutDir ("{0:00} {1} {2}.png" -f $i, $names[$wpid], ($title -replace '[\\/:*?"<>|]', '_'))
        try { [WindowSnapshot]::Save($hwnd, $width, $height, $file) } catch { Write-Host "  no picture: $($_.Exception.Message)" }
    }
}
if ($i -eq 0) { Write-Host "No visible window of $($ProcessName -join ', ')." }
