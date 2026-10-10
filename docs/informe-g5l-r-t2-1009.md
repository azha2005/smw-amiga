# G5L-R-T2 — por qué se saltan las fotos (2026-10-09)

Rama `g2t-b2bis`. Tarjeta **solo de medida** (`instrucciones-g5l-r-t2.md`).
No se cambió código del juego: solo herramientas (`tools/g5l.py`,
`tools/vbtrace.py`, `tools/t2_attrib.py`, `tools/t2_model.py`,
`tools/t2_keys.py`). D1 sigue roja. **Hay patrón: atraso acumulado por
rachas de fotos caras (21 de 25 saltos en el modelo). Dos fuentes
independientes, el camino lento de G5L (el Rex cambia de forma mientras se
solapa con Mario) y los picos de `build_mid`: la primera sola deja 8-12 saltos, la segunda
13-18, las dos juntas 0-4 (estimado).** La propuesta (§5) no está
implementada: necesita la autorización del usuario (parada de T).

## 1. Las dos cifras de la parada, con el defecto nuevo

Defecto = G5L + CUSHION + SPR_OAM (`53e6453`), WinUAE PAL cycle-exact,
KS 1.2 + A501, una sola WinUAE midiendo (`winuae_lock.ps1`).

| medida | build | fuente | resultado | informe T |
|---|---|---|---|---|
| fotos perdidas BENCH | `GDEFS='-DREPLAY -DBENCH'` (MD5 `e8ac5ee8…`) | `game_read.py --shot work/t2/bench/shot.png --auto` | **66** (1,05 %), racha 1, 68 VBL repetidos | 66 (`shared`) |
| fotos omitidas sin BENCH | `GDEFS='-DREPLAY -DVBTRACE'` | `vbtrace.py work/t2/vt/game.adf work/t2/vt/trace.bin 175` | **25**, mismos frames | 25 |

Los 25 frames (del replay; origen 5145):

```
1044 1127 1673 1711 2076 2078 2460 2630 2757 2794
3308 3311 3313 3328 3331 3345 3350 3364 4043 4217
4221 4559 4567 5445 5854
```

`vbtrace.py` no encontraba la traza con el defecto nuevo: su `.uae` no
llevaba `use_gui=no` y la lectura de memoria propia no recorría regiones
grandes. Ahora usa `winuae_memory.ProcessMemory`, como `bm_probe` y
`load_probe` (P120).

## 2. Coste por foto (Musashi, sin DMA)

`g5l.py game` guarda ahora, por foto, la lógica de la interrupción
(`dc_cop`), la captura, `columns`/`apply_colors`/`set_pointers`/`build_mid`
y las partes de `g5l_render` (`work/g5l/game_frames.json`).
`t2_attrib.py` lo pasa a `work/t2/frames.csv` (6313 fotos, ignorado).
`level_frame` no va en una columna aparte: corre dentro de `game_step`,
que llama `dc_cop`, y está en "lógica" (`player/game.s:1796`). La
herramienta de la tarjeta (`gamecheck.py`) no carga el binario G5L
(supera `DATA = $48000`), por eso todo sale de `g5l.py game`.

**Puerta del paso 2:** media de `g5l_render` 10 477,6 y máximo 93 752, igual
que `G5L GAME` del paso 0. OK.

| ciclos sin DMA | mediana | p90 | p99 | máximo |
|---|---:|---:|---:|---:|
| total (lógica + captura + render) | 52 521 | 86 864 | 122 544 | 156 864 |
| lógica | 42 807 | | | 59 792 |
| `build_mid` | 862 | | | 88 668 |
| `g5l_render` | 962 | | | 93 752 |

Musashi no es la Amiga: estas cifras ordenan y atribuyen; no son tiempo
real ni se suman entre frames distintos.

**Camino lento de G5L.** `g5l_sweep`/`g5l_plan` solo corren si
`g5l_fast` falla en todas las variantes (el Rex choca en color con las
filas de Mario) **y** falla la caché del plan (`g5l_pcget`; clave = pose de
Mario 52 B, `GV_R0`, `GV_MSH`, `GV_COL`, `GV_VLIST`; `player/g5l.s:560-640`,
`g5l_pckey`). Pasa en **145 de 6312 fotos (2,3 %)**, casi siempre
seguidas (90 de los huecos entre fallos son de 1 foto): mientras Mario y el
Rex se solapan, la clave cambia en cada foto. `g5l_render` medio en esas
fotos: **66 056** ciclos, contra **9 172** en el resto.

`build_mid` pasa de 10 000 ciclos en 1059 fotos y de 40 000 en 74.

## 3. Los 25 saltos

