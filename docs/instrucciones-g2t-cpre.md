# G2T-Cpre — el Rex en el copper del juego, con el plan precalculado

2026-10-08. Instrucciones paso a paso. Adelanta las fases C2, C3 y C4 de
`docs/instrucciones-g2t-bc.md` §4 **sin esperar a la fase B**: el plan no
lo calcula el 68000 sino `g2t_ref.py` en el PC, y entra al juego como una
tabla de datos solo en el replay (que es determinista). Así se prueba en
la Amiga lo que tiene más riesgo físico (el emisor y el copper) mientras
B se termina. Modelo previsto: Opus, worktree propio. Parte de master
`876d28d` (o posterior: C1 y el WIP de B2 ya están).

**Estado revisado 2026-10-08:** no hay entrega local Cpre; esta tarjeta
sigue por implementar. B35-asm no cerró rendimiento: comenzar por C2a
con el control vacío, sin llamar al planificador C/asm en el juego.
Esta prueba offline sigue siendo independiente del bloqueo de B35.

Corre en paralelo con `docs/instrucciones-g2t-b2bis.md` y
`docs/instrucciones-g2t-b35.md`. Es **la única de las tres que usa
WinUAE**.

---

## 0. Por qué existe y qué no es

C1 dejó, bajo `SPR_G5`, segmentos de 256 B (36 B libres detrás de las
cargas para el sufijo del Rex) y un bloque VBL de 128 B en la línea 30
(WAIT, 16 MOVE de SPR4-7, 15 ranuras de color), todo con valores neutros.
Nada escribe todavía el sufijo ni arma los sprites: **los enemigos todavía
no se ven en la Amiga**.

Esta tarjeta escribe el emisor (`g5_emit`, asm) que copia un plan B1 a la
lista que se está escribiendo, y prueba:

- C3: en Musashi, sobre las listas reales del juego, que lo emitido es
  exactamente lo que dice el modelo y no toca la capa 1;
- C4: en WinUAE cycle-exact, pantalla entera, que el Rex aparece con sus
  colores **sin un solo píxel distinto** de lo esperado.

No es: calcular el plan en el 68000 (fase B), la compuerta D1 ni el coste
final (C5 completa va después de B; acá se mide solo `g5_emit`), ni el
juego en vivo (la tabla precalculada solo existe con `REPLAY`).

## 1. Reglas que no se negocian

1. Builds por defecto idénticos byte a byte. Todo bajo `SPR_G5`; lo de
   la tabla precalculada, además, bajo `G5_PRE` (que exige `REPLAY` y
   `SPR_BANK`). Bucle de hashes de §5.1 antes de cada commit.
2. `tools/g2t_ref.py` es la especificación y **no se modifica**: las
   herramientas nuevas lo importan como biblioteca. Si hace falta cambiar
   el modelo o el contrato: parar.
3. El emisor escribe **exactamente** las palabras de
   `g2t_ref.suffix_words(L, plan, moves)` y el salto de tres MOVE detrás;
   ni una palabra de más en la capa 1. Nada en el segmento `WRAP_SEG`
   (211).
4. Comparador de C4 fijo: no se ajusta para que pase. P57 (capturas ×2:
   muestrear el centro del píxel).
5. WinUAE: siempre por el candado
   (`& C:\Users\JC\Downloads\sma\winuae_lock.ps1 .\tools\shot.ps1 -Exact …`,
   `docs/reglas-ola-pc.md`), desde PowerShell con el worktree como
   directorio actual; solo PIDs propios; si matás un worker, borrá solo tu
   `winuae.lockN`.
6. Convenciones de asm de `AGENTS.md` §7 (ABI, cabecera de rutina con
   ciclos, comentarios en español, accesos al chipset por `a4`). P40, P73,
   P89 (editar listas en el sitio no conviene en el 68000), P94, P102.
7. R9: derivados solo en `work/` (la tabla precalculada sale de la ROM:
   `work/`). No merge a master, no push.

## 2. Diseño

### 2.1 La tabla precalculada (`G5_PRE`)

Una herramienta nueva, `tools/g2t_preplan.py`, en **dos pasadas**:

