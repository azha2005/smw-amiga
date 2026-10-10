# PRÓXIMO — lo que sigue

2026-10-10. **Código en `g2t-b2bis`, sin merge ni push**; worktree:
`C:/Users/JC/Downloads/sma/wt-g2t-b2bis-1008`. Master conserva el código
anterior.

**L3 cerrada, sin integrar** (`docs/informe-g5l-r-l3-1010.md`): el perfil
de la lógica es plano (nada pasa del 10 %). La caché de `mspr_draw` era
exacta pero subía el máximo un 28 %, así que se retiró. El C que queda
pesa 0,8 % en YI1 y 5,7 % en back. Con S10, S11 y M1, el estrés no tiene
recortes de CPU con margen medido. Lo que lo separa de D1 es la
reconstrucción de la vuelta multiplicada por el DMA de los 6 planos.
**Ahora: ola 4, por G4-A.**

**D1 sigue roja** (control sin cambios): back 387/4126 (9,38 %, racha 5),
sprites 98/1914, normal BENCH 14/6312, VBTRACE 2. 50 Hz y colchón aceptados.

## 1. La próxima sesión, en orden

| tarjeta | responsable | ficheros / puerta | instrucciones |
|---|---|---|---|
| **G4-A** | coordinador; **en curso** | `tools/g4a.py` (nuevo), solo en la PC: inventario por tipo de enemigo, columnas por línea fuera de Mario, cota de bobs y memoria de la tabla G5L para todos. Puerta de cruce: el Rex da las 48 formas del banco | `docs/instrucciones-g4a.md` |
| G4 + G6 | después de G4-A | el plan G5L para N objetos, con el formato de tabla que salga de G4-A | `docs/instrucciones-olas.md` §3 |

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
