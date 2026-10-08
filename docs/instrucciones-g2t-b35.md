# G2T-B3/B5 — el plan del Rex en C, igual en el PC y en el 68000

2026-10-08. Instrucciones paso a paso. Detallan las fases B3, B4 y B5 de
`docs/instrucciones-g2t-bc.md` §3 con lo que se sabe después de la
parada de B2. Modelo previsto: Opus, worktree propio. Parte de master
`876d28d` (o posterior: C1 y el WIP de B2 ya están).

Corre en paralelo con `docs/instrucciones-g2t-b2bis.md` (la envolvente de
Mario barata) y `docs/instrucciones-g2t-cpre.md` (el copper con un plan
precalculado). La §3 dice qué toca cada una.

---

## 0. Por qué existe y qué no es

`tools/g2t_ref.py` calcula offline, para cada frame con Rex, el **plan**:
qué variante de la pose usar, qué colores COLOR17-31 recargar en qué
segmento de la lista del copper, y cómo armar SPR4-7 en el bloque VBL.
La puerta A-T prueba que ese plan existe y es correcto en los 3404
frames. Falta que **el juego** lo calcule. Esta tarjeta escribe
`g5_plan()` en C y demuestra que da **los mismos bytes** que
`g2t_ref.py` en el PC (B4) y en el 68000 (B5), y mide cuánto cuesta.

No es: optimizar a asm (si no entra en el presupuesto, se informa con un
perfil y se propone, §6), integrar en el juego (eso es de la tarjeta C
siguiente), ni tocar el modelo.

## 1. Reglas que no se negocian

1. `tools/g2t_ref.py` es la especificación: el C la imita, nunca al
   revés. Si algo del C no puede imitarla: **parar** y pedir
   instrucciones. Esta tarjeta **no modifica** `g2t_ref.py`: lo que haga
   falta volcar desde él va en herramientas nuevas que lo importan como
   biblioteca.
2. Builds por defecto idénticos byte a byte (todo bajo `SPR_G5`). Bucle
   de hashes de §5.1 antes de cada commit.
3. Constantes del contrato tal cual (`g2t_ref.py`: `END`, `X_D0`,
   `IDLE`, `K255`, `VBL_ARM`, `SUFFIX_SLOTS`, `WRAP_SEG`, `advance()` con
   231 → 243, `xh()` solo hasta `$CE`).
4. Función pura: `g5_plan()` lee solo lo que recibe por argumentos (la
   foto, las tablas, la lista); nada de `_ram` ni de globales que cambian
   (P97). Las tablas G3 por su base, nunca por símbolo absoluto (P102).
5. C para vbcc: tipos `u8 s8 u16 s16 u32 s32`, nunca `int`/`long` a secas
   (ni en retornos); sin `float`; sin `malloc`; sin `static` con la
   dirección tomada (P47); tablas C en bloques `#ifdef` (P78); cuidado con
   P36 (datos a menos de 32 KB de `a4`), P37 (vbcc mete en línea las
   `static`), P38/P62 (vbcc `-O=991` puede sumar dos veces la base de un
   puntero: si un resultado del 68000 difiere del PC sin explicación,
   sospechá de esto primero), P40 (`(An,Dn.w)` con signo). Divisiones y
   módulos: el C trunca hacia cero, Python redondea hacia abajo; usá solo
   operandos no negativos o escribilo explícito.
6. R9: derivados solo en `work/`. No merge a master, no push.

## 2. Las entradas de `g5_plan()`

```c
/* player/g5plan.h, bajo SPR_G5 */
u16 g5_plan(const u8 *blk,          /* la foto: bloque de g5_capture (B2) */
            const u8 *g3tab,        /* tablas del banco G3 (bank.idx) */
            const u8 *g3env,        /* envolventes del Rex por pose (§2.3) */
            const u8 *list,         /* la lista del copper que se escribe */
            u16 cl, u16 seg,        /* CL_LINES y SEG de ese build */
            u8 *out);               /* el plan, formato B1; devuelve su largo */
```

