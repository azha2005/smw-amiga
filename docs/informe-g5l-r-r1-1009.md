# G5L-R-R1 — reescrituras del render G5L y primera medida en WinUAE (2026-10-09)

Rama `g2t-b2bis`, commit `f837262`. Tarjeta autorizada por el usuario
(`instrucciones-g5l-r-r1.md`). Solo `player/g5l.s` y `tools/t2_keys.py`.

**Resultado.** Musashi: `g5l_render` media **10 477,6 → 9 895,5** ciclos
(−5,6 %), máximo 93 752 → 90 452. WinUAE cycle-exact: **BENCH 66 → 53
fotos perdidas** (0,84 %, racha 1) y **VBTRACE 25 → 17 omitidas**. Es la
primera medida de cuánto valen los ciclos de Musashi en fotos omitidas: el
modelo de cola predecía 19-22 para R1 y salieron 17 (16 de 17 en la misma
posición). El modelo es algo pesimista. D1 sigue roja (objetivo ≤ 5).

## 1. Por reescritura (Musashi, `g5l.py game`, 6313 fotos)

Medias acumuladas de `g5l_render` después de cada paso; `G5L GAME: OK` en
cada uno (lista y búfer byte a byte, ABI envenenada).

| paso | qué | media | máx. | estimado de Q |
|---|---|---:|---:|---|
| base (T2) | — | 10 477,6 | 93 752 | |
| 1 | `g5l_pckey`: `GV_PK` = `VLIST`, `R0`, `MSH`, `COL`, `KBUF` (`pcget` falla en la 1.ª `.l`) | 10 195,0 | — | −75 % de `pcget.c` |
| 2 | `g5l_patch`: copias del flujo DMA desenrolladas con salto calculado (`jmp .cle-4(pc,d1.w)`) | 10 145,6 | — | −35 % de `patch.cl` (con `movem`) |
| 3 | `g5l_place`: busca el segmento con lugar recorriendo el pool cuando es corto (2·NP ≤ filas − 1); si no, la fila de antes | 9 979,1 | 90 962 | −60 % de `place.f1` (mapa de bits) |
| 4 | copias fijas desenrolladas: `pcput` clave y remaps, `pcget` remaps, clave de Mario a cero | **9 895,5** | **90 452** | −35-60 % |

`g5l_patch` en las fotos con patch: media 1262 → 1109, máx. 19 094 →
17 790. En el paso 2 el desenrollado (`move.l (a0)+,(a4)+`, 20 ciclos por
`.l` contra 30) rinde más que `movem` (no hay registros libres para un
bloque de 8). En el paso 3 la búsqueda solo por el pool subía el máximo
(93 216 > 90 412 de la fila): por eso es híbrida.

No hechas:

- `g5l_emit.mv` desenrollado: estimado −9 % del bucle con el formato
  actual (los MOVE van de 8 en 8 B y el desplazamiento no se conoce sin
  recorrer). No vale el riesgo.
- `g5l_emit.jl`: recorre 3,8 pasos de media porque lo que hay entre las
  cargas y el salto `$0084` varía; el offset solo lo sabe `build_mid`
  (fuera de alcance de la tarjeta).

Render en las fotos dibujadas sin fallo: 27 562 → 25 819 por foto
(−6,3 %); en los 145 fallos 66 056 → 63 528 (−3,8 %). Las ventanas de
salto cambian de una corrida a otra (son otras fotos): 52 254 por foto en
98 fotos (T2) y 49 202 en 60 fotos (R1).

## 2. WinUAE (cycle-exact, `a500.uae`)

| medida | T2 | R1 |
|---|---:|---:|
| BENCH, fotos perdidas (`game_read.py --auto`) | 66 | **53** (0,84 %), racha 1, 55 VBL repetidos |
| VBTRACE, fotos omitidas (`vbtrace.py`) | 25 | **17** |

Omitidas en R1 (frame del replay): 1045 1127 1713 2075 2079 3308 3311 3313
3328 3349 3364 4042 4217 4219 4563 5445 5854. Primera causa
(`t2_attrib.py`, la parte que más sube en la foto más cara de la ventana):
`build_mid` 8, `g5l_sweep` 3, `g5l_patch` 3, lógica 2, `g5l_mfill` 1.
**Ahora la mitad son picos de `build_mid`**, casi todos de `bm_left` (la
cámara yendo a la izquierda): 4042, 4217/4219, 5445, 5854.

## 3. El modelo de cola recalibrado

Con las fotos de R1, los cinco ajustes de T2 dan 20 19 22 19 19 saltos;
WinUAE dio 17. El sesgo es de +2 a +5: sirve para ordenar palancas, no
para prometer números. Recortes de `build_mid` repartidos hacia adelante
(lo que haría un S5 ideal, sin coste extra): 16-19 con 3 fotos, 14-17 con
8, 13-17 con 12 (ESTIMADO, cota optimista).

## 4. Recomendación

Siguiente palanca: los picos de `build_mid` (sobre todo `bm_left`, la
vuelta), que dominan la mitad de los saltos que quedan. Se atacó en la
misma sesión: S5 (repartir) se descartó y S9 (compartir líneas entre las
listas) se integró: `docs/informe-g5l-r-s9-1010.md`.

## 5. Red de seguridad

`lint_port.py` OK; `regress.py --baseline tools/baseline_pc.json --level
--g5l --bm1` OK; memmap 0 violaciones. MD5 nuevos (es el candidato):

| build | MD5 |
|---|---|
| replay | `a993dddf5c2e0bd529114d97f03fe733` |
| vivo | `c51a2c971146d7bcb293c19a1c5bc30a` |
| bench | `623f5ef78951648ea25a26641fd830f6` |
| dec | = replay |
| decbench | = bench |

No se repitió la comparación visual del frame 1700: `G5L GAME` compara la
lista byte a byte contra el modelo, que es más estricto.

## Comandos

```sh
GDEFS=-DREPLAY OUT=work/r1/replay sh tools/game_build.sh
python tools/g5l.py game --bin work/r1/replay/game.bin --lst work/r1/replay/game.lst | tail -1
python tools/g5l.py game --bin work/r1/replay/game.bin --lst work/r1/replay/game.lst --pcprof work/r1/q_prof.json
python tools/q_report.py --prof work/r1/q_prof.json --frames work/r1/frames.json \
    --vblog work/r1/vt/vbtrace.out --lst work/r1/replay/game.lst
GDEFS='-DREPLAY -DBENCH' OUT=work/r1/bench sh tools/game_build.sh
GDEFS='-DREPLAY -DVBTRACE' OUT=work/r1/vt sh tools/game_build.sh
python tools/game_read.py --shot work/r1/bench/shot.png --auto | tail -9
python tools/vbtrace.py work/r1/vt/game.adf work/r1/vt/trace.bin 175 > work/r1/vt/vbtrace.out
```
