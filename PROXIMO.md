# PRÓXIMO — lo que sigue

2026-10-10. **Código en `g2t-b2bis`, sin merge ni push**; worktree:
`C:/Users/JC/Downloads/sma/wt-g2t-b2bis-1008`. Master conserva el código
anterior.

**G4-B hecha; los demás enemigos de YI1 quedan apagados por defecto**
(`docs/informe-g4-b-1010.md`). Con `G5L_TYPES=all`, G5L dibuja la
piraña, el Chuck, el Koopa, el caparazón, la caja, la cinta y `$02` con
la misma regla que el Rex: un objeto por foto, el más alto. El 68000 es
exacto en yi1, hills2, piranha y chuck. Las capturas de la piraña y del
Chuck salen exactas en el objeto. Pero D1 empeora más que el ruido:

| replay | fotos perdidas, control | todos los tipos |
|---|---:|---:|
| normal | 11 | 27 |
| back | 387 | 456 |
| piranha | 108 | 131 |
| sprites | 93 | 104 |
| hills2 | 216 | 225 |

**Ahora: G9**, la comparación de la imagen de los sprites contra la OAM
de la SNES, para juzgar el 1:1 sin depender de un control.

**D1 sigue roja**: back 387/4126, sprites 93/1914, hills2 216/2835 y
normal BENCH 11/6312 (controles de esta tanda). 50 Hz y colchón
aceptados.

## 1. La próxima sesión, en orden

| tarjeta | responsable | ficheros / puerta | instrucciones |
|---|---|---|---|
| **G9** | coordinador; **siguiente** | `tools/sprshot_cmp.py` (nuevo). La OAM del oráculo dibujada en Python contra la captura de WinUAE, por objeto: exacto, no dibujado con su motivo, o N px distintos. Puerta: 0 px en los objetos dibujados y en Mario, sobre las capturas de G4-B y un juego por tipo | `docs/instrucciones-g9.md` |
| G4-3 | aparcada | Rex en los pares de Mario: solo tiene sentido con G4-2 activado | `docs/instrucciones-g4-3.md` |

Antes de cada commit: `python tools/lint_port.py` y `python tools/regress.py
--baseline tools/baseline_pc.json --level --g5l --bm1`, en verde.

## 2. Pendiente del usuario

- **Trade de los demás enemigos** (G4-B, `G5L_TYPES=all`):
  - a favor: se ven la piraña, el Koopa, la caja, la cinta y `$02` casi
    siempre. El Chuck y el caparazón se ven poco, porque casi siempre hay
    otro objeto más alto (la cinta, la caja) y gana ese. Con 2 por foto
    se ve más de la mitad.
  - en contra: fotos perdidas normal 11 → 27, back +69, piranha +23.
  - además, la chip del replay queda a ≈ 3 KB del límite real (P126).
    El vivo (BM1) tiene 14,7 KB.

  Hoy está apagado por la regla de la tarjeta.
- **Trade de los 2 Rex por foto** (G4-2/G4-2o): más Rex visibles (hills2
  +32 %) contra ≈ 1,6× fotos perdidas en hills2 y ≈ 2× en sprites. Hoy
  está apagado.
  - Con todos los tipos y 2 por foto, el replay **no arranca** por chip
    (P126). En el vivo sí cabría.
  - Un objeto que no entra no se dibuja: la cola de bobs es G7.
- Probar el vivo a mano en esta rama y decidir cuándo integrar a master.
  Novedad visible: el Rex aplastado sobre pendientes.
  `G5L_TYPES=all GDEFS=" " OUT=work/live sh tools/game_build.sh` arma el
  vivo con todos los enemigos.
- **Solo como dato (no se propone):** S11 y L3 indican que el estrés back
  probablemente no entre en D1 solo con CPU. Con 5 planos (PF2 de 2) el
  ≈ 1,6× de los planos casi desaparecería, pero cambia D8 y el fondo. Es
  decisión tuya si alguna vez se quiere evaluar.
- En el checkout de master quedó sin commitear una versión vieja de
  `docs/investigacion-demoscene-1010.md` (264 líneas) y su fila en
  `docs/README.md`; la rama tiene la versión actualizada (320 líneas,
  `6797dd0`).
