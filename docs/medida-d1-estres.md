# D1: preparación de los replays de estrés

2026-10-06. Base de código: `07d4047`. **D1 pendiente de medida en WinUAE
real cycle-exact.** Este entorno Linux permite preparar y comprobar los
replays; no tiene WinUAE Windows. Unicorn y Musashi verifican CPU/lógica,
pero sus tiempos no sustituyen la medida con DMA. FS-UAE tampoco se usa
como sustituto para esta puerta.

## Construcción reproducible

Requiere el setup autorizado del proyecto: VBCC/vasm, fuente SMW, ROM local,
`player/gen`, assets y oráculos binarios generados. Nada derivado de la ROM
se versiona; las salidas y los logs quedan en `work/`.

```sh
export VBCC="$HOME/vbcc" PY=python3
export FSUAE_BASE=/tmp/fsuae-d1 FSUAE_DISPLAY=:79
CDEFS='-DNOOAM -DSPR_OAM' GDEFS='-DREPLAY -DBENCH' \
  ORACLE=work/oracle_stress_back.bin REPLAY=work/stress_back_replay.bin \
  OUT=work/d1-back sh tools/game_build.sh > work/d1-back-build.log 2>&1
NOCC=1 CDEFS='-DNOOAM -DSPR_OAM' GDEFS='-DREPLAY -DBENCH' \
  ORACLE=work/oracle_stress_sprites.bin REPLAY=work/stress_sprites_replay.bin \
  OUT=work/d1-sprites sh tools/game_build.sh > work/d1-sprites-build.log 2>&1
```

`game_build.sh` llama a `m68kverify.py --mode loop --sprites --oracle ...
--replay ...`. La clave `REPLAY.oracle` guarda SHA256 de oráculo y
`logicbench.bin`, para regenerar si cambian aunque sus fechas no lo indiquen.
Usar `NOCC=1` solo con las mismas opciones C ya compiladas (P36/P98).
Para replay alternativo se genera `OUT/game.replay.s`: cambia únicamente
el `incbin` a la ruta absoluta seleccionada. `player/game.s` y el replay
normal permanecen intactos. Vasm conserva flags, listado y PIC check.
Sin variables, continúa construyendo el replay de YI1.

| escenario | frames del oráculo | ops | RUN / LEVEL | bytes replay | bytes stage2 | PIC |
|---|---:|---:|---:|---:|---:|---|
| stress_back | 1453–5579 | 4127 | 4126 / 1 | 25486 | 199052 | 0 saltos/llamadas absolutos |
| stress_sprites | 1453–3367 | 1915 | 1914 / 1 | 12214 | 185780 | 0 saltos/llamadas absolutos |

Ambos lazos cerrados con sprites terminaron sin resincronizaciones. La
selección corresponde al tramo continuo más largo del oráculo, no a todos
sus registros. `STOPF` es relativo al inicio: aquí `F - 1453`, no `F - 5145`
(P75). `game_read.py` todavía imprime el desplazamiento fijo de YI1 5145:
su columna «oráculo» debe corregirse manualmente para estos escenarios.
Las advertencias preexistentes de vbcc (statement has no effect) y vasm
(entry conflicts with directive) no impidieron la construcción.

También se construyeron variantes `OUT=work/d1-back-check` y
`OUT=work/d1-sprites-check` con los mismos parámetros y
`GDEFS='-DREPLAY'`, y se ejecutó:

```sh
python3 tools/gamecheck.py --bin work/d1-back-check/game.bin \
  --lst work/d1-back-check/game.lst --oracle work/oracle_stress_back.bin --spr
python3 tools/gamecheck.py --bin work/d1-sprites-check/game.bin \
  --lst work/d1-sprites-check/game.lst --oracle work/oracle_stress_sprites.bin --spr
```

Resultado: 0 frames diferentes del oráculo; `mario_sprite` coincide en
4127/4127 y 1915/1915, incluido `mspr_draw` con dos buffers alternados.
No usar los binarios BENCH para este check en Unicorn (P97). En los dos
binarios BENCH se comprobó además que el replay elegido aparece íntegro
y una sola vez, y el harness temporal difiere solo en ese `incbin`.