1. Construye el juego `SPR_G5` + `G5_PRE` con una tabla **vacía** y lo
   corre en Musashi (como `gamecheck.py --engine musashi`). En cada render
   (cuando el render toma una foto, `DC_REND`) lee: el número de frame de
   la foto (`R_FRAME`), la lista que se está escribiendo (`V_BACK`) y sus
   segmentos con `g2t_ref.segments(mem, base, cl=344, seg=256)` (C1: el
   build `SPR_G5` tiene `CL_LINES` 344 y `SEG` 256; leelos del listado,
   no los escribas a mano).
2. Para cada foto con Rex, llama a `g2t_ref.plan_frame(recs, ctx, segs)`
   con los registros de la traza del frame del oráculo de esa foto y
   **los segmentos de la lista real**. Escribe la tabla y reconstruye el
   juego con ella.

Como el emisor no toca nada de lo que `segments` lee (el sufijo va
después de las cargas), los segmentos de la pasada 2 son los mismos que
los de la pasada 1. Comprobalo (C3 lo vuelve a mirar).

**El mapeo foto ↔ oráculo.** El replay de YI1 empieza en el frame 5145
del oráculo (lo imprime `gamecheck`). La foto lleva `R_FRAME`
(`DC_NLOG`). P75: `-DSTOPF=n` cuenta desde el primer frame del replay.
Antes de confiar en el mapeo, comprobalo con un frame conocido (por
ejemplo, la cámara `$1A` de la RAM del juego en la foto contra la del
oráculo) y escribilo en el informe.

**Formato de la tabla** (big endian, `work/g2t_pre.bin`): magia `G5PR`,
versión, número de entradas, un índice ordenado `frame u32 → offset u32`
y, por entrada, el registro B1 (`g2t_ref.dump_plans` de un solo plan)
seguido de una **firma por segmento con sufijo**: `fila u8`, `suma u16`
de las palabras del segmento desde su inicio hasta el salto (sin
incluirlo). El emisor calcula esa suma mientras recorre el segmento
buscando el salto (lo hace igual) y, si alguna no coincide, **no emite
nada en ese frame** (ni sufijos ni armado: el Rex no aparece) e
incrementa un contador `g5_miss`. Esto protege contra un historial de
scroll distinto en WinUAE (fotos omitidas) que deje otra lista que la de
Musashi.

**Tamaño.** El plan completo de YI1 en B1 ocupa 366 080 B: **no entra**
en la slow RAM junto al juego (memmap actual del vivo con banco: chip
483 640; slow, mirá `memmap`). Por eso:

- para WinUAE (C4) la tabla lleva solo una **ventana** de frames
  alrededor del `STOPF` (sugerido: los 16 frames anteriores; con eso las
  dos listas tienen el estado correcto), ≤ 16 KB, incluida en el binario
  con `incbin` desde un `.i` generado (como `work/sg3_bank.i`);
- para Musashi (C3) la tabla completa la inyecta el arnés en una zona de
  memoria fuera del mapa del juego y escribe su dirección en un puntero
  del juego (`g5_pre`); el build lleva `-DG5_PRE_EXT` y nada incluido.

`memmap.py` con 0 violaciones en los builds de C4.

### 2.2 El emisor `g5_emit` (`player/g5.s`, nuevo)

Dónde: en el render desacoplado de `player/game.s` (~líneas 1840-1880),
**después de `build_mid`** (marca `GBR 9`) y antes de `dc_hdr` y de
publicar. Escribe en `V_BACK` (la lista que se está armando). Con `BENCH`,
una marca `GBR` propia antes y después para medir su coste.

Qué hace, por la foto que se renderiza:

1. Busca el plan del frame de la foto en la tabla (`G5_PRE`); sin plan =
   plan vacío.
2. **Segmentos**: para cada fila con sufijo en el plan **o** con sufijo en
   el frame anterior **de esta misma lista** (guardá una máscara de 224
   bits por lista, A y B), recorre desde `ldoff` de esa fila (tabla de
   `build_copper`, `player/scroll.s` línea ~1840) hasta el primer MOVE a
   `$0084` (COP2LCH, el salto) o un MOVE a `$1A2-$1BE` (un sufijo viejo:
   `build_mid` nunca los escribe), sumando la firma. Si hay sufijo:
   escribe las palabras de `suffix_words` y detrás el salto (tres MOVE:
   `$0084`, `$0086`, `$008A`, con los valores que tenía). Si no: deja el
   salto donde estaba antes del sufijo viejo. **Verificá en el código de
   `build_mid` qué reescribe cada frame** (si reescribe el salto, el
   sufijo viejo puede quedar detrás como basura inofensiva o no: decidilo
   leyendo, no suponiendo).