Ventana = de dos fotos antes del VBL repetido hasta la foto salteada
(P115: la pareja repetir/saltear va a ~3 frames). Coste total en miles de
ciclos; a la derecha, las dos partes que más pasan su mediana en la foto
más cara de la ventana.

| salto | repite | fotos (total/1000) | lo que más sube |
|---:|---:|---|---|
| 1044 | 1041 | 1039:107 1040:111 1041:125 1042:135 1043:111 1044:85 | mfill +12 538, lógica +12 425 |
| 1127 | 1124 | 1122:90 1123:88 1124:146 1125:144 1126:127 1127:111 | sweep +13 786, mfill +13 472 |
| 1673 | 1670 | 1668:112 1669:102 1670:114 1671:117 1672:96 1673:126 | patch +17 630, mfill +14 186 |
| 1711 | 1708 | 1706:137 1707:116 1708:116 1709:121 1710:117 1711:116 | mfill +14 474, sweep +14 226 |
| 2076 | 2074 | 2072:114 2073:116 2074:121 2075:133 2076:132 | build_mid +33 282, sweep +8 800 |
| 2078 | 2074 | … 2077:126 2078:96 | build_mid +33 282, sweep +8 800 |
| 2460 | 2457 | 2455:27 2456:139 2457:125 2458:118 2459:82 2460:76 | sweep +13 786, mfill +13 412 |
| 2630 | 2627 | 2625:83 2626:83 2627:145 2628:124 2629:86 2630:86 | sweep +13 786, mfill +13 392 |
| 2757 | 2754 | 2752:104 2753:103 2754:140 2755:148 2756:135 2757:99 | build_mid +13 276, patch +12 870 |
| 2794 | 2791 | 2789:91 2790:89 2791:139 2792:128 2793:98 2794:101 | patch +12 870, sweep +12 842 |
| 3308 | 3308 | 3306:131 3307:150 3308:120 | patch +19 094, build_mid +17 322 |
| 3311 | 3309 | … 3309:105 3310:136 3311:141 | patch +19 094, build_mid +17 322 |
| 3313 | 3309 | … 3312:134 3313:100 | patch +19 094, build_mid +17 322 |
| 3328 | 3328 | 3326:156 3327:130 3328:103 | lógica +15 255, sweep +13 718 |
| 3331 | 3328 | … 3329:104 3330:103 3331:103 | lógica +15 255, sweep +13 718 |
| 3345 | 3342 | 3340:94 3341:90 3342:136 3343:127 3344:99 3345:97 | lógica +14 765, patch +12 864 |
| 3350 | 3347 | 3345:97 3346:97 3347:149 3348:127 3349:98 3350:98 | lógica +14 403, sweep +13 786 |
| 3364 | 3361 | 3359:113 3360:88 3361:92 3362:148 3363:129 3364:114 | sweep +13 814, mfill +13 670 |
| 4043 | 4040 | 4038:118 4039:120 4040:115 4041:108 4042:104 4043:101 | build_mid +66 108, lógica +3 819 |
| 4217 | 4214 | 4212:85 4213:129 4214:112 4215:128 4216:138 4217:105 | build_mid +87 806, lógica +2 721 |
| 4221 | 4218 | 4216:138 4217:105 4218:115 4219:82 4220:101 4221:78 | build_mid +87 806, lógica +2 721 |
| 4559 | 4556 | 4554:117 4555:115 4556:107 4557:114 4558:104 4559:114 | build_mid +26 236, lógica +15 789 |
| 4567 | 4564 | 4562:105 4563:98 4564:108 4565:110 4566:111 4567:104 | build_mid +21 224, lógica +15 661 |
| 5445 | 5442 | 5440:65 5441:128 5442:129 5443:130 5444:65 5445:60 | build_mid +78 076, lógica +5 327 |
| 5854 | 5851 | 5849:70 5850:120 5851:130 5852:130 5853:69 5854:66 | build_mid +81 772, lógica +2 117 |

Primera causa por salto: `build_mid` 10, `g5l_patch` 5, `g5l_sweep` 4,
lógica 4, `g5l_mfill` 2. Ningún salto sale de una sola foto cara: todos
llevan **3-6 fotos seguidas de 100-156 k ciclos**. Hay dos familias:

- **Camino lento de G5L** (1041-1127, 1670-1711, 2457-2794, daño de Mario
  3305-3364): sweep/plan/patch/mfill juntos, +13-19 k cada uno.
- **Picos de `build_mid`** (4040-4221, 5442-5854, y parte de 2074 y
  4556-4567): +21-88 k en la foto.

