# G7-3c — productor completo en 68000: diario disperso, ventana y EDF (2026-10-11)

Pedido del usuario: "hacé esa medición (G7-S0), seguí abaratando las filas
y pasá a asm el resto". La medida está en `docs/informe-g7-s0-1011.md`
(commit `eb39960`). Este informe cubre lo demás. Commits: `f9c59b9` (diario
disperso), `5990b41` (ventana), `a1988f5` (EDF; lo portó un subagente
Haiku a pedido del usuario y se verificó aparte). **G7_BOBS sigue opt-in**;
el vivo por defecto no cambia (SHA256 `33f2250a…`, `work/rg_bm1`).

## 1. Qué hay ahora

| pieza | qué es |
|---|---|
| `player/g7fast.s` | camino corto v2, capas 1-2, preparación de los pasos 3/3b (`g7f_umask`, `g7f_uses` por máscaras de palabra, `g7f_tidx`, `g7f_want`), tabla `g7f_hx`, `g7f_left` (ventana y después EDF) |
| `player/g7win.s` | paso 3: `window_row` y `place` (forma cerrada) |
| `player/g7edf.s` | paso 3b: `edf_assign`, `edf_row`, `reach_early`, `reach_exact` |
| `_g7b_save_sparse` | diario de palabras sueltas del camino corto (8 B por palabra) |
| `_g7b_save_row` | segundo argumento: mínimo de longs a guardar. Una lista nueva más larga que la original también se repone byte a byte |
| `tools/g7f_verify.py --check-clean` | tras cada foto, `g7b_clean` tiene que dejar la lista libre igual byte a byte |

`-DG7F_NOWIN` deja fuera la ventana en el 68000 (con `--layers fast,edf`
se cruza el EDF solo). Las capas siguen exactamente a `tools/g7_fast.py`,
sin cambios de especificación en esta sesión.

## 2. Verificación (capas completas, `--layers fast,window,edf --check-clean`)

Cinco trazas, todas las fotos: **0 diferencias** de segmento, índices PF1 o
fila de rechazo, y el diario repone la lista en todas. Ciclos del
productor por foto (Musashi, **sin DMA**, desde `g7b_draw`):

| traza | fotos | rechazadas (antes → ahora) | media | p99 | máximo |
|---|---:|---:|---:|---:|---:|
| yi1 | 6.312 | 129 → **40** | 56.185 | 1.042.360 | 3.021.656 |
| chuck_kill | 2.954 | 106 → **6** | 78.955 | 1.584.054 | 3.183.002 |
| pw_bloques | 2.075 | 26 → **0** | 53.554 | 518.291 | 1.403.622 |
| spin_kill | 1.006 | 14 → **0** | 69.287 | 517.476 | 1.327.924 |
| stress_piranha | 3.017 | 189 → **0** | 78.493 | 1.428.704 | 1.815.670 |

Los rechazos que quedan son las filas en las que la especificación no
tiene plan (YI1: la zona de la meta, la misma que G7-S0 y G7-C). Logs:
`work/g7f/e-<traza>.log`.

La media y el p99 suben respecto de G7-3b porque **antes esas fotos se
rechazaban en la primera fila sin plan** (y no costaban nada más). Ahora se
producen enteras, y las filas por ventana o EDF son las caras.

## 3. Coste

### Camino corto (el 94 % de las filas)

Diario disperso: −0,9 k por fila con índice libre (YI1 media 36.311 →
35.603 solo con las capas 1-2). Se probó y se descartó un overlay sin
control de rango por grupo entero: 25,02 M contra 24,95 M en k0-400,
dentro del ruido; más código para nada.

### Ventana y EDF

Son búsquedas acotadas (hasta 7 índices por color, dos `place` por índice,
cada uno sobre todos los huecos y los 46 h distintos). Lo que se hizo para
bajarlas, sin cambiar ninguna decisión:

| cambio | efecto |
|---|---|
| `want` completo solo antes del EDF; la ventana toma `base[r, hi]` de `W_EVT` | k1806: 803 k → 618 k |
| usos del terreno por máscaras de palabra (`W_UM`, índice mayor), una vez por fila | 618 k → 533 k |
| `g7f_hx` (h sin x repetidas, igual que `HX` de la especificación), `adv(t,2)` fuera del bucle, el primer `place` reusa el análisis | chuck máx. 5,49 M → 3,18 M |
| el EDF usa `g7f_hx` y `g7f_uses` | YI1 p99 1,33 M → 1,04 M; stress máx. 2,11 M → 1,82 M |

Perfil YI1 completo (354,6 M ciclos): overlay 15 %, free 10 %, place 7 %,
queue 7 %, v2 7 %, order 6 %, entries 5,5 % (≈ 3,1 k fijos por foto),
scan 5 %, `g7e_row` 4 %, uses 4 %.

Se evaluó y **no se hizo** (decisión de memoria, no de ciclos): fuente
predecodificada para el overlay (≈ −2 k por fila). Pide 4-8 KB de slow, y
el margen con G7_BOBS es de **5.040 B** (vivo) / **4.560 B** (replay).

## 4. Memoria y puertas

Lint, `regress.py --level --g5l --bm1`, `sws_gate`, `oam68k_gate` y
`g7_bobs_verify --core-only` (con el diario nuevo) OK. Memmap con
G7_BOBS: vivo chip 522.448 B (margen 1.840), slow 519.248 B (margen
5.040); replay chip 510.920 (13.368), slow 519.728 (4.560). 0 violaciones.

## 5. Lectura

- El productor ya resuelve en el 68000 todo lo que la especificación
  resuelve: 40 fotos sin plan en YI1, 6 en chuck y ninguna en las otras.
- **No cabe en el frame** (≈ 141.800 ciclos, ya repartido). La mediana
  (5,3 k) sí cabe, pero una foto con efectos cuesta de media el 40-55 % de
  un frame, y el p99, entre 3,7 y 11 frames. Las filas por ventana o EDF
  pueden costar 100-200 k cada una.
- Esto confirma la lectura de G7-3b. El esquema PF1 por fila tiene un
  suelo de 8-10 k por fila en el camino corto, y las filas difíciles son
  búsquedas. Según G7-S0, el híbrido con sprites deja 0,05-0,83 filas PF1
  por foto de media y 12-16 en el peor caso. Es la vía que más reduce el
  trabajo, pero no se empezó: **la decisión es del usuario** (PROXIMO §1).
