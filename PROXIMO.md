# PRÓXIMO — lo que sigue

2026-10-11. **G7-3b hecha y verificada; G7-3 sigue parcial, opt-in
`-DG7_BOBS`, no activa por defecto.**

El productor de efectos es ahora asm sin búsqueda (`player/g7fast.s`),
igual a la especificación `tools/g7_fast.py` en las cinco trazas (0
diferencias, `tools/g7f_verify.py`). Bajó de 82 M a 516 k ciclos en el
peor caso, pero **no cabe en el frame**: YI1 media 36 k, p99 376 k (sin
DMA). Ventana y EDF no están portadas: esas fotos se rechazan
explícitamente (129 en YI1). Informe: `docs/informe-g7-3b-1011.md`.

## 1. Decisión pendiente del usuario

Aun con las mejoras medibles de abajo, este esquema queda cerca de 8-10 k
ciclos por fila con efectos. Una foto con 16 filas (p99) cuesta 130-160 k,
más de un frame entero. Hay que decidir qué hacer con esas fotos
(presupuesto de G7 por frame, aceptar fotos omitidas en ráfagas de
efectos, u otra vía). **No activar G7_BOBS ni elegir por el usuario.**

## 2. La próxima sesión, en orden

| tarjeta | estado / qué hacer | instrucciones |
|---|---|---|
| **G7-3c** | bajar el coste por fila (tabla de usados por bloque, diario disperso, overlay, entradas), medir con `g7f_verify --profile all`; después portar ventana y EDF | `docs/instrucciones-g7-3c.md` |
| G7-3, puertas | k409 físico, SW1, A/B BENCH, cycle-exact; solo con la decisión del §1 | `docs/instrucciones-g7-3-retoma.md` pasos 4-8 |

D1 sigue roja; después de G7, `docs/instrucciones-d1-opt.md`.

## 3. Red de seguridad y continuidad

Antes de cada commit: `python tools/lint_port.py` y
`python tools/regress.py --baseline tools/baseline_pc.json --level --g5l --bm1`.
También `sh tools/sws_gate.sh` y `sh tools/oam68k_gate.sh`.
Builds secuenciales: comparten `work/cc` y `work/g5l.i`.

El vivo por defecto mantiene SHA256 `33f2250a…` (`work/rg_bm1/game.bin`).
G7_BOBS: `GDEFS="-DREPLAY -DG7_BOBS" OUT=… sh tools/bm_build.sh` (replay)
o `GDEFS="-DG7_BOBS" OUT=… sh tools/game_build.sh` (vivo).
No distribuir ADF ni derivados. No borrar worktrees, stash ni `.claude/`.
Al cerrar, archivar este fichero y escribir los pasos de la sesión siguiente.
