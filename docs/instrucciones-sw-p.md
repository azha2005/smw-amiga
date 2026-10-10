# SW-P — la prioridad de los sprites contra la capa 1 (la piraña delante de la tubería)

2026-10-10. Sale de SW1 (`informe-sw1-1010.md`, punto 2). **Fácil**: 2
MOVE del copper por objeto con prioridad baja.

## Por qué

En 11 fotos (k 3599, 3649, 4299, 4349, 4799-4899, 5599, 5649, 6149,
6199) la piraña se ve **delante** de la tubería.

- En la SNES está dentro: no se ve, o solo asoma la mitad de arriba.
- Su OAM tiene **prioridad 1** (`attr $1A`/`$5A`, bits 4-5 = 01): detrás
  de la capa 1 entera, delante del fondo (la capa 2 de baja prioridad).
  Mario y el Rex usan la prioridad 2.
- El port pone `BPLCON2 = $0024` una vez por frame (`scroll.s:1674`):
  todos los sprites delante de PF1 (capa 1) y de PF2 (capa 2).

En el OCS, `BPLCON2` da la prioridad **por parejas de sprites**:

| `BPLCON2` | PF1P (bits 0-2) | efecto |
|---|---|---|
| `$0024` (hoy) | 100 | las 4 parejas delante de PF1 |
| `$0022` | 010 | SP01 y SP23 (Mario) delante de PF1; **SP45 y SP67 (G5L) detrás** |

Con PF2P = 100 (`$20`), todo sigue delante de PF2, y `PF2PRI` = 0 (PF1
delante de PF2), como hoy. Un cambio de `BPLCON2` a mitad de pantalla
vale desde el píxel en que cae el MOVE: tiene que ir en el hueco antes
de la primera fila del objeto, como los colores.

## Pasos

1. **La prioridad ya está en la forma.** `g5l_choose` (`g5l.s:2071`)
   exige una sola prioridad por pose y la compara con el byte 3 de la
   variante. El plan sabe la prioridad del objeto que ubica.
2. **La referencia Python primero** (`tools/g5l.py`, `plan_frame` /
   `plan_frame_n` y la planificación de MOVE de `g2t_ref`):
   - si la prioridad del objeto es 0 o 1, dos transiciones más:
     `BPLCON2 = $0022` en la primera fila de su franja y `$0024` después
     de la última;
   - con 2 objetos por foto, cada uno con la suya, y sin solapar
     franjas (ya lo garantiza `bob_canal`);
   - si no hay lugar para el MOVE, el objeto **no se ubica** (motivo
     nuevo `sin_prioridad`), igual que `bob_color`; nunca dibujarlo con
     la prioridad mal.
3. **En el 68000** (`player/g5l.s`): las dos transiciones entran al
   pool de `g5l_place` como MOVE ya escritos (`.w $0104`, `.w valor`),
   con su `need`, por el mismo camino que los colores (P111: el último
   MOVE de una fila cae en x ≤ 351 − 8·nb).
4. **El VBL:** confirmar que la cabecera de cada lista vuelve a poner
   `$0024` (`scroll.s:1674/1677`). Si algún camino reutiliza una lista
   sin cabecera (CUSHION, la tercera lista), poner `$0024` también en el
   bloque VBL de G5L (`g5l_emit`), para que una franja de la foto
   anterior no deje la prioridad baja.
5. **Mario no cambia en esta tarjeta.** Entrando en la tubería, su OAM
   también baja la prioridad; queda para otra (los pares 0-1 necesitan
   PF1P = 000).

## Puertas

- `g5l.py game` **exacto** en yi1, stress_piranha, hills2 y chuck (la
  referencia y el 68000 dan la misma lista).
- Las capturas G9 (`sprshot_cmp.py`) siguen en 0 px. Agregar al juez de
  la imagen la prioridad SNES contra la capa 1 (G9 §3 ya cuenta aparte
  los píxeles tapados).
- SW1 repetida: **las 11 fotos de la piraña, exactas** (fuera de la
  barra de estado y de la deriva de lógica que mide L-DER).
- A/B BENCH de D1 (agrega MOVE): dentro del ruido.
- Regresión completa y lint.

## Trampas

- P32: con 5 planos, los sprites comparten los colores 16-31.
- P39, P42: un WAIT gasta una ranura y la rejilla del copper.
- P110, P111: dónde cae cada MOVE y cuántos entran en el hueco.
- P108: el banco es inmutable; Mario fija índices.
