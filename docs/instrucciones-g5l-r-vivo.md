# G5L-R-V — el colchón y G5L-R en el juego en vivo

2026-10-09. Sigue a `docs/informe-g5l-r-1009.md`. El usuario aceptó el
colchón (+20 ms) el 2026-10-09; hoy solo existe en el replay.

## Por qué existe

`player/game.s` falla a propósito con `-DCUSHION` sin `-DREPLAY`. Para
que el ADF jugable (U1) muestre a los Rex con la fluidez medida falta el
camino en vivo, y que `-DG5L -DCUSHION` pase a ser el build por defecto.

## Reglas que no se negocian

1. Las de `instrucciones-g5l-r-tirones.md` (G5L GAME OK, WinUAE para
   medir, sin builds paralelos, R9).
2. Hacer `-DG5L -DCUSHION` defecto **cambia los hashes por defecto**:
   eso se hace en un commit propio, al final, con la medida y el memmap
   delante; hasta entonces los 5 hashes no cambian.
3. Chip: con el colchón quedan ~40 KB (informe §2). Nada nuevo en chip
   sin `memmap.py` antes y después.

## Partida

```sh
export PATH="/c/msys64/ucrt64/bin:$PATH" VBCC=/c/Users/JC/vbcc PY=python
CDEFS='-DNOOAM -DSPR_OAM' GDEFS='-DG5L -DCUSHION' SPR_BANK=work/g3/bank OUT=work/g5l/live sh tools/game_build.sh
# hoy: fail "CUSHION (prueba) solo en el replay" y, en vivo,
# error 2030 en game.s ~1248: `move.b spr_lv(pc),d0` fuera de rango
# (el binario en vivo con el colchón crece: GETBASE + add.l, P102)
CDEFS='-DNOOAM -DSPR_OAM' GDEFS='-DG5L' SPR_BANK=work/g3/bank OUT=work/g5l/live sh tools/game_build.sh
# sin colchón, en vivo: compila (probado el 2026-10-09)
```

## Pasos (fase con puerta de medida)

1. Leer en `game.s` todo lo que toca `DC_PEND`, `DC_FRONT`, `DC_FLIST`
   y `V_BACK` fuera del replay: `dc_restart` (muerte y reinicio, Z1),
   el diagnóstico (`DIAG`, `diag_enter` elige "la lista que no es
   V_BACK": con tres listas no alcanza), la carga del nivel.
2. Quitar el `fail` y adaptar cada sitio a tres listas. `dc_act` = 0
   (carga/congelado) ya muestra la publicada sin esperar.
3. Puertas: ADF en vivo arranca, Mario se mueve con teclado (captura
   `tools/shot.ps1`), muerte y reinicio como en `docs/validacion-z1.md`,
   diagnóstico entra y sale; memmap sin violaciones.
4. Medir la latencia de entrada en frames (lectura del teclado → foto
   que se ve) y anotarla.
5. Con todo verde: commit propio que hace `-DG5L -DCUSHION` defecto en
   `tools/game_build.sh` (hashes nuevos registrados en el informe y en
   `regress.py` si los guarda).

Condición de parada: si el diagnóstico o el reinicio necesitan una cuarta
lista o más chip, parar y avisar con números.

## El informe

Qué sitios cambiaron, capturas, latencia medida, memmap, y los hashes
nuevos si se llegó al paso 5.
