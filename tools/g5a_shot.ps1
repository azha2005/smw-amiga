<# Captura G5a, timing Exact de shot.ps1, PID propio y candado G0.
   Pausa por foco verificada en fuente oficial WinUAE od-win32/win32.cpp.
   No cambia la configuración del proyecto ni los procesos de otras tarjetas. #>
param([Parameter(Mandatory=$true)][string]$Adf,
      [Parameter(Mandatory=$true)][string]$Out,
      [int]$Wait=90,
      [ValidatePattern('^[a-z0-9]+$')][string]$Slot='main')
$ErrorActionPreference='Stop'
$projectRoot=Split-Path -Parent $PSScriptRoot
$source=Get-Content -LiteralPath (Join-Path $PSScriptRoot 'g0shot.ps1') -Raw
$anchor='$source = $source.Replace(''Log "pid $($proc.Id)"'', ''Log "pid $($proc.Id)"'' + "`n" + $render)'
if (-not $source.Contains($anchor)) { throw 'g0shot.ps1 cambió' }
$addition=@'
$source = $source.Replace("'use_gui=no'", "'win32.active_not_captured_pause=false'`n    'win32.inactive_pause=false'`n    'win32.iconified_pause=false'`n    'use_gui=no'")
'@
$source=$source.Replace($anchor,$anchor+"`n"+$addition)
# La copia va en tools privado para conservar projectRoot del wrapper.
$slotRoot=Join-Path $projectRoot ('work/g5a-capture-'+$Slot)
$slotTools=Join-Path $slotRoot 'tools'
New-Item -ItemType Directory -Path $slotTools -Force | Out-Null
Copy-Item -LiteralPath (Join-Path $PSScriptRoot 'shot.ps1') -Destination (Join-Path $slotTools 'shot.ps1') -Force
# Candado absoluto: el slot tiene otra carpeta padre.
$lockPath=Join-Path (Split-Path -Parent $projectRoot) 'winuae_lock.ps1'
$source=$source.Replace('$lockPath = Join-Path (Split-Path -Parent $projectRoot) ''winuae_lock.ps1''',
                        '$lockPath = '''+$lockPath+'''')
$private=Join-Path $slotTools 'g5a_private.ps1'
Set-Content -LiteralPath $private -Value $source -Encoding utf8
$adfFull=if([IO.Path]::IsPathRooted($Adf)){$Adf}else{Join-Path $projectRoot $Adf}
$outFull=if([IO.Path]::IsPathRooted($Out)){$Out}else{Join-Path $projectRoot $Out}
& $private -Adf $adfFull -Out $outFull -Wait $Wait
