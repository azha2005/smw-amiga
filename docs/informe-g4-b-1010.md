# G4-B — los demás enemigos de YI1 por G5L

2026-10-10. Rama `g2t-b2bis`. Tarjeta: `instrucciones-g4-b.md`. Sigue a
G4-2o (`informe-g4-2o-1010.md`).

**Resultado:** G5L dibuja los demás enemigos de YI1 con la misma regla
que el Rex: un objeto por foto, el más alto que tenga forma, variante y
plazo. Los tipos son la piraña `$4F`, el Chuck `$95`, el Koopa `$BD`, el
caparazón `$05`, la caja `$B9`, la cinta `$7B` y `$02`. El 68000 es
exacto contra la referencia en todos los replays con esos enemigos.
**Va detrás de una opción (`G5L_TYPES=all`)**: §7 dice si D1 lo deja
activar.

## 1. La tabla G5L3 (`tools/g5l.py`)

- Las formas salen de G4-A (`work/g4a/shapes.json`, 30 grabaciones). Cada
  tipo nuevo tiene **un mapa limpio**: blanco en 1, negro en 2 y sus
  colores propios, ordenados, en los índices de `BAND_PREF`. El Rex
  conserva sus 4 mapas.
- Si una forma ya está en el banco (misma clave de fichas y prioridad),
  se usa la del banco: son los mismos píxeles con la misma paleta. Así
  quedan **todas** las formas del Koopa `$BD` (17), de la caja `$B9` (1)
  y de `$02` (4): usan los 4 mapas del Rex. La piraña, el caparazón, la
  cinta y el Chuck tienen mapa propio. Por eso el "tipo" que
  `g5l.py game` sacaba de la variante era la familia de mapas, y G9 lo
  renombró `familia` (el tipo sale de la traza por la ranura).
- La cabecera pasa de `G5L2` a `G5L3`:
  - en los bytes 10-11 va `oo`, el desplazamiento de los **órdenes de
    colores propios** (16 × 16 B). Los mapas 0-3 son los del Rex (antes
    eran `.ord` en `g5l.s`); el mapa 4 + i es el de `G5L_OTHER[i]`;
  - detrás van los **tipos de la captura** (256 bits).
- El byte 7 de cada variante lleva el mapa en el nibble alto (`nidx` sigue
  en el bajo; el 68000 nunca lo lee).
- `g5l.py mk --types all` (o `G5L_TYPES=all` en `tools/game_build.sh`)
  arma la tabla con todos los tipos. Por defecto solo va el Rex.
- `g5l.py game`/`shot` leen la tabla del binario (`g5l_table`), no la
  última que escribió `mk`.

| tabla | `g5l.bin` | variantes limpias (chip) | formas |
|---|---:|---:|---:|
| solo el Rex | 45.098 B | 16.656 B | 22 |
| todos los tipos | 82.376 B | 30.856 B | 70 |

Formas de G4-A por tipo: Chuck 90, Rex 59, piraña 24, Koopa 17,
caparazón 6, `$02` 4, cinta 3 y caja 1 (el Banzai, 6, es bob: G7).

## 2. La referencia (Python, trazas completas)

Las trazas `work/oam_*.trace` solo tenían el Rex y algunos tipos, así que
se generaron trazas nuevas, `work/oamb_<nombre>.trace`, con todos los
tipos. Son 11 grabaciones: yi1, normal, spin_kill, hills2, shells,
stress_back, stress_sprites, pw_estrella, stress_piranha, chuck y goal.
`g5l.py trace --prefix oamb --types all`:

- **0 errores de color** en las 11, con un objeto (`trace`) y con varios
  (`trace --multi`). Con varios, además: 0 píxeles tapados y la misma
  solución que con uno cuando ubica uno solo.
- Con `--types AB`, las trazas nuevas dan exactamente los mismos números
  que las de antes.
- Un Chuck de stress_back no encuentra índice libre para sus bandas
  (`sin_indice`, 1 de ≈ 16.000 objetos) y no se dibuja. Para los demás
  tipos ese motivo cuenta, pero no es un fallo; para el Rex sigue siendo
  un fallo.

Objetos en pantalla y dibujados, sumando las 11 trazas:

