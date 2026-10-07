# G5a-bis — el primer Rex de verdad: instrucciones paso a paso

Escrito el 2026-10-07 para quien ejecute la tarjeta (persona o agente).
Seguilo **en orden**; cada fase tiene una puerta automática y no se
empieza la siguiente con la anterior en rojo. Si algo no sale como dice
acá, **pará y avisá** con la salida exacta; no improvises un atajo.

Contexto obligatorio antes de empezar: `docs/diseno-9.2.md` §1-§3,
`docs/formato-sprgfx.md` (SG3F/2), `docs/medida-g0.md`, y en
`docs/pitfalls.md`: P35, P39, P42, P51, P59, P75, P97, P102, P108.

## 0. Qué es y qué no es

**Es:** en un build opt-in (`-DSPR_G5`, que exige `SPR_OAM` y
`SPR_BANK`), en **cada frame** se dibuja con sprites de hardware **un**
Rex (el de más arriba en pantalla), en la posición que dice la OAM del
juego, con la imagen de la **variante G3** compatible con los colores que
Mario usa en esas líneas. Mario conserva su paleta en todas las líneas.

**No es:** el asignador general (G4: varios enemigos, reuso de canales),
ni G6 completa, ni otros enemigos, ni bobs. Un segundo Rex en el mismo
frame **no se dibuja** y se cuenta ("sin destino"); eso es trabajo de G4.

### Por qué falló la primera G5a (no repetir nada de esto)

| error | regla |
|---|---|
| posición y colores de **un** frame escritos fijos en todas las listas | ningún número de un frame concreto en el código; todo sale de la foto |
| "restaurar" siempre la paleta 0 de Mario | la paleta de Mario es `R_PAL` de la foto, y solo se repone donde Mario la necesita |
| cargar los 15 colores del Rex en sus filas sin mirar a Mario | variante compatible con la máscara de Mario de cada línea |
| validar en un solo frame detenido | puertas sobre **todos** los frames con Rex (offline) y ≥ 10 capturas |
| A/B no capturado, docs con cifras sin fuente, trabajo sin commitear | cada número con su comando y su log; nada sin commitear |

## 1. Reglas que no se negocian

1. Los builds por defecto (`default`, `REPLAY`, `BENCH`,
   `SPR_OAM`+`BENCH`) salen **idénticos byte a byte** antes y después de
   cada commit. Comprobarlo con `sha256sum` (ver §6.1).
2. El banco G3 es **inmutable** (P108): G5 escribe registros por copper,
   nunca bytes del banco.
3. El render no lee `ram[]` viva (P97): todo lo que use sale de la foto O5.
4. Nunca cambiar baselines ni aflojar puertas. Un contador que tiene que
   dar 0 y no da 0 **se informa**, no se "arregla" cambiando la puerta.
5. Un paso por commit; nada sin commitear al terminar (lo que no pasa:
   `WIP:` diciendo qué falta).
6. No declarar nada que no se corrió: en el informe va la salida.

## 2. Entorno

Igual que `docs/instrucciones-loam.md` §2 (Git Bash, `PATH` con `ucrt64`
primero, `python` de WindowsApps con `machine68k`, `unicorn`, `numpy`).
Antes de empezar, en verde: `lint_port.py`, `regress.py --baseline
tools/baseline_pc.json --level`, `sh tools/oam68k_gate.sh`.

Necesitás estos derivados en `work/` (si falta alguno, **pará**):
`work/g3/bank.idx`, `work/g3/bank.dma`, `work/oam_{yi1,normal,spin_kill}.trace`,
`work/oracle_{yi1,normal,spin_kill}_oam.bin`, `work/cc/mario_pal.bin`,
`work/cc/gfx32.bin`.

## 3. Fase A — el modelo de referencia offline (`tools/g5ref.py`)

Todo en Python, sin la Amiga. Prueba que el plan existe y es exacto en
**todos** los frames con Rex de las tres trazas del lote G3.

### A1. Leer los frames

