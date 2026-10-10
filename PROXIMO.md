# PRÓXIMO — lo que sigue

2026-10-10. **Código en `g2t-b2bis`, sin merge ni push**; worktree:
`C:/Users/JC/Downloads/sma/wt-g2t-b2bis-1008`. Master conserva el código
anterior.

**G4-A hecha (solo medida)** (`docs/informe-g4a-1010.md`). Con trazas
exactas de las 30 grabaciones aparecen 9 tipos con gráfico; ninguno pasa
de 15 colores. **Hallazgo:** G5L no dibuja el Rex aplastado cuando
aparece con otro desplazamiento vertical: 340 de 2.110 frames con Rex en
`hills2`, también en `stress_*`, `shells` y `pw_estrella`. Con la clave
normalizada, 30 de esas 33 formas ya están en el banco, y el Rex baja de
48 a 22 formas. La tabla G5L de todos los enemigos solo entra en slow con
la clave normalizada y las máscaras compartidas (83 KB con 4 mapas). El
Banzai como bob (+59 KB) y el audio no entran en chip hasta C2/C4, que
además necesitan compresión (C3). **Ahora: G5L-N.**

L3 quedó cerrada antes, sin integrar (`docs/informe-g5l-r-l3-1010.md`):
ningún recorte de la lógica mueve D1.

**D1 sigue roja** (control sin cambios): back 387/4126 (9,38 %, racha 5),
sprites 98/1914, normal BENCH 14/6312, VBTRACE 2. 50 Hz y colchón aceptados.

## 1. La próxima sesión, en orden

| tarjeta | responsable | ficheros / puerta | instrucciones |
|---|---|---|---|
| **G5L-N** | coordinador; **en curso** | `tools/g5l.py` (formato `G5L2`), `player/g5l.s` (`g5l_choose`, `g5l_patch`): clave normalizada y máscaras una vez por forma. Puertas: `g5l.py trace` con las trazas nuevas (`rex_sin_forma` ≤ 3 formas), `g5l.py game`, regresión, memmap, A/B BENCH y captura de `hills2` | `docs/instrucciones-g5l-n.md` |
| G4 + G6 | después de G5L-N | el plan G5L para N objetos con el formato `G5L2`; Rex con 4 mapas y los demás con 1 (chip) | `docs/instrucciones-olas.md` §3, `informe-g4a-1010.md` §6 |

Antes de cada commit: `python tools/lint_port.py` y `python tools/regress.py
--baseline tools/baseline_pc.json --level --g5l --bm1`, en verde.

## 2. Pendiente del usuario

- Probar el vivo a mano en esta rama y decidir cuándo integrar a master.
- **Solo como dato (no se propone):** S11 y L3 indican que el estrés back
  probablemente no entre en D1 solo con CPU. Con 5 planos (PF2 de 2) el
  ≈ 1,6× de los planos casi desaparecería, pero cambia D8 y el fondo. Es
  decisión tuya si alguna vez se quiere evaluar.
- En el checkout de master quedó sin commitear una versión vieja de
  `docs/investigacion-demoscene-1010.md` (264 líneas) y su fila en
  `docs/README.md`; la rama tiene la versión actualizada (320 líneas,
  `6797dd0`).