| tipo | en pantalla | 1 por foto | `--multi` (2) |
|---|---:|---:|---:|
| Rex `$AB` | 19.701 | 10.954 | 16.377 |
| piraña `$4F` | 5.886 | 5.886 | 5.886 |
| caja `$B9` | 1.857 | 1.776 | 1.776 |
| Koopa `$BD` | 1.531 | 1.531 | 1.531 |
| Chuck `$95` | 998 | 71 | 531 |
| caparazón `$05` | 938 | 56 | 550 |
| cinta `$7B` | 642 | 502 | 586 |
| `$02` | 412 | 412 | 412 |

**El Chuck y el caparazón casi no se ven con un objeto por foto.** No es
un problema de forma ni de color: según la regla, gana el objeto más
alto, y casi siempre hay otro más arriba. Con el Chuck es la cinta de
meta (344 de 590 fotos en chuck) o la piraña. Con el caparazón es la
caja de mensaje (281 de 504 en shells) o un Rex. Con 2 por foto
(`-DG5L_MAXPL=2`) se ven más de la mitad. El resto, en la cola de bobs
(G7), va con su motivo (`bob_canal`, `bob_color`).

## 3. El 68000 (`player/g5l.s`)

- `g5l_capture` copia los objetos de los tipos que marca el mapa de bits
  de la tabla, en vez de `wm_SpriteNum == $AB`. Usa a5, que se guarda.
  El registro no lleva el tipo: `g5l_choose` busca por (fichas,
  prioridad), y la clave ya distingue los tipos.
- `g5l_plan` toma el orden de los colores propios de la tabla (`oo` + mapa
  × 16), no de `.ord` y la posición de la variante (`GV_VMAP`). La
  posición dejaba de ser el mapa en cuanto un tipo tiene uno solo.
  `.ord` y las escrituras de `GV_VMAP` desaparecen (el campo queda
  libre).
- El resto del camino no conoce el tipo: es una variante como otra.

## 4. Exactitud y costo (`g5l.py game`)

`G5L GAME: OK` en todos:

| replay | tabla | MAXPL | fotos con objeto | media (ciclos) | mediana con 1 |
|---|---|---:|---:|---:|---:|
| yi1 | Rex | 1 | 2.044 | 9.990 | 24.670 |
| yi1 | todos | 1 | 4.272 | 20.607 | 28.188 |
| hills2 | todos | 1 | 2.169 | 22.400 | 26.790 |
| hills2 | todos | 2 | 2.169 (847 con 2) | 31.053 | 25.282 |
| stress_piranha | Rex | 1 | 1.727 | 16.728 | 24.006 |
| stress_piranha | todos | 1 | 2.001 (878 pirañas) | 20.542 | 27.820 |
| chuck | Rex | 1 | 1.554 | 16.543 | 25.992 |
| chuck | todos | 1 | 2.126 | 21.716 | 27.044 |
| chuck | todos | 2 | 2.126 (1.040 con 2; 316 Chuck) | 35.037 | 25.928 |

goal no entra: el binario con su replay (699 KB) no cabe ni en el ADF ni
en el arnés. La cinta y el Chuck ya están en chuck.

## 5. Memoria (`memmap.py`, 0 violaciones en todos)

| build | chip | margen `memmap` | margen real | slow libre |
|---|---:|---:|---:|---:|
| replay yi1, solo el Rex | 483.808 B | 40.480 B | 17.464 B | 189.072 B |
| replay yi1, todos | 498.008 B | 26.280 B | **≈ 3.264 B** | 137.592 B |
| replay chuck, todos, MAXPL 2 | 502.808 B | 21.480 B | **−1.536 B: no arranca** | 158.400 B |
| vivo (BM1), todos | 509.536 B | **14.752 B** | 14.752 B | 101.344 B |

- La tabla de todos los tipos suma +14.200 B de chip (variantes limpias)
  y +51 KB de slow, lo que G4-A había estimado.
- **En el replay, el margen de `memmap.py` no es el real (P126).** El
  replay pide la chip a Exec, que retiene 23.016 B (medido en BM1). Con
  todos los tipos y 2 objetos por foto, un `AllocMem` falla y la pantalla
  queda en rojo (`gfail`): pasó en la captura de chuck. Con un objeto
  arranca, pero quedan ≈ 3 KB.
- El vivo usa el boot BM1 (sin Exec), y ahí el margen de 14,7 KB es
  real. `restart_verify.py` da OK con todos los tipos.
