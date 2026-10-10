# G5L-R-Pa — reutilizar el plan corrido: no sirve (2026-10-09)

Rama `g2t-b2bis`. Fase de medida autorizada por el usuario
(`instrucciones-g5l-r-pa.md`). Solo herramientas (`tools/g5l.py`,
`tools/pa_shift.py`, `tools/pa_levers.py`); el juego no cambió.
**La puerta no se cumple**: ninguna clave reducida da a la vez planes
iguales y aciertos. La vía de la caché queda descartada. Con el modelo de
T2 se midió qué combinación de palancas alcanza, y **ninguna palanca sola
baja de 4 saltos**.

## 1. Paso 1: el plan de Python por foto

`g5l.py game` guarda ahora, por foto, el plan de `plan_frame` (`vo`, `r0`,
`x0`, `groups`, `remaps`, `trans`) y la `s` del scroll, en
`work/g5l/game_frames.json` (copiado a `work/t2/frames.json`, ignorado).
Puerta: `G5L GAME: OK`, media 10 477,6, máximo 93 752, los mismos 145
fallos, y los 145 con plan. OK.

## 2. Paso 2: planes corridos (`tools/pa_shift.py`)

Se simula la FIFO de `g5l_pcput` con la clave reducida. En cada acierto
sobre un fallo se compara el plan con el de la foto que dejó la entrada:
`vo`, `groups` y `remaps` iguales, y `trans` igual con las filas corridas
en Δ = r0_k − r0_j.

`GV_MSH` es la altura **relativa** Rex-Mario (r0 − fila 0 de la caché de
Mario); `GV_R0` es la absoluta. Sacar solo `R0` es la única reducción
válida por construcción, y por eso se midió además de las dos de la tarjeta.

| clave | N | aciertos | iguales corridos | distintos (primera diferencia) |
|---|---:|---:|---:|---|
| sin `R0` | 4 | 0 | — | — |
| sin `R0` | 16 | 13 | 13 (100 %) | 0 |
| sin `R0` | sin límite | 30 | 30 (100 %) | 0 |
| sin `R0`/`MSH` | 4 | 36 | 3 (8 %) | 33 (`vo` 17, `groups` 16) |
| sin `R0`/`MSH` | 16 | 54 | 13 (24 %) | 41 |
| sin `R0`/`MSH` | sin límite | 76 | 30 (39 %) | 46 |
| sin `R0`/`MSH`/punteros | 4 | 84 | 7 (8 %) | 77 (`vo` 36, `groups` 37, `trans` 4) |
| sin `R0`/`MSH`/punteros | 16 | 117 | 17 (14 %) | 100 |

**Puerta (≥ 80 % iguales en los aciertos de una de las dos claves de la
tarjeta): no se cumple (8 %).** Sin `R0` el plan sí es el mismo corrido
(100 %), pero casi nunca acierta: los fallos seguidos cambian la altura
relativa en cada foto (T2: `MSH` en 109 de 145). Con otra altura relativa
cambia qué variante elige el Rex (`vo`) o qué índices pasan a banda
(`groups`). Esto confirma que el plan depende de la altura relativa.

## 3. Dónde está el coste de un fallo (`tools/pa_levers.py`)

`g5l_render` medio: **66 056** ciclos en las 145 fotos de fallo y
**27 562** en las 1898 dibujadas sin fallo (Musashi, sin DMA).

| parte | media en fallo | máx. | % del fallo | media sin fallo |
|---|---:|---:|---:|---:|
| `g5l_sweep` | 10 635 | 18 014 | 16,1 | 0 |
| `g5l_patch` | 8 954 | 19 094 | 13,6 | 673 |
| `g5l_plan` | 8 648 | 15 366 | 13,1 | 0 |
| `g5l_render` propio | 7 174 | 9 338 | 10,9 | 3 460 |
| `g5l_place` | 5 569 | 10 046 | 8,4 | 4 264 |
| `g5l_emit` | 5 290 | 8 852 | 8,0 | 3 553 |
| `g5l_fast` (falla) | 5 159 | 5 168 | 7,8 | 4 900 |
| `g5l_mario` | 4 859 | 6 018 | 7,4 | 4 687 |
| resto (mba, mfill, mwall, choose, clean, mrowba, mrow) | 9 761 | | 14,8 | |

