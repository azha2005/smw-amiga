# SW-B — los cambios del mapa en la pantalla (bloques rotos, usados, monedas)

2026-10-10. Sale de SW1 (`informe-sw1-1010.md`, punto 4). **Mediana**: hay
que agregar al scroll un mecanismo que hoy no existe.

## Por qué

En 6 fotos (k 6049-6249, en sincronía) la SNES ya rompió los bloques
giratorios y en el port siguen enteros.

- **La lógica sí los rompe.** `bounce_spawn` (`mcoll.c`), con el tipo
  7, llama a `generate_tile` con el bloque `$02` (vacío); `generate_tile`
  escribe `map16_lo/hi` y marca `MEV_TILE`.
- **Nada lleva ese cambio a la pantalla.** El scroll arma cada columna de
  PF1 desde datos precalculados:
  - `D_MAP` es un byte por celda (15 por columna), el índice de un
    bloque de `D_BLK`;
  - `D_BLK` son bloques de 96 B (16 filas × 3 planos × 2 B), ya con los
    índices de color de su línea;
  - `draw_column` (`scroll.s:1550`) y `blit_steps` copian esos bloques.

  Nunca leen el mapa vivo.

Lo mismo pasa, aunque en esta barrida casi no se vio, con:

- un bloque `?` golpeado (queda el `?` en vez del usado);
- una moneda recogida de la capa 1;
- una moneda de Yoshi tomada (`generate_tile` id `$18`, dos celdas);
- el bloque sólido invisible (`$152`) mientras rebota.

## Diseño

`D_MAP` está en RAM y es lo que leen las dos rutinas de columnas. Un
cambio del mapa se refleja así:

1. **parchear `D_MAP`** en la celda: las columnas que vuelvan a entrar
   ya salen bien;
2. **bliteando ese bloque** en PF1 si la columna está en el buffer (las
   dos copias del buffer circular, `SLOTS*2`), igual que un paso de
   `blit_steps`.

Lo difícil es el **índice del bloque nuevo**: los bloques de `D_BLK`
tienen los colores de su línea (los índices de PF1 son fijos por línea
del nivel), así que "vacío" o "bloque usado" no tienen un índice único:
depende de la celda.

## Pasos

1. **El inventario** (`mkscroll.py`):
   - qué celdas de YI1 pueden cambiar: los bloques que `generate_tile`
     o la lógica pueden reemplazar (giratorios `$1E`, `?`, monedas,
     moneda de Yoshi, bloques que rebotan; sacarlos de los llamadores de
     `generate_tile` y de `tile_pg0`/`tile_pg1`);
   - para cada (celda, bloque resultado posible): el bloque convertido
     con los colores de esa línea, agregado a `D_BLK` si no está;
   - si un resultado no entra en los colores de la línea, el informe lo
     dice; no aproximar en silencio.
2. **Una tabla nueva en `yi1_s.dat`, `D_TCHG`:** (celda, Map16 resultado)
   → índice de `D_BLK`, ordenada por celda para buscar rápido. Campo
   nuevo en la cabecera, al final.
3. **La cola.** `generate_tile` (y su equivalente en asm si lo hay, o
   cuando lo haya) encola (celda, Map16 nuevo).
   - **Cuidado con O5:** el cambio ocurre en la lógica del frame k y se
     tiene que ver en la foto de k. La cola va con la foto
     (`dc_capture` copia los cambios del frame a un anillo con el número
     de frame); el render aplica todos los cambios hasta el frame de la
     foto que dibuja, aunque se hayan salteado fotos.
4. **El render** (en el 68000, después de `columns` y antes de
   `build_mid`):
   - por cada cambio pendiente: buscar en `D_TCHG`, escribir `D_MAP`,
     y si la columna está en el buffer, blitear el bloque en sus dos
     copias;
   - con el segundo PF1 de bobs (G7), en los dos.
5. **El reinicio** (`live_death_restart`, `live_restart`): `D_MAP`
   vuelve al original. O una copia en slow (≈ 5 KB) o la lista de
   celdas tocadas con su valor viejo. `restart_verify.py` lo prueba.
6. **La referencia Python** (`scrollsim`/`g5l.py`) tiene que aplicar los
   mismos cambios para que las capturas comparables sigan dando 0.

Los trozos que vuelan al romper un bloque, la moneda que sale de un `?`
y el bloque que rebota son **sprites**, no capa 1: van en SW-S. Esta
tarjeta deja el mapa bien; SW-S los dibuja.

## Puertas

- Una barrida SW1 con un replay de bloques: `tools/snesorc/pw_bloques.orc`
  (ya existe), con `-DHOLDEVERY=10` en el tramo de los golpes. Las
  celdas de los bloques, exactas.
- SW1 de yi1: k 6049-6249 sin las cajas de 16×16 de los bloques
  (quedan los trozos, de SW-S).
- `restart_verify.py`: después de morir, los bloques vuelven.
- A/B BENCH de D1: el coste de un cambio (un blit por bloque) medido;
  dentro del ruido en yi1.
- Regresión completa y lint; `memmap` sin violaciones.

## Trampas

- P34: golpear un bloque cambia el mapa después, en la fase de sprites.
- P26: una celda vacía vale `$25`.
- P28: el ROM reapunta entradas Map16 según la pantalla (tuberías).
- P97, P107, P115: las fotos salteadas y la foto contra la lógica.
- P2, P31: el blitter roba ciclos; cada blit cuesta ~42 µs de CPU.
- P74: las tablas van en `yi1_s.dat`, no en `scroll.s`.
