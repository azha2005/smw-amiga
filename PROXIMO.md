# PRÓXIMO — lo que sigue

2026-10-10. **`g2t-b2bis` integrada a master** (sin push, a pedido del
usuario). El worktree `C:/Users/JC/Downloads/sma/wt-g2t-b2bis-1008` sigue
existiendo; se trabaja en master.

**G4-B y G9 hechas.**

- **G4-B** (`docs/informe-g4-b-1010.md`): con `G5L_TYPES=all`, G5L dibuja
  los demás enemigos de YI1 (piraña, Chuck, Koopa, caparazón, caja, cinta
  y `$02`). Exacto en el 68000. **Activado por defecto por el usuario
  (2026-10-10), con 2 objetos por foto (`G5L_MAXPL` = 2)**, aceptando que
  D1 empeora (1 por foto: normal 11 → 27, back 387 → 456, piranha 108 →
  131 fotos perdidas; con 2, más). `G5L_TYPES=AB` y `-DG5L_MAXPL=1`
  vuelven a lo anterior. **El replay con arranque Exec ya no entra en
  chip (P126): en WinUAE, `tools/bm_build.sh`** (arranque BM1).
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

- **Todos los tipos y 2 por foto, activados** (usuario, 2026-10-10). Falta
  el A/B de D1 con los dos juntos (la tanda de controles de arriba es con
  1 Rex por foto).
- **La regla de prioridad** (qué objetos se dibujan cuando no entran
  todos): hoy, de arriba abajo, hasta 2, y el segundo solo si no comparte
  filas con el primero (`bob_canal`) y hay índice de color (`bob_color`).
  Con 2 por foto el Chuck se ve 531 de 998 fotos y el caparazón 550 de
  938. Alternativas (decisión de fidelidad, del usuario): el más cercano
  a Mario, enemigos antes que la caja y la cinta, o mantener la elección
  de la foto anterior. El arreglo de fondo es la cola de bobs (G7).
- Probar en la Amiga real el ADF del vivo: `GDEFS=" " OUT=work/live sh
  tools/game_build.sh` → `work/live/smw.adf` (A500 con A501, 1 MB).
- **Solo como dato (no se propone):** S11 y L3 indican que el estrés back
  probablemente no entre en D1 solo con CPU. Con 5 planos (PF2 de 2) el
  ≈ 1,6× de los planos casi desaparecería, pero cambia D8 y el fondo. Es
  decisión tuya si alguna vez se quiere evaluar.
- En el checkout de master quedó sin commitear una versión vieja de
  `docs/investigacion-demoscene-1010.md` (264 líneas) y su fila en
  `docs/README.md`; la rama tiene la versión actualizada (320 líneas,
  `6797dd0`).
