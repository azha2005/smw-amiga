# G3 — formato verificable y banco pendiente (2026-10-05)

Se implementó SG3F/1: descriptores BE sin punteros absolutos, composición
por orden OAM, recorte con origen, columnas attached alineadas a ocho,
fuente planar de bob y máscara, mapas SNES→OCS por fila y reservas de los
índices de Mario. La ida y vuelta decodifica los archivos emitidos y
comprueba cada posición, índice, transparencia, orden y color. El formato
se documenta en `formato-sprgfx.md`. No se cambió código del juego.

**G3 final sigue pendiente; hay que reabrir G2 antes del asignador y del
simulador definitivos.** La estrategia actual de variantes exactas supera
el banco y la RAM para tablas. Esto no demuestra un mínimo matemático ni
autoriza aproximar colores. No se solicita cambiar la fidelidad.

## Resultados reproducibles

| lote / puerta | poses | chip / slow | resultado |
|---|---:|---:|---|
| fichas individuales observadas, 31 grabaciones | 241 | 37752 / 26312 B | 30338 píxeles, 0 diferencias |
| poses compuestas SOT1 + Rex legal | 48 | 10840 / 5276 B | 16431 píxeles, 0 diferencias |
| variantes con reservas reales de Mario, tres trazas, ocho paletas | 2593 | 145600 B requeridos por esta estrategia | 1241670 píxeles exactos, 0 rechazos COLOR |
| subconjunto de variantes que entra en el banco | 1724 | 65512 / 693884 B | 824686 píxeles exactos; 869 rechazos BANK |

La fila de 145600 B es una **medida sin emisión de banco cargable**. Todos
sus flujos/fuentes también se decodificaron. El archivo `.dma` emitido solo
contiene 65512 B; los 869 rechazos devuelven código 1. Las tablas del lote
parcial ocupan 693884 B pese a internar fichas, tablas de columnas y mapas:
el número de variantes/reservas hace inviable cargar ese conjunto entero
en slow. El lote base de 48 poses necesita solo 5276 B de tablas.

Las tres estrategias ensayadas fueron: asignación greedy por fila (662
variantes dentro de 64 KiB), mapa estable por pose con backtracking y
fallback exacto (1000), y reuso de mapas previos compatibles (1724).
Ninguna produjo un banco completo; la tercera es la implementación que
queda. Los dos primeros resultados son diagnósticos de las estrategias,
no puertas satisfechas ni cotas mínimas.

Caso concreto conservado en `work/sprgfx_mario_reuse.json`: la variante
`trace_ab_f6784_m0_828` requiere que el banco pase de su ocupación admitida
a 65968 B. El JSON distingue BANK de COLOR y conserva el nombre, frame y
variante; la receta exacta está en `work/sprgfx_mario_rows.json`. Otros
868 casos se listan, sin descartarlos silenciosamente.

## Cobertura y límites

Se extrajo pertenencia real de SOT1, sin `assign()` ni proximidad, y se
cotejó la secuencia visible de cada despacho con la OAM grabada del mismo
frame. YI1/normal/spin_kill suman **AB 4082, BD 594, 02 415, B9 307**
despachos exactos. Rex agrega las seis poses de `RexGfxRt`, ambas
direcciones, desde `RexTileDispX/Y`, `RexTiles` y `RexGfxProp` del fuente
ROM; incluye combinaciones que esos replays no recorren. La prioridad
normal es `$20`; las variantes de muerte/prioridad fuera de las trazas
siguen pendientes. Las poses del giro se incluyen en las trazas reales.

Las reservas reales de Mario salen de la VRAM dinámica reconstruida con
RAM `$0D85/$0D99` y GFX32, como `gamecheck.spr_ok`. La selección identifica
entradas por dirección de VRAM dinámica y paleta 0; no inventa un dueño.
Conserva el índice de Mario y prueba las ocho variantes OCS de
`mkmario.py` en las alturas coincidentes de esos replays. Las entradas de
partículas que compartan esa VRAM/paleta también se reservan. Reservar
Mario aunque otro enemigo lo tape puede ser conservador.

Una auditoría adicional de la unión de todo GFX32 encuentra catorce índices
opacos y rechaza 360 de 384 variantes. Esa unión sobre-reserva otras poses
y piezas del banco: **no es un conflicto contractual de Mario ni un caso
real sin color**. Está separada en `sprgfx_mario_audit.json` y no determina
el formato ni los resultados de filas reales.