Copiá la lectura de `read_trace()` de `tools/sprgfx_manifest.py` (no la
reescribas): por cada registro SOT1 da `frame`, `slot`, `num` (`0xAB` =
Rex), la posición de la ranura en pantalla `sx, sy`, las fichas visibles
y la RAM. Por frame:

- **Rex de ese frame:** los despachos con `num == 0xAB` y fichas visibles.
  El **elegido** es el de menor `sy + origen_y` de la pose (empate: el de
  menor `slot`). Los demás: contador `sin_destino` (informativo).
- **Paleta de Mario:** el índice `a` (0..7) tal que
  `T16(DATA_00E2A2 + 2a) == R16(wm_PlayerPalPtr)` (`$0D82`), con la RAM
  del registro (lo mismo que hace `player/mgfx.c` línea ~120). Colores:
  `struct.unpack_from('>16H', mario_pal.bin, 32*a)`.

### A2. Máscara de Mario por línea, de dos maneras

- **Verdad:** `mario_rows(ram, recorded, gfx)` de `sprgfx_manifest.py`
  (decodifica los píxeles de la VRAM dinámica).
- **La que va a usar la Amiga:** una tabla precalculada
  `mask[ficha GFX32][fila 0..7]` = conjunto de índices no cero de esa fila
  de esa ficha 8×8 (744 fichas × 8 filas, u16). Para cada entrada de Mario
  (las mismas que selecciona `mario_rows`: paleta 0, ficha dinámica), por
  cada fila de pantalla que cubre, OR de las máscaras de sus fichas
  (respetando volteo vertical: la fila `7-r`; el volteo horizontal no
  cambia el conjunto).

**Puerta A2:** las dos máscaras iguales en cada línea de cada frame de las
tres trazas. Si no, listar los primeros 20 casos (frame, línea, verdad,
tabla) y **parar**.

### A3. Elegir la variante

`poses, index = sprgfx_bank.deserialize_bank(idx, dma)`. La forma del Rex
elegido es la tupla `(fichas, prioridad)` (como `sprgfx_bank.shape`); sus
variantes son la lista del directorio para esa forma. Recorré las
variantes **en el orden del directorio** y tomá la primera compatible:

```
compatible(v) = para cada fila r de la pose, línea = sy + origen_y + r,
                si 0 <= línea < 224:
                  para cada (paleta, i_snes, d, color) en v.row_maps[r]:
                    si d está en mascara_mario[línea] y
                       colores_mario[d] != color: NO compatible
```

Ninguna compatible: contador `sin_variante`, ese frame no dibuja Rex.

### A4. Canales y control

Columnas de la pose: 1 → pareja (4,5); 2 → parejas (4,5) y (6,7). X de la
columna `c` = `sx + origen_x + 16*c`. POS/CTL: `g0bench.control(x,
vstart, vstop, canal)` con `vstart = 44 + línea_superior` y
`vstop = vstart + alto` (igual que la G5a original, que sí acertó en
esto). PT de cada canal: `base_dma + offset_del_flujo + 4` (el flujo
empieza con POS/CTL provisionales; el canal arranca en DATA).

### A5. Plan de escrituras de color (lo central)

> **Nota del 2026-10-07 (después de la fase A, `docs/informe-g5bis-1007.md`).**
> Esta regla es **demasiado estricta**: solo deja escribir un color en
> líneas donde nadie usa ese índice, y no modela el hueco horizontal entre
> el último píxel que lo usa en la línea `y-1` y el primero de la línea
> `y`. Por eso el 87 % de las 59 318 ventanas vacías son del propio Rex
> (un índice con colores distintos en filas contiguas de la variante
> elegida). La alternativa se define en la revisión G2T
> (`docs/instrucciones-revision-1007.md` §2, "Dato de partida"); no
> retomar B/C con esta regla.

Registros COLOR17..31 = índices DMA 1..15. Al principio del frame valen la
paleta de Mario (la cabecera ya los escribe). Para cada línea `y`:

