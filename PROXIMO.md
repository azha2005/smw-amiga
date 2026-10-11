# PRÓXIMO — lo que sigue

2026-10-10, cierre G7-0/G7-1. **SW-S: la lógica y la OAM de los puntos, el humo y los
sprites menores están en el 68000 (asm), exactas contra la SNES y activas
por defecto** (`docs/informe-sw-s-1010.md`): la RAM y la OAM de los tres
motores dan 0 distintos en yi1 y en 4 grabaciones. **El dibujo será por
bobs (G7): decisión del usuario del 2026-10-10.** Hasta que G7 funcione,
los efectos no se ven. Además, la regresión
vuelve a cruzar el C actual contra el asm en Windows (P131).

| tarjeta | estado | por defecto | informe |
|---|---|---|---|
| SW-Q | integrada | activa | `docs/informe-sw-q-recuperacion-1010.md` |
| SW-A, SW-P, SW-M, SW-B | hechas | **activas** (`SW_ANIM_POSTS=off`, `-DG5L_NOPRIORITY`, `-DCOINCONTROL`, `SW_TILES=0` las apagan) | `docs/informe-sw-ap-1010.md`, `-sw-m-retoma-`, `-sw-b-` |
| SW-D | cerrada, sin cambio | — | `docs/informe-sw-d-retoma-1010.md` |
| L-DER | cerrada (P130) | replay `run` | `docs/informe-l-der-1010.md` |
| SW-S | **lógica y OAM hechas**; dibujo por bobs (G7, decidido) | lógica activa (`-DNOSWS` la apaga, solo para el A/B) | `docs/informe-sw-s-1010.md` |

**G7-0 hecha:** el vivo libera 31.208 B de chip y 6.616 B de slow.
Segundo PF1 + 12 KiB de fuentes caben, con 1.840 B de chip libres.
**G7-1 implementada, opt-in** (`G7_DOUBLE`): preparar el copper antes
de esperar al PF1 libre pasa SW1 completo (126 fotos, 0 píxeles).
BENCH final: 269/6312 fotos omitidas frente a 217 del control;
racha máxima 2 en ambos, con la espera incluida en la medición. **D1 sigue roja**; efectos sin dibujo.
Detalles: `docs/informe-g7-1010.md`.

## 1. La próxima sesión, en orden

| tarjeta | responsable | ficheros / puerta | instrucciones |
|---|---|---|---|
| **G7-2/G7-3, efectos SW-S** | coordinador; **siguiente** | OAM en la foto, fuentes y color exactos, restauración y cola; SW1 y BENCH | `docs/instrucciones-g7-2.md` |
| **D1, optimizar** | coordinador; en paralelo o después de G7 | con todo activado: 217 fotos perdidas, peor `build_mid` 15 604 ticks, `resto de scroll_frame` 18 798. Primero lo que más pesa, medido por foto perdida | `docs/instrucciones-d1-opt.md` |
| SW-Q, resto | cuando haya grabaciones | una estrella real y flor/1-UP con más de una foto; A/B BENCH | `docs/informe-sw-q-recuperacion-1010.md` §"Qué sigue" |
| SW-B, resto | — | barrida de `turn_block` con `HOLDEVERY=10` y A/B BENCH en WinUAE | `docs/informe-sw-b-1010.md` §"Continuación" |
| G4-3 | aparcada | Rex en los pares de Mario | `docs/instrucciones-g4-3.md` |

Antes de cada commit: `python tools/lint_port.py` y `python tools/regress.py
--baseline tools/baseline_pc.json --level --g5l --bm1`, en verde. Si se
toca SW-S: `sh tools/sws_gate.sh` (RAM y OAM, `SWS RAM: OK` y `SWS OAM: OK`
en las 5 corridas) y `sh tools/oam68k_gate.sh`.

**Cuidado al compilar:** la regresión arma el build `game` antes de
regenerar los datos. Si se probó una opción de datos (`SW_ANIM_POSTS`,
`SW_TILES`), regenerar antes `mkbg`, `mkd8in`, `mkleveld`, `mkscroll` y
`mkscroll --g5` sin ella. El BENCH en WinUAE va con `tools/bm_build.sh`
(con `tools/game_build.sh` el replay no entra en chip: pantalla roja, P126).

## 2. Pendiente del usuario

- **G7, si falta memoria:** si ninguna opción de G7-0 libera la chip sin
  tocar algo visible, o si un color de un efecto no tiene lugar exacto en
  PF1, se te consulta antes de seguir (`docs/instrucciones-g7.md`).
- Para probar en la Amiga el vivo con todo: `GDEFS=" " OUT=work/live sh
  tools/game_build.sh` → `work/live/game.adf` (BM1, A501).
- **La regla de prioridad** (qué objetos se dibujan cuando no entran
  todos): hoy, de arriba abajo, hasta 2. Alternativas: el más cercano a
  Mario, enemigos antes que la caja y la cinta, mantener la elección de
  la foto anterior. El arreglo de fondo es la cola de bobs (G7).
- En el vivo por defecto, sin input, el Koopa mata a Mario hasta el game
  over, que no está portado (congela; GameMode `$15`).
- **Worktrees:** los de SW (`wt-sw-ap-1010`, `wt-sw-b-1010`,
  `wt-sw-qs-1010`) y `wt-p123-1010` ya están integrados; se pueden borrar.
  `wt-g5bis-1007`, `wt-review-1007` y los dos de `.claude/worktrees/agent-*`
  tienen commits que no están en master. No se borra nada sin tu permiso.
- **Solo como dato (no se propone):** S11 y L3 indican que el estrés back
  probablemente no entre en D1 solo con CPU. Con 5 planos (PF2 de 2) el
  ≈ 1,6× de los planos casi desaparecería, pero cambia D8 y el fondo.
- `stash@{0}` de master guarda el `docs/README.md` viejo de antes de
  integrar `g2t-b2bis`. Se puede tirar.
