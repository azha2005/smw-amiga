# G7-3b — productor 68000 sin búsqueda (2026-10-11)

Elección del usuario del 2026-10-11 ("probemos b"): antes de cerrar la
fidelidad de G7-3, rediseñar el productor para que su coste esté acotado
y se acerque al frame. Commits `528a64a` (especificación) y `4d326b5`
(68000). **G7_BOBS sigue opt-in**; el vivo por defecto no cambia (SHA256
`33f2250a1b4231069ab975bfdc4f7d2336cd814a0e4e95d13bd862659c5b638b`,
recompilado por la regresión en `work/rg_bm1`).

## 1. Qué hay ahora

| pieza | qué es |
|---|---|
| `tools/g7_fast.py` | especificación: camino corto `fast2_row` (v2) y, si no entra, capas 1-2 (`fast_row`), 3 ventana (`window_row`), 3b EDF (`edf_assign`). Cada plan se comprueba por píxel (`check`) |
| `player/g7fast.s` | productor 68000 (incluido solo con `G7_BOBS`): v2 + capas 1-2. **Ventana y EDF todavía no están portadas**: `g7f_left` rechaza la foto de forma explícita (`g7b_error` = 2 \| fila << 8) |
| `tools/g7f_verify.py` | Musashi ejecuta el bucle real de render de cada foto y exige al 68000 el mismo segmento palabra a palabra, los mismos índices PF1 y la misma fila de rechazo que la especificación. `--profile all [--local]` da el perfil por PC |
| retirados | `player/g7prod.c`, `tools/g7_compile.py` (el productor C con búsqueda: 82 M ciclos en una foto) |

### Camino corto v2 (`fast2_row`)

Si el prefijo es el canónico de `build_mid` (palabras 0-1 WAIT y 2..8 los
MOVE `$182..$18E`, el 100 % de las filas medidas), por color de efecto en
orden ascendente:

1. un índice **constante en la fila**: su MOVE del prefijo vale el color y
   el cuerpo no lo recarga (una pasada por el cuerpo; un WAIT con v = 1
   empieza por `$01xx` y no cuenta);
2. si no, un índice **libre** (el terreno visible no lo usa fuera de los
   efectos), probados **de 7 a 1**: se parcha su MOVE del prefijo y sus
   recargas del cuerpo pasan a NOP (misma ranura, nada se corre).

Sin modelo de tiempos, sin grupos y sin búsqueda. Si no alcanza, la fila
sigue por las capas desde cero. El orden 7..1 sale de la medida: en las
10.534 filas con efectos de YI1 el 7 está libre en el 89,5 % y el 6 en el
74,5 % (1: 29,7 %). Cualquier libre da la misma cobertura.

## 2. Cobertura de la especificación (sin máscara de hardware)

| traza | filas | v2 | capas 1-2 | ventana | EDF | sin plan | fotos sin plan | mal |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| yi1 | 10.534 | 9.937 | 51 | 263 | 168 | 115 | 38 | 0 |
| chuck_kill | 6.166 | 5.059 | 51 | 1.035 | 11 | 10 | 5 | 0 |
| pw_bloques | 4.478 | 4.226 | 35 | 217 | – | 0 | 0 | 0 |
| spin_kill | 3.143 | 3.021 | – | 122 | – | 0 | 0 | 0 |
| stress_piranha | 5.629 | 5.057 | – | 365 | 207 | 0 | 0 | 0 |

Total 29.950 filas (**el mensaje del commit `528a64a` dice 30 950: es un
error de suma**). Logs `work/g7fast/<traza>-v2.log`.

## 3. El 68000 contra la especificación (capas `fast`)

Cinco trazas, todas las fotos que la especificación resuelve sin ventana
ni EDF: **0 diferencias** de segmento, índices PF1 o fila de rechazo.
Ciclos del productor por foto (Musashi, **sin DMA**, desde `g7b_draw`):