3. **Bloque VBL** (`CL_VBL`, 128 B): siempre los 16 MOVE de SPR4-7
   (PTH/PTL/POS/CTL por canal, en el orden que dejó C1: `$130+4n`,
   `$132+4n`, `$160+8n`, `$162+8n`); canal activo: PT = base del DMA del
   banco G3 en chip (`sg3_dma`, ver `player/sprbank.s` y `game.s` ~296) +
   `pt` del plan, POS/CTL del plan; canal inactivo: PT al sprite nulo
   (`g_null`), POS/CTL = 0. Las 15 ranuras: los `vbl_moves` del plan como
   `MOVE COLOR(16+i)` (`$1A0 + 2i`), el resto `$01FE,0`.
4. **Choque conocido con C1**: `dc_null` y la rama `.q` de `mario_draw`
   también escriben los PT del bloque VBL (al nulo). Establecé el orden
   real en el render y en la interrupción y asegurate de que lo último que
   se escribe en la lista antes de publicarla es lo del emisor. Si hace
   falta cambiar `dc_null` o `mario_draw`, solo bajo `SPR_G5`.

`-DG5_EMPTY` (control de C4): el mismo recorrido y la misma búsqueda,
pero **sin escribir nada** (la lista queda como la deja C1). Mismo coste
de CPU aproximado, sin Rex en pantalla.

### 2.3 Prioridades (para el «esperado» de C4)

Mario (SPR0-3) tapa al Rex (SPR4-7) por hardware. Rex contra los
playfields: depende de `BPLCON2` en `player/scroll.s`. Leelo, y leé qué
compara el contador `prioridad_distinta` de `g2t_ref` (está en 0 en las
tres trazas). Si de ahí no queda claro que el Rex se dibuja delante de
PF1 y PF2 en todos los píxeles de C4: **parar y preguntar** antes de
escribir el comparador.

## 3. Qué toca esta tarjeta (y qué no)

| toca | no toca |
|---|---|
| `player/g5.s` **nuevo**; `player/game.s`: la llamada en el render, el puntero `g5_pre`, la máscara por lista, el `incbin`; todo bajo `SPR_G5`/`G5_PRE` | `player/g5plan.c`/`.h` (B3), `player/g5env.s` (B2bis), `dc_capture` |
| `tools/game_build.sh`: `G5_PRE`/`G5_EMPTY` (exigir `REPLAY` + `SPR_BANK` + `SPR_G5`) | `player/scroll.s` (salvo leerlo), `build_mid` |
| `tools/g2t_preplan.py`, `tools/g2t_listcheck.py`, `tools/g2t_shotcmp.py` **nuevos** | `tools/g2t_ref.py`, el banco G3, `tools/oam68k_gate.sh` |

## 4. Entorno y partida en verde

```sh
export PATH="/c/msys64/ucrt64/bin:$PATH" VBCC=/c/Users/JC/vbcc PY=python
git log --oneline -1                 # 876d28d o posterior; si no: git merge --ff-only master
```

Copiar desde la carpeta principal (`C:/Users/JC/Downloads/sma/port-amiga`)
lo ignorado por git: todos los ficheros sueltos de `work/`, y las carpetas
`work/g3`, `work/cc`, `work/g2t_ref`, `assets-out/`, más
`player/gen/smwrom00.c` y `player/gen/smwtabx.h`. La junction de
`../smw-src-master` ya existe en `.claude/worktrees/`; si no resuelve,
parar. Para encadenar `export` y `sh`, un guion envoltorio en `work/`.

Partida:

```sh
python tools/lint_port.py                                          # RESULTADO: OK
python tools/regress.py --baseline tools/baseline_pc.json --level  # RESULTADO: OK
sh tools/oam68k_gate.sh                                            # OAM68K: OK
python tools/scrollsim.py --g5 --data work/yi1_s_g5.dat --from 4 --to 4864 --ret
#   bloque VBL lista A/B: OK; 5119 px, 134 frames; vuelta igual en 1215/1215; sale con 0
```