- El ADF del replay de goal no entra (los datos acaban en 930.816 B; el disco tiene 901.120 B).

## 6. Evidencia visual (WinUAE cycle-exact, `-DSTOPF`, `work/g4b/`)

`g5l.py shot --only 0`: la captura del control más los píxeles que la
referencia espera del objeto, contra la captura del candidato.

| foto | control | candidato | objeto | píxeles del objeto | distintos |
|---|---|---|---|---:|---:|
| stress_piranha 1705 | solo el Rex (no dibuja nada) | todos | piraña (r0 67, x0 162) | 232 | **0** |
| chuck 2460 | `G5L_TYPES=02` (no dibuja nada) | todos | Chuck (r0 116, x0 173) | 478 | 12 |

- En chuck no hay ninguna foto en la que el control de solo el Rex no
  dibuje nada y el candidato dibuje el Chuck: el Chuck siempre está con
  un Rex al borde. Por eso el control de esa foto se armó con un tipo que
  no aparece (`02`; `build_table` ya no fuerza el Rex en los tipos).
- **Los 478 píxeles del Chuck son exactos.** Los 12 distintos son tres
  puntos de 1 px del borde derecho de un poste de la meta (filas 74, 82 y
  188), lejos del Chuck y fuera de las filas de su plan (141-143 y el
  VBL). Ese borde ya tiene rayitas de colores en el control: son las
  cargas tarde de los postes, donde no alcanza el ancho de banda del
  copper (P81, P45).
- Por qué cambian, como explicación y no como prueba: las tres listas se
  reescriben de a poco. El candidato gasta más CPU y omite otras fotos,
  así que la lista de la foto 2460 tiene otra historia y otras cargas
  tarde en ese borde.
- La captura de chuck 2845 con 2 objetos (cinta + Chuck) quedó en rojo
  por P126 (§5).

## 7. A/B WinUAE (BENCH, cycle-exact, `work/g4b/`)

Control = el defecto (solo el Rex); candidato = `G5L_TYPES=all`, un
objeto por foto. Fotos perdidas (racha):

| replay | control | todos los tipos | diferencia |
|---|---:|---:|---:|
| normal | 11 (1) | 27 (2) | +16 |
| back | 387 (4) | 456 (6) | +69 |
| sprites | 93 (2) | 104 (3) | +11 |
| hills2 | 216 (4) | 225 (3) | +9 |
| stress_piranha | 108 (2) | 131 (2) | +23 |

- Los controles repiten los de G4-2/G4-2o (11, 380-387, 91-93, 210-216):
  el ruido es de ±5-10.
- **normal, back y piranha empeoran más que el ruido.** Por la regla de
  la tarjeta, **los demás tipos quedan apagados por defecto** detrás de
  `G5L_TYPES=all`.
- La causa es esperada: las fotos que no tenían Rex ahora dibujan otro
  enemigo, y cada foto con un objeto cuesta ≈ 25-28 k ciclos. En yi1 las
  fotos con objeto pasan de 2.044 a 4.272 y la media de `g5l_render`, de
  10,0 k a 20,6 k ciclos (§4). La foto de otro tipo no es más cara que la
  del Rex (mediana 28 k contra 25 k).

## 8. Cierre

- Puertas cumplidas:
  - la referencia: 0 errores de color en 11 trazas, con uno y con varios
    objetos;
  - `g5l.py game` exacto en yi1, hills2, stress_piranha y chuck (MAXPL 1
    y 2);
  - capturas: la piraña con 0 px; el Chuck con 0 px en el objeto (§6);
  - memmap con 0 violaciones;
  - `restart_verify.py` del vivo con todos los tipos;
  - regresión completa `RESULTADO: OK` con el defecto, que ya usa la
    tabla G5L3 y la captura nueva;
  - lint OK.
- **Para el usuario, el trade:** con `G5L_TYPES=all` se ven la piraña,
  el Koopa, la caja, la cinta y `$02` casi siempre, y el Chuck y el
  caparazón poco (§2). A cambio:
  - fotos perdidas: normal 11 → 27, back +69, piranha +23;
  - chip del replay casi al límite (P126).
- Sigue **G9**, la comparación automática de la imagen de los sprites
  contra la OAM de la SNES (`instrucciones-g9.md`). Hace falta para
  juzgar el 1:1 sin depender de un control, como pasó con el Chuck.