`python3 tools/lint_port.py` y `VBCC="$HOME/vbcc" PY=python3 python3
tools/regress.py`: ambos **RESULTADO OK**. Cruces PC/68000 loop/spr:
6547/6549 llamadas con 0 diferencias RAM; memmap: 390704 B chip y 0
violaciones. La regresión informó 19 métricas mejores contra la referencia
cloud; no se actualizó baseline ni se atribuye una ganancia a D1 (esta
tarjeta no modifica el código del juego). Logs: `work/d1-lint.log` y
`work/d1-regress.log`.

## Captura y protocolo fijo

En Windows, cargar cada ADF en WinUAE usando una copia de `a500.uae` con
ROM KS1.2 y floppy0 local. Registrar versión WinUAE, SHA256 de ROM,
configuración realmente cargada, ADF, binario, datos, replay, oráculo y
commit. Valores obligatorios: OCS PAL, 68000, 512 KiB chip + 512 KiB slow,
sin fast, `cycle_exact=true`, `cpu_cycle_exact=true`,
`cpu_memory_cycle_exact=true`, `blitter_cycle_exact=true`, `cpu_speed=real`,
`immediate_blits=false`, `cachesize=0`, `floppy_speed=100`.
`tools/shot.ps1 -Exact -Adf ... -Out ...` sirve para la pantalla final
BENCH; sin `-Exact` los tiempos no valen (P30).

La pantalla final BENCH es evidencia parcial: contiene máximos/media,
`DC_NLOST` (fotos lógicas nunca dibujadas), `DC_REP` (VBL sin imagen nueva),
rachas de fotos lógicas perdidas y `DC_LATE` (COPER no llegó y la lógica
corrió en VERTB). **Estos pares no son equivalentes:** la puerta cuenta
VBL sin imagen nueva, no fotos descartadas; `DC_LATE` no demuestra un tick
perdido. La pantalla no contiene posición de cada omisión, ventana250,
edad ni distribución para p99. No inferir esos datos de sus agregados.
No sumar máximos de partes o escenarios distintos.

Falta implementar o disponer de un exportador de WinUAE por VBL. Esta
entrega no añade instrumentación al juego ni promete que WinUAE tenga
una API automática lista. El operador debe obtener una traza de RAM o
sondas revisadas, sin pausas que alteren la temporización. Debe observar
la foto **puesta** por `dc_vb`, después del cambio, no solo `DC_NPUB`:
`DC_FRONT` selecciona el registro `dc_rec`, cuyo `R_FRAME` identifica la
foto mostrada. El listado del mismo binario proporciona los símbolos;
no codificar direcciones de otro build. Registrar ticks realmente
terminados, con contadores extendidos sin wrap.

Para la traza completa, `tools/d1_count.py` recibe CSV:

```text
vbl,logic_frame,shown_frame,photo_ticks,tick_ticks
```

Primera fila: estado inicial con una foto válida, excluido del denominador.
Después una fila por VBL hasta el último VBL del tramo medido, sin huecos.
`logic_frame` cuenta ticks terminados, `shown_frame` es la foto puesta;
ambos usan el mismo origen lógico. `tick_ticks` mide el tick terminado en
ese intervalo; `photo_ticks` el tiempo integrado de preparación/render
de la foto nueva mostrada, con sus esperas y calibración, asociado a su
identidad. No sumar máximos de fases. Un campo de duración queda vacío
exactamente cuando no ocurrió su evento. La exportación debe conservar
por separado las fotos preparadas y descartadas si se quiere estudiar sus
tiempos: el p99 de esta herramienta corresponde a **fotos mostradas**.

```sh
python3 tools/d1_count.py work/d1-back/vbl.csv > work/d1-back/count.json
python3 tools/d1_count.py work/d1-sprites/vbl.csv > work/d1-sprites/count.json
```