La firma es una sugerencia; si la cambiás, documentalo en el informe. Lo
que no cambia es el formato de salida: **B1** (`g2t_ref.dump_plans`,
`docs/instrucciones-g2t-bc.md` §B1).

### 2.1 Mario: solo por la frontera

`g5_plan` lee a Mario **solo** por estas dos funciones de
`player/g5plan.c`. Escribilas primero, en un commit propio que diga
«frontera B2/B3», sobre el formato actual del bloque (`G5B_MROW`,
`G5B_MASK`, `G5B_ENV` de `g5plan.h`):

```c
/* bit i = Mario usa el indice i (1..15) en la fila R (0..223) */
u16  g5_mario_mask(const u8 *blk, s16 row);
/* primer y ultimo x (0..255, inclusivos) del indice idx en la fila R;
   solo se llama con el bit idx de g5_mario_mask encendido */
void g5_mario_span(const u8 *blk, s16 row, u8 idx, u8 *first, u8 *last);
```

La tarjeta B2bis va a reimplementar esas dos funciones para su caché, sin
cambiar la firma. No uses `G5B_MASK`/`G5B_ENV` en ningún otro lugar.

### 2.2 Los segmentos de la lista: perezosos

`g2t_ref.segments()` recorre las 224 filas de la lista (desde
`base + cl + seg·L` hasta el salto `$0084`) y saca por fila: `nb` (MOVE
del borrado), `last` (x de la última carga en el modelo, o ninguna),
`wrap` (cruza la línea 255) y `free`. Recorrer las 224 filas en el 68000
costaría del orden de 90 000 ciclos (estimación del coordinador, ~20 palabras por fila): **no** se puede hacer entero.

`g5_plan` pide solo los segmentos que usa: los de las filas entre la
primera y la última transición posible (las del Rex ± 1 y las filas en
que hay que restaurar R_PAL), más el siguiente de cada uno (la regla de
fin mira el `nb` del segmento siguiente). Escribí:

```c
/* un segmento: nb, x de la ultima carga ($7FFF = ninguna), cruce 255 */
void g5_segment(const u8 *list, u16 cl, u16 seg, s16 row, u8 *nb, s16 *last, u8 *wrap);
```

con la misma semántica que `g2t_ref.segments` (leerla entera, líneas
146-184: T empieza en `S.T0 + max(0, 16·(nb − 9))` con `T0 = −56` a
256 px; un WAIT deja `T = max(advance(T, 2), xh(h))`; un MOVE cae en T y
`T = advance(T)`; el NOP `$01FE` en las dos primeras palabras sustituye a
un WAIT del cruce; `$FFDF` marca el cruce). Que la salida sea idéntica es
lo que mide B4; la pereza es solo coste.

### 2.3 El Rex: envolventes por pose precalculadas

Las tablas G3 (`work/g3/bank.idx`, leídas por
`sprgfx_bank.deserialize_bank`) traen por pose: origen, ancho, alto,
fichas y, por fila, el mapa índice DMA → color (`row_maps`). **No traen
dónde está cada índice en x**: `g2t_ref` saca las filas de píxeles
decodificando los flujos DMA del chip (`sprgfx_final.decode_channels`).
Hacer eso en el 68000 por frame repetiría el problema de B2.

Solución: una tabla derivada nueva, `work/g3/bank.g5env`, generada
**desde el banco** por una herramienta nueva `tools/g5bank_env.py` (el
banco no se toca; R9: el fichero vive en `work/`). Medido por el
coordinador sobre el banco actual: **289 poses, 7198 filas, 27 616 pares
(fila, índice)**, ancho máx. 20, alto máx. 32. A 3 B por par + 1 B por
fila son **≈ 90 KB**.