Las fotos de más de p99 caen en 22 de las 25 ventanas; las de más de p90,
en las 25.

## 4. El patrón: atraso acumulado (21 de 25)

`t2_model.py`: un modelo de cola sobre el coste total por foto,
`L = max(0, L + T − B)`, salta cuando `L > S` (colchón) y entonces la
siguiente foto no se renderiza. B y S se ajustan por rejilla para
reproducir los saltos de VBTRACE.

**Ajuste: B = 102 000 ciclos/foto, S = 65 000; el modelo da 25 saltos, 21
de los 25 reales a ±4 frames.** Cumple la puerta "≥ 20 de 25". No
reproduce 1673, 4043, 4221 ni 4567. De sus 25 eventos, 8 no tienen salto
real a ±4: 1582, 1608, 1612 y 1638 (una racha de fallos del camino lento
que en la Amiga no saltó) y 1668, 2071, 2746 y 3323 (5-11 frames antes que
el real). El modelo no tiene DMA ni blitter: da un orden, no un reloj.

Contrafácticos (ESTIMADOS, saltos del modelo sobre base 25). Recortar una
parte "a su mediana" es el límite: quitar todo su exceso.

| cambio | saltos |
|---|---:|
| todas las partes G5L (fast…emit) a su mediana | 3 |
| … quitando el 75 % / 50 % / 25 % de su exceso | 3 / 5 / 9 |
| `build_mid` a su mediana | 14 |
| … quitando el 50 % de su exceso | 16 |
| `build_mid` ≤ 20 000 o ≤ 40 000 | 21 |
| sweep + plan a su mediana | 9 |
| patch a su mediana | 13 |
| mfill a su mediana (caché de Mario) | 23 |
| lógica a su mediana | 16 |
| todas las partes G5L y `build_mid`, 50 % del exceso cada uno | 0 |
| … 25 % del exceso cada uno | 4 |
| todo el render −5 / −10 / −15 / −20 % | 16 / 12 / 6 / 2 |
| `g5l_render` −5 / −10 / −15 / −20 % | 19 / 17 / 10 / 7 |

Robustez: con los seis mejores ajustes (B 96-105 k, S 50-105 k; 20-21 de
25), "todas las partes G5L a su mediana" da 2-3 y "`build_mid` a su
mediana" 12-15. Ojo: esas partes (fast, patch, place, emit) corren en las
~2000 fotos con Rex, no solo en los fallos; la fila no es "arreglar el
camino lento". Eso se mide en §4.1.

### 4.1 Por qué falla la caché del plan (`tools/t2_keys.py`)

`g5l.py game` guarda ahora también la clave del plan de cada foto
(`GV_PK`, 64 B). En los 145 fallos, el campo que cambió respecto de la foto
anterior:

| campo de la clave | fallos en que cambió |
|---|---:|
| `GV_VLIST` (forma del Rex: su fotograma de animación) | **145** |
| `GV_MSH` (fila del Rex respecto de la caché de Mario) | 109 |
| `GV_R0` (primera fila del Rex en la ventana) | 52 |
| punteros GFX32 de Mario | 27 |
| pose de Mario | 9 |
| paleta | 1 |

Un fallo es: **el Rex cambia de forma mientras se solapa en altura con
Mario, y la altura relativa ya no es la de la última vez.** La caché FIFO de
4 entradas (`g5l_pcput`), simulada sobre las mismas fotos (con la clave
entera da 0 aciertos, como la real):

| clave | N = 4 | N = 8 | N = 16 | sin límite |
|---|---:|---:|---:|---:|
| entera (hoy) | 0 | 8 | 11 | 26 |
| sin `R0`/`MSH` | 36 | 43 | 54 | 76 |
| sin `R0`/`MSH` ni punteros | 84 | 108 | 117 | 123 |

**Agrandar la caché no sirve** (26 de 145 sin límite). Quitar campos de la
clave solo vale si el plan no depende de ellos, y **no está demostrado**:
el plan sale de qué filas del Rex chocan con qué filas de Mario, que es
justamente la altura relativa.

Saltos del modelo (ESTIMADOS) con los cinco mejores ajustes:

| cambio | saltos |
|---|---|
| base | 25 |
| aciertos sin `R0`/`MSH`, N = 4 / 16 | 20 / 17-19 |
| aciertos sin `R0`/`MSH` ni punteros, N = 4 | 9-13 |
| **A**: sweep + plan gratis en los 145 fallos | **8-12** |
| sweep + plan + patch + mfill −50 % en los fallos | 9-13 |
| **B**: `build_mid` −50 % del exceso sobre su mediana (S5) | **13-18** |
| `build_mid` −75 % del exceso | 13-17 |
| **A + B** | **0-4** |
| A + B + patch a su mediana | 0 |
| A + B + resto de `g5l_render` −10 % | 0-1 |
| C: `g5l_render` −20 % / −30 % en todas las fotos | 7-8 / 4-5 |
| B + C −20 % / B + C −30 % | 1-2 / 0 |