El recuento entrega omitidas/total, porcentaje, racha máxima, peor ventana
de 250 VBL consecutivos y su inicio, edad de la foto en ticks lógicos,
ticks lógicos ausentes, media/p99/máximo de duraciones integradas en ticks
CIA-B. p99 usa rango más próximo (`ceil(0.99*N)`). 1 tick CIA-B PAL =
1/709379 s; edad lógica ×20 ms mientras la lógica cumpla 50 Hz. Si hay
ticks perdidos, la edad lógica subestima la edad en tiempo real: ampliar
el exportador con instante de captura para medirla también. Un salto de
foto cuenta fotos lógicas omitidas por separado de VBL repetidos.
Rechaza huecos, wrap, retrocesos, duraciones ausentes y más de un tick por
VBL, porque ese formato no representaría todos sus tiempos.

Puerta: objetivo 0 omisiones; mínimo ≤0.1%, racha ≤1 y ≤1 omisión en
cualquier ventana250. Menos de 250 VBL no demuestra el mínimo. El booleano
del JSON solo evalúa esos umbrales numéricos; la procedencia/configuración
y el alcance del juego requieren revisión externa. A/B con mismos flags,
assets, entradas y configuración salvo el cambio probado.

Escenarios: stress_back incluye la vuelta x `$1240`→`$0500`, revisar los
picos s≈2832 y 4580; stress_sprites incluye Banzai + tres Rex. Registrar
cámara x/y, sentido, Mario grande/poses, solapes, columnas, cambios de
mapa y estado del HUD/audio. Este build tiene O5 y OAM de sprites, pero
no el render definitivo G5, HUD ni audio. Sus resultados futuros valdrán
solo para ese alcance; repetir la prueba al integrarlos.

## Evidencia preparada y limitaciones

SHA256 de las salidas de la construcción anterior (R9: solo hashes):

```text
logicbench.bin       6451e5b681fd06ed6f50159b46cf7b22cc667e720f4d18e289057a671cc9ec76
yi1_s.dat            d9274027530ba5664dc928cf468299890ddb8850cab2ababa1835d1c9c8088e0
oracle_stress_back   bfdffcc3459cc94a28a62fcb4f1ec39274ebad7a2b16f9d19ad598fc4894b4f2
oracle_stress_sprites a5b2b0e6431c46b5907d661b8622cdf9a475056759066eab1344ecee9a936946
stress_back_replay   128394efbb743768c7477d4c4c6f8a605862546aa19533b539b9f99c794f52f5
stress_sprites_replay 89c916c7c3e426f71d72a1e97f7b337fc2c9cc8e243b143d714e84777cc1547d
d1-back/game.bin     fda191689958c226c62efc6ef366c380abfbe2ee803fad404576ab9293ee9dcd
d1-back/game.adf     9e1df3d89b4972f940e6d3b5f9f72346401a6f23715b5cf9b290ad619b184ca6
d1-sprites/game.bin  8e1cba5a56b88427fbab0b38303735f4dc272e3f343f9a824951b0c0f8ea994b
d1-sprites/game.adf  305c4e6c62eb0cea23d97aa3571163a2c50425c2b2f2776acd464dff0fae77f4
```

Verificación sintética del recuento: 1/1000=0.1% acepta, dos omisiones en
una ventana250 rechaza, dos contiguas dan racha2/edad2, p99 de 1..1000 es
990, hueco de VBL rechaza. **No son medidas del juego.**

No se han medido omitidas/total, porcentaje, racha, ventana250, edad,
ticks perdidos ni p99/máximo reales en estos dos escenarios. Falta WinUAE
real, exportador temporal completo y capturas cycle-exact contra referencia.
D1 sigue abierta; no hay comparación antes/después ni aprobación de
rendimiento basada en emulación de CPU.

Trampa propuesta para integrar: **Pnn — D1 exige distinguir `DC_NLOST`
de `DC_REP`, y racha de fotos lógicas de racha de VBL repetidos.** Los
agregados de BENCH no bastan para demostrar ventana250, edad o p99, y
`game_read.py` atribuye los frames a YI1 si se usa sin corregir el origen.
