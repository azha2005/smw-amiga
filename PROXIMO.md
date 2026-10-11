# PRÓXIMO — lo que sigue

2026-10-10, noche. **SW-S: la lógica y la OAM de los puntos, el humo y los
sprites menores están en el 68000 (asm), exactas contra la SNES y activas
por defecto** (`docs/informe-sw-s-1010.md`): la RAM y la OAM de los tres
motores dan 0 distintos en yi1 y en 4 grabaciones. **Falta el dibujo en
la Amiga, y cómo hacerlo lo decidís vos** (§2). Además, la regresión
vuelve a cruzar el C actual contra el asm en Windows (P131).

| tarjeta | estado | por defecto | informe |
|---|---|---|---|
| SW-Q | integrada | activa | `docs/informe-sw-q-recuperacion-1010.md` |
| SW-A, SW-P, SW-M, SW-B | hechas | **activas** (`SW_ANIM_POSTS=off`, `-DG5L_NOPRIORITY`, `-DCOINCONTROL`, `SW_TILES=0` las apagan) | `docs/informe-sw-ap-1010.md`, `-sw-m-retoma-`, `-sw-b-` |
| SW-D | cerrada, sin cambio | — | `docs/informe-sw-d-retoma-1010.md` |
| L-DER | cerrada (P130) | replay `run` | `docs/informe-l-der-1010.md` |
| SW-S | **lógica y OAM hechas**; dibujo pendiente de tu decisión | lógica activa (`-DNOSWS` la apaga, solo para el A/B) | `docs/informe-sw-s-1010.md` |

**D1 sigue roja**: en el BENCH de hoy, 202 fotos perdidas sin SW-S y 217
con SW-S (3,44 %). 50 Hz y colchón aceptados; optimizar después.

## 1. La próxima sesión, en orden

| tarjeta | responsable | ficheros / puerta | instrucciones |
|---|---|---|---|
| **SW-S, dibujo** | coordinador, **cuando elijas el camino** (§2) | (a) bobs G7, o (b) G5L con prioridad baja; después SW1 en las fotos de la lista y A/B BENCH | `docs/instrucciones-sw-s.md` (paso 3) |
| **D1, optimizar** | coordinador; **siguiente si el dibujo espera** | con todo activado: 217 fotos perdidas, peor `build_mid` 15 604 ticks, `resto de scroll_frame` 18 798. Primero lo que más pesa, medido por foto perdida | `docs/instrucciones-d1-opt.md` |
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

- **SW-S, cómo dibujar los puntos, el humo y los trozos** (fidelidad):
  - **(a) bobs (G7)**: el camino del plan. No compiten con nada, pero G7
    (la cola de bobs con restaurado) todavía no existe: hasta entonces no
    se ven.
  - **(b) G5L**, como objetos más con la prioridad más baja: se ven ya,
    pero con 2 objetos por foto un puntaje puede dejar sin dibujar a un
    Rex. Variante: solo cuando sobra lugar en la foto (no desplaza a
    ningún enemigo).
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
