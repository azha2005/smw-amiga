<# stress_ab_shots.ps1 - captura en WinUAE cycle-exact los ADF de
   tools/stress_ab_build.sh, en tres slots paralelos (cada uno con su copia
   de shot.ps1, sin pausa por foco) y por el candado comun.

   .\tools\stress_ab_shots.ps1 [-Prefix st]

   Cada captura queda en work\<prefijo>_<escenario>_<variante>\bench.png.
   Esperas: back 160 s, yi1 170 s, sprites 110 s (el BENCH deja los
   resultados en pantalla al terminar; esperar de mas no cambia nada).
   Despues: sh tools/stress_ab_read.sh <prefijo>. #>
param([string]$Prefix = 'st')
$ErrorActionPreference = 'Stop'
$proj = Split-Path -Parent $PSScriptRoot
$lock = Join-Path (Split-Path -Parent $proj) 'winuae_lock.ps1'
$runs = Get-ChildItem -Directory (Join-Path $proj 'work') |
    Where-Object { $_.Name -match "^$([regex]::Escape($Prefix))_(back|sprites|yi1)_(nooam|oam|g3)$" -and
                   (Test-Path (Join-Path $_.FullName 'game.adf')) } |
    ForEach-Object { $_.Name }
if (-not $runs) { throw "no hay work\${Prefix}_*\game.adf: correr antes tools/stress_ab_build.sh" }
$slots = @{ 'a' = @(); 'b' = @(); 'c' = @() }
$k = 0
foreach ($r in $runs) { $slots[@('a','b','c')[$k % 3]] += $r; $k++ }
$jobs = @()
foreach ($s in $slots.Keys) {
    if (-not $slots[$s]) { continue }
    $tools = Join-Path $proj "work\stslot\$s\tools"
    New-Item -ItemType Directory -Force -Path $tools | Out-Null
    New-Item -ItemType Directory -Force -Path (Join-Path $proj "work\stslot\$s\work") | Out-Null
    $src = Get-Content -Raw (Join-Path $PSScriptRoot 'shot.ps1')
    $src = $src.Replace("'use_gui=no'", "'win32.active_not_captured_pause=false'`n    'win32.inactive_pause=false'`n    'win32.iconified_pause=false'`n    'use_gui=no'")
    Set-Content -Encoding utf8 -Path (Join-Path $tools 'shot.ps1') -Value $src
    $jobs += Start-Job -ArgumentList $proj, $lock, $tools, $slots[$s] -ScriptBlock {
        param($proj, $lock, $tools, $list)
        foreach ($r in $list) {
            $wait = if ($r -like '*_back_*') { 160 } elseif ($r -like '*_yi1_*') { 170 } else { 110 }
            $dir = Join-Path $proj "work\$r"
            Remove-Item -ErrorAction SilentlyContinue (Join-Path $dir 'bench.png')
            & $lock (Join-Path $tools 'shot.ps1') -Exact -Adf (Join-Path $dir 'game.adf') `
                -Out (Join-Path $dir 'bench.png') -Wait $wait | Select-Object -Last 1
        }
    }
}
$jobs | Wait-Job | Receive-Job
$missing = $runs | Where-Object { -not (Test-Path (Join-Path $proj "work\$_\bench.png")) }
if ($missing) { Write-Output "FALTAN capturas: $($missing -join ', ')"; exit 1 }
Write-Output "STRESS_AB_SHOTS: OK ($($runs.Count) capturas)"
