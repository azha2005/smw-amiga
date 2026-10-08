# G2T-B2bis — la envolvente de Mario por pose, con caché, fuera de la interrupción

2026-10-08. Instrucciones paso a paso. Sustituye a la puerta de ciclos de
B2 de `docs/instrucciones-g2t-bc.md` §3 (B2 sigue valiendo como puerta de
**exactitud**). Modelo previsto: Opus, worktree propio. Parte de master
`876d28d` (o posterior), donde ya están C1 (`7df7ebe`, `ab50698`) y el
WIP de B2 (`876d28d`, «PARADA por ciclos»).

Corre en paralelo con `docs/instrucciones-g2t-b35.md` (el plan en C) y
`docs/instrucciones-g2t-cpre.md` (el copper con un plan precalculado). La
§3 dice qué toca cada una para no pisarse.

---

## 0. Por qué existe

B2 sacó la envolvente de Mario exacta: por fila del copper R y por índice
1..15, el primer y el último x en que Mario usa ese índice. Es igual a
`g2t_ref.mario_amiga` en 2288 + 661 + 455 frames, sin una diferencia.
Pero `g5_capture` decodifica los 512 píxeles de Mario en cada frame y
cuesta **231 612 ciclos** en el peor frame (YI1, frame 10364), contra un
límite de 3000. Aun en asm, píxel a píxel no baja de unos 16 000.

Dato medido por el coordinador sobre los volcados de B2
(`work/g2tb/cap_*.bin`):

| traza | frames con Rex | imágenes de Mario distintas | frames en que cambia la imagen |
|---|---:|---:|---:|
| yi1 | 2288 | 28 | 361 (16 %) |
| normal | 661 | 7 | 187 |
| spin_kill | 455 | 8 | 121 |
| las tres | 3404 | **32** | — |

La imagen de Mario casi nunca cambia, y cuando cambia suele volver a una
ya vista. Recalcular todo cada frame es desperdicio. El número de pose de
la RAM (`$13E0`, `$76`, `$19`) **no** sirve de clave: la misma clave da
otra imagen en 2641 casos. La clave buena ya existe en el juego: la ficha
de la caché MA1 de `mspr_draw` (§2.2).

**Qué no es:** no cambia el modelo (`g2t_ref.py`), ni el contrato, ni la
forma en que se decide el plan. La envolvente tiene que seguir siendo
**exactamente** la de `g2t_ref.mario_amiga`, también con Mario recortado
por el borde de la pantalla.

## 1. Reglas que no se negocian

1. Builds por defecto **idénticos byte a byte**. Todo va bajo `SPR_G5`
   (que exige `-DNOOAM -DSPR_OAM` en CDEFS, `game_build.sh` ya lo
   comprueba). Bucle de hashes de §5.1 antes de cada commit.
2. `tools/g2t_ref.py` es la especificación. Si te parece que hay que
   cambiarlo: **parar** y pedir instrucciones.
3. Exactitud: 0 diferencias contra `g2t_ref.mario_amiga` en las tres
   trazas, incluidos los frames con Mario recortado (fila < 0, fila > 223,
   x < 0 o x > 255).
4. En la interrupción (`dc_capture`), lo nuevo cuesta **≤ 300 ciclos** de
   Musashi en el peor frame. Todo lo demás corre en el render.
5. Render sin RAM viva (P97): lo que el render lee sale de la foto, nunca
   de `_ram` ni de variables que la lógica reescribe mientras se renderiza.
6. Convenciones: ABI de §7 de `AGENTS.md` (d0/d1/a0/a1 de trabajo),
   cabecera de rutina con entrada/salida/registros/ciclos, comentarios en
   español. Sin `int`/`long` a secas en C. P40 (`(An,Dn.w)` con signo),
   P47, P73 (`tst` con `(pc)` no existe), P94 (etiquetas globales cortan
   las locales), P102 (vasm relaja llamadas lejanas: revisar el listado).
7. R9: derivados solo en `work/`. No merge a master, no push.

## 2. Diseño

### 2.1 Qué se guarda

Una **entrada de caché por pose**: la envolvente de Mario en coordenadas
del sprite, no de la pantalla.