```
deseado[y][i] = color del Rex  si la fila del Rex en y usa el índice i
              = color de Mario si mascara_mario[y] contiene i
              = libre          si nadie usa i en y
```

Recorriendo las líneas de arriba abajo con el estado `reg[i]`: si
`deseado[y][i]` no es libre y `!= reg[i]`, hace falta una escritura
`(i, valor)` que tiene que estar hecha **antes de que empiece la línea y**.
Su **ventana** es `[lo, y-1]`, donde `lo` = la primera línea después de la
última anterior a `y` en que `i` no estaba libre. Dentro de la ventana
nadie usa `i`, así que no importa en qué x de la línea se escriba.
Si la ventana es vacía (alguien usa `i` justo en `y-1` con otro color):
contador `sin_plazo`.

Además, el **armado** del Rex: 8 MOVE de PT y 8 de POS/CTL, ventana
`[0, y0-1]` (`y0` = primera línea del Rex), PT antes que POS/CTL.

Colocación modelo (la real la hace la fase C): capacidad **8 MOVE por
línea**; colocar cada escritura en la **última** línea de su ventana que
tenga lugar. Lo que no entra: `sin_plazo`.

### A6. Comprobar el plan pintando

Simular los registros línea por línea aplicando cada escritura al final de
su línea, y pintar: cada píxel de Mario (de `mario_rows`, con su índice)
tiene que salir con el color de Mario de `R_PAL`; cada píxel del Rex con
el color de su `row_map`. Contador `errores_color`. Contar aparte
`prioridad_distinta`: píxeles donde en la SNES el Rex tapa a Mario (en la
Amiga Mario, canales 0-3, siempre queda delante).

### A7. Salida y puerta de la fase A

```sh
python tools/g5ref.py --trace work/oam_yi1.trace=work/oracle_yi1_oam.bin \
    --trace work/oam_normal.trace=work/oracle_normal_oam.bin \
    --trace work/oam_spin_kill.trace=work/oracle_spin_kill_oam.bin \
    --bank work/g3/bank --out work/g5ref
```

Escribe `work/g5ref/plan_<traza>.json` (por frame: Rex elegido, variante,
POS/CTL, PT, escrituras con ventana y línea modelo, contadores) y
`work/g5ref/resumen.json`, y una PNG de 12 frames repartidos (referencia
SNES arriba, plan abajo) en `work/g5ref/muestra.png`. Mirala.

**Puerta A:** frames con Rex > 0 en las tres trazas; `A2` igual;
`sin_variante = 0`, `sin_plazo = 0`, `errores_color = 0`. `sin_destino` y
`prioridad_distinta` se informan con su cuenta. Máximo de MOVE por línea y
de escrituras por frame: informarlos (son el presupuesto de la fase C).

Si `sin_variante` o `sin_plazo` no dan 0: **parar** e informar la lista de
frames. Es información de diseño para G2/G4, no un error a esconder.

Añadí un test sin assets (`tools/test_g5ref.py`, casos sintéticos: una
fila que choca con Mario, una ventana vacía, el orden del directorio) y
metelo en `regress.py` **comprobando que se llama** (`grep` en el log).

## 4. Fase B — el plan en C, igual en PC y en 68000

### B1. La tabla de máscaras de Mario

`tools/mkmario.py` (o un `tools/mkmariomask.py` nuevo) escribe
`work/cc/gfx32mask.bin` = 744 × 8 u16 big endian, la misma tabla que A2.
Prueba: el script la relee y la compara con la de `g5ref.py`.

### B2. La foto ampliada (solo con `SPR_G5`)

En `player/game.s`, por cada uno de los tres buffers de la foto, un bloque
en slow RAM (no en `DC_REC`, que es chico): número de Rex, el elegido
(posición de la ranura en pantalla, sus fichas como en el manifiesto),
`R_PAL` y la máscara de Mario por línea (224 × u16). Se llena en
`dc_capture`, **después** de `mspr_draw` (mismos datos de Mario), con una
función de C `g5_capture()` (fichero nuevo `player/g5plan.c`) que lee
`ram[]` (estamos en la lógica, todavía se puede) y escribe solo el bloque.
Medir su coste (ver B5): corre en la interrupción.

