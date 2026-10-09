<#
    shot.ps1 - arranca un ADF en WinUAE, captura la ventana y cierra.

        .\tools\shot.ps1 -Adf work\smw.adf -Out work\shot.png -Wait 25
        .\tools\shot.ps1 -Adf work\smw.adf -Out work\t.png -Wait 40 -Every 5
        .\tools\shot.ps1 -Exact -Wait 60     # temporizacion de A500 real

    Este script NO invoca ningun ejecutable de linea de comandos salvo
    WinUAE: solo escribe el .uae, lanza el emulador y captura con
    PrintWindow. Todo lo que hace queda en work\shot.log.

    La captura es de la VENTANA de WinUAE, no de la pantalla: PrintWindow
    pide a la ventana que se dibuje sola en un bitmap, asi que no importa
    que haya otra cosa encima y nunca se captura otra aplicacion.
#>
[CmdletBinding()]
param(
    [string]$Adf    = 'work\smw.adf',
    [string]$Out    = 'work\shot.png',
    [int]$Wait      = 25,
    [int]$Every     = 0,
    [string]$WinUAE = 'C:\Program Files\WinUAE\winuae64.exe',
    [string]$Rom    = 'C:\Users\JC\Downloads\amivideo\kick12.rom',
    [ValidateSet(0,2)][int]$SlowMem = 2,
    # Teclas reales del host a la ventana de WinUAE (SendInput por scancode;
    # llegan a la Amiga por el teclado emulado, no por PADTEST).  Formato:
    # "seg:down|up|tap:TECLA;..." con TECLA en RIGHT LEFT UP DOWN Z X A S
    # RETURN SPACE.  Los segundos cuentan desde el lanzamiento.  Exige -Every.
    [string]$Keys = '',
    # Sin -Exact el emulador va lo mas rapido posible (blits instantaneos): la
    # IMAGEN es correcta pero cualquier medida de tiempo es falsa.  Con -Exact
    # se usa la temporizacion de a500.uae (cycle-exact): es la unica config
    # valida para medir rendimiento (AGENTS.md §11).
    [switch]$Exact
)

$ErrorActionPreference = 'Continue'
$root = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
$work = Join-Path $root 'work'
if (-not (Test-Path $work)) { New-Item -ItemType Directory $work | Out-Null }
$script:LogPath = Join-Path $work 'shot.log'
Set-Content -Path $script:LogPath -Value ("shot.ps1  " + (Get-Date)) -Encoding utf8

function Log {
    param([string]$Text = '')
    Write-Host $Text
    Add-Content -Path $script:LogPath -Value $Text -Encoding utf8
}

if (-not [System.IO.Path]::IsPathRooted($Adf)) { $Adf = Join-Path $root $Adf }
if (-not [System.IO.Path]::IsPathRooted($Out)) { $Out = Join-Path $root $Out }

Log "ADF : $Adf"
Log "ROM : $Rom"
Log "OUT : $Out"

if (-not (Test-Path $Adf))    { Log "FALLO: no existe $Adf"; exit 2 }
if (-not (Test-Path $Rom))    { Log "FALLO: no existe $Rom"; exit 2 }
if (-not (Test-Path $WinUAE)) { Log "FALLO: no existe $WinUAE"; exit 2 }

