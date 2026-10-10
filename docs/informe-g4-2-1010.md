# G4-2 — dos Rex por foto en el 68000

2026-10-10. Rama `g2t-b2bis`. Tarjeta: `instrucciones-g4-2.md`. Sigue a
G4-1 (`informe-g4-1-1010.md`).

## 1. La decisión del paso 1 (medida)

En las 8 trazas, de los Rex que G4-1 suma **ninguno comparte filas con
otro ubicado**: todos van separados en vertical, y nunca hay más de 2 por
foto. Por eso G4-2 fija esta regla, igual en la referencia y en el 68000:

- Un Rex entra si deja una línea libre tras el último ubicado: el par c
  se reusa en vertical por encadenado DMA y la columna c va siempre al
  par c.
- Entran como mucho `G5L_MAXPL` = 2 (lo da el búfer de cadena). Si no,
  va a bob con motivo 'canal'.
- Como no comparten filas, sus colores solo dependen de Mario: variante y
  bandas como hoy.
- El plazo se calcula con todos juntos. Si no entra, el último ubicado
  pasa a bob con motivo 'plazo' y se repite.

Con esta regla, `trace --multi` da los mismos números de G4-1: 0 errores
y el mismo total de ubicados en las 8 trazas.

## 2. Qué se hizo

**`tools/g5l.py`:**

- `plan_frame_n` con la regla de arriba.
- `channels_n`: los canales y las cadenas.
- `game`, que ahora compara con `plan_frame_n` (con un Rex da lo mismo
  que `plan_frame`) y verifica cada cadena y el búfer de bandas de cada
  Rex.
- `shot --only`.

**`player/g5l.s`:**

- `g5l_choose`: deja los candidatos ordenados por (fila, ranura) en
  `GV_CAND`.
- `g5l_geo`: si por canal entra uno solo, se sigue el camino de siempre
  (rápido, con caché del plan), sin cambios.
- Si no, el camino de varios:
  - `g5l_rexmw` + `g5l_picksel` (la variante; antes estaba dentro de
    `g5l_render`) + `g5l_rxsave` por Rex;
  - `g5l_sweepn` (transiciones de todos);
  - `g5l_edges` (bordes de 8 dueños) + `g5l_place_e`;
  - `g5l_patch` por Rex, con su búfer y su clave (`GV_PBUF`, `GV_RKP`);
  - `g5l_emitn`.
- **Encadenado DMA** (`g5l_emitn`): si los dos Rex tienen la columna c en
  pantalla, el flujo 2c + mitad se copia a la cadena de la lista (filas
  del primero, POS/CTL del segundo, filas del segundo, fin). El copper
  solo apunta SPRxPT ahí, sin MOVE nuevos. Se cachea por (lista, flujo)
  cuando las dos fuentes son del banco (P125).
- `g5l_sweepn` agrupa en un bloque los tramos de un grupo sin nada entre
  ellos (ni filas de Mario ni otro grupo del índice en la ventana del
  Rex). El resultado es el mismo que `sweep_n` y el costo baja de 39 k a
  17,5 k ciclos de media.
- Memoria: `G5L_RBUF_SIZE` = 3 × `G5L_LBLK` (6.432 B de chip, antes
  1.632), con las bandas de los dos Rex y 4 cadenas de 264 B por lista.
  `G5L_MAXPL` se puede fijar con `-DG5L_MAXPL=1` (un Rex, como antes).

## 3. Exactitud (`g5l.py game`, Musashi, lista palabra por palabra)

| replay | fotos | con 1 Rex | con 2 Rex | cadenas | distintas |
|---|---:|---:|---:|---:|---:|
| `yi1` (regresión) | 6.313 | 2.044 | 0 | 0 | 0 |
| `hills2` | 2.836 | 1.288 | **605** | 1.380 | 0 |
| `stress_sprites` | — | 775 | **265** | 900 | 0 |
| `stress_back` | — | 2.304 | **136** | 354 | 0 |

`G5L GAME: OK` en los cuatro. Además: `dc_loop_verify` OK, memmap 0
violaciones y lint OK.