- fila relativa `j` = 0..39, contada desde VSTART del sprite (la primera
  fila de datos de SPR0; `MSPR_LINES` = 40);
- x relativa `u` = 0..31, contada desde HSTART de la columna 0
  (SPR0/SPR1 = columna 0, SPR2/SPR3 = columna 1);
- por (j, índice): los píxeles de ese índice en esa fila.

**El recorte del borde manda la representación.** `g2t_ref.mario_amiga`
solo cuenta los píxeles con `0 <= x < 256` y `0 <= R < 224`. Si se guarda
solo (primer, último) relativo, al recortar se pierde exactitud: si el
índice tiene un hueco justo en el borde, `max(primero + hx, 0)` cae en un
píxel que no es de ese índice. Hay dos salidas válidas; elegí una y
justificala en el informe con ciclos medidos:

- **(a) máscara de bits por (j, índice)**: un largo de 32 bits por fila e
  índice (40 × 15 × 4 = 2400 B por entrada, más 80 B de máscara de
  índices por fila). Recortar es enmascarar; primer/último salen con dos
  búsquedas de bit por tabla de 256 B. Exacta siempre.
- **(b) (primer, último) relativos** (40 × 15 × 2 = 1200 B + 80 B) y,
  cuando la caja de Mario cruza x = 0 o x = 256, **decodificar ese frame
  directamente** (sin caché) en el render. Contar cuántos frames de las
  trazas caen en este camino y su coste.

Las filas fuera de 0..223 no plantean problema: se descartan fila a fila
en las dos opciones.

### 2.2 La clave: la ficha MA1 de `mspr_draw`

Leé `player/mspr68k.s` líneas 18-48 y 480-500 antes de tocar nada.
`mspr_draw` guarda por buffer (`mspr_kA` para `g_spra`, `mspr_kB` para
`g_sprb`, 64 B cada una) una ficha de lo que dejó escrito:

- `+3`: los punteros de fichas (`wm_0D85` … `wm_Tile7FPtr`, 22 B);
- `+26`: la OAM de Mario (16 B); `+42`: `mario_osz` (4 B);
- `+46`: la clave de la pose: `n` + las entradas con la y relativa a la
  caja (18 B; `mspr_n`/`mspr_ent`).

La **pose** (lo que define la imagen, sin la posición) es `n` + entradas
(18 B en `+46`) + punteros (22 B en `+3`): **40 B**. Es exactamente lo que
usa el nivel 2 de MA1 («misma pose con otra posición»), así que dos fotos
con la misma clave tienen los mismos DATA/DATB. Comprobalo en el paso B2b-1
antes de construir sobre ello.

Casos sin ficha válida, que tienen que funcionar igual (exactos) aunque
sin caché:

- el buffer 2 (`g_sbuf` + 8, «buffer suelto», solo cuando el render va
  tarde): `mspr_draw` dibuja sin caché (`a5 = 0`), pero `mspr_n`/`mspr_ent`
  sí quedan con la clave de ahora. Verificalo en el código;
- el C (`mario_sprite` de `player/mspr.c`, los casos raros: volteo
  vertical, fichas que se tapan, entradas de 8×8) y Mario oculto:
  invalidan las fichas (`mspr_inval`). Ahí la foto **no tiene clave**: el
  render decodifica sin caché. Contá cuántos frames de las trazas pasan
  por aquí.

### 2.3 Dónde corre cada parte

| parte | dónde | coste objetivo |
|---|---|---|
| copiar la clave (40 B) y una bandera «sin clave» a la foto | `dc_capture`, después de `mspr_draw` | ≤ 300 ciclos (máx.) |
| buscar la clave en la caché | render, antes de `g5_plan` | ≤ 600 ciclos (acierto, máx.) |
| decodificar el buffer de la foto y guardar la entrada | render, solo si falla la búsqueda o no hay clave | medir; **parar si el máximo pasa de 12 000** |