Faltan Banzai/Piraña/Chuck/meta/power-ups/partículas cuyas rutinas G8 no
escriben aún OAM atribuida completa; estados legales de las compartidas
fuera de replay, todas las poses dinámicas de Mario y variantes de
prioridad. La auditoría de fichas individuales de G3a incluye nombres del
GFX00 estático; no sustituye el DMA dinámico de Mario. También faltan las
reservas simultáneas de varios enemigos, ventanas de recarga G6 y el
remapeo exacto de los bobs a siete índices PF1 con el terreno G7.

`--final` devuelve 1 por cobertura incompleta. `--selftest --format-test`
es la puerta del formato sobre el lote especificado; no marca G3 cerrado.
No se midieron tiempos del hardware: esta tarjeta solo cambia conversión
offline. No se ejecutó WinUAE ni se reservó su candado. El coste del renderer
integrado sigue fuera de esta entrega.

## Reproducción en esta PC

Ejecutar desde el worktree con Git Bash, `python` y PATH ucrt64 antes de
gcc, como `docs/reglas-ola-pc.md`. Es necesario conservar los oráculos
locales, la ROM personal y el fuente de SMW; todos los derivados van a
`work/`, ignorado por Git.

```sh
export PATH="$TEMP/pyshim:/c/msys64/ucrt64/bin:$PATH" VBCC=/c/Users/JC/vbcc PY=python
gcc -O2 -DNOOAM -DSPR_OAM -Iplayer -o work/marioverify_oam.exe tools/marioverify.c player/mario.c player/mcoll.c player/manim.c player/mgfx.c player/mcam.c player/msprite.c player/mspr.c player/spr_*.c player/gen/smwrom00.c
GAME_OAM_TRACE=work/oam_yi1.trace work/marioverify_oam.exe work/oracle_yi1.bin game
GAME_OAM_TRACE=work/oam_normal.trace work/marioverify_oam.exe work/oracle_normal.bin game
GAME_OAM_TRACE=work/oam_spin_kill.trace work/marioverify_oam.exe work/oracle_spin_kill.bin game
python tools/mkmario.py
python tools/sprgfx_manifest.py --trace work/oam_yi1.trace=work/oracle_yi1_oam.bin --trace work/oam_normal.trace=work/oracle_normal_oam.bin --trace work/oam_spin_kill.trace=work/oracle_spin_kill_oam.bin
python tools/mksprgfx.py --selftest --format-test --manifest work/sprgfx_manifest.json --out work/sprgfx_composite
python tools/mksprgfx.py --selftest --format-test --out work/sprgfx_final
python tools/sprgfx_selftest.py
python tools/sprgfx_manifest.py --trace work/oam_yi1.trace=work/oracle_yi1_oam.bin --trace work/oam_normal.trace=work/oracle_normal_oam.bin --trace work/oam_spin_kill.trace=work/oracle_spin_kill_oam.bin --mario-rows --out work/sprgfx_mario_rows.json
# Esperado: exit 1, 869 BANK; no es una puerta completa satisfecha.
python tools/mksprgfx.py --final --manifest work/sprgfx_mario_rows.json --out work/sprgfx_mario_reuse
# Auditoría conservadora separada, esperado exit 1.
python tools/sprgfx_selftest.py --audit-mario
python tools/lint_port.py && python tools/regress.py --baseline tools/baseline_pc.json --level
```

Evidencia visual inspeccionada: `work/sprgfx_composite.png`, referencia
SNES→OCS arriba y decode del SG3F debajo, las 48 poses visibles idénticas.
`work/sprgfx_final.png` hace la misma comparación para fichas individuales.
Cada prefijo emitido incluye `.idx`, `.dma` y `.json`; las trazas SOT1 y
los manifiestos también son regenerables y no se commitean.

Negativos: **12 rechazos** (ficha desconocida, tamaño desconocido,
desbordamiento de banco, salida R9 fuera de `work/` y escape `work/../assets-out`, reserva sin color,
cuatro offsets corruptos, terminador corrupto y bob distinto de DMA).
Se comprueba además un solapamiento donde invertir fichas cambia la imagen.
La prueba R9 usa la ruta real resuelta; rechaza también escapes por enlaces.
Los archivos derivados no están en el índice de Git. `lint_port.py` y la
regresión completa de PC con `--baseline tools/baseline_pc.json --level`
terminaron **RESULTADO: OK**, sin cambiar baselines ni métricas. El juego
base conserva 390704 B chip, cero violaciones de memoria y cero diferencias
de RAM en los cruces de level_frame/level_start_sprites.

Trampas nuevas, sin número: una ficha individual no identifica propietario
ni pose compuesta; la unión de índices de todo GFX32 no es una fila real de
Mario; remapear por fila puede multiplicar variantes aun cuando cada fila
se pueda colorear exactamente; un banco de gráficos que cabe no implica
que el diccionario de variantes quepa en slow.