Mismo problema que con Mario: `uses_of` solo cuenta píxeles con
`0 <= x < 256` y `0 <= R < 224`. Si se guarda solo (primer, último), un
Rex recortado por el borde izquierdo o derecho con un hueco en ese índice
da otro valor. Elegí y justificá con datos:

- **(a)** máscara de bits por (fila, índice) (≤ 20 px: un largo;
  ≈ 138 KB en total), recorte exacto por enmascarado; o
- **(b)** (primer, último) y, solo en los frames con el Rex cruzando
  x = 0 o x = 256, decodificar las columnas de DMA de ese Rex en el
  momento. Contá esos frames en las trazas (`rex_fuera_pantalla` y
  `recorte` de `work/g2t_ref/resumen.json` dan una pista).

Formato: big endian, con una cabecera (magia `G5EV`, versión, número de
poses, CRC del `bank.idx` y del `bank.dma` de los que salió) y una tabla
de offsets por número de pose. Test sin assets en `tools/test_g5bank_env.py`
(una pose sintética) y añadirlo a la lista de `g2t_checks` de
`tools/regress.py` (como `test_g2t_ref.py`).

**Memoria:** la tabla irá a slow RAM en el juego. No la cargues en el
juego en esta tarjeta, pero estimá con `python tools/memmap.py` (build
`SPR_G5` + `SPR_BANK=work/g3/bank`) cuánta slow queda y ponelo en el
informe. Si no entra: parar.

### 2.4 Qué hace `g5_plan` (en el orden de `g2t_ref.plan_frame`)

Leé `g2t_ref.plan_frame` (líneas 448-560) y las funciones que llama. El C
reproduce, en este orden:

1. **Elegir el Rex**: de los candidatos de la foto (`G5B_REX`), el de
   menor `sy + origen_y` de la primera variante de su forma y, a igualdad,
   la ranura menor. La forma es `sprgfx_bank.shape()`: la tupla de fichas
   (dx, dy, ficha, tamaño, volteos, paleta) más la prioridad; el
   directorio (`bank.idx`, `G2IX`) da la lista de variantes por forma.
   Construí la forma desde las entradas OAM del candidato **igual** que
   `B.shape(r)` en `g2t_ref` (mirá `g5ref.py`/`sprgfx_bank.py` para ver
   cómo se arma desde un registro de la traza).
2. **Paleta**: `R.palette_index(ram, pointers)` → R_PAL de la foto
   (`G5B_PAL`) y sus 16 colores (`mario_pal.bin`, 32 B por paleta: pasala
   como tabla, por base).
3. **Filtro A3** por variante (`a3_compatible`): con la máscara de Mario
   por fila (frontera §2.1).
4. Por variante compatible, **en orden de directorio**, hasta la primera
   con plan (`choose`): `uses_of` (Mario por la frontera, Rex por
   `bank.g5env`), `transitions`, `place` (ventana más corta primero y, a
   igualdad, el segmento más tardío; leer el código: el orden exacto de
   desempate es lo que decide los bytes) y `schedule` (cadena solo tras
   una carga real, WAIT solo con el copper libre ≥ `IDLE` px, regla de
   fin `END[nb]`, nada en `WRAP_SEG`, ≤ `SUFFIX_SLOTS` ranuras).
5. **Armado VBL**: canales 4-7 (`control()` de `g0bench.py` para
   POS/CTL, bit ATTACH en el canal impar, `pt = offsets[half] + 4 + 4·clip`
   con los offsets de la tabla de canales de la pose, canal invisible =
   inactivo) y los colores de partida (`lines[-1]`).
6. **Serializar** en B1.

La validación independiente de `plan_frame` (`F.compose`, `simulate`,
`pixel_errors`, `check_list`) **no** va en el C: es la prueba del
modelo. Las estructuras intermedias (usos, transiciones) van en un área
de trabajo que se pasa por puntero o en la pila; nada de `static` con
dirección tomada.

## 3. Qué toca esta tarjeta (y qué no)

