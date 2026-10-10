# G5L-R-Q — qué recortes de ciclos son posibles (2026-10-09)

Rama `g2t-b2bis`. Tarjeta de medida autorizada por el usuario
(`instrucciones-g5l-r-q.md`). Solo herramientas (`tools/g5l.py
--pcprof`, `tools/q_report.py`, `tools/q_levers.py`); el juego no cambió.

**Resultado.** El perfil es **plano**: el bucle más caro del render G5L en
las ventanas de salto es el 5,1 %. Las reescrituras concretas y fundadas
ahorran un **8 %** del render y un 8 % de `build_mid` en las ventanas.
Con el modelo de cola (ESTIMADO) eso deja **14-16 saltos**, y 10-11 con S5.
Llegar a ≤ 5 pide además un ajuste general de un 10 % de todo lo demás
(2-4 con S5), sin un bucle concreto que lo dé. **Ninguna meta de Pa es
alcanzable con lo que se ve hoy en el perfil.** Ver §5.

## 1. Paso 1: histograma por PC

`g5l.py game --pcprof OUT` corre `g5l_render` y `build_mid` instrucción por
instrucción (`m.execute(1)`; probado: `move.l (a0)+,(a1)+` 20 ciclos,
`dbf` 10 al saltar y 14 al salir). Guarda `{foto: {offset: [veces,
ciclos]}}` y no pisa `game_frames.json`.

**Puerta:** en las 6313 fotos, el total paso a paso de `g5l_render` y de
`build_mid` es **idéntico** al de la corrida normal (0 distintas), y cada
histograma suma exactamente su total (render: 2056 fotos > 3000 ciclos;
`build_mid`: 1059 > 10 000). `G5L GAME (pcprof): OK`.

## 2. `g5l_render` (`tools/q_report.py`)

Ciclos de Musashi, sin DMA. Ventanas = de la repetición − 2 hasta el salto
(98 fotos con Rex dibujado, 52 254 ciclos por foto).

| rutina | ventanas | fallos (145) | dibujadas sin fallo (1898) |
|---|---:|---:|---:|
| `g5l_patch` | 13,3 % | 13,6 % | 2,4 % |
| `g5l_place` | 11,6 % | 8,4 % | 15,3 % |
| `g5l_sweep` | 11,3 % | 16,1 % | — |
| `g5l_emit` | 10,8 % | 8,0 % | 12,6 % |
| `g5l_mario` | 9,2 % | 7,4 % | 17,0 % |
| `g5l_plan` | 8,9 % | 12,8 % | — |
| `g5l_fast` | 8,9 % | 7,8 % | 17,8 % |
| resto | 26,0 % | 25,9 % | 34,9 % |

Bucles más caros en las ventanas: `g5l_patch.cl` 5,1 % (copia del flujo
limpio de DMA, `move.l`+`dbf`, 30 ciclos por palabra larga), `g5l_fast.c`
3,9 %, `g5l_emit.mv` 3,0 %, `g5l_plan.fl` 2,7 %, `g5l_place.open` 2,5 %,
`g5l_pcget.c` 2,3 %; los 22 primeros suman ~40 %. Tabla completa en
`work/t2/q_report.txt` (ignorado).

Dos hallazgos:

- **`g5l_pcget` acierta 159 de 1980 llamadas** y compara **6,7 palabras
  largas por entrada** (51 411 `cmpm` en 7695 entradas): la clave empieza
  por la pose de Mario, que casi no cambia, y lo que cambia (`VLIST`,
  `MSH`, `R0`) va al final.
- `g5l_place.f1` busca hacia atrás fila por fila un segmento con lugar
  (`tst.b -(a0)` + `dbne`, ~20 ciclos por fila): 3,7 % de las dibujadas.

## 3. `build_mid`

| fotos | ciclos por foto | `bm_left` | `build_mid` |
|---|---:|---:|---:|
| > 40 000, cámara a la izquierda (60) | 58 861 | 99,6 % | 0,4 % |
| > 40 000, derecha o quieta (14) | 49 372 | 26,4 % | 73,6 % |
| ventanas de salto (55) | 38 076 | 84,0 % | 16,0 % |

En las ventanas, `build_mid` es casi todo `bm_left` (el camino de la vuelta,
SX/P72). Su bucle por carga (`.ld`/`.w`/`.mv`/`.k1`/`.k2`, `scroll.s:1380-1395`)
cuesta ~90 ciclos por carga, y unos 40 de ellos llevan el máx. de a y el
mín. de b.

