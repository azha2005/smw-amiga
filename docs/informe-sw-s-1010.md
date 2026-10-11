# SW-S — puntos, humo y sprites menores: lógica y OAM (2026-10-10)

Commits `a0c7c1d` (lógica) y `370e8e6` (OAM), más el control `-DNOSWS` de
este cierre. Instrucciones: `docs/instrucciones-sw-s.md`.

## Resultado

Los tres motores de efectos de la SNES corren en el 68000, en asm
(`player/logic68k.s`, al principio del fichero; el C de `msprite.c` es la
referencia). Activos por defecto (directiva 1:1). **El estado y la OAM
son exactos contra la SNES** en yi1 y en 4 grabaciones de snesorc. Lo
que falta es **cómo se ven en la Amiga** (paso 3): hoy la OAM se escribe
en `ram[$0200-$02FF]` y nadie la dibuja.

| motor | qué hace | SNES |
|---|---|---|
| puntos | `GivePoints` (cadena de pisotones, estrella, Chuck, power-ups, cinta), `ScoreSprGfx` sube el número, suma puntos / vidas / monedas al pasar SpeedY por `$2A`, dos fichas 8×8 | `sprite_2-clus.s:5757`, `_02AE5B` |
| humo | 1 nube, 2 estrella de contacto (`DisplayContactGfx`), 3 derrape (`CODE_00FE72`, el polvo del Koopa deslizante), 5 destellos (crea menores) | `CODE_0296C0` |
| menores | 1 trozo de bloque (`ShatterBlock` al romper un giratorio con spin, +50 puntos), 2 y 5 destellos | `CODE_028B67` |
| otros | destello de moneda (`CODE_00FD5A`), puntos de moneda de Yoshi y luna (`_00F38A`), vidas pendientes (`CODE_028AB1`) | `ex_sprite.s:424`, `player.s:4830` |

Orden por frame, como `CODE_028AB1`: sprites, vidas, menores, bloques que
rebotan, humo, puntos, carga de sprites.

## Puertas

- **RAM** (`tools/sws_gate.sh` → `sws_cmp.py`: la RAM de los tres motores
  del port tras el frame lógico f contra `snesorc --ram-out` en f):

  | traza | frames | puntos | humo | menores |
  |---|---:|---:|---:|---:|
  | yi1 (replay) | 6279 | 0 | 0 | 0 |
  | pw_bloques | 2075 | 0 | 0 | 0 |
  | chuck_kill | 2954 | 0 | 0 | 0 |
  | spin_kill | 1006 | 0 | 0 | 0 |
  | stress_piranha | 3017 | 0 | 0 | 0 |

  Se excluye 1 frame de yi1 (f11425, la tubería: P131).
  `pw_flor` no entra en el arnés (su replay de 79 KB pasa de `DATA`).
- **OAM** (`sws_cmp.py --oam`, grupos de fichas de cada ranura seguidos y
  exactos en `<oráculo>_oam.bin`): 0 distintos en las 5 (puntos 2295,
  humo 3671, menores 488 grupos).
- **Cruce PC = 68000**: `regress.py` (sin `SPR_OAM`) y `oam68k_gate.sh`
  (con `SPR_OAM`, `OAM68K: OK`): 0 llamadas distintas.
- Regresión completa y lint en verde.

## Coste

- Musashi, `level_frame` del juego: media 21 786 → 22 475 ciclos (+690,
  3 %); máx. 30 618 → 32 048 (base actualizada).
- **A/B BENCH de D1** (WinUAE cycle-exact, `tools/bm_build.sh` con
  `-DREPLAY -DBENCH`; control `-DNOSWS`, que no llama a los cuatro
  motores por frame):

  | | control | SW-S |
  |---|---:|---:|
  | fotos perdidas | 202 (3,20 %) | 217 (3,44 %) |
  | racha más larga | 2 | 2 |
  | total medio | 13 488 ticks | 13 501 |
  | peor `level_frame` | 4 145 | 4 640 |
  | frames de más de un frame | 573 | 583 |

  +15 fotos, sin dibujo todavía. El p99 sale de los frames con destellos
  de moneda (humo 5 + hasta 4 menores), que la SNES también procesa.

## Cosas que se encontraron

- **P131**: en Windows `regress.py` no recompilaba `work/libport.so`; el
  cruce PC = 68000 usaba el C del 7 de octubre. Ahora se compila siempre.
- C que llama a asm a más de 32 KB (P102): las rutinas van al principio
  de `logic68k.s`; `shatter_block` queda en C (la llama `mcoll.c`) y
  `score_at_mario` vive en `msprite.c`.
- El carry de `CODE_00FE72` (humo de derrape) viene del que llama:
  `fe4a(cin)` y `_fe_cin` en el asm.
- La ROM tiene dos curiosidades que se reproducen: la nube calcula un
  atributo con `LDA #0` + `ASL` ×4 (siempre 0), y la estrella de contacto
  de cualquier ranura escribe las mismas 4 fichas (`$02F0`).

## Qué sigue

El paso 3, **el dibujo** (decisión del usuario, `PROXIMO.md` §2):

- **(a) bobs (G7)**, el camino del plan: los efectos son chicos y cortos;
  barato una vez que exista el restaurado de bobs.
- **(b) G5L**, como objetos más con la prioridad más baja: compiten con
  los enemigos (2 por foto); un puntaje podría tapar a un Rex.

Después, SW1 de yi1 en las fotos de la lista (k 199 … 6299) y el A/B
BENCH con el dibujo.
