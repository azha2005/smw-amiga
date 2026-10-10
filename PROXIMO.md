# PRÓXIMO — lo que sigue

2026-10-10, noche. **Las tarjetas de SW1 abandonadas por el límite de uso
están retomadas e integradas a master** (sin push). Cada una se mezcló con
master, se repitieron lint, la regresión completa y memmap, y se midió
D1 en WinUAE donde hacía falta.

| tarjeta | estado | por defecto | informe |
|---|---|---|---|
| SW-Q | integrada: `$83` (con alas y usado) y power-ups en OAM/G5L; capturas 1199/1249/1299 a 0 px | **activa** | `docs/informe-sw-q-recuperacion-1010.md` |
| SW-A | hecha: postes del punto medio, VRAM exacta (42/42), fase 0 congelada | opcional, `SW_ANIM_POSTS=0` | `docs/informe-sw-ap-1010.md` |
| SW-P | hecha: piraña detrás de la tubería; SW1: sus 8 fotos a 0 px | opcional, `-DG5L_PRIORITY` | `docs/informe-sw-ap-1010.md` |
| SW-M | hecha: la moneda de Yoshi, 8 pasos; SW1: 13 fotos mejores, 0 peores | opcional, `-DCOINANIM` | `docs/informe-sw-m-retoma-1010.md` |
| SW-B | hecha: bloques rotos/usados en pantalla; 33/33 exactos | opcional, `SW_TILES=1` | `docs/informe-sw-b-1010.md` |
| SW-D | investigada: los píxeles BG1 son derrames del asignador; sin arreglo | — | `docs/informe-sw-d-retoma-1010.md` |
| SW-S | no empezada | — | `docs/instrucciones-sw-s.md` |

**Por qué cuatro opcionales:** las cuatro mejoran la imagen y las cuatro
cuestan frame; sus puertas de D1 piden "dentro del ruido" y no lo están
(costes en §2). Activarlas es decisión del usuario. Con los defaults el
juego es el de antes más SW-Q.

**D1 sigue roja** (normal BENCH 103/6312 en el control de SW-M; back,
sprites y hills2 como en la tanda anterior). 50 Hz y colchón aceptados.

## 1. La próxima sesión, en orden

| tarjeta | responsable | ficheros / puerta | instrucciones |
|---|---|---|---|
| **L-DER** | coordinador; **siguiente** | la deriva de la lógica de sprites en el 68000 (Rex yi1 70 %, piraña 74 %). Incluye el Rex 3770 de `pw_flor` que deja roja la puerta global de SW-Q. Puerta: `sprshot_cmp.py --logic` ≥ 99 % por tipo en yi1, stress_piranha, chuck y hills2; regresión; A/B si cambia la CPU | `docs/instrucciones-l-der.md` |
| SW-S | después de L-DER | puntos, estrellas, humo y trozos: primero el volcado de RAM de los tres motores (`snesorc --ram`, ya existe), después la lógica en asm. El dibujo por G5L compite con los enemigos: decisión del usuario o esperar G7 | `docs/instrucciones-sw-s.md` |
| SW-Q, resto | cuando haya grabaciones | una estrella real y flor/1-UP con más de una foto; A/B BENCH (`work/swq_*_yi1_oam`, en el worktree); SW1 k 1199-1449 | `docs/informe-sw-q-recuperacion-1010.md` §"Qué sigue" |
| SW-B, resto | si se activa | barrida de `turn_block` con `HOLDEVERY=10` y A/B BENCH en WinUAE | `docs/informe-sw-b-1010.md` §"Continuación" |
| SW-D, arreglo | si se decide | reasignar los registros de PF1 sin desplazar el error (`mkscroll`/`dpfsplit`); también reduciría el derrame de SW-A | `docs/informe-sw-d-retoma-1010.md` |
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

- **Qué opciones de SW1 activar.** Costes medidos:

  | opción | arregla | cuesta |
  |---|---|---|
  | SW-P `-DG5L_PRIORITY` | la piraña detrás de la tubería (8 fotos de SW1) | BENCH 113 → 124 fotos perdidas |
  | SW-M `-DCOINANIM` | el color de la moneda de Yoshi (13 fotos) | BENCH 103 → 148 fotos perdidas |
  | SW-A `SW_ANIM_POSTS=0` | los postes visibles (9 fotos; quedan las rayas, que giran) | `build_mid.max` 81 244 → 93 746 ciclos; 1-4 px de derrame |
  | SW-B `SW_TILES=1` | bloques rotos y usados en pantalla | `build_mid.max` +836 ciclos; falta medirla en WinUAE |

  Propuesta: SW-P (lo que más se ve, el coste más chico). Para probarlas
  todas juntas en la Amiga: `work/live_fid/game.adf` (vivo, BM1, A501;
  arranca a 49,9 FPS en WinUAE; chip con 42 KB de margen, slow con 10 KB).
  Se arma así (y después regenerar los datos sin las variables):

  ```
  for s in mkbg mkd8in mkleveld; do SW_ANIM_POSTS=0 python tools/$s.py; done
  SW_ANIM_POSTS=0 SW_TILES=1 python tools/mkscroll.py --g5
  GDEFS='-DG5L_PRIORITY -DCOINANIM' OUT=work/live_fid sh tools/game_build.sh
  ```
- **La regla de prioridad** (qué objetos se dibujan cuando no entran
  todos): hoy, de arriba abajo, hasta 2. Con SW-Q compiten también el
  bloque volador y los power-ups (en k 1299 la seta deja fuera el
  bloque). Alternativas: el más cercano a Mario, enemigos antes que la
  caja y la cinta, mantener la elección de la foto anterior. El arreglo
  de fondo es la cola de bobs (G7).
- Probar en la Amiga real el ADF del vivo por defecto: `GDEFS=" "
  OUT=work/live sh tools/game_build.sh` → `work/live/game.adf` (A500 con
  A501). Sin input, el Koopa mata a Mario hasta el game over, que no está
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
