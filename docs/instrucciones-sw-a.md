# SW-A — los tiles animados de la capa 1 (los postes del punto medio)

2026-10-10. Sale de SW1 (`informe-sw1-1010.md`, punto 3). **Fácil**: son
solo datos, con 0 ciclos en la Amiga.

## Por qué

En 9 fotos de la barrida (k 4899-5399) faltan los dos postes del punto
medio. La cinta sí se ve. Los postes no son sprites (la OAM de la SNES no
los tiene) sino capa 1: bloques Map16 `$2F`-`$34` de `h_midway_point`
(`mklvl.py`). Las palabras son:

| bloque | cuadrantes (tile, paleta, prioridad) |
|---|---|
| `$2F` | `$F8`/2, `$F8`/2, **`$74`/4**, **`$75`/4** |
| `$30` | `$F8`/2, `$F8`/2, `$75`/4, `$75`/4 |
| `$31` | `$F8`/2, `$F8`/2, `$75`/4, `$77`/4 |
| `$32`-`$34` | **`$74`-`$77`/7, prioridad 1**, `$F8`/6 |

Los tiles `$74`-`$77` **no están en el GFX estático**. Los sube en cada
frame la rutina de tiles animados:

- `CODE_05BB39` (`dialog.s:445`) elige con `wm_FrameB & 7` tres
  ranuras de VRAM de `DATA_05B93B`. `$0740` es el tile `$74`.
- Para cada ranura toma el origen de `AnimatedTileData` (`dialog.s:389`)
  según el paso (`wm_FrameB & $18`) y, en algunas ranuras, el tileset
  (`DATA_05B96B`, `DATA_05B98B`) o el interruptor P (`DATA_05B97D`,
  `wm_BluePowTimer`).
- `CODE_00A390` (`game.s:4096`) copia 128 B (4 tiles) desde el banco
  `$7E` a la VRAM.
- El origen es el GFX 33 ("Animations", 3 bpp, `graphics.txt:59`)
  descomprimido en la WRAM.

`mklvl.load_gfx` (que usan `mklvl.py` y `mkscroll.py`) toma los tiles
del GFX estático, donde esas ranuras están vacías. Por eso ni la
referencia `mklvl` dibuja los postes, aunque `m16diff` da 100 %: compara
índices, no píxeles. Es la misma trampa que P23 (la moneda de Yoshi).

## Pasos

1. **La verdad, desde la SNES.**
   - Agregar a `snesorc` un `--vram` que, con `--shots`, vuelque la VRAM
     (64 KB) del frame pedido junto a la pantalla (`snes_<f>.vram`).
     Mismo cuidado que `shot_frame`: no tocar el estado.
   - Volcar 8 frames seguidos de yi1 (un ciclo de `wm_FrameB & 7`) y 4
     pasos de `& $18`.
   - Con eso se sabe qué tiles de 4 bpp hay en cada ranura animada, en
     cada paso.
2. **El inventario.** ¿Qué tiles de la capa 1 de YI1 caen en ranuras
   animadas?
   - Recorrer los bloques Map16 que usa el nivel (`mklvl.build`) y listar
     sus tiles que estén en alguna ranura de `DATA_05B93B` (`$40`-`$83`,
     `$DA`-`$DD` y `$EA`-`$ED`; confirmarlo con la tabla).
   - Para cada una: si su contenido cambia con el paso (animación de
     verdad: monedas, bloque `?`) o es fijo (los postes, probablemente).
3. **En la tubería de assets** (`mklvl.load_gfx` o una función nueva que
   la envuelva):
   - reproducir `CODE_05BB39`: el GFX 33 de 3 bpp pasado a 4 bpp como lo
     hace el ROM, en la dirección de WRAM que lee `AnimatedTileData`
     (hay que localizar la descompresión y la conversión en el ROM; el
     volcado del paso 1 dice si el resultado es correcto);
   - poner en cada ranura el frame que corresponde al tileset 7;
   - **puerta:** los tiles generados, byte por byte iguales a la VRAM
     volcada en el paso 1.
4. **Animados de verdad** (si el inventario encuentra alguno visible en
   YI1, como los bloques `?`): por ahora, el paso que captura la
   referencia, como `COIN_ANIM_REF`. Animarlos de verdad es otra
   tarjeta: cuesta blits.
5. **Colores:** `mkscroll.py` tiene que poder asignar los colores de las
   paletas 4 y 7 en las líneas de los postes (7 colores por línea en
   PF1). Si no entran, el informe lo dice y se decide.
6. **Prioridad:** la columna derecha (`$32`-`$34`) tiene prioridad 1:
   en la SNES, Mario pasa **detrás** del poste de adelante. En el port
   la capa 1 siempre queda detrás de los sprites. Anotarlo como
   diferencia residual. Con SW-P se podría hacer igual que con la
   piraña, pero para Mario (sprites 0-3); no entra en esta tarjeta.

## Puertas

- La puerta del paso 3 (tiles iguales a la VRAM).
- `mklvl.py` + `m16diff.py`: 6111/6111. `cmp_ref` no tiene que empeorar.
- SW1 repetida (`sweep_cmp.py`, `informe-sw1-1010.md` §4): **las 9
  fotos de los postes, exactas** salvo la barra de estado y lo que ya
  difería por otra causa (el píxel de la fila 185 de SW-D).
- Regresión completa y lint.

## Trampas

- P9, P11: los ID de los GFX y su orden.
- P23: la moneda de Yoshi; la misma familia de problema.
- P5: LC_LZ2 con referencias absolutas.
- P28: el ROM reapunta entradas Map16 según la pantalla.
- R9: los tiles generados van a `work/`, nunca a git.
