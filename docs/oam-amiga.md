# SPR_OAM en el 68000 — 2026-10-05

Actualización del 2026-10-06: G8b amplía la OAM opt-in a Banzai, piraña,
Chuck, cinta de meta y caparazones. La validación nueva y sus puentes están
en `docs/validacion-g8b.md`; las medidas WinUAE de este documento
corresponden al alcance anterior. La lógica ampliada alcanza 43,8 % PAL
sin DMA en Musashi: no se activa por defecto.

El paso 3 después de la ola 3 queda implementado como **opción**, con
`CDEFS='-DNOOAM -DSPR_OAM'`. Mario conserva `mario_oam`, `mario_E2BD` y
`mspr_draw` en asm; el Rex llama a `_rex_gfx` desde `_rex_main_asm` en la fase
original. Las rutinas G8 que ya corren en C también escriben su OAM: caja
`$B9`, Koopa deslizante `$BD`, Koopa sin caparazón `$02` y nube del giro.
El código de gráficos permanece en la lógica, porque modifica pose,
temporales y flags además de escribir fichas (G2/P35/P98).

No se activa por defecto hasta medir el juego integrado en WinUAE
cycle-exact con DMA y comprobar los ticks lógicos de O5. Todavía faltan el
asignador, el dibujo de enemigos, otras rutinas OAM y ampliar la foto O5.
El formato de `spr_oam_first` es un índice **en bytes** en `$0300`; su ranura
es `first/4+64`. `spr_oam_n` incluye las fichas ocultas. Para normalizar solo
las fichas visibles de una foto, hay que reconstruir sus rangos y pertenencia.

## Integración y limpieza

Los builds de logicbench y game derivan el flag asm de `CDEFS`, conforme a
`msprite.h`. No hace falta repetirlo en `LBDEFS` ni `GDEFS`. Activarlo solo
en asm se rechaza; `game_build.sh NOCC=1` comprueba que el C generado tenga
el mismo modo antes de ensamblar.

`level_frame` limpia las 128 Y de la OAM a `$F0` también con
`NOOAM+SPR_OAM`, y reinicia las 12 cantidades antes del despacho. El
verificador siembra fichas y marcas antiguas, corre el `level_frame` real sin
fase de sprites y exige que desaparezcan todas: evita enemigos fantasma.

## Puerta del despacho y del oráculo

`GAME_OAM_TRACE` añade al modo `marioverify game` una salida opcional
`SOT1`: tamaño de mapa y, por cada despacho que escribe OAM, frame,
ranura, tipo, primera ficha y cantidad, RAM/mapa antes y después.
Los temporizadores y poses no grabados los calcula el C host siguiendo la
partida; no se inyectan desde la SNES. La salida derivada vive en `work/` (R9).

`sprite_oam_verify.py` carga el binario real de vbcc/vasm en Musashi,
prepara esos estados de entrada y llama a `_sprite_run`, incluido el Rex
en asm. Comprueba RAM entera, mapa, marcas y ABI (`d2-d7/a2-a6`, pila).
Después busca las fichas visibles completas y su orden en el `_oam.bin` del
mismo frame. Falla si hay diferencias o la traza está vacía; `--require` exige Rex
por defecto y puede seleccionar otros tipos (G8b), siempre con muestras
visibles no vacías. `--require-state` exige los estados deseados.

Esto prueba el **despacho 68000** contra el host validado por el oráculo.
La equivalencia del `level_frame` completo se verifica aparte con `--cross`;
el replay integrado con `gamecheck --spr` es una tercera puerta.

| grabación | despachos exactos (RAM/mapa/marcas/ABI) | OAM Rex exacta | otras OAM exactas |
|---|---:|---:|---|
| YI1 | 3712/3712 | 2671/2671 | `$02`: 412/412; `$B9`: 307/307; `$BD`: 322/322 |
| normal | 1045/1045 | 881/881 | `$02`: 3/3; `$BD`: 161/161 |
| spin_kill | 641/641 | 530/530 | `$BD`: 111/111; **90 despachos en estado 4**, nube |

Orden OAM: 0 diferencias en las tres. Cruce de fase Rex con
anterior/mismo/siguiente: YI1 **785/2671/785**, normal **4/881/4** y
spin_kill **39/530/39**. Evidencia regenerable:
`work/oam_68000_rex.png`, referencia arriba y resultado del 68000 abajo.
El PNG usa G3a y la paleta SNES: prueba la reconstrucción desde la OAM,
no el remapeo de color ni el DMA del OCS que aún faltan.

El arnés `m68kverify --mode loop` omite todos los frames animados/bloqueados;
`marioverify game` procesa las animaciones portadas y conserva su fase de
sprites al reanudar. Por eso comparar directamente la OAM de ese `loop`
con la grabación dio Rex 1834/2622 después de encoger, aun con RAM
host/68000 idéntica. No se usa ese arnés para la puerta OAM ni se rebaja la
exigencia; el stream procede del modo `game` y reproduce el despacho real.

## Coste y memoria

Medidas de Musashi, **sin DMA**, con vbcc de esta PC:

| juego integrado (`gamecheck --spr`) | sin SPR_OAM | con SPR_OAM |
|---|---:|---:|
| `level_frame`, media | 28 588 | 32 692 |
| `level_frame`, máximo | 39 026 | 46 718 (frame 7925) |
| total, media | 39 053 | 43 074 |
| total, máximo | 117 796 | 120 142 (frame 10587) |

