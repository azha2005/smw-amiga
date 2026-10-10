# PRÓXIMO — lo que sigue

2026-10-10. **Código en `g2t-b2bis`, sin merge ni push**; worktree:
`C:/Users/JC/Downloads/sma/wt-g2t-b2bis-1008`. Master conserva el código
anterior.

**G4-B y G9 hechas.**

- **G4-B** (`docs/informe-g4-b-1010.md`): con `G5L_TYPES=all`, G5L dibuja
  los demás enemigos de YI1 (piraña, Chuck, Koopa, caparazón, caja, cinta
  y `$02`), un objeto por foto. Exacto en el 68000. **Apagado por
  defecto**: D1 empeora más que el ruido (normal 11 → 27, back 387 → 456,
  piranha 108 → 131 fotos perdidas) y la chip del replay queda casi al
  límite (P126).
- **G9** (`docs/informe-g9-1010.md`): `tools/sprshot_cmp.py` compara la
  captura con la OAM de la SNES. **El dibujo es exacto**: en 10
  capturas, los 8 tipos (limpios y con bandas) y Mario dan 0 px
  distintos. Lo que no es exacto es la **lógica** de unas pocas
  instancias, que se desvían 1-2 px u otra pose durante cientos de fotos
  (Rex de yi1: 70 % de fotos iguales; piraña de stress_piranha: 74 %).

**Ahora: L-DER**, encontrar y corregir esa deriva de la lógica.

**D1 sigue roja**: back 387/4126, sprites 93/1914, hills2 216/2835 y
normal BENCH 11/6312 (controles de esta tanda). 50 Hz y colchón
aceptados.

## 1. La próxima sesión, en orden

| tarjeta | responsable | ficheros / puerta | instrucciones |
|---|---|---|---|
| **L-DER** | coordinador; **siguiente** | la lógica de sprites en el 68000. El primer frame en que cada instancia se separa de la SNES (RAM de la ranura contra la traza `oamb`), su causa y el arreglo. Puerta: `sprshot_cmp.py --logic` ≥ 99 % por tipo en yi1, stress_piranha, chuck y hills2 (o cada tramo explicado); regresión; A/B si cambia la CPU de la lógica | `docs/instrucciones-l-der.md` |
| G4-3 | aparcada | Rex en los pares de Mario: solo tiene sentido con G4-2 activado | `docs/instrucciones-g4-3.md` |

Antes de cada commit: `python tools/lint_port.py` y `python tools/regress.py
--baseline tools/baseline_pc.json --level --g5l --bm1`, en verde.

## 2. Pendiente del usuario

- **Trade de los demás enemigos** (G4-B, `G5L_TYPES=all`):
  - a favor: se ven la piraña, el Koopa, la caja, la cinta y `$02` casi
    siempre. El Chuck y el caparazón se ven poco, porque casi siempre hay
    otro objeto más alto y gana ese. Con 2 por foto se ve más de la mitad.
  - en contra: fotos perdidas normal 11 → 27, back +69, piranha +23.
  - además, la chip del replay queda a ≈ 3 KB del límite real (P126).
    El vivo (BM1) tiene 14,7 KB.

  Hoy está apagado por la regla de la tarjeta.
- **Trade de los 2 Rex por foto** (G4-2/G4-2o): más Rex visibles contra
  ≈ 1,6-2× fotos perdidas. Hoy está apagado.
  - Con todos los tipos y 2 por foto, el **replay no arranca** por chip
    (P126). El vivo sí tendría lugar.
- **La regla de "un objeto por foto: el más alto"** (de la tarjeta G4-B)
  deja casi invisibles al Chuck y al caparazón, porque la caja y la cinta
  ganan casi siempre. Cambiar la prioridad es una decisión de fidelidad,
  y queda para ti: por ejemplo, el enemigo más cercano a Mario, o dejar
  la caja y la cinta al final.
- Probar el vivo a mano en esta rama y decidir cuándo integrar a master.
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
