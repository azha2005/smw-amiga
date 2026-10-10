# L-DER — la deriva de la lógica de sprites (informe)

2026-10-10. Tarjeta: `docs/instrucciones-l-der.md`. Trampa nueva: P130.

## Resultado

**La deriva no estaba en la lógica de ningún sprite: estaba en el replay.**
Ningún cambio en el 68000 del juego. `sprshot_cmp.py --logic` da
**G9 LOGICA: OK** en las trazas con oamb (todas menos goal, que no entra
en el disco ni antes ni ahora):

| traza | antes (G9) | después |
|---|---|---|
| yi1 | Rex 69,9 %, Mario 99,0 % | todo 100 % |
| stress_piranha | piraña 73,7 %, Rex 83,9 %, Mario 96,0 % | todo 100 % |
| chuck | Chuck 91,2 %, cinta 90,6 %, Mario 95,5 % | todo 100 % |
| hills2, normal, shells, spin_kill, stress_back, stress_sprites | Koopa 96,3 % | 100 % |
| pw_estrella | Rex 96,4 % | 100 % (salvo `sin_captura`) |

(Los 8-13 casos del Rex por traza que quedan fuera del 100 % son
`sin_captura`, que el veredicto ya excluía.)

## Causas

1. **El primer frame bloqueado se saltaba** (yi1, stress_piranha, chuck).
   El estado del oráculo es el de *después* del frame; `m68kverify.py`
   marcaba SKIP todo frame con `$71`/`$9D` ≠ 0, incluido el que la SNES
   corrió entero: el del contacto. En yi1 f7552 el Rex 7 se movió, puso
   `$154C = 8` y llamó a `HurtMario`; el port no. El SYNC de f7600 no toca
   las tablas de sprites, así que el Rex quedó un frame atrás (x −1, luego
   el Rex 6 x −2) para el resto del tramo. Además encoger, crecer, flor y
   morir están portados (P8) y se saltaban igual.
   **Arreglo:** `m68kverify.py --lock run` (por defecto): el primer frame
   bloqueado se corre siempre, y los siguientes si la animación está
   portada. yi1: 2 SYNC + 129 SKIP → 0 SYNC + 32 SKIP (la tubería del
   final, `$71` = 6); tramo continuo 3824 → 6183 frames. stress_piranha
   y chuck: sin SKIP ni SYNC.
2. **El Koopa deslizante, y −1 en las primeras fotos** (todas las trazas
   de snesorc). Ahí el primer estado trae las tablas de sprites de la
   emulación de snesorc (su `replay_hook` copia de la grabación solo dp y
   `$13C0-$14FF`), con una pasada de sprites más que la grabación de yi1
   y que el vivo (`$1540` = 2 contra 3). El juego está bien: con la pasada
   extra en el juego, el Koopa de yi1 pasaba a fallar (161 → 155).
   **Arreglo:** `-DLSS_SNESORC` (C, `level_start_sprites`), solo para
   verificar contra snesorc: `XCDEFS=-DLSS_SNESORC tools/bm_build.sh`.
3. **La estrella de pw_estrella** viene de un `poke $1490 FF` del guion
   (P101); el port la recibía en la primera resincronización por Mario,
   9 frames tarde, y mataba al Rex un frame después que la SNES.
   **Arreglo:** `$1490` en `FIELDS` de `m68kverify.py`: se resincroniza en
   el frame del poke.
4. **El comparador**: la ficha fija `$0C` de Mario (8×8, al derrapar)
   no es dinámica y `sprshot_cmp.py` la descartaba del lado SNES (3 casos
   en stress_piranha). Ahora cada ficha del port tiene que estar en la
   OAM grabada y cada dinámica de la SNES en la del port.

## Herramientas

- `tools/lder.py` (nuevo): RAM de cada ranura del port, frame a frame en
  Musashi, contra la RAM del despacho de la traza oamb. **Usar
  `--key f`**: la clave `mejor` (f o f + 1) escondía el frame de atraso
  del Koopa.
- `tools/m68kverify.py`: `--lock skip|first|run` (`REPLAY_LOCK`), `$1490`
  en `FIELDS`.
- `tools/bm_build.sh`: `XCDEFS` agrega defines al C.
- `tools/sprshot_cmp.py`: comparación de Mario (punto 4).

## Lo que cambia para el resto

El replay por defecto (`work/yi1_replay.bin`) se regenera con `run`: corre
~100 frames más con `level_frame` (el daño en lugar de SKIP), y las fotos
de esos frames ahora tienen gráficos nuevos (P114 deja de aplicar en
f7552-f7600). La regresión se volvió a correr con la base nueva (ver el
commit).

## Tabla final

`work/lder_final.sh` (replay `run`; yi1 con el C normal, el resto con `-DLSS_SNESORC`):

| traza | ops del replay | veredicto |
|---|---|---|
| yi1 | RUN 6280, SYNC 0, SKIP 32, RUNSYNC 0, LEVEL 1 | OK |
| stress_piranha | RUN 3017, SYNC 0, SKIP 0, RUNSYNC 0, LEVEL 1 | OK |
| chuck | RUN 2990, SYNC 0, SKIP 0, RUNSYNC 0, LEVEL 1 | OK |
| hills2 | RUN 2835, SYNC 0, SKIP 0, RUNSYNC 0, LEVEL 1 | OK |
| normal | RUN 1254, SYNC 0, SKIP 0, RUNSYNC 0, LEVEL 1 | OK |
| shells | RUN 2272, SYNC 0, SKIP 0, RUNSYNC 0, LEVEL 1 | OK |
| spin_kill | RUN 1006, SYNC 0, SKIP 0, RUNSYNC 0, LEVEL 1 | OK |
| stress_back | RUN 4126, SYNC 0, SKIP 0, RUNSYNC 0, LEVEL 1 | OK |
| stress_sprites | RUN 1914, SYNC 0, SKIP 0, RUNSYNC 0, LEVEL 1 | OK |
| pw_estrella | RUN 1834, SYNC 0, SKIP 0, RUNSYNC 1, LEVEL 1 | OK |
