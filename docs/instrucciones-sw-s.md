# SW-S — puntos y efectos: puntuación, estrellas, humo, trozos y monedas que saltan

> **Estado (2026-10-10, noche):** pasos 1, 2 y 4 **hechos**
> (`docs/informe-sw-s-1010.md`): la RAM y la OAM de los tres motores son
> exactas contra la SNES (`sh tools/sws_gate.sh`). Falta el **paso 3, el
> dibujo**: **por bobs (G7), decisión del usuario del 2026-10-10**
> (`docs/instrucciones-g7.md`). Hoy la OAM
> de los efectos queda en `ram[$0200-$02FF]` (ExOamSlot): puntos en
> `$B0 + 8x` (2 fichas 8×8), humo en `$20 + 4x` (la nube 16×16, el derrape 8×8) y la estrella
> de contacto en `$F0-$FF` (4 fichas 8×8), menores en `$50 + 4x` (8×8).
> La opción (b), G5L, quedó descartada. Después: SW1 en las
> fotos de la lista y el A/B BENCH con el dibujo (control `-DNOSWS`).

2026-10-10. Sale de SW1 (`informe-sw1-1010.md`, puntos 5 y 10, y los
trozos del punto 4). **Mediana**: la lógica es chica, pero el dibujo
compite por los sprites.

## Por qué

En ≈ 15 fotos faltan:

- los **puntos** (200, 400, 1000) al pisar un enemigo o tomar un ítem
  (k 199, 1199, 1349, 1399, 1549, 1799, 2199, 2749, 2899, 3149, 3449,
  4699);
- las **estrellas** del pisotón (k 1549);
- los **trozos** de un bloque giratorio roto (k 6049-6299).

En la SNES son tres motores de sprites sencillos, aparte de los sprites
normales:

| motor | RAM | lo crea | hoy en el port |
|---|---|---|---|
| sprites de puntos | `wm_ScoreSprNum` `$16E1`-… (número, x, y, velocidad) | `GivePoints` / `CODE_02ACEF` (`sprite_2-clus.s:5757`) | solo `MEV_SPRITE` ("etapa 10"); no se crean |
| humo / estrellas de contacto | `wm_SmokeSprite` `$17C0`-… | `DisplayContactGfx`, `_01AB72` | `mario.c` crea algunos; no se dibujan |
| sprites extendidos menores (trozos…) | `wm_MExSprNum` `$17F0`-… | `ShatterBlock` (`sprite_2-clus.s:751`), los bloques | no |

## Pasos

1. **La verdad.** El registro del oráculo guarda `dp` y `$13C0-$14FF`,
   no estas tablas.
   - Agregar a `snesorc` un volcado opcional por frame de los rangos de
     RAM de los tres motores (`--ram $16E1:$1700,...`).
   - Grabar con guiones que los usan: yi1 (puntos), `pw_bloques` (trozos,
     monedas), `chuck_kill` / `spin_kill` (estrellas, humo).
2. **La lógica, en el 68000** (directiva: todo en asm; el C es solo
   referencia):
   - `GivePoints`: la puntuación y el sprite de puntos (incluida la
     cadena de pisotones, `$1697`);
   - el movimiento y el fin de cada motor (por frame, en la fase de
     sprites, en el orden de la SNES);
   - `ShatterBlock` desde `bounce_spawn` tipo 7.
   - **Puerta:** las tablas de RAM de los tres motores, iguales al volcado
     del paso 1 en cada frame de los replays (`m68kverify`/`marioverify`
     con el rango nuevo).
3. **El dibujo.** Son 8×8 o 16×8, con 1-3 colores, y duran menos de 1 s.
   Los 8 sprites de hardware están tomados (Mario 0-3, G5L 4-7). Dos
   caminos, a medir:
   - **(a) bobs (G7):** el camino del plan (`plan-tecnico.md` §10.6).
     Los efectos son chicos, así que es barato una vez que exista el
     restaurado;
   - **(b) G5L, como objetos más:** entran en la regla de la foto con
     la prioridad más baja. Compiten con los enemigos: con 2 por foto,
     un puntaje podría tapar a un Rex.

   Recomendado: (a). Si G7 tarda, (b) como paso intermedio, solo con lo
   que no desplace a un enemigo (decidirlo con el usuario: es
   fidelidad).
4. **La OAM:** el port arma la OAM de los sprites (`SPR_OAM`); estos
   motores escriben la suya en la SNES (`CODE_02xxxx` de cada uno).
   Portarlo y compararlo como G8 (la OAM contra la grabación).

## Puertas

- La puerta del paso 2 (RAM de los tres motores igual a la SNES).
- La OAM de los efectos, igual a la grabación.
- SW1 de yi1: las fotos de la lista de arriba, exactas en esas cajas.
- A/B BENCH de D1: la lógica nueva y su dibujo medidos.
- Regresión completa y lint.

## Trampas

- P98: las rutinas de gráficos que escriben la OAM.
- P66: los congelamientos que pone un sprite (el humo de un enemigo
  aplastado).
- P68, P75: el oráculo y el mando.
- P35: los gráficos de Mario se calculan antes que su física.
