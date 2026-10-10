# G5L-R-L2 — la lógica en C a asm, por partes (opción A)

2026-10-10. **Solo si el usuario elige la opción A** de `PROXIMO.md`
(`docs/informe-g5l-r-l1-1010.md` §4). Toca `player/*.c` y `player/logic68k.s`.

## Por qué existe

Después de S9 quedan 12 omitidas. La lógica es plana; según el modelo,
≤ 5 pide −20 % de toda la lógica (≈ 8,6 k de 43 k ciclos por foto). El C
suma ~21 k por foto: es lo único que no pasó por asm a mano.

## Reglas

- Worktree `C:/Users/JC/Downloads/sma/wt-g2t-b2bis-1008`, rama
  `g2t-b2bis`; sin merge ni push; builds en serie; una WinUAE midiendo; R9.
- **V1**: cada función pasada se verifica con `marioverify` (PC) y
  `m68kverify` (68000); `regress.py` las cruza (`cruce full/loop/RAM
  PC=68000`, `game.diferencias` 0, oráculos `orc.*` exactos). Ninguna
  métrica empeora.
- vbcc: P36, P37, P38, P47, P62. asm: P40, P73, P88, P94, P102; ABI de vbcc
  (`d0-d1/a0-a1` de trabajo); cabeceras `registros destruidos` (V3).
- Cómo se hizo antes: L1a/L1b/L1c/MA1 (`docs/archivo/sesiones.md`, P79,
  P88, P92, P109).

## Partida verde

```sh
export PATH="$TEMP/pyshim:/c/msys64/ucrt64/bin:$PATH" VBCC=/c/Users/JC/vbcc PY=python
python tools/lint_port.py                       # RESULTADO: OK
python tools/regress.py --baseline tools/baseline_pc.json --level --g5l --bm1   # RESULTADO: OK
python tools/g5l.py game --bin work/s9/replay/game.bin --lst work/s9/replay/game.lst \
    --pcprof work/l/prof.json --pclogic 1020-1130,1690-1715,2050-2080,2730-2760,3280-3370,4195-4225
python tools/l_funcs.py work/l/prof.json work/s9/replay/game.lst work/s9/frames.json 40
#   fotos 321, 49448 por foto
```

## Pasos

1. Orden por ciclos (`l_funcs.py`): `_level_frame` (2,7 k, `manim.c`),
   las cuatro de `mcoll.c` (`mcoll_l590`, `l784`, `l834`, `l424`: 3,9 k),
   `_banzai_gfx` (1,45 k), `_sprites_all` (1,4 k), `_mario_D5F2`,
   `_mario_player`, `manim_l116`, `spr_gfx_l127`, `msprite_l125`,
   `_get_draw_info1`, `_mario_spr_interact`. Antes de cada una, ver por
   qué cuesta (`q_report.py`-style por línea): a veces es una llamada que
   se evita, no la función.
2. Por función: asm en `logic68k.s` con la misma interfaz, el C queda de
   referencia (como `mspr.c`/`mspr68k.s`). `regress.py` verde y el ahorro
   medido con `--pclogic` + `l_funcs.py`. Si ahorra menos del 25 % de la
   función, revertir.
3. Cada 3-4 funciones: el modelo (`t2_model.py` con las fotos nuevas) y,
   si baja, **WinUAE** BENCH y VBTRACE (base: 36 fotos, 12 omitidas).
4. Red: lint, regress, los cinco MD5, memmap.

## Paradas

- Un cruce PC = 68000 o un oráculo deja de ser exacto → revertir esa
  función.
- BENCH o VBTRACE empeoran → parar y avisar.

## Informe

`docs/informe-g5l-r-l2-<fecha>.md`: por función, ciclos antes/después;
la lógica por foto; el modelo y WinUAE; cuánto falta para ≤ 5. Cerrar
según ROADMAP §7.
