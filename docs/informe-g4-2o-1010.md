# G4-2o — abaratar el camino de varios Rex

2026-10-10. Rama `g2t-b2bis`. Tarjeta: `instrucciones-g4-2o.md`. Sigue a
G4-2 (`informe-g4-2-1010.md`), que quedó apagado por defecto porque
empeora D1.

## 1. Qué se hizo (`player/g5l.s`)

Tres cambios, cada uno verificado con `g5l.py game` exacto antes del
siguiente:

1. **Sin `g5l_plan` cuando no hay choque.** En el camino de varios Rex
   (`GV_PSF`), si la variante elegida por `g5l_picksel` no choca con
   Mario, no hay bandas y los grupos son los de la tabla en pantalla. Es
   la misma suposición que ya usa `g5l_fast` con un Rex. `g5l_rxsavef`
   arma el registro del Rex directo desde la tabla. `g5l_plan` pasa de
   605 a 64 fotos en hills2.
2. **`g5l_sweepn`, bloques rápidos.** Primero se sacan los tramos de
   Mario. Después, cada Rex con un solo grupo del índice y sin tramos de
   Mario entre su primera y su última fila es un único bloque (LOWB y
   HIGHB), sin la búsqueda de separadores. Si algún Rex no cumple, va el
   camino general sobre los mismos tramos de Mario. El resultado ordenado
   es idéntico.
3. **Tramos de Mario en su caché.** Los tramos de cada índice (filas
   relativas a la 0, sin recortar) se calculan la primera vez y se
   guardan en la entrada de la caché de Mario (`MC_RV`/`MC_RN`/`MC_RS`,
   +1.042 B por entrada en slow). `g5l_mfill` los invalida.

Además, `g5l.py game` informa las partes y la mediana por cantidad de Rex
ubicados (`partes_rex`, `mediana_rex`).

## 2. Exactitud

`G5L GAME: OK` con `-DG5L_MAXPL=2`:

| replay | fotos con 2 Rex | cadenas |
|---|---:|---:|
| hills2 | 605 | 1.380 |
| stress_sprites | 265 | 900 |
| stress_back | 136 | 354 |

Con el defecto (1): regresión completa (§5).

## 3. Costo (Musashi, ciclos de `g5l_render`)

| | G4-2 | G4-2o |
|---|---:|---:|
| hills2, mediana con 2 Rex | 63.496 | **52.296** |
| hills2, media con 2 Rex | 66.946 | 56.164 |
| hills2, mediana con 1 Rex | 25.160 | 25.182 |
| stress_sprites, mediana con 2 Rex | 71.970 | **62.878** |

Lo que queda en una foto con 2 Rex de hills2 (media, perfil de 488 fotos):

| parte | ciclos |
|---|---:|
| `g5l_sweepn` | 13.351 |
| `g5l_emitn` + `g5l_emitc` | 9.792 |
| `g5l_place_e` | 4.776 |
| `g5l_mario` | 4.630 |
| `g5l_choose` | 4.225 |
| `g5l_rxsavef` | 4.089 |
| `g5l_need` | 2.891 |
| `g5l_mwall` | 2.391 |

Por qué no baja más:

- `g5l_sweepn`: el resto son LOWB/HIGHB por bloque (3,4 k), el recorrido
  (2,8 k), el ordenamiento (1,5 k) y el arranque de cada índice (1,7 k).
- `g5l_emitn`: ≈ 5 k es el armado de los 8 pares (flujo, Rex) y ≈ 1,9 k
  las copias de las cadenas.

## 4. A/B WinUAE (BENCH, cycle-exact, `work/g42o/`)

Control = el defecto (`G5L_MAXPL` = 1) del código nuevo; candidato =
`-DG5L_MAXPL=2`.

| replay | control | 2 Rex (G4-2o) | diferencia | diferencia en G4-2 |
|---|---:|---:|---:|---:|
| back | 385 (racha 5) | 407 (5) | +22 | +38 |
| sprites | 91 (3) | 180 (5) | +89 | +103 |
| hills2 | 211 (3) | 346 (4) | +135 | +188 |

Los controles repiten los de G4-2 (380/91/210): el ruido es de ±5. **El
castigo baja entre un 14 y un 42 %, pero sigue muy por encima del ruido.
G4-2 sigue apagado por defecto** (regla de la tarjeta).

Para que entre en el ruido, la foto con 2 Rex tendría que costar casi lo
mismo que la de uno (≈ 25 k). El camino de varios Rex hace por índice y
por Rex un trabajo que el de uno resuelve con `g5l_fast`. Ninguna de las
palancas que quedan, medidas en §3, cierra esa distancia:

- armado de flujos de `g5l_emitn`: ≈ −2 k;
- caché por variante de `g5l_rxsavef`: ≈ −2 k;
- precalcular la primera y la última fila de cada grupo en la tabla:
  ≈ −2 k;
- fusionar `g5l_need` con `g5l_rxsavef`: ≈ −2 k.

Todas juntas dejarían la foto en ≈ 44 k. Queda registrado para cuando
la ola 7 vuelva sobre D1 con todo junto.

## 5. Cierre

- Puertas: `g5l.py game` exacto con MAXPL 2 en hills2, stress_sprites y
  stress_back; regresión completa `RESULTADO: OK` con el defecto (1); lint
  OK; memmap 0 violaciones; slow del vivo con margen de 136.504 B (la
  caché de Mario crece 4.168 B).
- El trade para el usuario no cambia de forma, solo de tamaño: más Rex
  visibles a cambio de fotos perdidas en los replays con muchos Rex.
- **Sigue G4-B**, los demás enemigos de YI1 (`instrucciones-g4-b.md`): es
  la diferencia visible más grande que queda. G4-3 (los pares de Mario)
  queda aparcada mientras G4-2 esté apagado.
