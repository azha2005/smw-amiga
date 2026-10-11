# PRÓXIMO — lo que sigue

2026-10-11. **G7-3c hecha: el productor de efectos está entero en 68000**
(camino corto, capas 1-2, ventana `player/g7win.s` y EDF `player/g7edf.s`).
Es igual a la especificación `tools/g7_fast.py` en las cinco trazas (0
diferencias, el diario repone la lista byte a byte). **Sigue opt-in
`-DG7_BOBS`, no activa por defecto.** Fotos sin plan: YI1 40 (meta), chuck
6, las demás 0. Informe: `docs/informe-g7-3c-1011.md`.

## 1. Decisiones del usuario (2026-10-11)

- **Criterio de fidelidad: 1:1 lo más posible; si hay que recortar, que
  no se note**, medido contra la SNES y mostrado lado a lado. Antes de
  sumar más costo se resuelve la arquitectura del frame (ARQ-0); el
  usuario elige con los números.

- **G7: se elige (a), el híbrido con sprites de hardware**, frente a (b)
  un presupuesto con fotos omitidas y (c) otra vía. Por ahora solo
  queda anotado; se empieza en la próxima sesión. El productor PF1 (G7-3c)
  queda para las filas que no entren en sprites. Hoy no cabe en el frame:
  YI1 p99 1,04 M ciclos sin DMA (`docs/informe-g7-3c-1011.md`).
- **Dos Rex en las mismas filas**: hoy uno queda invisible y cuál se ve
  cambia cada ~15 cuadros (el "flicker"). Arreglo exacto: usar los pares
  de Mario cuando él no está en esas filas.
- **Dibujar el Banzai Bill** (`$9F`): hoy tiene lógica pero es invisible.
  Va como bob del PF1 y primero hay que hacerle lugar en chip.
- **Prioridad: mejorar el rendimiento al final del nivel** (zona de la
  meta). Ahí se juntan el pico de scroll de los postes (P81) y las fotos
  de efectos más caras o sin plan de G7.

## 2. La próxima sesión, en orden

**ARQ-0 primero; lo demás en pausa hasta que el usuario elija la
arquitectura del frame** (decisión del usuario, 2026-10-11). Con la libertad
creativa que dio el usuario el 2026-10-11 ("modificar el plano para el mayor
parecido con la mayor ganancia"): ARQ-C, después P1-B, después el contrato.

| tarjeta | estado / qué hacer | instrucciones |
|---|---|---|
| **ARQ-C** | **pasos 1 y 2 hechos (2026-10-11)**: los saltos entran en el segundo WAIT (`SEGIN`) y `COP2LCH` solo en la cabecera y al cambiar de banco (`$0086`): 4 palabras por línea, imagen igual. Fotos perdidas hoy → paso 2: yi1 217 → 210, back 1128 → 1074, sprites 397 → 390, hills2 686 → 673, meta 581 → 482 (racha 22 → 8). **La ganancia no es lineal con el DMA** (informe §5). **Siguiente: decidir si el paso 3 (borrado compacto, ~4 palabras netas, pide eventos nuevos en `mkscroll.py`, indirección en `apply_colors` y tiempos del borrado variable en G5L/G7) vale su costo, o pasar a P1-B** | `docs/instrucciones-arq-c.md` |
| **ARQ-0** | pasos 0-2 y P1-V medidos (`docs/informe-arq-0-1011.md` §5). Vara ΔE ≥ 2 (ΔE ≤ 3 tolerable). **P1-V: los cortes de paleta PF2 se comen la ganancia** (BENCH: conservan 20-55 % sin contar su CPU), no se adoptan. **Bandas de 5 planos por fila (sin CPU, 2 MOVE de BPLCON0): 0-16 + 208-223 invisibles (≈ 4 px), 17-24 % de la ganancia (51 % en goal)** → tarjeta P1-B después de ARQ-C. Las filas de las colinas a 5 planos (P1 entero, ≈ 3.900 px más) quedan para el usuario. Después, el contrato. Aparte: el master empeoró desde el 10/10 (yi1 14 → 217, back racha 28), sin bisect | `docs/informe-arq-0-1011.md`, `docs/instrucciones-arq-0.md` |
| META-R | en pausa (el tramo de la meta entra en la medida de ARQ-0) | `docs/instrucciones-meta-r.md` |
| G7-S1 | en pausa | `docs/instrucciones-g7-s1.md` |
| REX2 | en pausa | `docs/instrucciones-rex2.md` |
| BANZAI | en pausa | `docs/instrucciones-banzai.md` |
| G7-3, puertas | en pausa | `docs/instrucciones-g7-3-retoma.md` pasos 4-8 |

D1 sigue roja; `docs/instrucciones-d1-opt.md` queda absorbida por ARQ-0 (su paso 1 es la medida de partida).

## 3. Red de seguridad y continuidad

Antes de cada commit: `python tools/lint_port.py` y
`python tools/regress.py --baseline tools/baseline_pc.json --level --g5l --bm1`.
También `sh tools/sws_gate.sh` y `sh tools/oam68k_gate.sh`.
Builds secuenciales: comparten `work/cc` y `work/g5l.i`. Si trabajan dos
agentes a la vez, cada build pasa por `sh work/buildlock.sh <comando>`.

El vivo por defecto: SHA256 `b07e2757…` desde ARQ-C paso 2 (paso 1 `425b658a…`, antes `33f2250a…`; `work/rg_bm1/game.bin`).
G7_BOBS: `GDEFS="-DREPLAY -DG7_BOBS" OUT=… sh tools/bm_build.sh` (replay)
o `GDEFS="-DG7_BOBS" OUT=… sh tools/game_build.sh` (vivo). Margen slow con
G7_BOBS: 5.040 B (vivo), 4.560 B (replay).
Productor: `python tools/g7f_verify.py --bin … --lst … --layers
fast,window,edf --check-clean [--profile all]`.
No distribuir ADF ni derivados. No borrar worktrees, stash ni `.claude/`.
Al cerrar, archivar este fichero y escribir los pasos de la sesión siguiente.