| traza | fotos | filas | rechazadas (ventana/EDF) | media | mediana | p99 | máximo |
|---|---:|---:|---:|---:|---:|---:|---:|
| yi1 | 6.183 | 9.031 | 129 | 36.311 | 5.300 | 375.998 | 516.112 (k2182, 30 filas) |
| pw_bloques | 2.049 | 4.040 | 26 | 44.498 | 5.300 | 431.685 | 521.686 |
| chuck_kill | 2.848 | 4.690 | 106 | 39.607 | 5.300 | 409.087 | 521.686 |
| spin_kill | 992 | 2.917 | 14 | 59.884 | 5.302 | 465.408 | 521.740 |
| stress_piranha | 2.828 | 4.492 | 189 | 37.057 | 5.302 | 303.601 | 521.686 |

El prototipo C medía 2,5 M de media y 82 M de máximo. Logs
`work/g7f-v2-yi1.log`, `work/g7f/v2-<traza>.log`. `g7_bobs_verify
--core-only` (consumidor: fuentes, minterm, IRQ, dos copias,
restauración, cola) OK sobre el binario nuevo.

### Coste por fila (perfil YI1 completo)

| rutina | ciclos por fila con efectos |
|---|---:|
| `g7f_overlay` (+ `ovmiss`) | 5.640 + 730 |
| `g7f_free` (libre de 7 a 1, contra el PF1) | 3.660 |
| `g7f_queue` (planos y cola) | 2.510 |
| `g7f_order` (orden de colores, máscara) | 2.320 |
| `g7f_v2` (+ `reloads`) | 2.080 + 320 |
| `_g7b_save_row` (diario: copia el segmento entero) | 1.510 |
| `g7f_unov` | 700 |
| **total** | **≈ 19.500** |

Fijo por foto, con o sin efectos: `g7f_entries` 3.170, `g7b_begin` 1.060,
resto de `g7b_draw` ≈ 1.700 (la mediana de 5.300).

## 4. Lectura

- El diseño ya no busca: el coste es lineal en filas y píxeles y está
  acotado. Pero **no cabe en el frame** (≈ 141.800 ciclos, ya repartido
  en lógica, scroll y sprites; D1 sigue roja sin G7). La foto media cuesta
  el 26 % de un frame y el p99 2,6 frames.
- El suelo de este esquema (una pasada por fila: overlay, libre, cola,
  diario) está cerca de 8-10 k por fila aun con las mejoras de abajo. Con
  16 filas (p99) son 130-160 k: **una foto con muchos efectos no entra en
  un frame por mucho que se afine.**
- Mejoras medibles que quedan (estimadas, no hechas):
  1. índices usados por bloque Map16 (tabla de ~80 bloques × 16 filas)
     en vez de leer el PF1: `free` 3,7 k → ~1 k. Riesgo: el PF1
     materializado no siempre es el mapa (por eso hoy se lee el PF1); hay
     que demostrarlo contra `g7f_verify`;
  2. diario disperso (solo las palabras parchadas) en vez del segmento
     entero: −1,5 k por fila con libre; cambia `g7b_restore`;
  3. overlay sin control de rango por píxel en grupos enteros y fuente
     ya decodificada: −1 a −2 k;
  4. `g7f_entries` con salida temprana: −1 a −2 k por foto.
- Lo que no mejora el peor caso: caché entre fotos (con la cámara en
  movimiento casi no acierta).

## 5. Qué falta para cerrar G7-3

1. **Decisión de presupuesto (usuario)**: cuánto frame puede usar G7 y qué
   pasa con las fotos de muchos efectos (ver PROXIMO).
2. Ventana y EDF en el 68000 (129 fotos rechazadas en YI1, 106 en
   chuck, 189 en estrés) y el apoyo hardware del residuo (G7-C).
3. k409 físico (la puerta roja de G7-3), SW1, A/B BENCH, todo
   cycle-exact.

Memoria con G7_BOBS: replay 510.920 B chip / 512.008 B slow (márgenes
13.368 / 12.280 B); vivo 522.448 / 511.520 B (márgenes 1.840 / 12.768 B);
0 violaciones. El slow pasó de 152 B a 12,7 KB de margen al retirar el
productor C.
