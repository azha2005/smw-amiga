# PRÓXIMO — lo que sigue

2026-10-10. **Código en `g2t-b2bis`, sin merge ni push**; worktree:
`C:/Users/JC/Downloads/sma/wt-g2t-b2bis-1008`. Master conserva el código
anterior.

**S10 cerrada por su puerta; nada integrado.** El prototipo de speedcode
(`tools/s10_speedcode.py`) ocupa 118 480 B (vasm), contra 61 288 B de slow
libres en el vivo, y ahorra un 6,2 % de la CPU de `build_mid` en Musashi
(cota 13,5 %). El bucle por carga es solo el 30,6 % de `build_mid`; el resto
es trabajo fijo por línea. Informe: `docs/informe-g5l-r-s10-1010.md`.

**Lo que manda ahora es el hardware:** en back, `build_mid` llega al 180,4 %
del frame en WinUAE frente a ≈ 65 % en Musashi (≈ 2,8×). La lógica corre en
el borde (COPER, línea 272); `build_mid` corre en `dc_loop`, casi siempre en
líneas visibles, con 6 planos, el copper y la slow compartiendo el bus.
Esa hipótesis hay que medirla antes de otra optimización.

**D1 sigue roja** (sin cambios): back 387/4126 (9,38 %, racha 5), sprites
98/1914, normal BENCH 14/6312, VBTRACE 2. 50 Hz y colchón aceptados.

## 1. La próxima sesión, en orden

| tarjeta | responsable | ficheros / puerta | instrucciones |
|---|---|---|---|
| **G5L-R-M1** | coordinador, Sol high | flags opt-in de medida en `game.s`/`scroll.s` (`-DM1POS`, `-DM1NOBPL`, `-DM1BW`); pares por foto Musashi↔WinUAE, histograma de líneas de pantalla, reparto CPU/planos/copper+slow/blitter. Binario sin flags idéntico | `docs/instrucciones-g5l-r-m1.md` |
| **G5L-R-L3** | coordinador, Sol high; en paralelo con M1 (no depende de S10) | `logic68k.s`, `mspr68k.s`: elegir por perfil entre `mario_E2BD`, `spr_tile`, `mc_pxy`, cámara y Mario. Fuzz/copper/ABI exactos y A/B real; retirar si empeora | `docs/instrucciones-g5l-r-l3.md` |

M1 es solo medida: entrega una propuesta de tarjeta (mover la
reconstrucción al borde o a líneas sin fetch, partirla entre frames,
reducir accesos por línea o copper→blitter), sin implementarla. No
reintentar speedcode: la cota del 30,6 % no alcanza.

Antes de cada commit: `python tools/lint_port.py` y `python tools/regress.py
--baseline tools/baseline_pc.json --level --g5l --bm1`, en verde.

## 2. Pendiente del usuario

Probar el vivo a mano en esta rama; decidir cuándo integrar a master.
En el checkout de master quedó sin commitear una versión vieja de
`docs/investigacion-demoscene-1010.md` (264 líneas) y su fila en
`docs/README.md`; la rama tiene la versión actualizada (320 líneas,
`6797dd0`). Descartarla o no es decisión del usuario.