### B3. `g5_plan()`

En `player/g5plan.c`: entrada = bloque de la foto + tablas G3
(`sg3_tables`, leídas por la base: P102) + paleta de Mario; salida = un
plan con el mismo contenido que A3-A5 **salvo la colocación**: variante,
canales, POS/CTL, PT relativos, y la lista de escrituras con su ventana.
Función pura: no lee `ram[]`, no escribe nada fuera del plan. Sin `int`
a secas, sin `static` con dirección tomada (P47), tablas de C en bloques
`#ifdef` (P78).

### B4. Puerta en el PC

Un modo nuevo de `tools/marioverify.c` (`g5`, con `GAME_G5_TRACE=...`)
que en cada frame del modo `game` arma el bloque, llama `g5_plan()` y
vuelca el plan. `python tools/g5ref.py --check <volcado>` lo compara con
`work/g5ref/plan_*.json`: **0 diferencias** en las tres trazas.

### B5. Puerta en el 68000

`CDEFS='-DNOOAM -DSPR_OAM -DSPR_G5' sh tools/logicbench_build.sh` y un
arnés en Musashi `tools/g5plan_verify.py`, copiado de la estructura de
`tools/sprite_oam_verify.py`: carga el binario, escribe el bloque de cada
frame, llama `_g5_plan` y compara el plan byte a byte con el del PC.
**0 diferencias**, y ciclos de `g5_capture` y `g5_plan` (media y máximo)
en el informe. Agregá el paso a `tools/oam68k_gate.sh` (y comprobá que
corre). Si `g5_capture` pasa de ~3000 ciclos de máximo, avisá antes de
seguir: se come lo que gana L-OAM.

## 5. Fase C — el copper

### C1. Lugar en el segmento (opt-in)

Hoy cada segmento de línea mide `SEG = 220` B: 2 WAIT + borrado (7-14
MOVE, terminan justo antes de x = 0, medido), hasta 12 cargas de
`build_mid` y el salto (COP2LC + COPJMP2). Con `SPR_G5`:

- `SEG` crece en `G5K*4` B (`G5K = 8` MOVE) en `player/scroll.s` **y** en
  `tools/mkscroll.py` (opción `--g5`, que escribe `work/yi1_s_g5.dat`; el
  plan del scroll guarda offsets de segmento). `game_build.sh` usa ese
  `.dat` solo con `SPR_G5`. Chip: +2 × 224 × 32 = 14 336 B; comprobar
  con `memmap.py` en replay **y vivo** (vivo con G3 ya usa 467 256 B).
- Los builds por defecto, idénticos (regla 1).

### C2. Dónde va el bloque del Rex en cada línea

`build_mid` **solo reescribe las líneas que dejan de valer**; las demás
quedan de un frame a otro. Por eso el bloque **no** va antes de las
cargas (las movería): va **después de la última carga y antes del salto**.

`g5_emit` (asm nuevo, `player/g5.s`), llamado en el render después de
`build_mid` (donde la G5a original llamaba a `g5a_apply`), para la lista
que se escribe:

1. Por cada línea que tenía bloque en esa lista o lo necesita ahora:
   recorrer el segmento desde el inicio de las cargas (`ldoff`) hasta el
   primer MOVE a `$0084` (salto) o a un registro de sprite
   (`$120`-`$17E`, `$1A2`-`$1BE`; `build_mid` nunca escribe esos). Ahí
   termina lo de `build_mid`.
2. Escribir allí los MOVE de esa línea y después el salto (3 MOVE:
   `$0084`, `$0086` con la dirección del segmento siguiente, `$008A`).
   En una línea que ya no necesita bloque, escribir solo el salto.
