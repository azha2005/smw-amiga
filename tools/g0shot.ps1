<# Captura privada G0: mismo shot.ps1 y timing Exact. Inicia Hidden; el HWND
   se vuelve dibujable sin activar foco y se coloca detras de otras ventanas.
   Una ventana totalmente oculta no renderiza y PrintWindow devuelve negro.
   Cierra solo el PID propio. No altera tools/shot.ps1 ni otros worktrees.

   .\tools\g0shot.ps1 -Adf work\bench_g0.adf -Out work\bench_g0.png -Wait 25
#>
param([Parameter(Mandatory=$true)][string]$Adf,
      [Parameter(Mandatory=$true)][string]$Out,
      [int]$Wait=25)
$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path -Parent $PSScriptRoot
$sourcePath = Join-Path $PSScriptRoot 'shot.ps1'
$source = Get-Content -LiteralPath $sourcePath -Raw
$extra = @'
    public delegate bool EnumProc(IntPtr h, IntPtr arg);
    [DllImport("user32.dll")] public static extern bool EnumWindows(EnumProc proc, IntPtr arg);
    [DllImport("user32.dll")] public static extern uint GetWindowThreadProcessId(IntPtr h, out uint pid);
    [DllImport("user32.dll")] public static extern bool ShowWindow(IntPtr h, int cmd);
    [DllImport("user32.dll")] public static extern bool SetWindowPos(IntPtr h, IntPtr after, int x, int y, int w, int ht, uint flags);
    public static IntPtr WindowFor(int wanted) {
        IntPtr found = IntPtr.Zero;
        EnumWindows((h, a) => { uint pid; GetWindowThreadProcessId(h, out pid); RECT r;
            GetWindowRect(h, out r);
            if (pid == wanted && r.R-r.L >= 640 && r.B-r.T >= 512) { found=h; return false; }
            return true; }, IntPtr.Zero);
        return found;
    }
'@
$render = @'
for ($wi = 0; $wi -lt 40; $wi++) {
    $renderHwnd = [A5Shot]::WindowFor($proc.Id)
    if ($renderHwnd -ne [IntPtr]::Zero) {
        [A5Shot]::ShowWindow($renderHwnd, 4) | Out-Null
        [A5Shot]::SetWindowPos($renderHwnd, [IntPtr]::new(1), 0, 0, 0, 0, 0x13) | Out-Null
        break
    }
    Start-Sleep -Milliseconds 250
}
'@
foreach ($anchor in @('public static class A5Shot {', 'Log "pid $($proc.Id)"',
                     '$Process.MainWindowHandle', '-PassThru')) {
    if (-not $source.Contains($anchor)) { throw "shot.ps1 cambio: falta $anchor" }
}
$source = $source.Replace('-PassThru', '-WindowStyle Hidden -PassThru')
$source = $source.Replace('public static class A5Shot {', 'public static class A5Shot {' + $extra)
$source = $source.Replace('$Process.MainWindowHandle', '[A5Shot]::WindowFor($Process.Id)')
$source = $source.Replace('Log "pid $($proc.Id)"', 'Log "pid $($proc.Id)"' + "`n" + $render)
$workRoot = Join-Path $projectRoot 'work'
if (-not (Test-Path $workRoot)) { New-Item -ItemType Directory -Path $workRoot | Out-Null }
$privateScript = Join-Path $workRoot 'shot_g0.ps1'
Set-Content -LiteralPath $privateScript -Value $source -Encoding utf8
$lockPath = Join-Path (Split-Path -Parent $projectRoot) 'winuae_lock.ps1'
if (Test-Path $lockPath) {
    & $lockPath $privateScript -Exact -Adf $Adf -Out $Out -Wait $Wait
} else {
    & $privateScript -Exact -Adf $Adf -Out $Out -Wait $Wait
}
$outputPath = if ([IO.Path]::IsPathRooted($Out)) { $Out } else { Join-Path $projectRoot $Out }
if (-not (Test-Path -LiteralPath $outputPath)) { throw "No se genero la captura $outputPath" }
