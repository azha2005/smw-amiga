# G3 — conversor SG3F/2 y carga mínima del banco acotado

2026-10-06. Rama `wt/g3-1006`, base `44ba9dc`. G3 pasa la puerta acotada;
no declara cobertura global YI1, asignador G4, renderer G5/G6 ni bobs PF1.
El commit local de esta tarjeta se entrega al coordinador junto con este informe.

## Resultado

| componente | resultado |
|---|---:|
| peticiones SOT1/yi1/normal/spin_kill con reservas reales | 2593 |
| formas observadas + Rex legal | 43 + 5 = 48 |
| descriptores enemigos deduplicados | 289 |
| candidatos máximos por forma | 31 |
| DMA inmutable sin/con solapes | 66336 / 64528 B |
| metadata + directorio + trailer SG3F/2 | 71554 + 1162 + 8 = 72724 B |
| reserva DMA / tablas reales | 65024 chip / 72728 slow |
| scratch disco transitorio | 512 chip |
| celdas verificadas peticiones / catálogo decodificado | 1241670 / 134119 |
| rechazos / diferencias | 0 / 0 |

SG3F/2 conserva descriptor de 32 B, fichas de 10 B, mapas exactos y offsets
relativos. Source/mask = $FFFFFFFF exige ausencia bob explícita. El directorio
se concatena a la metadata y se localiza con trailer de 8 B `S2IX/u32`.
`sprgfx_final.deserialize` despacha por versión; SG3F/1 permanece y SG2A se
rechaza. Detalle completo: `formato-sprgfx.md`.

La puerta `--final --scope g2-bounded` requiere manifiestos con las cuentas
G2 (AB 4082, BD 594, 02 415, B9 307), 2593 reservas y Rex legal. Enumera las
ocho paletas mediante `sprgfx_manifest.py --mario-rows`: su deduplicación
conserva una sola petición cuando varias paletas dan reservas idénticas.
Las cuentas fijas son el lote aprobado, no una interfaz genérica. El JSON
expone `scope_complete=true`, `final_complete=false`, cero rechazos y bob
ausente. El comando global `--final` continúa rechazando cobertura incompleta.

`work/g3/bank.png`: fuente SNES independiente arriba, DMA decodificado abajo.
Las dos mitades son idénticas píxel a píxel y se inspeccionaron visualmente.
Los derivados quedan ignorados. SHA-256:

| archivo | SHA-256 |
|---|---|
| bank.dma | `4dd51fcc9bd03edd9afaad0b0a2459af7113259f43caa8c0789ff457a839f4fc` |
| bank.idx | `8589b85a0e7368333b91b26d42a4f5cec7febbecc918bbebfb0743ce6f689cd2` |
| bank.png | `4888cb1a10c7c35155fae5cb5fa9f178c3586bcb23c05bfc2ab51b4cca3cdea3` |

## Memoria real y pico del loader

Medido con `memmap.py` sobre listados/ADF de `game_build.sh`, mismos flags
SPR_OAM y mismo replay regenerado, antes y después del loader:

| modo | chip antes → después | slow antes → después | pico chip |
|---|---:|---:|---:|
| replay | 390704 → 455728 | 213624 → 286816 | 455728 |
| vivo | 402232 → 467256 | 249856 → 323048 | 467256 |

Los listados son `work/g3-base-replay/game.lst`, `work/g3-base-live/game.lst`,
`work/g3-replay/game.lst` y `work/g3-live/game.lst`; cada modelo da cero
violaciones. El crecimiento del binario es 460 B; la reserva Exec crece 464 B.
La cifra slow anterior difiere de la proyección histórica G2 porque el replay
actual regenerado ocupa 39754 B; no se usa aquella proyección como medida.

Fases concretas: stage2 ocupa 214528 B chip en replay o 220160 B en vivo,
coexistiendo con su copia slow. **Se libera antes de cargar el scroll.**
Scroll reserva 230400 B, banco 65024 B y scratch 512 B: pico de la fase de
carga **295936 B chip**. Scratch se libera antes de reservar PF1, copper,
Mario y diagnóstico. El máximo global corresponde a todos los residentes
del juego de la tabla, sin copia transitoria del banco o de tablas en stage2.
Son presupuestos del programa/listado; AllocMem decide direcciones físicas
en cada arranque, y el loader comprueba chip/slow y alineación en ejecución.

Tras C2/C4, usando traslado CPU redondeado de 135472 B, **proyección vivo**:
323048 + 135472 + 32768 trabajo G4/G6 + 2376 fotos = **493664 B slow**,
margen 30624 B. Si las tablas crecieran hasta el tope de 98304 B, total
**519240 B**, margen **5048 B**, con este binario. C2/C4, trabajo y fotos no
se declaran implementados por esta suma. Banco bob/audio/segundo PF1 conservan
sus presupuestos y puertas independientes.

## Carga y validación

`SPR_BANK=work/g3/bank` activa loader solo junto a SPR_OAM. El empaquetador
verifica estructura y emite offsets/CRC32 en `work/sg3_bank.i`. Los archivos
se agregan después de los datos del scroll en el ADF; `hdr_data_len` sigue
midiendo exclusivamente scroll. Trackdisk lee DMA directamente a chip;
tablas se leen con scratch chip por sectores y se copian a slow. El padding
del último sector DMA cuesta 496 B chip, incluido en memmap. El último sector
de tablas copia solamente bytes válidos, sin escribir fuera de la reserva.

Antes de publicar los dos punteros, se verifican CRC32 completos, SG3F/2,
alineación 8, límites físicos y IO_ACTUAL de cada DoIO. La CRC corresponde al
asset estructuralmente verificado; no se reemplaza el lector offline por una
comprobación de magic. El banco se conserva inmutable (P108).