3. **Capacidad real:** si la última carga cae tarde, el bloque se come el
   borrado de la línea siguiente. Regla: con `n` MOVE, la última carga
   tiene que terminar en `h <= $E2 - 8n` (con la tabla `htab` de
   `scroll.s`). Las escrituras de color tienen ventana (fase B): si la
   línea no alcanza, ponerlas en una línea anterior de su ventana. Lo que
   no entra: contador `g5_sin_plazo` en la salida de BENCH.

### C3. Puerta con `scrollsim.py` (sin la Amiga)

Agregá a `tools/scrollsim.py` una opción `--g5k N --g5lines A-B` que mete
un bloque de `N` MOVE nulos en cada línea de `A` a `B` con la regla C2
(después de las cargas). **Puerta:** todo el recorrido
(`python tools/scrollsim.py --g5k 8 --g5lines 100-223`) con **0 px** de
error en la capa 1, igual que sin la opción. Si da errores: bajar a
`--g5k 6`, `4` y anotar el máximo que da 0; con ese `G5K` sigue C1.
Si ni con 4 da 0: **parar**.

### C4. Puerta en WinUAE, frame a frame

1. Elegí ≥ 10 frames del replay de YI1 con Rex usando
   `work/g5ref/plan_yi1.json`: arriba y abajo de la pantalla, las dos
   direcciones, Mario en las mismas líneas que el Rex (al menos 3 de
   esos), y alguno con escrituras en ventana corta. Ojo **P75**:
   `-DSTOPF` cuenta desde el primer frame del replay, no el del oráculo.
2. Por cada frame `N`, dos builds iguales salvo el Rex:
   `-DSPR_G5 -DSTOPF=N` (visual) y `-DSPR_G5 -DG5_EMPTY -DSTOPF=N`
   (control: mismo segmento, sin escrituras).
3. Capturas con `tools/shot.ps1 -Exact` por el candado (en paralelo,
   copias de `shot.ps1` por slot como hace `tools/stress_ab_shots.ps1`).
4. `tools/g5cmp.py` (nuevo; partir de `read()` de la G5a original:
   `git show wt/g5a-1006:tools/g5a.py`): esperado = captura de control
   con los píxeles del Rex del plan encima (Mario sigue delante); comparar
   **la pantalla entera** (P57: centro del píxel).

**Puerta C4:** 0/57344 píxeles distintos en **cada** frame elegido.
Guardar `work/g5/compare_<N>.png` y mirarlas.

### C5. Coste

Con `tools/stress_ab_build.sh` como modelo, A/B en YI1 y estrés:
`SPR_G5` contra `SPR_G5 -DG5_EMPTY`. Informar fotos perdidas, racha,
`level_frame`, `build_mid` y total medio, y `g5_sin_plazo`.

## 6. Cierre

### 6.1 Antes de cada commit

```sh
python tools/lint_port.py
python tools/regress.py --baseline tools/baseline_pc.json --level
sh tools/oam68k_gate.sh
for v in "||" "-DREPLAY||" "-DREPLAY -DBENCH||" "-DREPLAY -DBENCH||-DNOOAM -DSPR_OAM"; do
  g=$(echo "$v" | cut -d'|' -f1); c=$(echo "$v" | cut -d'|' -f3)
  CDEFS="${c:--DNOOAM}" GDEFS="$g" OUT=work/hash sh tools/game_build.sh > work/hash.log 2>&1
  sha256sum work/hash/game.bin
done
```

Los cuatro hashes tienen que ser los mismos que en el commit anterior.

### 6.2 Puerta de la tarjeta

A, B y C en verde. Si alguna fase se para por su condición de parada, la
tarjeta se entrega **parcial** con lo medido; no se "termina" de otra
manera.

### 6.3 Informe

Commits; resumen de `work/g5ref/resumen.json`; salida de las puertas B4,
B5, C3 y C4 (con las PNG mirada por vos); tabla A/B de C5; lo que no se
hizo y por qué; trampas nuevas como "Pnn sin número".
