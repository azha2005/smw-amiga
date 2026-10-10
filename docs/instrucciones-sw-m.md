# SW-M — la moneda de Yoshi: la animación de paleta

2026-10-10. Sale de SW1 (`informe-sw1-1010.md`, punto 9). **Fácil**: unas
pocas escrituras por foto, solo con monedas en pantalla.

## Por qué

En 12 fotos la moneda de Yoshi sale con otro tono (≈ 100 px por moneda).

- P22: `CODE_00A418` pisa **todos los frames** el color 4 de la paleta 6
  con `PALETTE_Flashing[(wm_FrameB & $1C) >> 1]`, 8 pasos (`$02DF $27FF
  $73FF $27FF $01BF $001B $0018 $001F`) que cambian cada 4 frames.
- El port toma un solo paso (`palette.COIN_ANIM_REF = 1`, `$27FF`) y lo
  deja fijo en los datos del scroll. Coincide 1 de cada 8 fotos.

Los colores de la capa 1 llegan a las listas así:

- `D_INI`: la carga inicial;
- `D_CHG`: entradas de 8 B (`x`, desplazamiento en la lista, color
  nuevo, color viejo), que `apply_colors` (`scroll.s:609`) escribe o
  deshace según la cámara, en las 2 o 3 listas.

## Pasos

1. **Dónde está el color.** En `mkscroll.py`, al armar `D_INI` y `D_CHG`,
   marcar cada palabra de color cuyo origen sea el CGRAM `$32` (paleta 6,
   color 4). Por origen, no por valor: otro color puede valer lo mismo en
   12 bits.
2. **Una sección nueva en `yi1_s.dat`:** `D_COIN`, con la lista de
   punteros (relativos a la base) a esas palabras de `D_INI`/`D_CHG`, y
   el campo nuevo de la cabecera (`D_W`… `D_LNS` en `scroll.s:174`;
   agregar al final, sin mover los demás).
3. **En cada foto** (en el render, no en la lógica: O5):
   - el paso = `(wm_FrameB & $1C) >> 1` del **frame de la foto**. Hace
     falta capturarlo en el registro de la foto (`dc_capture`, un `R_*`
     nuevo de 1 byte); la RAM de la lógica ya va adelantada (P97);
   - si cambió desde la última foto dibujada en esa lista: escribir el
     color de 12 bits (`snes_to_amiga12` de la tabla, precalculada) en
     todas las palabras de `D_COIN`. Así `apply_colors` ya escribe el
     color correcto cuando la cámara se mueve;
   - y en las palabras de la lista que hoy muestran ese color (las de
     `D_INI` y las de `D_CHG` ya aplicadas): guardar con cada entrada de
     `D_COIN` su desplazamiento en la lista y escribirlo en la lista de
     atrás.
   - P89 (no editar listas en el sitio) habla de ediciones masivas. Esto
     son unas pocas palabras; medirlo igual.
4. **La referencia Python** (lo que dibuja `g5l.py`/`scrollsim` para
   las capturas) tiene que animar igual, o las puertas de las capturas
   viejas cambian: `palette.build_cgram(coin_frame=...)` con el paso de
   cada foto.

## Puertas

- SW1 repetida: **las 12 fotos de la moneda, exactas** (fuera de la
  barra de estado).
- `scroll_check.py`/`cmp_ref`: sin cambios (comparan con el paso de la
  referencia; usar `coin_frame=COIN_ANIM_REF` donde haga falta).
- Ciclos: el coste por foto medido (`-DBENCH`); tiene que ser ruido.
- Regresión completa y lint.

## Trampas

- P22, P23.
- P74: tablas grandes dentro de `scroll.s` rompen `game.s`; `D_COIN` va
  en `yi1_s.dat`, no en el código.
- P97: la foto y la lógica no son el mismo frame.
- P48: lo que se agrega delante de los datos del C los corre.