# --- config: A500 PAL, OCS, 512K chip + 512K slow (A501), KS 1.2 ---------
$cfg = Join-Path $work 'shot.uae'
$lines = @(
    'config_description=SMW port-demo - A500 PAL 512K+512K A501 KS1.2'
    'chipset=ocs'
    'chipset_compatible=A500'
    'ntsc=false'
    'cpu_type=68000'
    'cpu_model=68000'
    'chipmem_size=1'
    "bogomem_size=$SlowMem"
    'fastmem_size=0'
    'z3mem_size=0'
    "kickstart_rom_file=$Rom"
    "floppy0=$Adf"
    'floppy0type=0'
    'floppy0wp=false'
    'nr_floppies=1'
    'floppy_speed=100'
    # 720x568 es la ventana que da escala EXACTAMENTE 2x sobre la pantalla
    # PAL 320x256 (comprobado con autocorrelacion: paso de tile = 16 px de
    # pantalla para 8 px Amiga).  Con esta config, la captura recortada en
    # (67,70) + 640x512 coincide PIXEL A PIXEL con el oraculo del PC
    # (render_dat.py --scale 2): 100.00% de pixeles identicos.
    # No cambiar estos valores sin volver a medir el offset del recorte.
    'gfx_width=720'
    'gfx_height=568'
    'gfx_lores=true'
    'gfx_linemode=double'
    'gfx_framerate=10'
    'win32.start_not_captured=true'
    'win32.nonotificationicon=true'
    'use_gui=no'
)
# Temporizacion: rapida (solo imagen) o la de a500.uae (para medir).
if ($Exact) {
    $lines += @('cpu_compatible=true', 'cpu_speed=real', 'cycle_exact=true',
                'cpu_cycle_exact=true', 'cpu_memory_cycle_exact=true',
                'blitter_cycle_exact=true', 'immediate_blits=false', 'cachesize=0')
    Log "TIEMPO : cycle-exact (valido para medir)"
} else {
    $lines += @('cpu_compatible=false', 'cpu_speed=max', 'cycle_exact=false',
                'blitter_cycle_exact=false', 'immediate_blits=true')
    Log "TIEMPO : rapido (la imagen vale, los tiempos NO)"
}
Set-Content -Path $cfg -Value $lines -Encoding ascii
Log "CFG : $cfg"

# --- captura -------------------------------------------------------------
Add-Type -AssemblyName System.Drawing
if (-not ('A5Shot' -as [type])) {
    Add-Type @"
using System;
using System.Runtime.InteropServices;
public static class A5Shot {
    [StructLayout(LayoutKind.Sequential)]
    public struct RECT { public int L, T, R, B; }
    [DllImport("user32.dll")] public static extern bool GetWindowRect(IntPtr h, out RECT r);
    [DllImport("user32.dll")] public static extern bool IsIconic(IntPtr h);
    [DllImport("user32.dll")] public static extern bool ShowWindow(IntPtr h, int command);
    [DllImport("user32.dll")] public static extern bool PrintWindow(IntPtr h, IntPtr hdc, uint flags);
    [DllImport("user32.dll")] public static extern bool SetProcessDPIAware();
    [DllImport("user32.dll")] public static extern IntPtr SetThreadDpiAwarenessContext(IntPtr context);
}
"@
}
[A5Shot]::SetProcessDPIAware() | Out-Null

function Save-Shot {
    param($Process, [string]$Path)
    # PowerShell puede tener ya fijada la DPI del proceso. La del hilo
    # evita rectangulos virtualizados en monitores con escala de 125%.
    [A5Shot]::SetThreadDpiAwarenessContext([IntPtr](-4)) | Out-Null
    $h = [IntPtr]::Zero
    for ($i = 0; $i -lt 30; $i++) {
        $Process.Refresh()
        $h = $Process.MainWindowHandle
        if ($h -ne [IntPtr]::Zero) { break }
        Start-Sleep -Milliseconds 500
    }
    if ($h -eq [IntPtr]::Zero) { Log "FALLO: WinUAE no tiene ventana"; return $false }
    # La ventana puede existir sin area de cliente todavia (se vio una
    # captura de 199x34: solo la barra de titulo).  Esperar a que tenga al
    # menos el tamano de la pantalla escalada (640x512) antes de capturar.
    $r = New-Object A5Shot+RECT
    for ($i = 0; $i -lt 20; $i++) {
        $Process.Refresh()
        $h = $Process.MainWindowHandle
        if ([A5Shot]::IsIconic($h)) { [A5Shot]::ShowWindow($h, 9) | Out-Null }
        [A5Shot]::GetWindowRect($h, [ref]$r) | Out-Null
        if (($r.R - $r.L) -ge 640 -and ($r.B - $r.T) -ge 512) { break }
        Start-Sleep -Milliseconds 1000
    }
    $w = $r.R - $r.L
    $ht = $r.B - $r.T
    if ($w -lt 640 -or $ht -lt 512) { Log "FALLO: ventana de tamano $w x $ht (sin contenido)"; return $false }
    $bmp = New-Object System.Drawing.Bitmap $w, $ht
    $g = [System.Drawing.Graphics]::FromImage($bmp)
    $hdc = $g.GetHdc()
    $ok = [A5Shot]::PrintWindow($h, $hdc, 2)   # 2 = PW_RENDERFULLCONTENT
    $g.ReleaseHdc($hdc)
    $g.Dispose()
    if (-not $ok) { $bmp.Dispose(); Log "FALLO: PrintWindow"; return $false }
    $bmp.Save($Path, [System.Drawing.Imaging.ImageFormat]::Png)
    $bmp.Dispose()
    Log ("captura -> $Path  ($w x $ht)")
    return $true
}