scrollsim ensambla a ficheros fijos de `work/`: **nunca dos a la vez** en
el mismo worktree (se pisan, P76).

## 5. Pasos

### 5.1 Bucle de hashes (antes de cada commit)

El de `docs/instrucciones-g2t-b2bis.md` §5.1, con los mismos cuatro
SHA256 (`c03b5696…`, `9403f71c…`, `2bc486d7…`, `71071566…`).

### C2a. La tabla y el mapeo

`g2t_preplan.py` pasada 1 sobre el build con tabla vacía: listar fotos
con Rex, comprobar el mapeo foto ↔ oráculo (§2.1) y que los segmentos de
la lista real dan, con `plan_frame`, `PUERTA`-equivalente: 0
`sin_variante_temporal`, 0 `sin_plazo`, 0 `errores_color`, 0
`errores_capa1`, 0 `prioridad_distinta` (los contadores de `plan_frame` y
`check_list`) en todas las fotos con Rex del replay. Informar cuántas
fotos con Rex hay y si alguna foto del juego no tiene frame del oráculo.

### C2b. El emisor en Musashi

Escribir `g5_emit` (§2.2) y construir con la tabla completa por
`G5_PRE_EXT`. `gamecheck.py --engine musashi`: 0 frames distintos del
oráculo y 0 por encima de un frame PAL (la lógica no cambia; esto prueba
que el emisor no rompe nada). Coste de `g5_emit` con `BENCH`: media,
máximo, frame. **Objetivo ≤ 2500 ciclos máx.; parar si pasa de 4000.**

### C3. Puerta sobre las listas reales

`tools/g2t_listcheck.py`: corre el build `G5_PRE_EXT` y, en paralelo
lógico, el mismo con `G5_EMPTY` (o el mismo binario con el emisor
desactivado por un byte que el arnés pone), en Musashi. En cada lista
publicada (`DC_PLIST`) con plan:

1. por segmento: palabras emitidas = palabras del control + `suffix_words`
   del plan + el salto; **0 segmentos distintos**;
2. `g2t_ref.check_list(mem, base_control, 344, 256, sufijos)`: 0 en capa 1
   y 0 posiciones distintas;
3. 0 sufijos en el segmento 211; 0 sufijos viejos que queden vivos
   (segmentos con sufijo en el frame anterior de esa lista y sin sufijo
   ahora: el salto vuelve detrás de las cargas);
4. bloque VBL: los 16 MOVE y las 15 ranuras exactamente como §2.2
   (activo e inactivo), en las dos listas;
5. `g5_miss` = 0 en todo el replay.

Prueba negativa: cambiar una palabra de un sufijo en la tabla y ver que
falla el punto 1 (y que el emisor cuenta `g5_miss` si cambiás una firma).

### C4. Puerta en WinUAE, pantalla entera

**Selección** (desde `work/g2t_ref/plan_yi1.json` y los planes de C2a):
≥ 12 frames del replay de YI1 que incluyan, cada uno al menos una vez:

- f6150 del oráculo (el de los informes anteriores);
- ≥ 3 frames con solape de píxeles Mario/Rex (`ev['mario']` ∩ `ev['rex']`
  de `plan_frame`);
- Rex mirando a cada lado (las dos orientaciones de la variante);
- Rex recortado por el borde derecho (x + ancho > 255);
- un sufijo de 7 MOVE (`k = 7`);
- una cadena tras una carga en x = 231 (primer MOVE en 243, P110);
- una transición en el bloque VBL (`vbl_moves` no vacío).

**Por frame N** (en frames del replay, P75):

```sh
CDEFS='-DNOOAM -DSPR_OAM -DSPR_G5' GDEFS='-DREPLAY -DG5_PRE -DSTOPF=N' SPR_BANK=work/g3/bank OUT=work/g2tc/b<N> sh tools/game_build.sh
CDEFS='-DNOOAM -DSPR_OAM -DSPR_G5' GDEFS='-DREPLAY -DG5_PRE -DG5_EMPTY -DSTOPF=N' SPR_BANK=work/g3/bank OUT=work/g2tc/c<N> sh tools/game_build.sh
```

