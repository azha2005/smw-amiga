param([string]$Folder,[int]$Limit=300)
$ErrorActionPreference='Stop'
$cfg=Join-Path $Folder 'run.uae'
# WinUAE es la interfaz del emulador solicitada para evidencia visual.
# El helper PowerShell se lanza oculto; la ventana propia permite PrintWindow.
$proc=Start-Process -FilePath 'C:\Program Files\WinUAE\winuae64.exe' -ArgumentList @('-f', ('"'+$cfg+'"')) -PassThru
Set-Content (Join-Path $Folder 'pid.txt') $proc.Id
try {
  $until=(Get-Date).AddSeconds($Limit)
  while ((Get-Date) -lt $until -and -not $proc.HasExited -and -not (Test-Path (Join-Path $Folder 'close.flag'))) { Start-Sleep -Seconds 2; $proc.Refresh() }
} finally {
    Add-Type -AssemblyName System.Drawing
    Add-Type @"
using System;using System.Runtime.InteropServices;
public static class D1Shot {
 [StructLayout(LayoutKind.Sequential)]public struct RECT {public int L,T,R,B;}
 [DllImport("user32.dll")]public static extern bool GetWindowRect(IntPtr h,out RECT r);
 [DllImport("user32.dll")]public static extern bool PrintWindow(IntPtr h,IntPtr dc,uint f);
}
"@
    $proc.Refresh();$h=$proc.MainWindowHandle
    if ($h -ne [IntPtr]::Zero) {
        $rect=New-Object D1Shot+RECT
        [D1Shot]::GetWindowRect($h,[ref]$rect)|Out-Null
        if (($rect.R-$rect.L) -gt 0 -and ($rect.B-$rect.T) -gt 0) {
            $bmp=New-Object System.Drawing.Bitmap ($rect.R-$rect.L),($rect.B-$rect.T)
            $g=[System.Drawing.Graphics]::FromImage($bmp);$dc=$g.GetHdc()
            $ok=[D1Shot]::PrintWindow($h,$dc,2);$g.ReleaseHdc($dc);$g.Dispose()
            if ($ok) {$bmp.Save((Join-Path $Folder 'final.png'),[System.Drawing.Imaging.ImageFormat]::Png)}
            $bmp.Dispose()
        }
    }
  if (-not $proc.HasExited) { $proc.CloseMainWindow() | Out-Null; if (-not $proc.WaitForExit(6000)) { $proc.Kill() } }
}
