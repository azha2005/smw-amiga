# O4 — Informe del peor frame (compuerta D1), 2026-10-03

> D1 ya está decidida (50 Hz, haciendo todo lo posible; ROADMAP §2 y §3).
> Este informe dice dónde estamos con números y qué conviene hacer ahora.
> **Lo que NO tiene:** la medida en WinUAE cycle-exact (`game.s -DBENCH`,
> `tools/game_read.py`). El factor del DMA (×1,2-1,3) es la estimación de
> ROADMAP §2, no una medida de este binario. Es lo primero que hay que
> cerrar para que el informe sea definitivo.

## 1. El juego entero en el replay de YI1 (Musashi, sin DMA)

`python3 tools/gamecheck.py --engine musashi --bin work/rg_game/game.bin
--lst work/rg_game/game.lst` (el `game.bin` de `regress.py`, commit
6e1e7f0): 6310 frames, 0 distintos del oráculo.

| parte | peor | % frame | media | % frame |
|---|---|---|---|---|
| `level_frame` (lógica con sprites) | 39 026 | 27,5 | 28 588 | 20,1 |
| `mspr_draw` (Mario) | 7 750 | 5,5 | 4 188 | 3,0 |
| columna nueva | 3 516 | 2,5 | 426 | 0,3 |
| `build_mid` (scroll) | 75 816 | 53,4 | 3 928 | 2,8 |
| resto de `scroll_frame` | 6 448 | 4,5 | 1 243 | 0,9 |
| **total** | **117 796** | **83,0** | **39 053** | **27,5** |

Cuántos frames pasarían de 20 ms (líneas `O4` nuevas de `gamecheck.py`):

| supuesto | límite (ciclos Musashi) | frames que pasan | racha más larga | dónde (s) |
|---|---|---|---|---|
| sin DMA | 141 875 | 0 | — | — |
| DMA ×1,2 | 118 229 | **0** | — | — |
| DMA ×1,3 | 109 135 | **3** (0,05 %) | 2 | 1792-2303 |
| DMA ×1,3 y 15 % reservado para dibujar los sprites del nivel, HUD y audio | 92 764 | **14** (0,22 %) | 2 | ídem |

**Lectura:** jugando el nivel hacia adelante, como en la grabación, el
juego ya entra a 50 Hz salvo un puñado de frames sueltos, todos en el
mismo tramo (s = 1792-2303; peor frame 10587, s = 2151). Con lo que falta sumar, ~14
frames de 6310, de a uno o dos seguidos: un tirón casi invisible. La
afirmación del handoff del 2026-10-01 ("los peores frames siguen pasando
del frame") era con el binario de ese día (peor 133 140 en el mismo
replay; hoy 117 796).

## 2. El caso que sigue mal: el scroll hacia atrás

`regress.py` mide el scroll solo (`scrollprof.py`) recorriendo el nivel
entero en los dos sentidos, como estrés:

| | peor | % frame | media |
|---|---|---|---|
| ida, 4 px/frame | 80 492 (s = 4588) | 56,7 | 16 251 |
| **vuelta, 2 px/frame** | **106 012** (s = 4580) | **74,7** | 18 989 |

La vuelta sola más la lógica de un frame malo (~39 000) da ~145 000:
**pasa del frame aun sin DMA**. El replay no lo muestra porque en la
grabación Mario casi no vuelve atrás. Un jugador que retrocede frente a
los postes de la meta (s ≈ 4580) lo va a ver.

## 3. Opciones

| | qué | coste | qué gana | riesgo |
|---|---|---|---|---|
| **1** | Seguir optimizando solo el pico: `build_mid` en s ≈ 4580 a la vuelta y los postes de la meta (S5/S7: pico a 4 px; P81 dice que agrupar no baja el pico) | 1-2 sesiones | elimina los 3-14 frames y la vuelta | puede no alcanzar; ya se intentó (P81) |
| 2 | Dibujo a 25 Hz fijo | poco | todo entra | se ve peor **siempre** por 14 frames de 6310: desproporcionado |
| 3 | Recortar (menos sprites) | poco | lógica | no toca el pico, que es del scroll |
| **4** | **Lógica a 50 Hz fija + imagen que pierde un frame solo cuando no llega** (Robocod; `investigacion-ports.md` §2.1, tarjeta O5) | 1 sesión (prototipo O5) | cualquier pico futuro (sprites, HUD, audio) se vuelve un tirón de imagen, nunca juego lento | coherencia `(cámara, OAM)` del mismo frame (P35) |

## 4. Recomendación

1. **Medir en WinUAE** (`game.s -DBENCH`) para confirmar el factor ×1,2-1,3.
   Si da ×1,2 o menos, el replay entra entero hoy.
2. **No pasar a 25 Hz.** Los números no lo justifican.
3. **Hacer O5 (opción 4) como red de seguridad** antes de 9.2/10/11, que
   suman coste: convierte "el juego va lento" en "la imagen saltea un frame",
   que es lo que hacían los plataformas comerciales de la A500.
4. **Opción 1 acotada** al scroll hacia atrás en s ≈ 4580 (el único caso que
   pasa del frame sin DMA), con un límite de una sesión. Si no baja, lo
   cubre la 4.

**Decisión del usuario (2026-10-03): hacer O5 como red de seguridad.** Sin 25 Hz.
