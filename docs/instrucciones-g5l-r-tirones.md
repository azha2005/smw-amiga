# G5L-R-T — bajar los tirones que quedan del Rex

2026-10-09. Sigue a `docs/informe-g5l-r-1009.md` (léase antes, §3-§4).

## Por qué existe

Con G5L-R y el colchón (`-DG5L -DCUSHION`) el replay de YI1 pierde **67
fotos** en WinUAE cycle-exact (`052dac2`); el control sin enemigos, 27.
Cada repetición de imagen se paga con un salto unos frames después (P115):
el usuario lo ve como "el Rex salta pasos". Objetivo: acercar las fotos
perdidas al control (≤ 35 sería la mitad del exceso; 27 es el piso de
hoy) sin tocar la exactitud.

## Reglas que no se negocian

1. Worktree `wt-g2t-b2bis-1008` (o el que indique PROXIMO), sin merge ni
   push salvo pedido del usuario. Nada derivado de la ROM en git (R9).
2. `tools/g5l.py game` tiene que dar **G5L GAME: OK** después de cada
   cambio en `player/g5l.s`: es la prueba de que las listas del asm son
   las de la referencia. Una optimización que la rompe no cuenta.
3. Solo valen fotos medidas en WinUAE cycle-exact. Musashi orienta.
4. No compilar en paralelo (work/cc, includes y `work/g5l.i` se
   comparten). Una sola instancia de WinUAE midiendo a la vez.
5. Los 5 builds por defecto no cambian de binario.

## Entorno y partida en verde (Git Bash, desde el worktree)

```sh
export PATH="/c/msys64/ucrt64/bin:$PATH" VBCC=/c/Users/JC/vbcc PY=python
CDEFS='-DNOOAM -DSPR_OAM' GDEFS='-DREPLAY -DG5L' SPR_BANK=work/g3/bank OUT=work/g5l/rep sh tools/game_build.sh
python tools/g5l.py game | tail -1
# G5L GAME: OK
CDEFS='-DNOOAM -DSPR_OAM' GDEFS='-DREPLAY -DG5L -DCUSHION -DBENCH' SPR_BANK=work/g3/bank OUT=work/g5l/cb sh tools/game_build.sh
```

Si vasm da `error 2029` (salto corto fuera de rango) en `player/g5l.s`,
pasar ese `bxx.s` a largo. Si un `bsr` pasa a `jsr` absoluto ("ERROR
PIC"), usar `FBSR` en `game.s` o `GETBASE` + `add.l` (P102).

PowerShell (medida, ~4 min):

```powershell
& C:\Users\JC\Downloads\sma\winuae_lock.ps1 .\tools\shot.ps1 -Exact -Adf work\g5l\cb\game.adf -Out work\g5l\cb\shot.png -Wait 190
```
```sh
python tools/game_read.py --shot work/g5l/cb/shot.png --auto | tail -9
# fotos perdidas : 67 (1.06 %), racha 1, VBL sin imagen nueva 69
```

## Pasos

1. **Dónde están los tirones hoy.** Armar con `-DCUSHION -DVBTRACE`
   (sin `-DBENCH`) y `python tools/vbtrace.py work/g5l/vt/game.adf
   work/g5l/vt/trace.bin 175`. Lista de VBL repetidos y fotos salteadas;
   tiene que reproducir las zonas del informe §4 (±).
2. **Perfil de esas fotos en Musashi.** `tools/g5l.py game` da el
   máximo y la media por rutina; para un tramo, el bucle de `run_game`
   con `fr.call(..., regions)` por foto (así se midió en el informe).
3. **Fase con puerta de medida — candidatos, en este orden** (cada uno
   con G5L GAME OK y una medida WinUAE; quedarse solo con lo que baja
   fotos):
   - `g5l_patch` (8-18 k): la clave por lista (`GV_RKA/B/C`) falla con 3
     listas rotando; probar un búfer de parche compartido por clave
     (variante + bandas) además del de la lista.
   - camino rápido fallido en los 4 mapas (5 k) cuando la caché del plan
     falla: ¿se puede saber antes, desde `GV_NEED` de la foto anterior?
   - sweep/plan con Mario moviéndose (fallos de caché): perfilar dentro
     de sweep (11-14 k) antes de reescribir.
   - `place`/`emit` (6-8 k cada una con camino completo).
4. Si después de dos candidatos medidos no baja de ~55 fotos, **parar** y
   llevarle al usuario los números (zonas, coste por rutina, techo
   estimado) antes de seguir.

## Puertas antes de cada commit

`python tools/lint_port.py` y `python tools/regress.py --baseline
tools/baseline_pc.json --level` en verde; `tools/g5l.py game` OK; los 5
hashes por defecto iguales (comparar `md5sum` de `game.bin` con
`GDEFS` = `-DREPLAY`, vacío, `-DREPLAY -DBENCH`, `-DREPLAY -DDECOUPLE`,
`-DREPLAY -DDECOUPLE -DBENCH`, contra el commit de partida).

## El informe

Fotos perdidas y VBL repetidos antes/después (WinUAE, con el control de
la misma tanda), la traza de vbtrace (zonas), coste por rutina en
Musashi, qué se probó y no sirvió, y la próxima palanca.
