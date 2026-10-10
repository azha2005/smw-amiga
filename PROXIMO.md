# PRÓXIMO — lo que sigue

2026-10-10. **Código en `g2t-b2bis`, sin merge ni push**; worktree:
`C:/Users/JC/Downloads/sma/wt-g2t-b2bis-1008`. Master conserva el código
anterior.

**G5L-N hecha e integrada en la rama** (`docs/informe-g5l-n-1010.md`).
La tabla del Rex pasa a `G5L2`, con la clave normalizada y las máscaras
una vez por forma. Ocupa 44.810 B en vez de 128.724, y la slow libre del
vivo sube de 61 a 145 KB. **El Rex aplastado sobre una pendiente ya se
dibuja**: en `hills2`, 340 frames → 0 sin forma. En la foto 1720, la
captura WinUAE es el control más el Rex planeado, con 0 de 327.680
píxeles distintos. El A/B BENCH no empeora (normal 14→9, back 392→373,
sprites 98→88). Trampa nueva: P124. **Ahora: G4-1.**

G4-A (medida) quedó antes (`docs/informe-g4a-1010.md`): 9 tipos con
gráfico, ninguno de más de 15 colores. El Banzai es bob, y el bob y el
audio no entran en chip hasta C2/C4 + C3.

**D1 sigue roja**: back 373/4126 (racha 4), sprites 88/1914, normal BENCH
9/6312 (tanda de G5L-N). 50 Hz y colchón aceptados.

## 1. La próxima sesión, en orden

| tarjeta | responsable | ficheros / puerta | instrucciones |
|---|---|---|---|
| **G4-1** | coordinador; **en curso** | `tools/g5l.py` (`plan_frame_n`, `check_trace_n`, `trace --multi`), solo Python: varios Rex por foto en los pares 4-5 y 6-7, con reuso vertical y colores compartidos con Mario. Puerta: 0 errores de color en las 8 trazas; cada Rex visible queda dibujado o en la cola de bobs con su motivo | `docs/instrucciones-g4-1.md` |
| G4-2 | después de G4-1 | el 68000 de `plan_frame_n` en `g5l.s`, `g5l.py game` exacto, A/B | (la escribe G4-1) |

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