## 4. Reescrituras concretas y su recorte (ESTIMADO, `tools/q_levers.py`)

Fracción de los ciclos del bucle que se ahorra, con los ciclos del 68000
de la reescritura contra los medidos. **Ninguna está escrita ni probada.**

| bucle | reescritura | ahorro | % del render en ventanas | % en todas las dibujadas |
|---|---|---:|---:|---:|
| `g5l_pcget.c` | clave con `VLIST`/`MSH`/`R0` primero | 75 % | 1,69 | 2,31 |
| `g5l_patch.cl` | copia con `movem.l` de 8 | 35 % | 1,79 | 0,54 |
| `g5l_emit.mv` | MOVE empaquetados de 4 B, bucle desenrollado | 45 % | 1,35 | 1,19 |
| `g5l_emit.jl` | el salto `$0084` en offset conocido (`GV_NB`) | 90 % | 1,18 | 0,86 |
| `g5l_place.f1` | mapa de bits de segmentos con lugar | 60 % | 1,01 | 2,23 |
| `g5l_mario.kz`, `pckey.k`, `pcput.bc`, `pcget.bc/.r` | borrar/copiar con `movem` | 35-60 % | 1,19 | 1,52 |
| **total render** | | | **8,2** | **9,1** (fallos 6,4) |
| `bm_left.mv/.k1/.k2` | sacar del bucle el máx. a / mín. b (**sin probar** que se pueda) | 25-60 % | — | `build_mid` en ventanas 8,1 |

Saltos del modelo (cinco ajustes de T2; base 25):

| supuesto | solo render | render + `build_mid` | + S5 (−50 % del exceso que queda) |
|---|---|---|---|
| reescrituras concretas | 17-18 | 14-16 | **10-11** |
| + resto −5 % | 13-16 | 9-13 | 6-10 |
| + resto −10 % | 9-12 | 6-9 | **2-4** |

"Resto −10 %" es ajuste a mano de todo lo que no tiene reescritura
concreta, y no hay bucle que lo justifique. No se modeló pasar
`g5l_patch` (copia y XOR, 13,3 % de las ventanas) al blitter: la lista y
el búfer están en chip, pero el blitter compite con el DMA (R7, P31: ~42 µs
de CPU por blit) y Musashi no lo ve. Sería la única palanca estructural
grande que queda sin medir.

## 5. Conclusión y recomendación

- **Lo seguro** (reescrituras concretas, exactas por construcción: las
  verifica `G5L GAME` byte a byte) da ~8-9 % del render. Según el modelo
  baja los saltos de 25 a 14-16. Es una sesión.
- **≤ 5 saltos** pide eso, más S5, más un 10 % general sin bucle
  identificado, o el patch por blitter. Son 3-5 sesiones con resultado
  incierto.
- D1 (2026-09-30 y 2026-10-09): 50 Hz haciendo todo lo posible, colchón
  aceptado, 25 Hz solo con la optimización agotada. No está agotada; pero
  el retorno de cada sesión baja.

**Recomendación:** G5L-R-R1, implementar las reescrituras concretas del
render (§4, sin `bm_left`) y **medir en WinUAE** (BENCH y VBTRACE). Es la
primera medida real de cuánto valen los ciclos de Musashi en las fotos
omitidas. Con ese número, el usuario decide entre S5, el patch por
blitter o revisar D1. Instrucciones: `docs/instrucciones-g5l-r-r1.md`.
**Pendiente de autorización** (es un candidato: toca `player/g5l.s`).

## 6. Red de seguridad

Solo herramientas. Los cinco MD5 del defecto, rehechos (ver el commit),
iguales a `informe-g5l-r-t2-1009.md` §6. `lint_port.py` y `regress.py
--baseline tools/baseline_pc.json --level --g5l --bm1`: OK.

## Comandos

```sh
python tools/g5l.py game --bin work/t2/replay/game.bin --lst work/t2/replay/game.lst --pcprof work/t2/q_prof.json
python tools/q_report.py --prof work/t2/q_prof.json --frames work/t2/frames.json \
    --vblog work/t2/vt/vbtrace.out --lst work/t2/replay/game.lst --top 22
python tools/q_levers.py --prof work/t2/q_prof.json --lst work/t2/replay/game.lst \
    --csv work/t2/frames.csv --frames work/t2/frames.json --vblog work/t2/vt/vbtrace.out
```