(con la tabla de la ventana de N generada antes; la sintaxis exacta de
`GDEFS`/variables la definís vos en `game_build.sh`, manteniendo las
comprobaciones). Capturas, desde PowerShell, en el worktree:

```powershell
& C:\Users\JC\Downloads\sma\winuae_lock.ps1 .\tools\shot.ps1 -Exact -Adf work\g2tc\b<N>\game.adf -Out work\g2tc\b<N>.png -Wait <s>
& C:\Users\JC\Downloads\sma\winuae_lock.ps1 .\tools\shot.ps1 -Exact -Adf work\g2tc\c<N>\game.adf -Out work\g2tc\c<N>.png -Wait <s>
```

`-Wait`: el replay corre a 50 Hz desde la carga (~15 frames PAL de carga
según `restart_verify`, más la lectura del disco); con `STOPF` el juego se
congela en N, así que un margen generoso no cambia la imagen. Calculá
`N/50` + carga + margen y anotalo.

**Comparador** `tools/g2t_shotcmp.py` (escala y origen como
`tools/game_read.py --auto` o `tools/g2t_cal.py read-suite`; P57):

- esperado = control (`c<N>.png`) con los píxeles del Rex del plan encima
  (pose en `x0, r0`, colores del plan), salvo donde hay un píxel de Mario
  (Mario delante);
- comparar la captura `b<N>.png` contra el esperado en los 256 × 224 =
  57 344 píxeles (en 12 bits por canal de la Amiga: `rgb()` de
  `g0bench.py`);
- escribir `work/g2tc/compare_<N>.png`: control | captura | esperado |
  diferencias en magenta, y un recorte ×4 centrado en el Rex.

**Puerta: 0 / 57 344 píxeles distintos en cada frame.** Mirá cada
`compare_<N>.png` vos mismo (abrila con la herramienta de lectura de
imágenes) y describí en el informe qué se ve.

Si un frame da `g5_miss` (el Rex no aparece: la captura es igual al
control), no es un fallo del emisor sino del historial de scroll:
anotalo, elegí otro frame del mismo criterio y seguí. **Más de 3
reemplazos: parar** (quiere decir que la lista de WinUAE no es la de
Musashi y la tabla precalculada no sirve para C4).

### C5 (parcial). Coste del emisor

Del build `BENCH` en Musashi (C2b): `g5_emit` media/máx./frame, y lo
mismo con `G5_EMPTY`. No declares nada sobre D1 ni sobre fotos omitidas:
eso va con el plan real.

### C6. Red de seguridad

lint, regress, `oam68k_gate.sh`, bucle de hashes, `memmap.py` de los
builds de C4 (0 violaciones) y `restart_verify` del vivo `SPR_G5` sin
`G5_PRE` (el vivo no debe cambiar de comportamiento).

## 6. Paradas

- Cualquier cambio necesario en `g2t_ref.py`, el contrato o el banco.
- El mapeo foto ↔ oráculo no se puede establecer sin ambigüedad.
- `g5_emit` > 4000 ciclos máx.
- Prioridad Rex/playfields no clara (§2.3).
- Una captura C4 con **un solo píxel distinto** (que no sea `g5_miss`):
  parar, guardar la PNG, el plan del frame y la lista; no ajustar el
  comparador.
- Más de 3 reemplazos por `g5_miss` en C4.
- Cualquier cambio en los hashes por defecto.
- Tres intentos distintos sin cerrar una puerta: entregar parcial (WIP).

## 7. Informe

- Commits (hash de `git log`).
- C2a: fotos con Rex, mapeo comprobado (con el ejemplo), contadores.
- C2b/C5: gamecheck y ciclos de `g5_emit` (con y sin `G5_EMPTY`).
- C3: salida literal por punto y la prueba negativa.
- C4: tabla por frame (N del replay, frame del oráculo, criterio, px
  distintos, `g5_miss`), las rutas de `compare_<N>.png` y qué se ve en
  cada una.
- memmap de los builds de C4, hashes por defecto, lint, regress, OAM68K.
- Lo no hecho y lo que no pudiste confirmar.