## 4. Costo (ciclos de `g5l_render`, Musashi)

| | mediana | máximo |
|---|---:|---:|
| foto con 1 Rex (hills2) | 25.160 | 91.988 |
| foto con 2 Rex (hills2) | 63.496 | 132.166 |
| foto con 2 Rex (stress_sprites) | 71.970 | 132.534 |

Una foto con 2 Rex cuesta ≈ 40 k ciclos más (≈ 28 % de un frame PAL).
Desglose típico: `g5l_sweepn` 17,5 k, `g5l_emitn` 7 k + `g5l_emitc` 3 k,
`g5l_rxsave` 6 k, dos `g5l_plan` 6 k y `g5l_place_e` 5,5 k.

## 5. A/B WinUAE (BENCH, cycle-exact, `work/g42/`)

Control = `G5L_MAXPL` 1 (un Rex, el plan de antes), candidato = 2. El
mismo binario en todo lo demás.

| replay | fotos | control: perdidas (racha) | G4-2: perdidas (racha) | fotos con 2 Rex |
|---|---:|---:|---:|---:|
| normal | 6.312 | 11 (1) | 11 (1) | 0 |
| back | 4.126 | 380 (5) | **418** (5) | 136 |
| sprites | 1.914 | 91 (3) | **194** (4) | 265 |
| hills2 | 2.835 | 210 (3) | **398** (4) | 605 |

Ruido del control: back daba 373 (racha 4) en la tanda de G5L-N, ±10.
**D1 empeora mucho más que el ruido** en todos los replays con fotos de
2 Rex: entre 0,28 y 0,39 fotos perdidas por cada foto con 2 Rex. Sirve
de comprobación: +40 k ciclos son ≈ 28 % de un frame, y en el estrés
el frame ya va al 95-97 %.

**Decisión (regla de la tarjeta): G4-2 queda apagado por defecto**
(`G5L_MAXPL` = 1). Se activa con `-DG5L_MAXPL=2`. El trade, para el usuario:

- con G4-2 se dibujan más Rex: hills2 de 1.893 a 2.498 (+32 %),
  stress_sprites de 1.040 a 1.305;
- a cambio se pierden 1,9 veces más fotos en hills2 y 2,1 veces más en
  sprites.

Hoy los Rex que no entran **no se dibujan** (la cola de bobs es G7).

Con `G5L_MAXPL` = 1 el búfer por lista vuelve a 4 × 136 B (no hay
cadenas). El camino de un Rex y la elección de otro candidato cuando el
primero no tiene variante quedan como en el control. `g5l.py game`/`shot`
leen `G5L_MAXPL` y `G5L_LBLK` del listado.

## 6. Evidencia visual (WinUAE cycle-exact, `-DSTOPF`)

Dos fotos de hills2 con 2 Rex: frames 1825 y 2130 (`work/g42/h2{ctrl,cand}<f>/`,
`h2_run.ps1`). `g5l.py shot --only 1` toma la captura del control (un Rex)
y le suma lo esperado del segundo Rex:

| foto | Rex 0 (r0, x0) | Rex 1 (r0, x0) | píxeles del Rex 1 | distintos |
|---|---|---|---:|---:|
| 1825 | 50, 42 (aplastado, arriba) | 161, 115 | 421 | **0** |
| 2130 | 133, 93 | 162, 32 | 418 | **0** |

En `check.png` (control / captura / esperado) el segundo Rex aparece en
el suelo, debajo del primero, sobre el mismo par de sprites (encadenado).

## 7. Cierre

- Puertas: `g5l.py game` exacto (§3), `dc_loop_verify` OK, memmap 0
  violaciones, lint OK y regresión completa `RESULTADO: OK` con el
  defecto (1). Replay: chip 390.704 B.
- **G4-2 hecho, apagado por defecto por D1** (§5).
- Sigue **G4-2o**: abaratar el camino de varios Rex hasta que el A/B
  quede en el ruido (`instrucciones-g4-2o.md`). Después G4-3, los pares
  de Mario (`instrucciones-g4-3.md`).
