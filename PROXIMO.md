# PRÓXIMO — lo que sigue

2026-10-10. **Código en `g2t-b2bis`, sin merge ni push**; worktree:
`C:/Users/JC/Downloads/sma/wt-g2t-b2bis-1008`. Master conserva el código
anterior.

**G4-2 hecha, pero apagada por defecto** (`docs/informe-g4-2-1010.md`).
El 68000 ubica hasta 2 Rex por foto, separados en vertical, con encadenado
DMA por lista y sin MOVE nuevos en el copper:

- `g5l.py game` es exacto en yi1, hills2, stress_sprites y stress_back.
- Capturas de hills2 con el segundo Rex: 0 píxeles distintos.

Una foto con 2 Rex cuesta ≈ 63 k ciclos contra ≈ 25 k, y **D1 empeora**:

| replay | fotos perdidas sin G4-2 | con G4-2 |
|---|---:|---:|
| hills2 | 210 | 398 |
| sprites | 91 | 194 |
| back | 380 | 418 |

Por eso `G5L_MAXPL` = 1 por defecto. Con `-DG5L_MAXPL=2` se dibujan más
Rex: en hills2, de 1.893 a 2.498. **Ahora: G4-2o, abaratarlo.**

**D1 sigue roja**: back 380/4126 (racha 5), sprites 91/1914, hills2
210/2835 y normal BENCH 11/6312 (control de la tanda de G4-2). 50 Hz y
colchón aceptados.

## 1. La próxima sesión, en orden

| tarjeta | responsable | ficheros / puerta | instrucciones |
|---|---|---|---|
| **G4-2o** | coordinador; **en curso** | `player/g5l.s`: el camino de varios Rex más barato (rápido sin bandas, caché, `g5l_emitn`). Puerta: `g5l.py game` exacto con MAXPL 1 y 2; A/B BENCH con MAXPL 2 dentro del ruido del control → el defecto pasa a 2 | `docs/instrucciones-g4-2o.md` |
| G4-3 | después de G4-2o | Rex en los pares de Mario (0-1/2-3) fuera de sus filas: la referencia con colores y prioridad primero | `docs/instrucciones-g4-3.md` |

Antes de cada commit: `python tools/lint_port.py` y `python tools/regress.py
--baseline tools/baseline_pc.json --level --g5l --bm1`, en verde.

## 2. Pendiente del usuario

- **Trade de G4-2, si querés decidirlo antes de G4-2o:** más Rex visibles
  (hills2 +32 %) contra ≈ 2× fotos perdidas en los replays con muchos Rex.
  Hoy queda apagado (la regla de la tarjeta). Un Rex que no entra no se
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
