# PRÓXIMO — lo que sigue

2026-10-10. **Código en `g2t-b2bis`, sin merge ni push**; worktree:
`C:/Users/JC/Downloads/sma/wt-g2t-b2bis-1008`. Master conserva el código
anterior.

**G4-1 hecha (solo Python)**, ver `docs/informe-g4-1-1010.md`.
`plan_frame_n` ubica varios Rex por foto en los pares 4-5 y 6-7, con reuso
vertical (gap 1). En las 8 trazas hay 0 errores de color y 0 píxeles
tapados. Ningún Rex queda afuera por color ni por plazo: **el límite son
los canales**. hills2 sube de 1.893 a 2.498 Rex, stress_sprites de 1.040 a
1.305 y stress_back de 2.440 a 2.576. yi1 queda igual porque los Rex que
faltan comparten filas. Con un solo Rex el plan es igual al de hoy.
**Ahora: G4-2.**

Antes quedaron G5L-N (`informe-g5l-n-1010.md`), con la tabla `G5L2`, el
Rex aplastado y +84 KB de slow, y G4-A (`informe-g4a-1010.md`).

**D1 sigue roja**: back 373/4126 (racha 4), sprites 88/1914, normal BENCH
9/6312 (tanda de G5L-N). 50 Hz y colchón aceptados.

## 1. La próxima sesión, en orden

| tarjeta | responsable | ficheros / puerta | instrucciones |
|---|---|---|---|
| **G4-2** | coordinador; **en curso** | `player/g5l.s` y `tools/g5l.py`: el 68000 de `plan_frame_n` (hasta 4 Rex en los pares 4-7, encadenado DMA por lista, sin MOVE nuevos). Puerta: `g5l.py game --multi` exacto, regresión, memmap, A/B BENCH y captura con 2 Rex | `docs/instrucciones-g4-2.md` |
| G4-3 | después de G4-2 | los pares de Mario (0-1/2-3) fuera de sus filas: la cota de G4-1 §3 | (la escribe G4-2) |

Antes de cada commit: `python tools/lint_port.py` y `python tools/regress.py
--baseline tools/baseline_pc.json --level --g5l --bm1`, en verde.

## 2. Pendiente del usuario

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