El aumento es **14,4 % relativo de media y 19,7 % del máximo de lógica**;
incluye limpieza OAM, marcas y puentes PIC. Reemplaza el cálculo anterior
de 13,7 %. El máximo nuevo equivale a 32,9 % del frame PAL sin DMA;
P96 ×1,05 da una estimación de 34,6 %, que no sustituye WinUAE.

Replay: 6313 operaciones, **0 frames distintos**; Mario y dibujo asm/cache
**6184/6184**. De los 6310 frames medidos, 0 superan los 141 875 ciclos PAL.
Cruce de RAM entera de `level_frame`/`level_start_sprites`:
**6549 llamadas, 0 distintas**, host con `NOOAM+SPR_OAM`.

`memmap` sobre el ADF opt-in: **0 violaciones**, chip **390 704 B**,
binario slow **210 064 B** (antes 207 288; el build por defecto actual, sin OAM,
da 207 296 con `memmap.py`, 2026-10-05). La OAM vive en RAM de CPU; no
reserva gráficos de enemigos ni banco DMA. `cdata1 < $7FFE` sigue comprobado
al ensamblar. Las fotos ampliadas propuestas en G2 todavía no están añadidas.

## Llamadas lejanas (P102)

Al crecer el código, `jsr _f44d_asm` desde `mcoll` y sus dos retornos al C
excedieron ±32 KB. Vasm los relajaba a `JSR/JMP` absolutos del binario: en
`gamecheck`, cargado en `$10000`, saltaban a datos. Logicbench no excedía el
rango y sus pruebas aisladas pasaban.

Con SPR_OAM, `pic68k.s` pone un puente cerca del C de `mcoll`;
`PICCALL/PICJUMP` calculan el destino desde una etiqueta PC local más un
delta de 32 bits. Solo usan registros de trabajo; el análisis ABI conoce el
destino real mediante `lint: targets`. Los dos fallbacks de asm al C ya
excedían el rango en logicbench por defecto; el guard los descubrió porque
los oráculos no ejecutaban esas ramas. También se corrigen con PIC en el
build normal. Su camino habitual conserva el coste; la regresión completa
comprueba los resultados y tiempos sin cambiar baseline.

`piccheck.py` inspecciona **los opcodes del listado ensamblado**, no una
lista permitida de nombres. Rechaza `4EB8/4EB9/4EF8/4EF9` (absolutas
cortas/largas), incluso si proceden de `BRA/BSR` relajados, y falla con
listados vacíos. Se ejecuta en ambos builds. Pruebas negativas:
el juego previo reconstruido falla con 3 absolutas; un banco ensamblado de
`JSR/JMP/BRA/BSR` largos y `JSR/JMP` cortos falla con 6, sin confundir
`dc.l $4EB90000` con una instrucción; un listado vacío también falla.

## Medida integrada en WinUAE (2026-10-05)

[Comparación OAM + O5 contra base](medida-oam-o5.md): la lógica alcanza
37,24 % del frame PAL y la interrupción lógica + foto, 46,40 %. En ambos
builds: 6312 frames lógicos, 0 incidencias COPER detectadas y 14 fotos
omitidas por O5. La puerta de lógica ≤ 40 % pasa para este replay.
El renderer de enemigos/bobs, HUD y audio sigue pendiente; `SPR_OAM`
permanece opt-in. Estos tiempos incluyen el DMA actual y no deben
confundirse con los resultados anteriores de Musashi.

## Reproducir (bash, en worktree separado)

```sh
CDEFS='-DNOOAM -DSPR_OAM' sh tools/logicbench_build.sh
SRC='player/mario.c player/mcoll.c player/manim.c player/mgfx.c player/mcam.c player/msprite.c player/mspr.c'
gcc -O2 -DNOOAM -DSPR_OAM -Iplayer -o work/marioverify_oam.exe tools/marioverify.c $SRC player/spr_*.c player/gen/smwrom00.c
gcc -shared -O2 -DNOOAM -DSPR_OAM -Iplayer -o work/libport_oam.dll $SRC player/spr_*.c player/gen/smwrom00.c
GAME_OAM_TRACE=work/oam_yi1.trace work/marioverify_oam.exe work/oracle_yi1.bin game
python3 tools/sprite_oam_verify.py --trace work/oam_yi1.trace --require AB,B9,BD,02 --preview work/oam_68000_rex.png
GAME_OAM_TRACE=work/oam_normal.trace work/marioverify_oam.exe work/oracle_normal.bin game
python3 tools/sprite_oam_verify.py --trace work/oam_normal.trace --oracle work/oracle_normal.bin
GAME_OAM_TRACE=work/oam_spin_kill.trace work/marioverify_oam.exe work/oracle_spin_kill.bin game
python3 tools/sprite_oam_verify.py --trace work/oam_spin_kill.trace --oracle work/oracle_spin_kill.bin --require-state 04
python3 tools/m68kverify.py --engine musashi --mode loop --sprites --cross work/libport_oam.dll
CDEFS='-DNOOAM -DSPR_OAM' NOCC=1 OUT=work/oam_game sh tools/game_build.sh
python3 tools/gamecheck.py --bin work/oam_game/game.bin --lst work/oam_game/game.lst --engine musashi --spr
python3 tools/memmap.py work/oam_game/game.lst
# Volver al build por defecto antes del commit; no actualizar baseline.
python3 tools/lint_port.py && python3 tools/regress.py
```

En Linux: usar `.so`, `-fPIC` para la biblioteca y el nombre de ejecutable
sin `.exe`; las opciones del C deben ser las mismas en ambas arquitecturas.