El fallo cuesta 38 k ciclos más que una foto sin fallo. De eso, sweep +
plan son 19 k y el exceso de patch (las bandas: `remaps` medio 1,48 por
plan) 8 k.

**`build_mid` por sentido de la cámara** (ds de la s entre fotos):

| sentido | fotos | % del exceso sobre la mediana | máx. | fotos > 40 000 |
|---|---:|---:|---:|---:|
| izquierda | 826 | 39 | 88 668 | 60 |
| derecha | 2193 | 56 | 54 764 | 11 |
| quieta | 3293 | 6 | 78 938 | 3 |

Los picos más altos son de la vuelta (s ≈ 1780-1900 y 2016-2152; P72),
pero el exceso total está más en la ida.

## 4. Palancas (modelo de cola de T2, ESTIMADO)

Saltos con los cinco mejores ajustes (base 25 en todos):

| cambio | saltos |
|---|---|
| sweep + plan −30 % / −50 % en los fallos | 18-20 / 15-18 |
| sweep + plan + exceso de patch −50 % | 10-13 |
| … + S5 (`build_mid` −50 % del exceso) | **2-6** |
| cota: el fallo cuesta como una foto sin fallo | 5-8 |
| cota + S5 | 0-1 |
| S6: la vuelta con `build_mid` ≤ p99 de la ida (36 858) | 21-23 |
| S6 + sweep/plan/patch −50 % | 6-10 |
| S6 + `g5l_render` −20 % | 3-6 |
| `g5l_render` −10 / −20 / −30 % en todas las fotos | 15-17 / 7-8 / 4-5 |
| `g5l_render` −10 / −20 / −30 % + S5 | 9-11 / **1-2** / 0 |

**Lectura.** El exceso está repartido entre el render de G5L (fallos y no
fallos) y `build_mid` (los dos sentidos). Para llegar a ≤ 5 saltos hacen
falta dos palancas: S5 junto con el camino lento −50 %, o S5 junto con un
20 % de todo `g5l_render`. Sin S5, solo un 30 % de `g5l_render`. Todos son
recortes de asm sin diseño: el T especializó `patch` y bajó su máximo un
22 % (18 804 → 14 646).

## 5. Recomendación

Antes de otro candidato hace falta saber qué recortes son **posibles**,
no solo cuáles bastarían. Tarjeta siguiente, **solo de medida**
(`docs/instrucciones-g5l-r-q.md`, pendiente de autorización):

1. perfil por instrucción (histograma de PC en Musashi) de `g5l_render` en
   las fotos de las 25 ventanas de salto, con las rutinas más calientes
   y sus bucles;
2. lo mismo de `build_mid` en los picos de las dos direcciones;
3. por rutina, el recorte que da una reescritura concreta (estimado, con
   el razonamiento de ciclos por instrucción del 68000) y el total contra
   las dos metas: S5 −50 % y camino lento −50 %, o `g5l_render` −20 %.

Si ninguna combinación posible llega, se le plantea al usuario D1 con los
números (el colchón ya se aceptó; 25 Hz solo con la optimización
agotada, D1).

## 6. Red de seguridad

Los cinco MD5 del defecto, rehechos después del cambio (ver el commit),
iguales a `informe-g5l-r-t2-1009.md` §6. `lint_port.py` y `regress.py
--baseline tools/baseline_pc.json --level --g5l --bm1`: OK.

## Comandos

```sh
python tools/g5l.py game --bin work/t2/replay/game.bin --lst work/t2/replay/game.lst
cp work/g5l/game_frames.json work/t2/frames.json
python tools/t2_attrib.py --frames work/t2/frames.json --vblog work/t2/vt/vbtrace.out --csv work/t2/frames.csv
python tools/pa_shift.py --frames work/t2/frames.json
python tools/pa_levers.py --frames work/t2/frames.json --csv work/t2/frames.csv
```
