# PRÓXIMO — lo que sigue

2026-10-11. **G7-3c hecha: el productor de efectos está entero en 68000**
(camino corto, capas 1-2, ventana `player/g7win.s` y EDF `player/g7edf.s`).
Es igual a la especificación `tools/g7_fast.py` en las cinco trazas (0
diferencias, el diario repone la lista byte a byte). **Sigue opt-in
`-DG7_BOBS`, no activa por defecto.** Fotos sin plan: YI1 40 (meta), chuck
6, las demás 0. Informe: `docs/informe-g7-3c-1011.md`.

## 1. Decisión pendiente del usuario

El productor PF1 **no cabe en el frame** (≈ 141.800 ciclos): YI1 media
56 k, p99 1,04 M, máx. 3,0 M (sin DMA). Las filas por ventana/EDF cuestan
100-200 k cada una, y el camino corto tiene un suelo de 8-10 k por fila.
Opciones:

- **(a) híbrido con sprites de hardware** (medido en G7-S0,
  `docs/informe-g7-s0-1011.md`): deja 0,05-0,83 filas PF1 por foto de media
  y 12-16 en el peor caso. Es la que más reduce el trabajo (recomendada);
  instrucciones en `docs/instrucciones-g7-s1.md`;
- (b) presupuesto de G7 por frame y fotos omitidas en ráfagas de efectos;
- (c) otra vía.

**No elegir por el usuario ni activar G7_BOBS.**

## 2. La próxima sesión, en orden

| tarjeta | estado / qué hacer | instrucciones |
|---|---|---|
| **G7-S1** | solo con (a): especificación de efectos en sprites con su verificador de píxeles, después el 68000 | `docs/instrucciones-g7-s1.md` |
| G7-3, puertas | k409 físico, SW1, A/B BENCH, cycle-exact; con la decisión del §1 | `docs/instrucciones-g7-3-retoma.md` pasos 4-8 |

D1 sigue roja; después de G7, `docs/instrucciones-d1-opt.md`.

## 3. Red de seguridad y continuidad

Antes de cada commit: `python tools/lint_port.py` y
`python tools/regress.py --baseline tools/baseline_pc.json --level --g5l --bm1`.
También `sh tools/sws_gate.sh` y `sh tools/oam68k_gate.sh`.
Builds secuenciales: comparten `work/cc` y `work/g5l.i`. Si trabajan dos
agentes a la vez, cada build pasa por `sh work/buildlock.sh <comando>`.

El vivo por defecto mantiene SHA256 `33f2250a…` (`work/rg_bm1/game.bin`).
G7_BOBS: `GDEFS="-DREPLAY -DG7_BOBS" OUT=… sh tools/bm_build.sh` (replay)
o `GDEFS="-DG7_BOBS" OUT=… sh tools/game_build.sh` (vivo). Margen slow con
G7_BOBS: 5.040 B (vivo), 4.560 B (replay).
Productor: `python tools/g7f_verify.py --bin … --lst … --layers
fast,window,edf --check-clean [--profile all]`.
No distribuir ADF ni derivados. No borrar worktrees, stash ni `.claude/`.
Al cerrar, archivar este fichero y escribir los pasos de la sesión siguiente.
