# G5L-R-Pa — ¿el plan de G5L se puede reutilizar a otra altura? (medida)

2026-10-09. **Necesita la autorización del usuario antes de empezar**
(parada de T; `docs/informe-g5l-r-t2-1009.md` §5). Es la primera fase de
la propuesta P-a: **solo medida, offline, en Python. No se toca código del
juego.**

## Por qué existe

T2 (`informe-g5l-r-t2-1009.md` §4.1): los 25 saltos de VBTRACE son atraso
acumulado por rachas de fotos caras (21/25 en el modelo de cola). La fuente
más grande es el **camino lento de G5L**: 145 de 6312 fotos con
`g5l_sweep`/`g5l_plan`, `g5l_render` medio 66 056 ciclos contra 9 172.
En los 145 fallos cambió la forma del Rex (`GV_VLIST`) y en 109 la altura
relativa a Mario (`GV_MSH`; `GV_R0` en 52). Agrandar la caché no sirve
(26/145 sin límite). Sin `R0`/`MSH` en la clave, una FIFO de 4 acertaría
36 (sin los punteros de Mario además, 84). Eso **solo vale si el plan es
el mismo corrido** a otra altura, y no está demostrado: el plan sale de qué
filas del Rex chocan con qué filas de Mario.

Estimado del modelo: con sweep + plan gratis en los fallos, 25 → 8-12
saltos; junto con S5 (`build_mid`), 0-4.

## Reglas

- Worktree `C:/Users/JC/Downloads/sma/wt-g2t-b2bis-1008`, rama `g2t-b2bis`;
  sin merge/push. R9. Ninguna WinUAE hace falta en esta fase.
- Solo herramientas (`tools/g5l.py`, `tools/t2_keys.py` o una nueva). Los
  cinco MD5 del defecto no cambian (`informe-cierre-v-bm1-1009.md` §2).
- La referencia del plan es `tools/g5l.py plan_frame` (la que `G5L GAME`
  compara contra el asm byte a byte).

## Partida verde

```sh
export PATH="$TEMP/pyshim:/c/msys64/ucrt64/bin:$PATH" VBCC=/c/Users/JC/vbcc PY=python
python tools/lint_port.py                       # RESULTADO: OK
GDEFS=-DREPLAY OUT=work/t2/replay sh tools/game_build.sh
md5sum work/t2/replay/game.bin                  # 4328e9c83a309e7527c62d0da7e3a6c4
python tools/g5l.py game --bin work/t2/replay/game.bin --lst work/t2/replay/game.lst | tail -1
# G5L GAME: OK
cp work/g5l/game_frames.json work/t2/frames.json
python tools/t2_keys.py --frames work/t2/frames.json --csv work/t2/frames.csv | sed -n 18,20p
#   sin -             N=4:   0  N=8:   8  N=16:  11  N=1000000:  26
#   sin R0+MSH        N=4:  36  ...
#   sin R0+MSH+ptrs   N=4:  84  ...
```

(`work/t2/frames.csv` sale de `t2_attrib.py`, comando en el informe T2.)

## Pasos

1. **Guardar el plan de Python por foto.** En `run_game` (`tools/g5l.py`),
   para cada foto con `p`: `vo`, `r0`, `groups`, `remaps` y `trans` (lo que
   devuelve `plan_frame`, `g5l.py:516`), y si la foto es fallo
   (`g5l_sweep` en `parts`). Salida en `work/t2/plans.json`. Puerta: `G5L
   GAME: OK` y las mismas 145 fotos de fallo.
2. **Comparar con corrimiento.** Simular la FIFO de 4 con la clave sin
   `R0`/`MSH` (como `t2_keys.fifo_hits`) y, en cada acierto, comparar el
   plan de la foto con el de la foto que dejó esa entrada: `vo`, `groups`
   y `remaps` iguales, y `trans` igual con las filas corridas en
   `Δ = r0_k − r0_j`. Contar iguales y distintos; repetir sin los
   punteros (84 aciertos). Para los distintos, la primera diferencia.
3. **Puerta de la fase:** si son iguales **≥ 80 %** de los aciertos de una
   de las dos claves, escribir el diseño (dónde se corre el resultado:
   `g5l_place` ya recibe la x de la foto; la fila es nueva) con su coste
   estimado y re-correr `t2_keys.py`/`t2_model.py` contando solo los
   aciertos válidos. Si queda por debajo, decirlo: la vía es abaratar
   sweep + plan en asm (perfil por rutina en Musashi) y S5.

## Paradas

- Paso 1 cambia `G5L GAME` o el número de fallos → parar: el volcado
  alteró la corrida.
- Cualquier cambio en `player/` → fuera de alcance.
- No implementar el diseño: necesita otra autorización con el número de
  la puerta.

## Informe

`docs/informe-g5l-r-pa-<fecha>.md`: el número de planos iguales tras el
corrimiento (por clave), las primeras diferencias de los distintos, el
contrafáctico del modelo con solo los aciertos válidos, y la
recomendación (clave reducida, asm o S5 primero). Cerrar según ROADMAP §7.
