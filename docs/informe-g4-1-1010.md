# G4-1 — varios Rex por foto: la referencia en Python

2026-10-10. Rama `g2t-b2bis`. **Solo Python; el binario no cambia.**
Tarjeta: `instrucciones-g4-1.md`.

## 1. Qué se hizo

En `tools/g5l.py` se agregó `plan_frame_n` sin tocar `plan_frame`, que
sigue siendo la referencia del 68000:

- Los Rex visibles con forma se ubican en orden (fila, ranura): el
  primero es el mismo que elige hoy `plan_frame`.
- **Canales:** pares 4-5 y 6-7, una columna por par (como `channels`). Un
  par se reusa en vertical con una línea libre: G0 midió que el encadenado
  DMA funciona con gap 1 (`medida-g0.md`).
- **Colores:** `band_need_n`/`band_assign_n` ven la ocupación por fila e
  índice (Mario y los Rex ya ubicados, con su color). Con solo Mario dan
  lo mismo que `band_assign`.
- `sweep_n` mezcla los tramos de Mario y de todos los Rex en el orden del
  original. `EMap` da los bordes por máscara de dueños: con un Rex, la
  tupla `E` de siempre.
- `place` se aplica a todas las transiciones juntas. Si un Rex no entra
  por canal, color o plazo, va a la cola de bobs con ese motivo.
- `check_trace_n` cuenta los errores de color de cada píxel de Mario y de
  todos los Rex (`g2t_ref.simulate` y `pixel_errors`), y los píxeles de
  Rex tapados por otro Rex.
- `g5l.py trace --multi`: la puerta. Además compara con `plan_frame` las
  fotos en las que se ubica un solo Rex, el mismo (`igual_a_uno`).

## 2. Resultado (8 trazas; `work/g5l/trace_multi.json`)

| traza | Rex visibles | hoy (1 por foto) | G4-1 | bob: canal | bob: color/plazo | errores | iguales a hoy / distintos |
|---|---:|---:|---:|---:|---:|---:|---|
| `yi1` | 2.294 | 2.043 | 2.043 | 251 | 0 | 0 | 2.043 / 0 |
| `normal` | 691 | 567 | **632** | 59 | 0 | 0 | 502 / 0 |
| `spin_kill` | 446 | 418 | **446** | 0 | 0 | 0 | 390 / 0 |
| `hills2` | 3.042 | 1.893 | **2.498** | 544 | 0 | 0 | 1.288 / 0 |
| `shells` | 1.716 | 1.253 | **1.387** | 329 | 0 | 0 | 1.119 / 0 |
| `stress_back` | 3.262 | 2.440 | **2.576** | 686 | 0 | 0 | 2.304 / 0 |
| `stress_sprites` | 1.513 | 1.040 | **1.305** | 208 | 0 | 0 | 775 / 0 |
| `pw_estrella` | 1.288 | 940 | **1.067** | 221 | 0 | 0 | 813 / 0 |

`G4-1 TRACE: OK`. 0 píxeles tapados entre Rex y hasta 2 Rex por foto.
**Ningún Rex queda afuera por color ni por plazo: el límite son los
canales.** En `yi1` los Rex que faltan comparten filas con el dibujado
(caminan sobre el mismo suelo), así que no se gana nada sin más canales.

Costo del plan (máximos en todas las trazas): 24 transiciones (el 68000
admite `G5L_MAXTR` = 200), 10 segmentos con sufijo (`G5L_NPOOL` = 32) y 6
colores en el VBL (15). Hoy los máximos son 18-20, 8-9 y 5.

## 3. Lo que da más canales (cota, sin colores)

Con los pares de Mario (0-1, 2-3) en las filas donde Mario no está
(±1 línea), la cota por canales (`g41_chan`, la misma regla de reuso)
sube: `yi1` 2.111, `normal` 691, `hills2` 2.865, `stress_back` 2.882 Rex.
Para eso hay que encadenar el flujo del Rex detrás del de Mario en sus
canales. Además, la prioridad del hardware (0-3 delante de 4-7) puede no
coincidir con el orden de la OAM de la SNES cuando dos objetos se cruzan
en una fila. Se deja medido para después de G4-2.

## 4. Siguiente: G4-2 (el 68000)

Llevar `plan_frame_n` a `g5l.s`, con los pares 4-7 y el reuso por
encadenado DMA en un búfer de chip por lista, sin MOVE nuevos en el
copper. `g5l.py game` tiene que dar la lista exacta. Tarjeta:
`instrucciones-g4-2.md`.
