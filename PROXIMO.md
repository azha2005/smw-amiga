# PRÓXIMO — lo que sigue

2026-10-10. **Código en `g2t-b2bis`, sin merge ni push**; worktree:
`C:/Users/JC/Downloads/sma/wt-g2t-b2bis-1008`. Master conserva el código
anterior.

**P123 corregida y verificada.** `columns` destruía `a2`; el bucle G5L
leía una foto falsa y `g5l_choose` pisaba `GV_TAB`. Recarga de `dc_st`
antes de leer `DC_REND`; nuevo `dc_loop_verify.py` en la regresión.
Guru viejo reproducido con watchpoint; e7234ab + arreglo, 150 s en
WinUAE cycle-exact sin excepción. Informe:
`docs/informe-p123-scroll-1010.md`.

**Perfil hecho; optimización detenida por su puerta.** Domina `bm_left`
en la vuelta. Los recortes `bm_share`/FinishOAM eran exactos y ahorraban
CPU, pero empeoraron BENCH (back 387 → 389, sprites 98 → 104), por lo
que se retiraron. No está implementado el generador de speedcode.

**D1 sigue roja con el bucle corregido:** back 387/4126 (9,38 %, racha 5),
sprites 98/1914 (5,12 %, racha 3). Normal: VBTRACE 2 omitidas; BENCH
14/6312 (0,22 %, racha 1). Las cifras de L2 con el
bucle defectuoso quedan históricas; no sirven de control para el código
corregido. Se mantienen 50 Hz y el colchón aceptado.

## 1. La próxima sesión, en orden

| tarjeta | responsable | ficheros / puerta | instrucciones |
|---|---|---|---|
| **G5L-R-S10** | coordinador, Sol high | `mkscroll.py`, `scroll.s`, pipeline y arnés. Prototipo offline de speedcode por línea/tramo; demostrar tamaño y ahorro antes de integrar. Copper exacto en los tres replays, memoria/PIC válidos, BENCH/VBTRACE mejores contra el control con P123 corregida | `docs/instrucciones-g5l-r-s10.md` |
| **G5L-R-L3** | coordinador, Sol high; después de la puerta S10 | `logic68k.s`, `mspr68k.s`: elegir por perfil entre `mario_E2BD`, `spr_tile`, `mc_pxy`, cámara y Mario. Fuzz/copper/ABI exactos y A/B real; retirar si empeora | `docs/instrucciones-g5l-r-l3.md` |

S10 empieza por coste y memoria: MLD 3.409 cargas útiles, 125.296 B de
slow libres en BENCH back (no es el margen de todos los builds). Si
domina la espera en hardware, medirla antes de elegir copper→blitter.
No repetir recortes de CPU sin su puerta integrada. No hace falta una
elección nueva del usuario para esta investigación/optimización ya autorizada.

Antes de cada commit: `python tools/lint_port.py` y `python tools/regress.py
--baseline tools/baseline_pc.json --level --g5l --bm1`, en verde.

## 2. Pendiente del usuario

Probar el vivo a mano en esta rama; decidir cuándo integrar a master.
