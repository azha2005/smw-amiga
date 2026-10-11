# PRÓXIMO — lo que sigue

2026-10-11. **G7-3c hecha: el productor de efectos está entero en 68000**
(camino corto, capas 1-2, ventana `player/g7win.s` y EDF `player/g7edf.s`).
Es igual a la especificación `tools/g7_fast.py` en las cinco trazas (0
diferencias, el diario repone la lista byte a byte). **Sigue opt-in
`-DG7_BOBS`, no activa por defecto.** Fotos sin plan: YI1 40 (meta), chuck
6, las demás 0. Informe: `docs/informe-g7-3c-1011.md`.

## 1. Decisiones del usuario (2026-10-11)

- **G7: se elige (a), el híbrido con sprites de hardware**, frente a (b)
  un presupuesto con fotos omitidas y (c) otra vía. Por ahora solo
  queda anotado; se empieza en la próxima sesión. El productor PF1 (G7-3c)
  queda para las filas que no entren en sprites. Hoy no cabe en el frame:
  YI1 p99 1,04 M ciclos sin DMA (`docs/informe-g7-3c-1011.md`).
- **Dibujar el Banzai Bill** (`$9F`): hoy tiene lógica pero es invisible.
  Va como bob del PF1 y primero hay que hacerle lugar en chip.
- **Prioridad: mejorar el rendimiento al final del nivel** (zona de la
  meta). Ahí se juntan el pico de scroll de los postes (P81) y las fotos
  de efectos más caras o sin plan de G7.

## 2. La próxima sesión, en orden

| tarjeta | estado / qué hacer | instrucciones |
|---|---|---|
| **META-R** | medir el reparto por componente en la meta (WinUAE cycle-exact) y proponer con números | `docs/instrucciones-meta-r.md` |
| **G7-S1** | híbrido (a): especificación de efectos en sprites con su verificador de píxeles, después el 68000 | `docs/instrucciones-g7-s1.md` |
| **BANZAI** | presupuesto de chip exacto (qué necesita el bob, qué libera C2/C3/C4); después especificación, verificador y 68000 | `docs/instrucciones-banzai.md` |
| G7-3, puertas | k409 físico, SW1, A/B BENCH, cycle-exact | `docs/instrucciones-g7-3-retoma.md` pasos 4-8 |

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