El registro de la foto es `DC_REC` (`dc_rec`, `dc_recp` en
`player/game.s`, ~línea 1559). Agregar los campos bajo `ifd SPR_G5`; con
eso cambia `DC_REC` solo en ese build. El buffer de sprites de la foto no
se reescribe mientras el render lo usa (P97, comentario de `dc_capture`:
«lo que se escribe nunca es lo que se va a ver»): el render puede leerlo.

Caché: N entradas fijas en slow RAM (sugerido N = 16; las trazas usan 32
poses en total y 28 en YI1, así que medí la tasa de aciertos con N = 8,
16 y 32 y elegí). Reemplazo simple (round-robin o LRU por contador). Todo
en una sección `ifd SPR_G5`; `memmap.py` con 0 violaciones.

### 2.4 Decodificación exacta en asm (el camino de fallo)

Sugerencia, no obligación: un **árbol de máscaras por plano**. Por cada
fila y columna hay 4 palabras de plano (`a`, `b`, `c`, `d`: DATA/DATB de
la pareja atada, ver `mspr68k.s` cabecera y `g5plan.c`). Partir el
conjunto de 16 píxeles por plano: `d` y `~d & opacos` (2 máscaras), luego
por `c` (4), por `b` (8), por `a` (16 hojas = índices 0..15), podando las
ramas en cero. Para cada hoja no vacía, primer/último bit con una tabla de
256 B por byte (o la máscara tal cual en la opción (a)). Estimación del
coordinador: 6000-8000 ciclos por pose completa; **no medido**.

La referencia exacta para comparar es la de B2: `player/g5plan.c`
(`g5_capture`) y `tools/g5plan_verify.py` (`block_env`, `canonical`).

### 2.5 La frontera con el plan (B3)

El plan en C (`docs/instrucciones-g2t-b35.md`) lee a Mario **solo** por
dos funciones de `player/g5plan.c`, que B3 escribe primero sobre el
formato actual del bloque de B2:

```c
/* bit i = Mario usa el indice i (1..15) en la fila R (0..223) */
u16  g5_mario_mask(const u8 *blk, s16 row);
/* primer y ultimo x (0..255, inclusivos) del indice idx en la fila R;
   solo se llama con el bit idx de g5_mario_mask encendido */
void g5_mario_span(const u8 *blk, s16 row, u8 idx, u8 *first, u8 *last);
```

Esta tarjeta **reimplementa esas dos funciones** para su formato (puntero
a la entrada de caché + HSTART/VSTART de la foto, o lo que elijas), sin
cambiar su firma. Las demás funciones de `g5plan.c` no se tocan. Si B3
todavía no las escribió cuando llegues, escribilas vos con esa firma
exacta, sobre el formato de B2, en un commit aparte que diga «frontera
B2/B3» (el coordinador resuelve el choque al integrar).

## 3. Qué toca esta tarjeta (y qué no)

| toca | no toca |
|---|---|
| `player/game.s`: `dc_capture` y el registro de la foto (`DC_REC`), bajo `SPR_G5`; la llamada desde el render | `player/scroll.s`, `build_mid`, el emisor (`player/g5.s` es de la tarjeta C-pre) |
| `player/g5env.s` **nuevo**: caché, búsqueda, decodificación | `g5_plan` y el resto de `player/g5plan.c` (de B3) salvo las dos funciones de §2.5 |
| `player/mspr68k.s` solo si hace falta exponer la ficha (sin cambiar su comportamiento: los hashes por defecto lo prueban) | `tools/g2t_ref.py`, `g5ref.py`, el banco G3 |
| `tools/g5env_verify.py` **nuevo**, `tools/g5env_gate.sh` **nuevo** | `tools/oam68k_gate.sh` (el coordinador agrega tu puerta al integrar) |

## 4. Entorno y partida en verde

```sh
export PATH="/c/msys64/ucrt64/bin:$PATH" VBCC=/c/Users/JC/vbcc PY=python
git log --oneline -1                 # 876d28d o posterior; si no: git merge --ff-only master
```

El worktree no trae lo ignorado por git. Copiar desde la carpeta
principal (`C:/Users/JC/Downloads/sma/port-amiga`): todos los ficheros
sueltos de `work/`, y las carpetas `work/g3`, `work/cc`, `work/g2t_ref`,
`work/g2tb`, `assets-out/`, más `player/gen/smwrom00.c` y
`player/gen/smwtabx.h`. `../smw-src-master` desde `.claude/worktrees/` ya
resuelve por una junction que dejó C1; si no resuelve, regress da cientos
de FALLO: parar y avisar, no crear otra.

