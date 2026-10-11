# PRÓXIMO — lo que sigue

2026-10-11. Cierre de G7-3 pedido por el usuario por límite de uso.
**G7-3 parcial, opt-in `-DG7_BOBS`. No está terminada ni activa por defecto.**

Hay productor C/68000, cola BLIT con IRQ, restauración de dos anillos,
diario de copper y flujos hardware por lista. Las fuentes se cargan por
BM1 sin retener otra copia en slow. El vivo por defecto mantiene su hash.

La barrida del prototipo previo a las últimas correcciones terminó:
YI1 6.313 fotos/88.550 píxeles, pw_bloques 2.076/36.543,
spin_kill 1.007/26.875, stress_piranha 3.018/33.840: cero rechazos y
cero diferencias comprobadas. **chuck_kill tiene rechazos**, incluso
tras ampliar la búsqueda: 13 en k2681..2688 y k2814..2821.
La referencia offline sí resuelve k2681; el renderer requiere corrección.

**Puerta física roja:** k409 arranca y termina en WinUAE cycle-exact,
cola vacía y error=0, pero el comparador encuentra 1.484 píxeles distintos,
principalmente terreno. Se cambió después el productor para leer el PF1
materializado y esperar el último blit; esa corrección todavía no tiene
captura física. No confundir los cuatro cruces CPU verdes con el árbol final.

## 1. La próxima sesión, en orden

| tarjeta | estado / qué hacer | instrucciones |
|---|---|---|
| **G7-3, retoma** | corregir k409 físico y los 13 rechazos; repetir cinco trazas sobre el código final, propiedad/NOSWS, SW1 y A/B BENCH | `docs/instrucciones-g7-3-retoma.md` |

Leer `docs/informe-g7-3-1011.md`. No activar por defecto, aproximar
colores ni interpretar un buscador agotado como imposibilidad de Amiga.
El apoyo hardware puntual ya está autorizado; no repetir la elección.
D1 sigue roja: el prototipo midió 82.181.366 ciclos en una foto YI1,
sin DMA; no hay A/B BENCH ni SW1 completo de G7-3. Después de cerrar
su fidelidad, seguir `docs/instrucciones-d1-opt.md`.

## 2. Red de seguridad y continuidad

Antes de cada commit: `python tools/lint_port.py` y
`python tools/regress.py --baseline tools/baseline_pc.json --level --g5l --bm1`.
También `sh tools/sws_gate.sh` y `sh tools/oam68k_gate.sh`.
Builds secuenciales: comparten `work/cc`, `work/g5l.i` y `work/g7/prod.s`.

SW-S lógica/OAM siguen activas; G7_BOBS solo experimental.
El vivo se arma con `GDEFS="-DG7_BOBS" OUT=work/g73/live sh tools/game_build.sh`.
No distribuir ADF ni derivados. No borrar worktrees, stash ni `.claude/`.
Al cerrar, archivar este fichero y escribir los pasos de la sesión siguiente.
