# REX2 — dos Rex en las mismas filas (sin Rex invisible)

2026-10-11. Pedido del usuario: el "flicker" con dos Rex juntos.

## El problema (medido)

Cuando dos Rex comparten filas en pantalla, uno solo entra en los canales
de sprite (`tools/g5l.py plan_frame_n`, `player/g5l.s` `.multi`). El otro
queda como bob `'canal'`, que no existe, así que **no se dibuja**. Y como se
elige por fila de arriba y el Rex sube y baja al caminar, **cuál** se ve
cambia cada ~15 cuadros.

Medida sobre las trazas SNES (script de la sesión, a rehacer como
herramienta en el paso 1):

| traza | cuadros con un Rex invisible | intercambios | Mario fuera de las filas del Rex invisible (±1) |
|---|---:|---:|---:|
| yi1 | 251 | 42 | 55 |
| hills2 | 544 | 95 | 454 |
| stress_sprites | 208 | 48 | 181 |
| stress_back | 686 | 139 | 452 |

Canales hoy: Mario = pares 0-1 y 2-3, Rex = pares 4-5 y 6-7 (la columna c
del Rex va al par c, reusados en vertical por encadenado DMA, G4-2).

## La solución (opción 1)

El Rex sin canal va a **los pares de Mario** cuando Mario no ocupa sus
filas (con una línea libre arriba y abajo para los controles de la
cadena), encadenado en esos pares igual que los Rex de G4-2.

**Extensión (medir aparte):** si Mario y el Rex caben cada uno en una sola
columna de 16 px (`v0['cols'] == 1`; yi1 tiene 74 cuadros con un Rex así),
pueden compartir los pares 0-3 aun en las mismas filas.

## Pasos

1. **Herramienta de medida** `tools/rex2_room.py` (o `g5l.py trace
   --rex2`): por cuadro, Rex visibles, dibujados, invisibles e
   intercambios. Es la línea base de la tabla de arriba y la puerta final
   (**0 Rex invisibles en los casos que la regla cubre**).
2. **Especificación** en `tools/g5l.py`:
   - la regla nueva de ubicación (`plan_frame_n`): pares 0-3 si Mario
     está libre;
   - colores: las cuatro parejas adosadas comparten COLOR17-31, así que
     `band_assign_n` y `sweep_n` tienen que contar a los dos Rex y a
     Mario en las mismas filas (hoy suponen que los Rex no comparten
     filas);
   - **orden delante/detrás**: en la Amiga, los canales bajos tapan a los
     altos. Si los dos Rex se solapan, el que está delante en la OAM de la
     SNES tiene que ir en el par más bajo; si no se puede, el caso no se
     cubre (explícito, no aproximado);
   - prioridad contra el PF (BPLCON2) igual que hoy, por par.
3. **Verificador**: `g5l.py trace --multi` con 0 errores de color en las
   ocho trazas y comparación por píxel contra la OAM de la SNES en
   capturas (`g5l.py shot`, como G9) de cuadros con dos Rex en las mismas
   filas.
4. **68000** (`player/g5l.s`, `g5l_render` camino `.multi`, `g5l_emitn`,
   cadenas en los pares de Mario coordinadas con `mspr_draw`), cruzado
   con `g5l.py game` palabra por palabra en `hills2`, `stress_sprites`,
   `stress_back` y yi1.
5. Coste (Musashi y BENCH WinUAE, puerta D1: decir cuánto empeora) y
   memoria (búfer de cadenas: `G5L_RBUF_SIZE`, memmap con 0
   violaciones).
6. Lo que la regla no cubre (Mario en las mismas filas): queda para el bob
   (`docs/instrucciones-banzai.md`, misma infraestructura). Solo si el
   usuario lo pide, una **elección estable** (que el invisible sea siempre
   el mismo) como paliativo.

## No hacer

- No alternar cuadros (multiplexado a 25 Hz): no es fiel.
- No reusar canales a mitad de línea con el copper (unos 12 MOVE por línea;
  P39, P111).
- No aproximar colores. No usar tablas por número de frame.
- Puertas de siempre antes de cada commit (lint, regresión, `sws_gate`,
  `oam68k_gate`). Si cambia el vivo por defecto, decirlo con el hash nuevo.