| toca | no toca |
|---|---|
| `player/g5plan.c` y `player/g5plan.h`: `g5_plan`, `g5_segment`, la frontera §2.1 | `g5_capture` (queda como referencia exacta de B2) |
| `tools/marioverify.c`: modo `g2t` | `player/game.s`, `player/scroll.s`, `player/g5.s`, `player/g5env.s` |
| `tools/g5bank_env.py`, `tools/test_g5bank_env.py`, `tools/g2t_segdump.py` **nuevos** | `tools/g2t_ref.py`, `g5ref.py`, el banco G3 |
| `tools/g5plan_verify.py`: modos nuevos `plan` y `segs`; `tools/logicbench_build.sh` si hace falta | `tools/oam68k_gate.sh` **solo** para agregar el paso 4c al final (no cambies 4b) |
| `tools/regress.py`: agregar `test_g5bank_env.py` a `g2t_checks` | |

## 4. Entorno y partida en verde

```sh
export PATH="/c/msys64/ucrt64/bin:$PATH" VBCC=/c/Users/JC/vbcc PY=python
git log --oneline -1                 # 876d28d o posterior; si no: git merge --ff-only master
```

Copiar desde la carpeta principal (`C:/Users/JC/Downloads/sma/port-amiga`)
lo ignorado por git: todos los ficheros sueltos de `work/`, y las carpetas
`work/g3`, `work/cc`, `work/g2t_ref`, `work/g2tb`, `assets-out/`, más
`player/gen/smwrom00.c` y `player/gen/smwtabx.h`. `../smw-src-master`
desde `.claude/worktrees/` resuelve por una junction ya creada; si no
resuelve, parar y avisar. Para encadenar `export` y `sh`, un guion
envoltorio en `work/` (sin versionar).

Partida:

```sh
python tools/lint_port.py                                          # RESULTADO: OK
python tools/regress.py --baseline tools/baseline_pc.json --level  # RESULTADO: OK
sh tools/oam68k_gate.sh                                            # OAM68K: OK
python tools/g2t_ref.py --dump --trace work/oam_yi1.trace=work/oracle_yi1_oam.bin --trace work/oam_normal.trace=work/oracle_normal_oam.bin --trace work/oam_spin_kill.trace=work/oracle_spin_kill_oam.bin --bank work/g3/bank --out work/g2t_ref
sha256sum work/g2t_ref/plan_*.bin work/g3/bank.idx work/g3/bank.dma
```

Tiene que dar `PUERTA A-T: OK` y estos SHA256 (si no: parar):

```
0520d1b19bf87874e5f0a4cb837dfc3b75849ba6985cff3adaad6881c0c73894  plan_normal.bin
749deb0459d768472172d44ac39e90be0882d2bfcf16a0e8fbbe9ee0db2a13f6  plan_spin_kill.bin
0a5792792c1e3a4244a8963c271d4423419f9091bea89a855dc8cc3f0bd06441  plan_yi1.bin
8589b85a0e7368333b91b26d42a4f5cec7febbecc918bbebfb0743ce6f689cd2  bank.idx
4dd51fcc9bd03edd9afaad0b0a2459af7113259f43caa8c0789ff457a839f4fc  bank.dma
```

## 5. Pasos

### 5.1 Bucle de hashes (antes de cada commit)

El mismo de `docs/instrucciones-g2t-b2bis.md` §5.1; los cuatro SHA256
esperados están ahí (`c03b5696…`, `9403f71c…`, `2bc486d7…`, `71071566…`).
Además, el logicbench por defecto (`sh tools/logicbench_build.sh` sin
CDEFS): `ec8147ac…c37e` según B2; anotá el completo en tu primera
corrida y que no cambie.

### B3-0. La frontera (commit propio)

