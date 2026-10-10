# PRÓXIMO — lo que sigue

2026-10-10. **Código en `g2t-b2bis`, sin merge ni push**; worktree:
`C:/Users/JC/Downloads/sma/wt-g2t-b2bis-1008`. Master conserva el código
anterior.

**M1 hecha (solo medida).** El ≈ 2,8× de `build_mid` en el hardware se
reparte en dos partes: fotos omitidas ≈ 1,6× (Musashi con la secuencia real
de la Amiga: 146.860 ciclos contra 92.078) y DMA de los 6 planos ≈ 1,6×
(sin planos, WinUAE queda a 1,07 de Musashi). Copper, slow y blitter juntos
suman ≈ 6-9 %. Los picos son una **espiral en la vuelta**: cada lista se
reescribe con un |Δs| creciente (−12 … −48); con |Δs| > 16 hay 86 fotos de
10.386 ticks de media. Informe: `docs/informe-g5l-r-m1-1010.md`.

S10 (speedcode) quedó cerrada antes: 118 KB, −6,2 % de CPU, no cabe en el
vivo (`docs/informe-g5l-r-s10-1010.md`).

**D1 sigue roja** (control sin cambios): back 387/4126 (9,38 %, racha 5),
sprites 98/1914, normal BENCH 14/6312, VBTRACE 2. 50 Hz y colchón aceptados.

## 1. La próxima sesión, en orden

| tarjeta | responsable | ficheros / puerta | instrucciones |
|---|---|---|---|
| **G5L-R-S11** | coordinador, Sol high | `player/scroll.s` (`bm_left`, LNS de `mkscroll.py`): medir por línea en las fotos de la espiral; candidatos A (buscar desde `prevlt`) y B (LNS para \|Δs\| ≤ 48). Lista exacta en los tres replays y A/B WinUAE con menos fotos perdidas | `docs/instrucciones-g5l-r-s11.md` |
| **G5L-R-L3** | coordinador, Sol high; después o en paralelo | `logic68k.s`, `mspr68k.s`: elegir por perfil entre `mario_E2BD`, `spr_tile`, `mc_pxy`, cámara y Mario. Fuzz/copper/ABI exactos y A/B real; retirar si empeora | `docs/instrucciones-g5l-r-l3.md` |

Herramientas nuevas para medir: `-DM1POS` (+ `tools/m1_read.py`) da una fila
por foto dibujada en WinUAE y `g5l.py game --render-list` repite esa
secuencia en Musashi. Cada ciclo de CPU que se ahorra en la vuelta vale
doble: lo multiplican los planos y baja el Δs de la espiral.

Antes de cada commit: `python tools/lint_port.py` y `python tools/regress.py
--baseline tools/baseline_pc.json --level --g5l --bm1`, en verde.

## 2. Pendiente del usuario

- Probar el vivo a mano en esta rama y decidir cuándo integrar a master.
- **Solo como dato (no se propone):** con 5 planos (PF2 de 2) el ≈ 1,6× de
  los planos casi desaparecería, pero cambia D8 y el fondo. Es decisión
  tuya si alguna vez se quiere evaluar.
- En el checkout de master quedó sin commitear una versión vieja de
  `docs/investigacion-demoscene-1010.md` (264 líneas) y su fila en
  `docs/README.md`; la rama tiene la versión actualizada (320 líneas,
  `6797dd0`).
