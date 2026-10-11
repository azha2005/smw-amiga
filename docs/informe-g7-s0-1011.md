# G7-S0 — ¿caben los efectos en sprites de hardware? (medida, 2026-10-11)

Pedido del usuario tras G7-3b: medir si los efectos (puntos, humo,
sprites menores) pueden ir en sprites de hardware en vez del PF1. **Es una
medida, no un plan ni un render.** Herramienta: `tools/g7_sprite_room.py`
sobre los binarios G7_DOUBLE de `work/g7fast/bins/<traza>`; resultados
`work/g7s0/<traza>[-single|-pack].json`.

## Modelo

Por foto con efectos, desde lo que va a leer el chipset:
`g7_hw_support.dma_image` (flujos de los ocho canales, cadenas y
controles), `sprite_palette` (COLOR17-31 y BPLCON2 por píxel con todos los
eventos del copper) y `visibility`. Cada ficha de efecto, en orden de OAM:

- los píxeles que otro sprite ya tapa delante del PF1 no se ven en la
  referencia SNES (el render PF1 los deja detrás): no se dibujan;
- **canal**: el canal o la pareja no tiene tramos en [y0-1, y1] (una línea
  de margen para los controles de la cadena), ni de Mario/enemigos ni de
  otro efecto ya puesto;
- **frente**: BPLCON2 deja la pareja delante del PF1 en todos sus píxeles;
- **color**: cada píxel tiene su color en un COLOR17-31 vigente en esa fila
  y esa x (canal suelto: los 3 de su pareja; adosada: los 15). Sin recargas.

Variantes: solo parejas adosadas; `--single` (canal suelto primero);
`--pack` (sumar la ficha a un sprite propio si todo cabe en 16 px).

## Resultados (`--single --pack`)

| traza | fotos con efectos | fichas | tapadas | no entran | fotos con resto | filas PF1 por foto (media / p99 / máx.) | solo PF1 |
|---|---:|---:|---:|---:|---:|---|---|
| yi1 | 1.416 | 3.498 | 458 | 260 (color 209, frente 21, canal 30) | 111 | 0,83 / 16 / 16 | 6,48 / 22 / 30 |
| chuck_kill | 676 | 1.916 | 160 | 22 (canal) | 14 | 0,16 / 8 / 15 | 8,05 / 24,25 / 28 |
| pw_bloques | 514 | 1.454 | 120 | 23 (canal) | 15 | 0,23 / 8 / 14 | 7,66 / 25 / 28 |
| spin_kill | 369 | 980 | 66 | 8 (canal) | 7 | 0,14 / 8 / 12 | 7,58 / 23,3 / 28 |
| stress_piranha | 979 | 2.081 | 326 | 8 (canal) | 7 | 0,05 / 0 / 12 | 4,78 / 22,2 / 28 |

Sin empaquetar, solo parejas: yi1 536 fichas fuera (15 %); con canal suelto,
494. **Juntar fichas de 8 px en un sprite de 16 px es lo que más rinde**
(humo y puntos vienen en grupos de 2-4 fichas pegadas).

Los fallos de color de YI1 están todos en la zona de la meta (k6019-6070,
k6229-6268): la misma zona que G7-C resolvió con apoyo puntual. 25 fotos
de YI1 no tienen plan ni en el PF1 solo (`g7_fast.py`) ni en sprites
(4687-4688, 6039-6067, 6229, 6256-6263); en las otras cuatro trazas no
hay ninguna foto así.

## Lo que el modelo no prueba (optimista)

- Encadenar tramos en canales que Mario o los enemigos usan en otras filas
  exige coordinarse con sus constructores de flujos (G5L copia la cadena
  por lista, P125). Las asignaciones a una pareja con otros tramos son la
  mitad de las de YI1.
- Solapes entre dos efectos (1.581 píxeles en YI1): el orden de sus
  canales tiene que respetar el de la OAM; no se comprobó.
- No mide el coste de CPU (armar datos de sprite y cadenas por foto) ni el
  DMA; no hay captura WinUAE.

## Lectura

Un híbrido (sprites con empaquetado; PF1 para el resto) reduce las filas
que tiene que producir `player/g7fast.s` en un 87-99 % según la traza.
El peor caso baja de 28-30 a 12-16 filas; la meta de YI1 necesita el apoyo
de color de G7-C o el PF1.
