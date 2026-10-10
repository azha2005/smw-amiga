# PRÓXIMO — lo que sigue

2026-10-10. **Código en `g2t-b2bis`, sin merge ni push**; worktree:
`C:/Users/JC/Downloads/sma/wt-g2t-b2bis-1008`. Master conserva el código
anterior.

**G4-2 y G4-2o hechas; los 2 Rex por foto siguen apagados por defecto**
(`docs/informe-g4-2-1010.md`, `docs/informe-g4-2o-1010.md`). El 68000
ubica hasta 2 Rex con encadenado DMA, y es exacto. G4-2o abarató la foto
con 2 Rex (hills2: mediana de 63,5 k a 52,3 k ciclos; con un Rex, 25 k),
pero D1 sigue empeorando más que el ruido:

| replay | fotos perdidas, control | con 2 Rex |
|---|---:|---:|
| hills2 | 211 | 346 |
| sprites | 91 | 180 |
| back | 385 | 407 |

`-DG5L_MAXPL=2` los activa. **Ahora: G4-B, los demás enemigos de YI1**:
hoy solo se ven Mario y el Rex, y la piraña, el Chuck, los Koopa, la caja
de mensaje y la cinta de meta no se dibujan.

**D1 sigue roja**: back 385/4126 (racha 5), sprites 91/1914, hills2
211/2835 y normal BENCH 11/6312 (controles de esta tanda). 50 Hz y
colchón aceptados.

## 1. La próxima sesión, en orden

| tarjeta | responsable | ficheros / puerta | instrucciones |
|---|---|---|---|
| **G4-B** | coordinador; **en curso** | `tools/g5l.py`, `player/g5l.s` y la tabla: los demás enemigos de YI1 por G5L, un objeto por foto (el Banzai es bob, G7). Primero las formas y la referencia Python (0 errores de color), después el 68000. Puerta: `g5l.py game` exacto, memmap, A/B BENCH reportado como trade y capturas de la piraña y el Chuck | `docs/instrucciones-g4-b.md` |
| G4-3 | aparcada | Rex en los pares de Mario: solo tiene sentido con G4-2 activado | `docs/instrucciones-g4-3.md` |

Antes de cada commit: `python tools/lint_port.py` y `python tools/regress.py
--baseline tools/baseline_pc.json --level --g5l --bm1`, en verde.

## 2. Pendiente del usuario

- **Trade de los 2 Rex por foto** (G4-2/G4-2o): más Rex visibles (hills2
  +32 %) contra ≈ 1,6× fotos perdidas en hills2 y ≈ 2× en sprites. Hoy
  está apagado por la regla de la tarjeta. Un Rex que no entra no se
  dibuja: la cola de bobs es G7.
- Probar el vivo a mano en esta rama y decidir cuándo integrar a master.
  Novedad visible: el Rex aplastado sobre pendientes.
- **Solo como dato (no se propone):** S11 y L3 indican que el estrés back
  probablemente no entre en D1 solo con CPU. Con 5 planos (PF2 de 2) el
  ≈ 1,6× de los planos casi desaparecería, pero cambia D8 y el fondo. Es
  decisión tuya si alguna vez se quiere evaluar.
- En el checkout de master quedó sin commitear una versión vieja de
  `docs/investigacion-demoscene-1010.md` (264 líneas) y su fila en
  `docs/README.md`; la rama tiene la versión actualizada (320 líneas,
  `6797dd0`).