**Lectura:** ninguna palanca sola baja de 4 saltos (la mejor, recortar
un 30 % de todo `g5l_render`, deja 4-5). Hay dos fuentes de
coste independientes, y hace falta atacar las dos:

- el **camino lento de G5L** (sweep + plan, 145 fotos, 66 k ciclos de
  `g5l_render` contra 9 k): solo, 25 → 8-12;
- los **picos de `build_mid`** (S5, ya en `docs/plan-tecnico.md` §9.2):
  solo, 25 → 13-18.

Juntas: 0-4. La alternativa sin tocar el camino lento es un recorte del
20-30 % de todo `g5l_render` más S5.

## 5. Propuesta de candidato (NO implementada)

**Recomendación: G5L-R-P, en dos partes que se miden por separado.**
Pide autorización del usuario antes de tocar código del juego.

**P-a. Camino lento de G5L más barato o reutilizable** (la parte más
grande). Primera fase **solo de medida, offline, en Python**
(`tools/g5l.py plan_frame` es la referencia del plan): para las 145 fotos
del fallo, ¿el plan de una foto con la misma forma y pose pero otra altura
relativa es el mismo plan corrido (filas + Δ), o cambian los grupos y las
bandas? Si es el mismo corrido en ≥ 80 de las 84-117 que acertarían, una
clave sin la altura con el resultado corrido en `g5l_place`. Si no, bajar
el coste de sweep + plan en asm. Puerta de esa fase: el número de planos
iguales tras el corrimiento, y no implementar nada si queda por debajo.

**P-b. S5 en `build_mid`** (cola por plazo con tope de ciclos por frame;
plan técnico §9.2). Ya está en el plan; el modelo dice que sola no basta,
pero es necesaria.

**Coste estimado (ESTIMADO):** P-a fase de medida, media sesión; P-a
implementación, una sesión si el plan se corre, más si hay que
optimizar sweep/plan en asm; P-b, una o dos sesiones (S5 se estimaba
aparte en ROADMAP §4). Memoria: P-a nada de chip; P-b la cola en slow
RAM. Con A + B el modelo da 0-4 saltos sin BENCH.

**Puerta que lo mediría:** BENCH ≤ 9 fotos perdidas (el control sin G5L),
racha 1; VBTRACE ≤ 5 omitidas; `G5L GAME: OK`; comparación del frame 1700
con 0 píxeles distintos; los cinco MD5 del defecto cambian solo en el
commit del candidato; lint + regress verdes.

**Lo que el usuario decide:** (1) autorizar P-a fase de medida (no toca el
juego), (2) el orden P-a / P-b, o (3) la alternativa de recorte uniforme
del 20-30 % de `g5l_render` más S5, que no tiene diseño todavía.

## 6. Red de seguridad

Solo cambiaron herramientas. Los cinco MD5 del defecto, rehechos después
de los cambios (`work/t2/md5/`), iguales a `informe-cierre-v-bm1-1009.md`
§2:

| build | MD5 de `game.bin` |
|---|---|
| REPLAY | `4328e9c83a309e7527c62d0da7e3a6c4` |
| vivo | `ab75abb4f839d9e2201622375a2726e7` |
| REPLAY BENCH | `e8ac5ee84e5a4a801d5ae9b0e9568026` |
| REPLAY DECOUPLE | `4328e9c83a309e7527c62d0da7e3a6c4` |
| REPLAY DECOUPLE BENCH | `e8ac5ee84e5a4a801d5ae9b0e9568026` |

`lint_port.py`: OK. `regress.py --baseline tools/baseline_pc.json
--level --g5l --bm1`: OK. `G5L GAME: OK` con el volcado nuevo.

## Comandos

```sh
python tools/g5l.py game --bin work/t2/replay/game.bin --lst work/t2/replay/game.lst
cp work/g5l/game_frames.json work/t2/frames.json
python tools/t2_attrib.py --frames work/t2/frames.json --vblog work/t2/vt/vbtrace.out --csv work/t2/frames.csv
python tools/t2_model.py --csv work/t2/frames.csv --vblog work/t2/vt/vbtrace.out
python tools/t2_keys.py --frames work/t2/frames.json --csv work/t2/frames.csv
```

(`work/t2/vt/vbtrace.out` = salida de `vbtrace.py` redirigida.)