Log "lanzando WinUAE..."
$uaeArgs = @('-f', "`"$cfg`"")
# RawInput no ve bien las teclas de SendInput: con -Keys el teclado va por
# DirectInput/mensajes de Windows.
if ($Keys -ne '') { $uaeArgs += '-norawinput_keyboard' }
$proc = Start-Process -FilePath $WinUAE -ArgumentList $uaeArgs -PassThru
Log "pid $($proc.Id)"

if ($Keys -ne '' -and -not ('A5Keys' -as [type])) {
    Add-Type @"
using System;
using System.Runtime.InteropServices;
public static class A5Keys {
    [StructLayout(LayoutKind.Sequential)]
    public struct KEYBDINPUT { public ushort wVk, wScan; public uint dwFlags, time; public IntPtr extra; }
    [StructLayout(LayoutKind.Explicit, Size = 40)]
    public struct INPUT { [FieldOffset(0)] public uint type; [FieldOffset(8)] public KEYBDINPUT ki; }
    [DllImport("user32.dll", SetLastError = true)] public static extern uint SendInput(uint n, INPUT[] i, int size);
    [DllImport("user32.dll")] public static extern bool SetForegroundWindow(IntPtr h);
    [DllImport("user32.dll")] public static extern IntPtr GetForegroundWindow();
    [DllImport("user32.dll")] public static extern void keybd_event(byte vk, byte scan, uint flags, UIntPtr extra);
    public static uint Key(ushort scan, bool ext, bool up) {
        INPUT[] a = new INPUT[1];
        a[0].type = 1;
        a[0].ki.wScan = scan;
        a[0].ki.dwFlags = 8u | (ext ? 1u : 0u) | (up ? 2u : 0u);   // SCANCODE
        return SendInput(1, a, Marshal.SizeOf(typeof(INPUT)));
    }
    [DllImport("user32.dll")] public static extern uint GetWindowThreadProcessId(IntPtr h, IntPtr pid);
    [DllImport("kernel32.dll")] public static extern uint GetCurrentThreadId();
    [DllImport("user32.dll")] public static extern bool AttachThreadInput(uint a, uint b, bool attach);
    [DllImport("user32.dll")] public static extern bool BringWindowToTop(IntPtr h);
    [DllImport("user32.dll")] public static extern void SwitchToThisWindow(IntPtr h, bool alt);
    [DllImport("user32.dll")] public static extern IntPtr SetFocus(IntPtr h);
    public static bool Front(IntPtr h) {
        if (GetForegroundWindow() == h) return true;
        // Windows solo deja cambiar el foco al hilo que tiene la entrada:
        // se engancha la cola de entrada del hilo en primer plano.
        uint me = GetCurrentThreadId();
        uint fg = GetWindowThreadProcessId(GetForegroundWindow(), IntPtr.Zero);
        uint tg = GetWindowThreadProcessId(h, IntPtr.Zero);
        AttachThreadInput(me, fg, true);
        AttachThreadInput(me, tg, true);
        keybd_event(0x12, 0, 0, UIntPtr.Zero);       // ALT: permite el foco
        keybd_event(0x12, 0, 2, UIntPtr.Zero);
        BringWindowToTop(h);
        SetForegroundWindow(h);
        SwitchToThisWindow(h, true);
        SetFocus(h);
        AttachThreadInput(me, tg, false);
        AttachThreadInput(me, fg, false);
        return GetForegroundWindow() == h;
    }
}
"@
}
$scan = @{ RIGHT = @(0x4D, $true); LEFT = @(0x4B, $true); UP = @(0x48, $true);
           DOWN = @(0x50, $true); Z = @(0x2C, $false); X = @(0x2D, $false);
           A = @(0x1E, $false); S = @(0x1F, $false); RETURN = @(0x1C, $false);
           SPACE = @(0x39, $false) }
$events = @()
foreach ($e in ($Keys -split ';' | Where-Object { $_ -ne '' })) {
    $p = $e.Split(':')
    $k = $p[2].ToUpper()
    if (-not $scan.ContainsKey($k)) { Log "FALLO: tecla desconocida $k"; exit 2 }
    if ($p[1] -eq 'tap') {
        $events += [pscustomobject]@{ T = [double]$p[0]; Up = $false; K = $k }
        $events += [pscustomobject]@{ T = [double]$p[0] + 0.15; Up = $true; K = $k }
    } else {
        $events += [pscustomobject]@{ T = [double]$p[0]; Up = ($p[1] -eq 'up'); K = $k }
    }
}
$events = @($events | Sort-Object T)

if ($Every -gt 0) {
    $base = [System.IO.Path]::ChangeExtension($Out, $null).TrimEnd('.')
    $t0 = Get-Date
    $ei = 0
    for ($t = $Every; $t -le $Wait; $t += $Every) {
        while ($ei -lt $events.Count -and $events[$ei].T -le $t) {
            $ev = $events[$ei]
            $left = $ev.T - ((Get-Date) - $t0).TotalSeconds
            if ($left -gt 0) { Start-Sleep -Milliseconds ([int]($left * 1000)) }
            $proc.Refresh()
            $fg = [A5Keys]::Front($proc.MainWindowHandle)
            $s = $scan[$ev.K]
            $n = [A5Keys]::Key([uint16]$s[0], [bool]$s[1], [bool]$ev.Up)
            Log ('tecla {0:f2}s {1} {2} (foco={3}, enviados={4})' -f ((Get-Date) - $t0).TotalSeconds, $ev.K, $(if ($ev.Up) {'up'} else {'down'}), $fg, $n)
            $ei++
        }
        $left = $t - ((Get-Date) - $t0).TotalSeconds
        if ($left -gt 0) { Start-Sleep -Milliseconds ([int]($left * 1000)) }
        if ($events.Count -gt 0) {
            $proc.Refresh()
            Log ('foco {0}s = {1}' -f $t, [A5Keys]::Front($proc.MainWindowHandle))
        }
        Save-Shot $proc ('{0}_{1:d3}s.png' -f $base, $t) | Out-Null
    }
} else {
    # Borrar la captura anterior: si esta falla, verify_shot.py no puede
    # comparar (y aprobar) una imagen vieja.
    if (Test-Path $Out) { Remove-Item $Out -Force }
    Log "esperando $Wait s..."
    Start-Sleep -Seconds $Wait
    $script:shotOk = Save-Shot $proc $Out
}

if (-not $proc.HasExited) {
    $proc.CloseMainWindow() | Out-Null
    if (-not $proc.WaitForExit(6000)) { $proc.Kill(); $proc.WaitForExit(4000) | Out-Null }
}
Log "fin"
if ($Every -eq 0 -and -not $script:shotOk) { exit 1 }
