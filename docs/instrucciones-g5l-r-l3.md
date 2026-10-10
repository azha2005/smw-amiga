# G5L-R-L3 — recortes de los núcleos asm restantes

2026-10-10. Tarjeta posterior a la puerta de S10. Misma rama/worktree,
sin merge ni push. La lógica caliente de L2 ya está en asm; esto es
optimizar lo existente, conservando el C como referencia.

## Partida y reglas

Leer `instrucciones-g5l-r-l2.md`, ABI de AGENTS §7, P36/P40/P69/P74/P102/
P116/P123 y `informe-p123-scroll-1010.md`. FinishOAM ahorraba 80 ciclos,
pero el candidato combinado empeoró BENCH; se retiró. No resucitarlo
solo por su cota de CPU. No tocar la recarga de `a2` en `dc_loop`.

```sh
export PATH="$TEMP/pyshim:/c/msys64/ucrt64/bin:$PATH" VBCC=/c/Users/JC/vbcc PY=python
python tools/lint_port.py
python tools/regress.py --baseline tools/baseline_pc.json --level --g5l --bm1
GDEFS='-DREPLAY' OUT=work/l3/control sh tools/game_build.sh
python tools/g5l.py game --bin work/l3/control/game.bin --lst work/l3/control/game.lst \
  --pcprof work/l3/control_pc.json --pclogic 1020-1130,1690-1715,2050-2080,2730-2760,3280-3370,4195-4225
```

Esperado: lint/regresión `RESULTADO: OK` y `G5L GAME: OK`. Archivar los
binarios/listados del control antes de cambiar asm. No construir dos
veces a la vez: el pipeline comparte `work/cc` y datos generados.

## Pasos

1. Elegir por el perfil nuevo entre `mario_E2BD`, `spr_tile`, `mc_pxy`,
   cámara y `mspr_draw`. Consultar el C y medir por rama antes de editar
   `logic68k.s`/`mspr68k.s`. Identificar llamadas repetidas, índices,
   cargas y cambios de endian; distinguir un coste propio del de un hijo.
2. Un cambio por vez. Medir media/máximo de la función con la misma RAM.
   Una optimización que gane menos del 25 % de esa función se retira,
   salvo que elimine un pico integrado medido y se justifique con el A/B.
3. Para una función pública o exportable, `fuzzcall.py` con al menos
   20.000 casos y la RAM real; comparar toda la RAM, mapas, retorno y
   globales escritos. Ejemplo para el núcleo con contrato ya comprobado:

   ```sh
   CDEFS='-DNOOAM -DSPR_OAM' sh tools/logicbench_build.sh
   python tools/fuzzcall.py --func finish_oam_write --export spr_gfx.c --asm _finish_oam_write_asm \
     --arg 0-11 --arg 0-255 --arg 0-255 --src player/spr_gfx.c \
     --cdefs '-DNOOAM -DSPR_OAM' --n 20000
   ```

   Para rutinas internas (`mc_pxy`) verificar el llamador y un arnés
   dirigido que cubra el contrato de registros y flags. `mspr_draw`
   requiere buffers/píxeles contra el C y todos los niveles de caché;
   no basta con comparar los ciclos de una pose. La opción `--src`
   controla qué bytes muta fuzzcall; limitar índices que el C considera
   válidos con `--keep`/`--setx`, sin ocultar ramas soportadas.
4. Regresión completa, PC=68000 y oráculos exactos; `g5l.py game` y
   `dc_loop_verify.py` en los tres replays, memmap/PIC. Para cambios OAM,
   `sh tools/oam68k_gate.sh`: `OAM68K: OK`.
5. A/B WinUAE con los comandos de S10 §5, ambas partes con P123 corregida.
   BENCH en normal/back/sprites y VBTRACE normal, sin mezclar las cifras
   del bucle defectuoso de L2. Guardar una captura de juego y observarla.
6. Informe por función: semántica, ramas cubiertas/no cubiertas, ciclos
   CPU y medidas reales, memoria y fuentes. Red verde antes del commit
   local en español; reescribir PROXIMO y estados según ROADMAP §7.

## Paradas

PC=68000, cobre, píxeles o ABI diferentes: revertir ese cambio. BENCH o
VBTRACE peores: retirarlo y parar, aunque Musashi mejore. Tres intentos
sin pasar la puerta: documentar y cerrar. No modificar la base ni
rebajar una comprobación para aceptar un recorte.