§2.1 sobre el formato de B2. Prueba: `tools/g5plan_verify.py env` sigue
dando OK, y un modo nuevo (o una opción) que compare, para todos los
frames con Rex y las 224 filas, `g5_mario_mask`/`g5_mario_span` contra
`g2t_ref.mario_amiga`: 0 diferencias en las tres trazas.

### B3-1. Volcados de referencia (Python, sin tocar `g2t_ref.py`)

`tools/g2t_segdump.py`: repite el bucle de `g2t_ref.run` (mismo
`P.assemble('player/scroll.s', ['VIS=256', 'SPRITES'])`, mismo
`P.Scroll`, mismo `scroll_frame` por frame de la traza, misma condición
«frame con Rex») y escribe, por traza:

- `work/g2tb35/segw_<traza>.bin`: por frame con Rex, `frame u32` y, por
  fila 0..223, `n u8` + las `n` palabras dobles (`u16 u16`) del segmento
  desde su inicio hasta el salto `$0084` **incluido**. Es lo que
  `g5_segment` va a leer. Tamaño esperado: decenas de MB (es `work/`).
- `work/g2tb35/segs_<traza>.bin`: por frame con Rex, `frame u32` y por
  fila `nb u8`, `last s16` (`$7FFF` = ninguna), `wrap u8`: lo que da
  `g2t_ref.segments`.

Comprobación de que el volcado es fiel: para cada frame, reconstruir una
lista en memoria desde `segw` y pasarla por `g2t_ref.segments` →
idéntico a `segs`. Si no: parar.

### B3-2. `g5_segment` en C

Prueba en el PC (gcc, desde `marioverify.c` o un `tools/g5seg_test.c`
nuevo): para cada frame y fila de `segw`, `g5_segment` = `segs`.
**0 diferencias** en las tres trazas. Prueba negativa: cambiar un WAIT de
un segmento y ver que falla.

### B3-3. `bank.g5env`

`tools/g5bank_env.py --bank work/g3/bank --out work/g3/bank.g5env`
(opción (a) o (b) de §2.3). Comprobación: para cada pose y fila, lo que
da la tabla = lo que da `uses_of` sobre `pose['rows']` sin recorte; y con
recorte, en todos los frames con Rex de las trazas, igual a `uses_of` de
`g2t_ref`. Test sin assets en `tools/test_g5bank_env.py`.

### B3-4. `g5_plan` en C

Siguiendo §2.4. Recomendación de trabajo: portar función por función
(`a3_compatible`, `transitions`, `place`, `schedule`, armado VBL,
serializar) y, antes de juntar, comparar cada una contra su par de
Python con entradas volcadas desde `g2t_ref` (un modo de depuración de
`marioverify` que imprima, por ejemplo, las transiciones de un frame).
Los empates de ordenamiento son la fuente más probable de diferencias.
`place` ordena las transiciones por la clave `(hasta − desde, hasta,
indice)` (orden estable de Python), prueba los segmentos desde `hasta − 1`
hacia abajo hasta `desde` (el −1 es el bloque VBL, con cupo
`VBL_COLORS`), y al final ordena los MOVE de cada segmento por
`(x mínimo, indice)` antes de asignarles las posiciones de `schedule`.
Reproducí esas claves exactas, no una aproximación.

### B4. Puerta en el PC

Modo `g2t` en `tools/marioverify.c` (`GAME_G2T_TRACE=<traza>`): en cada
frame con Rex arma el bloque con `g5_capture` (exacto, en el PC el coste
no importa), arma una lista en memoria desde `segw` y llama a `g5_plan`
con `bank.idx` y `bank.g5env` cargados en memoria. Escribe
`work/g2tb35/plan_<traza>.bin`.

```sh
cmp work/g2tb35/plan_yi1.bin work/g2t_ref/plan_yi1.bin
cmp work/g2tb35/plan_normal.bin work/g2t_ref/plan_normal.bin
cmp work/g2tb35/plan_spin_kill.bin work/g2t_ref/plan_spin_kill.bin
```