El arnés rechaza `export … && sh …` en una sola orden y algunos bucles
con `sh`. Usar un guion envoltorio en `work/` (sin versionar), como hizo
C1 (`work/envrun.sh`).

Partida (las tres tienen que dar esto **antes** de tocar nada):

```sh
python tools/lint_port.py                                          # RESULTADO: OK
python tools/regress.py --baseline tools/baseline_pc.json --level  # RESULTADO: OK
sh tools/oam68k_gate.sh                                            # OAM68K: OK (incluye 4b G2T-B2)
```

Si algo no da: parar con la salida.

## 5. Pasos

### 5.1 Bucle de hashes (antes de cada commit)

```sh
for v in "||" "-DREPLAY||" "-DREPLAY -DBENCH||" "-DREPLAY -DBENCH||-DNOOAM -DSPR_OAM"; do
  g=$(echo "$v" | cut -d'|' -f1); c=$(echo "$v" | cut -d'|' -f3)
  CDEFS="${c:--DNOOAM}" GDEFS="$g" OUT=work/hashv sh tools/game_build.sh > work/hashv.log 2>&1 || echo "FALLO $v"
  sha256sum work/hashv/game.bin
done
```

Tienen que salir, en este orden:

```
c03b569643c7bf5ac62f55cdd2813951a6895a6d4801d1eef241e96cfa422769
9403f71c76bc2df9a92a3cc24d8db1e9e67c47e5e62a558e441c3994d0538109
2bc486d77af939aedfb183457e33cc41eba172521959bb0192ddbe6f594363bb
71071566e75a0c1a9dd5391d8398fc44f69ace2e1a4dd489e936c5f7c8bbfad4
```

### B2b-1. Confirmar la clave (sin tocar el juego)

Con los volcados de B2 (`work/g2tb/cap_<traza>.bin`, lector
`g5plan_verify.read_cap`) y los mismos datos que usa `marioverify` en el
modo game, reconstruir la clave de 40 B de §2.2 para cada frame (el
contenido de `mspr_n`/`mspr_ent` sale de `mario_oam`/`mario_osz`, que el
modo game calcula para `mario_sprite`; los punteros, de `ram[$0D85..$0D9A]`).
Puerta: **misma clave ⇒ mismos DATA/DATB** (sin las palabras de control)
en las tres trazas, 0 colisiones; e informar cuántas claves distintas
hay. Si hay colisiones: parar e informar con un ejemplo (frame, clave, las
dos imágenes).

### B2b-2. La decodificación exacta en asm, aislada

`player/g5env.s`: `g5env_decode` (entrada: puntero al buffer de 4
sprites; salida: la entrada de caché en el formato elegido, en una
dirección dada). Arnés en Musashi como el modo `m68k` de
`tools/g5plan_verify.py` (`run_m68k`: carga, llamada, ciclos, ABI). Para
cada frame de las tres trazas: decodificar el `spr` del volcado y aplicar
el recorte con HSTART/VSTART del propio buffer. Puerta: igual a
`block_env` de B2 en todos los frames, **0 diferencias**; ABI distinta 0;
ciclos máx. y media. Si el máximo pasa de 12 000: **parar** con el perfil.

Prueba negativa obligatoria: alterar un píxel de un buffer y ver que la
puerta falla (como hizo B2).

### B2b-3. La caché y la búsqueda

`g5env_lookup` (entrada: la clave de la foto y el puntero al buffer;
salida: puntero a la entrada, decodificando si falta). Arnés: recorrer las
trazas **en orden de frame** (la caché arrastra estado), con la clave de
B2b-1. Puerta: la envolvente de cada frame igual a `block_env`;
informar aciertos/fallos con N = 8, 16 y 32, el coste de acierto
(≤ 600 máx.) y de fallo (≤ 12 000 máx.).

### B2b-4. La frontera §2.5

