# PRÓXIMO — lo que sigue

2026-10-10, noche. **Las cuatro opciones de SW1 están activadas por defecto**
(usuario: "la idea es 1:1, después vemos cómo optimizar"; costes en la base
de la regresión y en P129). **SW-D cerrada sin cambio. L-DER cerrada: la
deriva de la lógica venía del replay, no del 68000** (P130,
`docs/informe-l-der-1010.md`): `sprshot_cmp.py --logic` da OK en las 10
trazas con oamb.

| tarjeta | estado | por defecto | informe |
|---|---|---|---|
| SW-Q | integrada | activa | `docs/informe-sw-q-recuperacion-1010.md` |
| SW-A, SW-P, SW-M, SW-B | hechas | **activas** (`SW_ANIM_POSTS=off`, `-DG5L_NOPRIORITY`, `-DCOINCONTROL`, `SW_TILES=0` las apagan) | `docs/informe-sw-ap-1010.md`, `-sw-m-retoma-`, `-sw-b-` |
| SW-D | cerrada, sin cambio (límite de 7 registros de PF1) | — | `docs/informe-sw-d-retoma-1010.md` |
| L-DER | **cerrada**: replay `--lock run`, `$1490` en `FIELDS`, `-DLSS_SNESORC` para verificar snesorc, comparador de Mario | replay `run` | `docs/informe-l-der-1010.md` |
| SW-S | **siguiente** | — | `docs/instrucciones-sw-s.md` |

**D1 sigue roja**, y más con las cuatro opciones (BENCH: SW-P 113 → 124,
SW-M 103 → 148 fotos perdidas). 50 Hz y colchón aceptados; optimizar
después.

## 1. La próxima sesión, en orden

| tarjeta | responsable | ficheros / puerta | instrucciones |
|---|---|---|---|
| **SW-S** | coordinador; **siguiente** | puntos, estrellas, humo y trozos: primero el volcado de RAM de los tres motores (`snesorc --ram`, ya existe), después la lógica en asm. Por la directiva 1:1, activa por defecto si pasa; el dibujo por G5L compite con los enemigos (o esperar G7) | `docs/instrucciones-sw-s.md` |
| D1, optimizar | después de SW-S | con todo activado: `build_mid.max` 95 756, `total.max` 126 958; SW-P y SW-M en el BENCH. Primero lo que más pesa (perfil de los tramos tarde, P115) | `docs/plan-tecnico.md` |
| SW-Q, resto | cuando haya grabaciones | una estrella real y flor/1-UP con más de una foto; A/B BENCH; el Rex 3770 de `pw_flor` probablemente era P130 (la flor es una animación que el replay saltaba; sin traza oamb, no verificado) | `docs/informe-sw-q-recuperacion-1010.md` §"Qué sigue" |
| SW-B, resto | — | barrida de `turn_block` con `HOLDEVERY=10` y A/B BENCH en WinUAE | `docs/informe-sw-b-1010.md` §"Continuación" |
| G4-3 | aparcada | Rex en los pares de Mario | `docs/instrucciones-g4-3.md` |

Antes de cada commit: `python tools/lint_port.py` y `python tools/regress.py
--baseline tools/baseline_pc.json --level --g5l --bm1`, en verde.

**Cuidado al compilar:** la regresión arma el build `game` antes de
regenerar los datos. Si se probó una opción de datos (`SW_ANIM_POSTS`,
`SW_TILES`), regenerar antes `mkbg`, `mkd8in`, `mkleveld`, `mkscroll` y
`mkscroll --g5` sin ella. Si no, mide los datos viejos. En otro checkout,
regenerar `shapes.json` como dice el informe de SW-Q (`g4a.py traceall
--merge`).

## 2. Pendiente del usuario

- Para probar en la Amiga el vivo con todo: `GDEFS=" " OUT=work/live sh
  tools/game_build.sh` → `work/live/game.adf` (BM1, A501; chip con 42 KB
  de margen, slow con 10 KB).
- **La regla de prioridad** (qué objetos se dibujan cuando no entran
  todos): hoy, de arriba abajo, hasta 2. Con SW-Q compiten también el
  bloque volador y los power-ups (en k 1299 la seta deja fuera el
  bloque). Alternativas: el más cercano a Mario, enemigos antes que la
  caja y la cinta, mantener la elección de la foto anterior. El arreglo
  de fondo es la cola de bobs (G7).
- En el vivo por defecto, sin input, el Koopa mata a Mario hasta el game over, que no está
  portado (congela; GameMode `$15`).
- **Worktrees:** los de SW (`wt-sw-ap-1010`, `wt-sw-b-1010`,
  `wt-sw-qs-1010`) y `wt-p123-1010` ya están integrados; se pueden borrar.
  `wt-g5bis-1007` (2 commits WIP de G5a-bis), `wt-review-1007` (L-OAM
  pasos 3-4, `600abf5`) y los dos de `.claude/worktrees/agent-*` (G2T-B2
  WIP y revisión L-OAM) tienen commits que no están en master; antes de
  borrarlos hay que ver si sobra algo. No se borra nada sin tu permiso.
- **Solo como dato (no se propone):** S11 y L3 indican que el estrés back
  probablemente no entre en D1 solo con CPU. Con 5 planos (PF2 de 2) el
  ≈ 1,6× de los planos casi desaparecería, pero cambia D8 y el fondo.
- `stash@{0}` de master guarda el `docs/README.md` viejo de antes de
  integrar `g2t-b2bis`. Se puede tirar.
