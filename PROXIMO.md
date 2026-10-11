# PRÓXIMO — lo que sigue

2026-10-11, G7-C verificada. **SW-S: la lógica y la OAM de los puntos, el humo y los
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

**G7-0 hecha y G7-1 opt-in. G7-2 parcial:** la OAM de cada foto
coincide en cinco trazas; las fuentes exactas ocupan 7.616 B de los
12 KiB reservados. Tres sondas (k409, k5026, k6015) dan **0 píxeles
distintos en WinUAE cycle-exact**. Todavía no hay cola de bobs en el juego.

**G7-C: testigo k6047 resuelto sin cambiar D8.** Apoyo puntual de
SPR2/3 (y SPR6/7 en las fotos vecinas), controles DMA auditados y colores
existentes de Mario compartidos sin recargas nuevas. Cuatro fotos
consecutivas k6046..6049: **848 píxeles de efectos, 0 diferencias en
pantalla completa**, WinUAE cycle-exact; negativo de armado detectado
solo en el apoyo hardware. La cota negativa de PF1 sigue siendo válida;
el apoyo hardware la evita. `docs/informe-g7-c-1011.md`.

La barrida híbrida automática de esas cuatro fotos también pasa:
1 foto solo PF1, 3 híbridas, máximo 160 B DMA en la reserva existente.
El tramo 6015..6060 pasa offline: 46 fotos, 8.929 píxeles; 40 fotos PF1
y seis híbridas, ninguna sin resolver.
**Cobertura offline completa de las cinco trazas:** 3.754 fotos con
efectos, 250.347 píxeles, 0 fotos sin destino. 3.733 fotos solo PF1 y
21 híbridas; hasta 160 B DMA por foto. Los casos con recargas
k6064..6066 también pasan en WinUAE: **siete sondas, 1.180 píxeles y
0 diferencias en pantalla completa**. Sigue pendiente la cola y el
renderer del juego; la referencia no mide su coste ni propiedad en movimiento.

G7_DOUBLE vivo: 522.448 B chip / 511.656 B slow, 0 violaciones;
el vivo por defecto conserva su binario. **D1 sigue roja**; 217→269
omitidos fue el A/B histórico de G7-1, anterior a copiar OAM. No hay
BENCH nuevo ni efectos activados.

## 1. La próxima sesión, en orden

| tarjeta | responsable | ficheros / puerta | instrucciones |
|---|---|---|---|
| **G7-3, efectos SW-S** | coordinador; **siguiente** | llevar los destinos exactos de la referencia al render; fuentes, restauración/cola y almacenamiento hardware por lista; después SW1 y BENCH | `docs/instrucciones-g7-hibrido.md` |
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

## 2. Decisiones y pendientes

- **G7-C, decidido por el usuario el 2026-10-11:** «Apoyo puntual de
  sprites hardware para conservar los colores exactos». La excepción ya
  pasó en k6046..6049: parejas detenidas, armado VBL y paleta compartida
  exacta o recargas calibradas, con cobertura offline en cinco trazas.
  No volver a pedir la elección. No se ha demostrado reuso de canales
  ocupados ni cola en movimiento; seguir `docs/instrucciones-g7-hibrido.md`.
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