El loader ensamblado real pasó **7 casos por modo en Unicorn**: válido,
corrupción DMA, corrupción tablas, lectura parcial y cada uno de los tres
fallos de AllocMem. Valida ABI d2-d7/a2-a6, 144 lecturas, bytes cargados,
publicación solo tras validar todo y liberación exacta del scratch. El caso
válido tardó **2.583 s replay / 2.595 s vivo de host** (incluye arnés); son
tiempos Unicorn con disco simulado, **no ciclos ni latencia de Amiga PAL**.

Capturas propias WinUAE cycle-exact, KS 1.2, 512 KB chip + A501, mediante
candado: `work/g3/boot.png` y `work/g3/live_boot.png`, ambas inspeccionadas.
Después de la carga/CRC muestran el nivel y Mario. Capturadas a 80 s; esto
prueba arranque en ambos modos, no mide tiempo de arranque ni frames omitidos.
Los enemigos nuevos todavía no se dibujan; esa evidencia pertenece a G5a/G5.
Este cambio no llama conversión, CRC, copia ni búsqueda de variantes por frame.
No se atribuye un coste G4/G5 medido a esta representación.

### Corrección del 2026-10-06 (revisión posterior): CRC por tabla

El `sg3_crc` integrado en `3b42a2e` calculaba la CRC32 **bit a bit**:
46 941 522 ciclos para los 137 252 B (DMA 64 528 + tablas 72 724), **6,62 s
de arranque** a 7,09 MHz, medido en Musashi (sin esperas de DMA, así que en
la A500 es algo más). Ahora `sg3_crc_init` arma una tabla de 256 entradas
(87 572 ciclos, 1 KB dentro del binario, en slow) y `sg3_crc` va byte a
byte por tabla: **12 627 324 ciclos = 1,78 s**. Da el mismo valor que
`zlib.crc32` en los dos ficheros; el loader pasa otra vez los 7 casos por
modo en Unicorn (las dos corrupciones se siguen detectando). Memmap (con el cambio
siguiente): slow 287 888 B replay / 324 120 B vivo, chip sin cambio, cero
violaciones. Medir el arranque real en WinUAE sigue pendiente.

### Corrección del 2026-10-06: el loader va detrás de los datos (P102)

`sprbank.s` estaba incluido justo antes de `entry`, entre `scroll.s` y el
código del juego. Al fusionar D1, el build `SPR_BANK` + BENCH + D1TRACE
falló `piccheck`: cuatro `bsr` del banco de pruebas a `columns`,
`apply_colors`, `set_pointers` y `build_mid` pasaban de 32 KB (ya faltaban
2 bytes con la CRC original). Al final del código, en vivo, era `spr_lv(pc)`
el que quedaba fuera de alcance. Ahora `sprbank.s` va detrás de `replay`
(antes de `binend`) y `entry` lo llama por la base (`add.l
#sg3_load-binstart,a0; jsr (a0)`). Los punteros `sg3_dma`/`sg3_tables`
están igual de lejos: G5 tiene que leerlos con `GETBASE`. Replay, vivo,
BENCH y BENCH + D1TRACE: cero llamadas absolutas, loader 7/7 en Unicorn.

## Reproducción y comprobaciones

En PC, usar Bash con PATH/VBCC/PY de `docs/reglas-ola-pc.md`. Manifiestos
regenerados de las tres trazas SOT1 actuales (`work/oam_{yi1,normal,spin_kill}.trace`)
y sus oráculos; sus despachos son exactamente el lote G2. Comandos principales:

```sh
python tools/mksprgfx.py --final --scope g2-bounded --manifest work/g3/variants.json --base work/g3/base.json --out work/g3/bank
SPR_BANK=work/g3/bank CDEFS='-DNOOAM -DSPR_OAM' OUT=work/g3-replay sh tools/game_build.sh
SPR_BANK=work/g3/bank CDEFS='-DNOOAM -DSPR_OAM' GDEFS='' OUT=work/g3-live sh tools/game_build.sh
python tools/test_sprgfx_bank.py
python tools/test_sprgfx_memory.py
python tools/test_sprbank_loader.py --game work/g3-replay --bank work/g3/bank
python tools/test_sprbank_loader.py --game work/g3-live --bank work/g3/bank
python tools/memmap.py work/g3-replay/game.lst
python tools/memmap.py work/g3-live/game.lst
python tools/lint_port.py
python tools/regress.py --baseline tools/baseline_pc.json --level
```

Cuatro tests de formato y tres de memoria en verde: controles/terminadores,
padding opaco, offsets y alineaciones, bob presente, directorio incompleto o
variante ajena, límites chip/tablas y rechazo SG2A. También pasan los cinco
tests G2 y las 14 autopruebas memmap. Los dos tests sintéticos G3 entran en
`regress.py` sin requerir assets; sprbank.s entra en asmlint. PIC: cero llamadas
absolutas en replay/vivo. Lint y regresión PC completa con `--level`: OK,
baseline intacto, cruces PC/68000 y nivel en verde.

Límites: no cobertura fuera del lote, selección/simultaneidad G4/G6, renderer
G5, bobs G7, audio ni ejecución en A500 física. Si falla el loader, `gfail`
congela en rojo y requiere reinicio; las reservas parciales no se liberan.
Sin trampa nueva: se aplican P36/P102/P108 y el flujo PC existente. Cambios
de integración en game.s/build.sh son opt-in y aditivos; no tocan scroll ni
lógica. El coordinador fusiona los registros/docs de cierre.
