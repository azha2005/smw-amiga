# Revisión e integración A1, G8b y preparación D1 — 2026-10-06

El coordinador revisó los cambios y repitió sus puertas en las ramas y
en el árbol conjunto. Se integra el conversor A1, la OAM ampliada G8b
como opción y la preparación D1. D1 no se declara medida ni aprobada.

## Revisión y evidencia

- A1: cuatro pruebas CLI, 1024 bloques sintéticos y las 20 muestras reales
  contra `dsp_decodeBrr` original de snesrev. **0 diferencias PCM16**;
  correlación mínima PCM8/PCM16 0,99963021. El lote ocupa **50560 B**,
  dentro de 65536 B. El informe A1 conserva la evidencia de los 13 loops
  y explica por qué repetir una vuelta PCM fija no basta para 12 de ellos.
- D1: se revisaron la clave de caché por hashes y el cambio acotado de
  `incbin` en un harness temporal. Se repitieron ambos replays con las
  tres ramas juntas: **4127/4127** y **1915/1915** coincidencias de Mario
  y doble buffer, **0 frames distintos del oráculo**. También compilaron
  los dos ADF BENCH, con **0 llamadas/saltos absolutos**.
- Recuento D1: seis pruebas sintéticas persistentes comprueban el límite
  0,1 %, ventanas móviles con separación 249/250, racha, edad, fotos
  saltadas, ticks perdidos, p99 y rechazo de trazas discontinuas. Sus
  resultados no son medidas del juego.
- G8b: se revisaron los enganches C/asm, la extracción de tablas y los
  puentes PIC cercanos a cada emisor. Se repitieron cinco trazas con el
  compilador real y Musashi: **18076 despachos**, **0 diferencias de
  RAM/mapa/marcas/ABI** y **3150/3150 OAM exactas**, orden 0. Se revisaron
  las reconstrucciones PNG de Banzai y piraña, referencia SNES arriba y
  OAM 68000 abajo. Son evidencia de OAM, no capturas OCS.
- Cruce opt-in: **6549 llamadas, 0 RAM distintas**. Juego opt-in completo:
  **6313 operaciones, 0 frames distintos**, Mario/doble buffer 6184/6184.
  PIC: logicbench 14882 y juego 17241 instrucciones, **0 absolutas**.
- Memoria replay: chip **390704 B**, slow opt-in **214880 B**,
  **0 violaciones**. También compilaron PROF normal/opt-in y el modo
  en vivo normal/opt-in, todos sin absolutas. En vivo: chip **402232 B**,
  slow normal **242640 B** y opt-in **251120 B**, **0 violaciones**.
  El ADF normal en vivo queda en `work/live/game.adf`; no se probó su
  arranque en emulador. La regresión normal con `--level` pasa, con RAM
  PC/68000 idéntica.

Los logs de revisión están en `/tmp/review-a1.log`, `/tmp/review-d1.log`,
`/tmp/review-g8b.log`, `/tmp/integrated-stress.log` y
`/tmp/integrated-variants.log` y `work/regress.log`; las salidas derivadas están en `work/review_*` y
`work/integrated_*`, ignoradas por git. Las métricas de OAM nuevas y la
cobertura `stress_piranha` añaden **41 campos** a cada baseline cloud/PC.
Se comprobaron intactos todos los valores previos; no se cambiaron
tolerancias ni se aceptó un empeoramiento de rendimiento por ese medio.

## Comandos de reproducción

Con el setup del proyecto ya preparado:

```sh
export VBCC="$HOME/vbcc" PY=python3
python3 tools/test_brr2pcm.py
python3 tools/test_d1_count.py
python3 tools/brr2pcm.py ../smw-src-master/project/mw_e10/sound/samples \
  --selftest --reference-dsp "$HOME/.cache/snesrev-smw/src/snes/dsp.c"
python3 tools/lint_port.py
python3 tools/regress.py --level
```

Las cinco trazas OAM, cruce RAM, variante PROF y medida Musashi se
reproducen con los comandos de `validacion-g8b.md`. Para repetir ambos
escenarios de estrés con OAM ampliada:

```sh
for name in stress_back stress_sprites; do
  CDEFS='-DNOOAM -DSPR_OAM' GDEFS='-DREPLAY' \
    ORACLE=work/oracle_$name.bin REPLAY=work/integrated_$name.bin \
    OUT=work/integrated_$name sh tools/game_build.sh
  python3 tools/gamecheck.py --bin work/integrated_$name/game.bin \
    --lst work/integrated_$name/game.lst --oracle work/oracle_$name.bin --spr
  NOCC=1 CDEFS='-DNOOAM -DSPR_OAM' GDEFS='-DREPLAY -DBENCH' \
    ORACLE=work/oracle_$name.bin REPLAY=work/integrated_$name.bin \
    OUT=work/integrated_${name}_bench sh tools/game_build.sh
done
```

## Límites

G8b continúa **opt-in**: la lógica alcanza **62110 ciclos, 43,8 % PAL**
en Musashi **sin DMA**; el total máximo es 132650 ciclos, 93,5 %. Esto
reabre el objetivo de lógica ≤40 % para la OAM ampliada. No se activa por
defecto ni se atribuye una ganancia de fluidez al resultado de CPU.

No hubo WinUAE ni nuevas medidas/capturas cycle-exact. D1 necesita aún
un exportador completo por VBL; los agregados BENCH no demuestran racha
de VBL, ventana250, edad ni p99. R8 WAV y escucha siguen pendientes.
No se cerraron el banco G2/G3, el render de enemigos G5, HUD ni audio
reproducido. Los límites de meta/caparazones no cubiertos se conservan
en `validacion-g8b.md`.