Reimplementar `g5_mario_mask` y `g5_mario_span` para tu formato. Prueba
en el PC (gcc, `marioverify` modo game): para todos los frames con Rex de
las tres trazas y todas las filas 0..223, los valores de las dos funciones
iguales a los de `g2t_ref.mario_amiga` (la misma comparación que
`g5plan_verify.py env`, pero a través de las funciones). Y en el 68000
(logicbench `SPR_G5`): iguales al PC.

### B2b-5. En el juego

1. `dc_capture` (bajo `SPR_G5`): copiar a la foto la clave de 40 B (de
   la ficha del buffer `d6` si es 0 o 1; de `mspr_n`/`mspr_ent` + punteros
   si es el buffer suelto) o la bandera «sin clave». Medir con `BENCH`
   (marcas `GBS`, ver `game.s` ~1986): **≤ 300 ciclos**.
2. Render: llamar `g5env_lookup` con la foto que se renderiza, antes de
   donde irá `g5_plan` (después de `build_mid`; la tarjeta C-pre pone el
   emisor también ahí: coordinar por el informe, no por código).
3. Gamecheck en Musashi del replay YI1 con `SPR_G5`:
   `CDEFS='-DNOOAM -DSPR_OAM -DSPR_G5' GDEFS='-DREPLAY' OUT=work/b2b_r sh tools/game_build.sh`
   y `python tools/gamecheck.py --engine musashi --bin work/b2b_r/game.bin --lst work/b2b_r/game.lst`:
   0 frames distintos del oráculo, 0 por encima de un frame PAL.
4. Puerta **B2 en el juego** (lo que B2 no llegó a hacer):
   `tools/g5env_verify.py game`, que corre ese build en Musashi y, en cada
   render de una foto con Rex, lee la envolvente por la frontera y la
   compara con `g2t_ref.mario_amiga` del frame del oráculo de esa foto.
   El mapeo foto ↔ oráculo: el replay empieza en el frame 5145 del
   oráculo (`gamecheck` lo imprime) y la foto lleva `R_FRAME` (P75:
   `-DSTOPF` cuenta desde el primer frame del replay). **Comprobá el
   mapeo** con un frame conocido antes de confiar en él. Puerta: 0
   diferencias en todas las fotos con Rex del replay.
5. Vivo: build sin `REPLAY` y `python tools/restart_verify.py --dir <carpeta>`
   pasa. `memmap.py` del replay y del vivo, con y sin
   `SPR_BANK=work/g3/bank`: 0 violaciones, chip ≤ 524 288. Anotar el
   cambio de slow RAM.

### B2b-6. Puerta y red de seguridad

`tools/g5env_gate.sh`: B2b-2, B2b-3 y B2b-4 (PC y 68000) en las tres
trazas; termina en una línea `G5ENV: OK` o `G5ENV: FALLO`. Correrla
entera. Luego lint, regress, `oam68k_gate.sh` y el bucle de hashes.

## 6. Paradas

- Colisión de clave en B2b-1.
- Decodificación > 12 000 ciclos máx. (B2b-2) o acierto > 600 (B2b-3) o
  la parte de `dc_capture` > 300 (B2b-5).
- Cualquier diferencia contra `g2t_ref.mario_amiga` que no entiendas en
  dos intentos.
- Cualquier cambio en los hashes por defecto.
- Necesidad de tocar `g2t_ref.py`, el contrato o `scroll.s`.
- Tres intentos distintos sin cerrar una puerta: entregar parcial (WIP).

## 7. Informe

- Commits (hash de `git log`), uno por paso cerrado como mínimo.
- B2b-1: claves distintas por traza, colisiones (0).
- B2b-2/3: salidas literales de las puertas, ciclos (máx., media, frame),
  aciertos con N = 8/16/32, opción (a) o (b) y por qué.
- B2b-4/5: salidas literales; frames sin clave y por qué camino pasaron;
  mapeo foto ↔ oráculo comprobado; memmap (4 builds); coste de
  `dc_capture` nuevo.
- Hashes por defecto, lint, regress, OAM68K, `G5ENV`.
- Lo no hecho y lo que no pudiste confirmar.