**Idénticos los tres.** Si no: el primer frame distinto, se decodifica con
`g2t_ref.read_dump` y se compara campo por campo (variante, canales,
`vbl`, por segmento tipo/h/k/moves). Tres intentos distintos sin cerrar →
entregar parcial con el frame y el campo.

### B5. Puerta en el 68000

1. `CDEFS='-DNOOAM -DSPR_OAM -DSPR_G5' sh tools/logicbench_build.sh`: el
   logicbench ya compila `g5plan.c` con `SPR_G5` (B2). Revisar el listado
   (P102) y el ABI.
2. `tools/g5plan_verify.py plan --name <traza>`: carga en la memoria de
   Musashi el bloque de cada frame (de `work/g2tb/cap_<traza>.bin` o del
   volcado de B4), `bank.idx`, `bank.g5env`, `mario_pal.bin` y una lista
   armada desde `segw`; llama a `_g5_plan`; compara la salida con la del
   PC byte a byte; mide ciclos (sin DMA) y comprueba el ABI (d2-d7/a2-a6
   intactos), como el modo `m68k` existente.
3. Puerta: **0 frames distintos** en las tres trazas, ABI distinta 0.
   Informar ciclos de `g5_plan`: media, máximo, frame del máximo, y los
   de `g5_segment` dentro de él (cuántos segmentos pidió de media y máx.).
4. Agregar el paso **4c G2T-B5** al final de `tools/oam68k_gate.sh`
   (copiar la estructura de 4b: build, por traza `ok`/`fail` con la línea
   de resumen). Correr la puerta entera y comprobar con
   `grep -c 'G2T-B5' <log>` que corre (6 líneas `ok`) y que termina en
   `OAM68K: OK`.

### B6. Red de seguridad

lint, regress `--baseline tools/baseline_pc.json --level` (comprobar con
`grep test_g5bank_env work/regress.log` que el test nuevo corre),
`oam68k_gate.sh`, bucle de hashes.

## 6. Presupuesto y paradas

El render tiene para todo G4/G5 **≤ 8 % del frame = 11 350 ciclos**,
incluyendo la envolvente de Mario (B2bis apunta a ≤ 600 en acierto) y la
emisión (`g5_emit`, tarjeta C). Objetivo para `g5_plan` con sus
segmentos: **≤ 8 000 ciclos máx.** en Musashi.

Es probable que el C de vbcc quede muy por encima (P54: el dibujo
genérico en vbcc costaba 300 000). Regla: **un solo intento** de bajar el
coste en C (estructuras, evitar recorridos repetidos). Si sigue por
encima, **no** sigas optimizando ni pases a asm: entregá B4/B5 verdes con
un perfil por función (ciclos de cada parte en el frame del máximo, con el
perfilador de Musashi que usó la revisión L-OAM en
`work/revision-loam-1007/`) y una propuesta de qué pasar a asm y cuánto se
espera ahorrar.

Paradas:

- Cualquier cambio necesario en `g2t_ref.py`, en el contrato o en el
  banco G3.
- El volcado `segw` no reproduce `segs` (B3-1).
- `bank.g5env` no entra en la slow RAM estimada.
- Cualquier cambio en los hashes por defecto.
- Tres intentos distintos sin cerrar una puerta: entregar parcial (WIP).

## 7. Informe

- Commits (hash de `git log`), uno por paso cerrado como mínimo.
- Salidas literales de B3-0, B3-1, B3-2, B3-3, B4 (los tres `cmp`), B5
  (por traza) y de `oam68k_gate` (las líneas 4b y 4c).
- Opción (a)/(b) para `bank.g5env`, su tamaño y la slow RAM estimada.
- Ciclos de `g5_plan` y `g5_segment` (media, máx., frame) y, si pasa de
  8 000, el perfil y la propuesta.
- Hashes por defecto y del logicbench, lint, regress.
- Lo no hecho y lo que no pudiste confirmar.
