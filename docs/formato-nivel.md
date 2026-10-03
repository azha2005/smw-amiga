# Assets y formato del nivel

> Movido textual desde `AGENTS.md` (§5, §5b, §5c y §8b) el 2026-10-03. Los números
> de sección se conservan: las referencias "§5b" del resto de la documentación
> apuntan aquí.

---

## 5. Pipeline de assets (etapa 1 — HECHA)

```bash
# entorno
PY="C:/Users/JC/.workbuddy-ai/binaries/python/envs/default/Scripts/python.exe"

# convertir todo
cd port-amiga/tools
$PY smw2amiga.py --all --selftest --planes 4

# solo algunos ficheros, con 5 planos (32 colores)
$PY smw2amiga.py --gfx chr obj-3 spr-2 --planes 5
```

**Estado verificado (22/09/2026):**
- 52/52 ficheros descomprimidos con tamaños exactos
- Auto-test de ida y vuelta del codificador planar: **pasa en 52/52**
- Salida total: **228,5 KB** de tilesets planares

**Verificación visual obligatoria:** antes de dar por buena cualquier salida,
abre el PNG correspondiente y confirma que las formas son reconocibles.
Referencias que ya sabemos correctas:
- `spr-1.lz2` @ 3bpp → logo **"Nintendo Presents"** + seta + flor + estrella
- `chr.lz2` @ **4bpp** → bloques `?`, monedas, setas, tuberías
- `obj-3.lz2` @ 3bpp → suelo de hierba, rampas, arbusto, tubería fina

### Profundidades de color (tabla autoritativa)

| Ficheros | bpp |
|---|---|
| `chr` | **4** |
| `boss-6` | **4** |
| `gb-1` … `gb-5` | **2** |
| todo lo demás (`spr-*`, `obj-*`, `bg-*`, `map-*`, `boss-1..5`, `cin-*`, `anim`) | **3** |

Fuente: `document/graphics.txt` (IDs en hex) + verificación empírica del
tamaño descomprimido. **`chr.lz2` está mal documentado — es 4bpp, confirmado
renderizando.** La verificación visual (4/3/2 bpp de cada fichero) está en
`work/bpp_matrix.png`: `spr-1`=3bpp da el logo "Nintendo Presents",
`gb-1`=2bpp da el set de caracteres, `chr`=4bpp da la cara de Mario.

### Pendiente en la pipeline

- [x] Resolver el layout real de las paletas → `tools/palette.py`, ver §8b
- [x] Corregir `BPP_TABLE` con verificación visual → `work/bpp_matrix.png`
- [x] Parsear `.lv` → buffer Map16 → `tools/lvparse.py`, ver §5b
- [x] Mapear tileset → ficheros GFX y Map16 → tile + paleta
      → `tools/mklvl.py` + `tools/map16.py`
- [x] Corregir el orden de cuadrantes Map16 y el filtro de cuadrante vacío
      → §5b / P12 / P13
- [x] Comparación 1:1 contra la referencia SNES → §5c
- [x] Herramientas de diagnóstico: `tools/m16sheet.py` (tabla Map16 como
      grilla, `--order row|col`), `tools/tilesheet.py` (tiles crudos de un
      fichero GFX), `tools/quadtest.py` (las dos hipótesis de orden lado a
      lado), `tools/diag_pipe.py` (recortes de tubería)
- [x] Handlers de objeto: 92/92, capa 1 **1:1 con la referencia** (§5c)
- [ ] Capa de fondo del nivel (cielo, pilares, nubes) — etapa 7, **después** de decidir D8
- [x] Cerrar D7 (color de tuberías) → paleta por pantalla, P28
- [ ] Cuantización 128 → 16/32 colores por nivel
- [ ] Generar máscaras de sprite
- [ ] BRR → PCM 8 bits
- [ ] Secuencias SMW → MOD de 4 canales
- [ ] Transcribir las tablas de física de `player.s`

---

## 5b. Formato de nivel (etapa 2 — HECHA)

Referencias: `document/` no trae nada del formato de nivel. La fuente de verdad
es el desensamblado (`lv_read.s`, `tiles.s`) cruzado con la documentación
pública (SnesLab / SMW Speedruns). **Los tres coinciden.**

### Cabecera primaria (5 bytes al principio de Layer 1)

```
byte0 : BBBLLLLL   BBB = paleta de BG (0..7)   LLLLL = nº de pantallas - 1
byte1 : CCCOOOOO   CCC = color de fondo        OOOOO = modo de nivel
byte2 : 3MMMSSSS   3 = prioridad layer 3       MMM = musica   SSSS = gfx sprites
byte3 : TTPPPFFF   TT = tiempo  PPP = pal sprites  FFF = pal de FG
byte4 : IIVVZZZZ   II = item memory  VV = scroll vertical  ZZZZ = tileset
```

Yoshi's Island 1 = `33 40 08 80 27`: 20 pantallas, modo 0, bgcolor 2,
tileset 7, pal FG 0, pal sprites 0.

### Objetos (3 bytes; 4 el "screen exit")

```
byte0 : NBBYYYYY   N = flag "nueva pantalla" (screen++)
                   BB = 2 bits altos del nº de objeto
                   YYYYY = Y (0..31)
byte1 : bbbbXXXX   bbbb = 4 bits bajos del nº de objeto
                   XXXX = X dentro de la pantalla (0..15)
byte2 : SSSSSSSS   settings (objeto estandar)
                   o nº de objeto extendido (si el nº estandar = 0)

nº de objeto (6 bits) = bbbb | (BB << 4)      ; 0..63
    == 0  -> EXTENDIDO  (byte2 = nº 0..255, dispatch en CODE_0DA106)
    != 0  -> ESTANDAR   (byte2 = settings, dispatch en CODE_0DA44B por nº-1)
```

`$FF` como primer byte = fin de datos.

Semántica del byte de settings de los objetos estándar (nibble alto, nibble bajo):

| Objeto | Semántica | | Objeto | Semántica |
|---|---|---|---|---|
| 01-0E | Height, Width | | 14 Ground ledge | Height, Width |
| 0F Vertical pipes | Height, Type | | 15 Midway/Goal | Height, Type |
| 10 Horizontal pipes | Type, Width | | 16 Blue coins | Height, Width |
| 11 Bullet shooter | Height, Unused | | 17 Rope/Clouds | Type, Width |
| 12 Slopes | Height, Type | | 1C Donut bridge | Unused, Width |
| 13 Ledge edges | Height, Type | | 1E Net vertical edge | Height, Type |
|  |  | | 21 Long ground ledge | **Width (byte entero)** |

### Buffer Map16

El nivel se divide en pantallas de **27 filas × 16 columnas** (confirmado por
`tiles.s:_0DA95D`, que avanza el puntero $1B0 = 27*16 bytes al cruzar de
pantalla). Cada pantalla tiene **dos arrays paralelos** de $1B0 bytes:

- `wm_Map16BlkPtrL` → **índice Map16** (9 bits, ver abajo)
- `wm_Map16BlkPtrH` → byte alto del índice

`offset dentro de la pantalla = Y * 16 + X` (row-major).

**IMPORTANTE — el buffer NO guarda tile numbers, guarda índices Map16.**
El nombre (`wm_Map16BlkPtr`) lo dice. Esto es lo que hacía que el primer render
saliera con los colores del gradiente del cielo: usaba el índice como si fuera
un tile number y le aplicaba la paleta 0.

`tiles.s:BlockIsPage1` escribe $00 y `BlockIsPage2` escribe $01 en el **byte
alto** del índice → el índice es `valor | (page << 8)`, de 9 bits (0..511).

### Resolución de un índice Map16

`tools/map16.py`. Cada entrada son **8 bytes = 4 palabras**. Formato de palabra:

```
bits 0-9   tile number de VRAM (0..1023)
bits 10-12 paleta (0..7)
bit  13    prioridad
bit  14    flip X
bit  15    flip Y
```

**ORDEN DE LAS 4 PALABRAS (esto costó un rato): son column-major.**
`word0=TL`, `word1=BL`, `word2=TR`, `word3=BR`. NO es el orden raster.

Confirmado de dos formas independientes:

1. Empírica: `tools/m16sheet.py --order row|col` renderiza la tabla completa.
   Con column-major aparecen objetos coherentes (tuberías, cerros redondeados,
   bloques `?`, monedas, bloques `ON`/`OFF` legibles); con row-major todo sale
   despedazado.
2. En el desensamblado, el expansor Map16→tilemap (`lv_read.s:1161`) escribe
   `word0` y `word2` en la MISMA columna (`TopLeft` y `TopLeft+2`) y `word1` y
   `word3` en la otra (`BottomLeft` y `BottomLeft+2`).

**Cuadrante vacío = la palabra entera `$0000`**, no `tile == 0`. El tile number
0 es un tile válido (p.ej. la boquilla de tubería es el tile 0 a paleta 5,
palabra `$1400`). Hay que comprobar la palabra cruda; para eso
`Map16.get_raw(idx)`.

Ficheros (`project/mw_e10/tilemaps/`): comunes 0x000-0x1FF repartidos en
`000-072`, `100-106`, `111-152`, `16E-1C3`, `1C4-1C7`, `1C8-1EB`, `1EC-1EF`,
`1F0-1FF`; específicos del estilo en `set_N/073-0FF`, `set_N/107-110`,
`set_N/153-16D`. El tileset 7 usa **set_0** (Normal). Los índices ≥ 0x200 son
específicos del tileset y viven en el banco que da `TilesetMAP16Loc`.

### Mapa tileset → GFX → VRAM

`game.s:OBJECTGFXLIST` (13 filas de 8 bytes, indexado con `Y = tileset*4`) da
4 índices de fichero GFX. Cada uno sube **128 tiles** (bucle `LDY #$7F`) a un
bloque de **$800 palabras**:

```
bloque 0  VRAM $0000  tiles   0..127   <- OBJECTGFXLIST[t*4 + 0]
bloque 1  VRAM $0800  tiles 128..255   <- OBJECTGFXLIST[t*4 + 1]
bloque 2  VRAM $1000  tiles 256..383   <- OBJECTGFXLIST[t*4 + 2]
bloque 3  VRAM $1800  tiles 384..511   <- OBJECTGFXLIST[t*4 + 3]
```

(el orden sale invertido porque el bucle hace `LDA OBJECTGFXLIST,Y / STA m4,X`
con `X` de 3 a 0)

Los ficheros GFX son `main.S:99-168` → `GFX00`..`GFX31`. Tileset 7 da
**obj-2 + obj-5 + bg-3 + obj-3**.

### Cómo se renderiza

`tools/mklvl.py` transcribe los handlers de `tiles.s` (rectángulos de índices
Map16), y luego resuelve índice → 4 cuadrantes → tile + paleta.

Primeros handlers transcritos (la lista completa, 92/92, está más abajo):

| Objeto | Handler | Fórmula |
|---|---|---|
| 01-0E | `CODE_0DA8C3` | rect (w+1)×(h+1) de `DATA_0DA8B4[num-1]`; `+256` si `idx>=7` |
| 0F Vertical pipes | `CODE_0DAA26` | `DATA_0DAA12/17` arriba, `$35/$36` cuerpo, `DATA_0DAA1C/21` abajo |
| 13 Ledge edges | `CODE_0DB075` | `DATA_0DB039` / `DATA_0DB048` / `DATA_0DB057` / `DATA_0DB066` |
| 14 Ground ledge | `CODE_0DB1D4` | fila de `$100` + `h+1` filas de `$3F` |
| 21 Long ground ledge | `CODE_0DB1C8` | fila de `$100` (width+1) + 2 filas de `$3F` |
| 3C Arch ledge | `CODE_0DB604` | `DATA_0DB5E8` |
| 3F Bushes | `CODE_0DB5B7` | `DATA_0DB5A8` + n×`DATA_0DB5AD` + `DATA_0DB5B2` |
| ext 10-42 | `CODE_0DA57B` | `DATA_0DA548[type-0x10]`, `+256` si `type-0x10 >= 0x13` |
| ext 8E ! block | `CODE_0DB583` | `$6B` |

Verificación: `work/level_final.png` (5120×432) reproduce Yoshi's Island 1 —
suelo de tierra con hierba, arbustos, colinas, bloques `!` amarillos y
tuberías (boquilla + cuerpo de 2 tiles). Paletas usadas: 2 (suelo), 4, 5
(tuberías), 6 (bloques). Comparado 1:1 contra el mapa de SNESMaps: la
geometría del primer tramo coincide (ver §5c).

### Handlers: 92 de 92 (HECHO 2026-09-22)

Los 12 que faltaban están transcritos y verificados contra la referencia:

| objeto | rutina | forma |
|---|---|---|
| `Yoshi Coin` (ext 0x41) | `CODE_0DB2CA` | `$02D` arriba, `$02E` abajo |
| `Midway/Goal point` (0x15) | `CODE_0DB224` | 3 columnas × (h+1) filas, poste `$25` |
| `Rope/Clouds` (0x17) | `CODE_0DB3BD` | (w+1) bloques en fila, `$105`/`$106` |
| `Midway point rope` (ext 0x46) | `CODE_0DA68E` | `$035` a la izquierda, `$038` en la posición |
| `Arrow sign` (ext 0x86) | `CODE_0DA7E7` | 2×2: `$066`-`$069` |
| `Vert. Pipe/Bone/Log` (0x1F) | `CODE_0DB51F` | columna: `$153`, (h-1)×`$154`, `$155` |
| `Right facing diagonal pipe` (0x39) | `CODE_0DB73F` | `DATA_0DB72F` con página 2 |
| `Left facing diagonal ledge` (0x3A) | `CODE_0DB7AA` | escalera `$1AA`/`$1E2`/`$1F7` + relleno `$03F` |
| `Slopes` (0x12) | `CODE_0DAB3E` | tipo = `(settings & 0x0F) mod 10` → 10 rutinas |
| `3-UP moon` (ext 0x18) | `CODE_0DA57B` | `DATA_0DA548[8]` = `$06E` |
| `Turn block Star` (ext 0x2B) | `CODE_0DA57B` | `DATA_0DA548[0x1B]` = `$11C` |
| `? block (Flower)` (ext 0x30) | `CODE_0DA57B` | `DATA_0DA548[0x20]` = `$121` |

Los extendidos `0x10..0x40` (menos `0x17`) son todos "escribir un bloque"
(`CODE_0DA57B` → `DATA_0DA548[type-0x10]`, página 2 si el índice ≥ `0x13`).

### El cursor de bloques (`tools/mklvl.py: class Cur`)

Los handlers NO escriben en un buffer 2D: mueven un puntero con estas
primitivas, y **la diferencia entre ellas es la forma del objeto**. Modelarlas
mal hace que una tubería diagonal salga como una escalera al revés.

**El estado del cursor son TRES cosas distintas, y hay que modelarlas por
separado** (P25):

| estado | en el ROM | en `Cur` |
|---|---|---|
| puntero a la pantalla (vivo / guardado) | `wm_Map16BlkPtrL` / `m4,m5` | `scr` / `saved` |
| fila y columna **base**, persistentes | `wm_BlockSubScrPos` | `row` / `pcol` |
| columna donde se escribe | registro `Y` | `col` |

| primitiva | rutina | efecto |
|---|---|---|
| `w()` | `CODE_0DA95B` + `_0DA95D` | escribe y avanza `col`; al pasar de la 15 → col 0 de la **pantalla siguiente**, fila base |
| `put()` | `STA [ptr],Y` | escribe **sin** avanzar |
| `down()` | `CODE_0DA97D` | `pos += $10`: fila base +1 (permanente), `col = pcol` |
| `down_left()` | `CODE_0DA992` | `pos += $0F`; de la col 0 → col 15 de la pantalla ANTERIOR, y mueve **también** `saved` |
| `down_right()` | `CODE_0DA9B4` | `pos += $11`; simétrico |
| `set_pos()` | `STY wm_BlockSubScrPos` | la columna actual pasa a ser la base |
| `save()` | `CODE_0DA6B1` | `saved = scr` (**solo** el puntero de pantalla) |
| `restore()` | `CODE_0DA6BA` | `scr = saved`; **NO** toca ni la fila ni la columna |

**Trampa que costó una iteración entera:** media docena de handlers escriben con
`STA [ptr],Y` seguido de `CODE_0DA97D` (columna fija, baja fila), NO con
`CODE_0DA95B` (avanza columna). Si se usa `w()` en lugar de `put()` el objeto se
va corriendo una columna por fila. Le pasó a `Midway/Goal point`, `Yoshi Coin` y
`Vert. Pipe/Bone/Log` — el poste del goal apareció 10 columnas a la derecha, en
la pantalla siguiente.

### Dos "blends" que hay que respetar

Dos rutinas no escriben el tile tal cual: lo **ajustan según lo que ya haya** en
la celda. Hay que leer el byte bajo del bloque existente:

- `CODE_0DABFD` (`_abfd`): si ya hay `$03` → `+4`; si `$01` → `+3`; si `$3F` → `+1`.
- `CODE_0DB84E` (`_84e`): si ya hay `$25` → `+0`; si `$3F` → `+1`; si no → `+2`.

Las mezclas leen lo que YA hay en la celda, y **una celda vacía vale `$25`** en
el ROM (P26). En nuestro `Level` el vacío es la palabra 0, así que `_low_at()`
traduce 0 → `$25`. `h_ledge_edges` tiene además sus propias mezclas
(`CODE_0DB114` para el tope, `CODE_0DB198` para el cuerpo), ya transcritas.

Y ojo con el bug de Nintendo en `CODE_0DB7AA`: pone `LDA.W BlockIsPage1` donde
debería ir `JSR`. `BlockIsPage1/2` **escriben el byte alto en la celda
actual** (`STA [wm_Map16BlkPtrH],Y`), así que sin la llamada el `$A1` conserva
la página que ya tenía la celda: vacía → 0 → **`Map16 $0A1`** (la cima de las
colinas). Hay que reproducir el bug así (P21, corregido).

---

## 5c. Comparar contra la referencia real de SNES (HECHO)

Tener un "oráculo" visual cambia el juego: en vez de razonar si un tile está
bien, se mira. La referencia que usa Az es el mapa completo de Yoshi's Island 1
de **SNESMaps.com** (Rick N. Bruns, 2013), fichero
`C:\Users\JC\Downloads\SuperMarioWorldMap02.png`.

**Dato clave: esa imagen está alineada 1:1 con nuestro render.**

| | referencia | nuestro render |
|---|---|---|
| tamaño | 5120 × 432 | 5120 × 432 (`--scale 1`, el defecto; ver P24) |
| ancho | 20 pantallas × 256 px | 20 × 16 tiles × 16 px |
| alto | 27 tiles × 16 px | 27 tiles × 16 px |
| corte | el panel de leyenda empieza exactamente en y=432 | — |

O sea: `ref.crop((0,0,5120,432))` se superpone píxel a píxel con
`work/level_final.png`. Se puede comparar cualquier columna directamente.

Cómo se comprueba (el patrón que hay que repetir):

```python
ref  = Image.open(r'C:\Users\JC\Downloads\SuperMarioWorldMap02.png').convert('RGB').crop((0,0,5120,432))
mine = Image.open('work/level_final.png').convert('RGB')
# mismo recorte en las dos, apiladas -> se ve al instante qué falta o está corrido
```

Resultado de la comparación (2026-09-22, **capa 1 cerrada**):

| métrica | antes | ahora | qué mide |
|---|---|---|---|
| **bloques Map16 correctos** | 5999 / 6109 = 98.2 % | **6111 / 6111 = 100 %** | la capa 1, bloque a bloque |
| imagen completa, 5 bits, `--mask none` | 33.52 % | **25.52 %** | incluye capa 2 y sprites, que no dibujamos |
| píxeles que dibujamos y difieren | — | **0.95 %** | todos caen bajo sprites (Rex, Bullet Bill, `?` volador) |

El último dato se comprobó pintando de magenta, sobre la referencia, cada píxel
nuestro que no coincide: **todos** están debajo de un sprite. No queda ningún
error de terreno. (El denominador pasó de 6109 a 6111 porque las tuberías
lavanda ahora se identifican, ver P28.)

**Regla: para comparar dos versiones nuestras, usar siempre `--mask none`.** La
máscara `--mask mine` depende de lo que dibujamos, así que dos renders distintos
dan denominadores distintos y los porcentajes no se pueden restar.

### El barrido de colores: el diagnóstico más rápido que tenemos

Comparar los **colores** de la referencia contra el CGRAM reconstruido delata
errores de paleta al instante, y no depende de la geometría:

```python
# cuantos colores distintos tiene la referencia (5 bits) y cuales no estan en
# nuestro CGRAM.  Un color con muchos pixeles que no exista en el CGRAM es un
# bug de paleta; un color con 1..17 px es antialiasing de la imagen de origen.
```

Estado actual: **24 colores de la referencia no están en nuestro CGRAM**, y solo
uno importa de verdad — `$5D80` (el cielo, que por diseño no va al CGRAM,
ver P14). Todos los demás tienen ≤ 64 px. Con esto se encontró el bug de la
moneda de Yoshi (P22): `$27FF` aparecía exactamente 400 px = 4 monedas.

Lo que falta, en orden de peso visual:

- **capa de fondo (layer 2)**: cielo con pilares, nubes y la plataforma blanca.
  Es casi todo el 25.5 % que queda. Va en la etapa 7, cuando D8 diga cómo existe en la Amiga.
- sprites (etapa 6) y el frame de animación de la moneda de Yoshi (P23).

### Cómo se cerraron los 110 bloques (2026-09-22)

No eran tres bugs de handlers sino **cinco errores de modelo**, casi todos
compartidos por varios handlers. Por eso un solo arreglo movía decenas de
bloques:

| arreglo | efecto | pitfall |
|---|---|---|
| `Cur.restore()` solo repone el puntero de pantalla; `down*()` mueven la fila base de forma permanente | 110 → 26 (pendientes de las pantallas 5 y 11, cornisa de la 0) | P25 |
| `h_ledge_edges`: nº de filas + mezclas `CODE_0DB114`/`CODE_0DB198`; celda vacía = `$25` | 26 → 11 | P26 |
| `h_diag_ledge_left`: faltaba `STY wm_BlockSubScrPos` (`set_pos()`) | 11 → 1 | P25 |
| `h_bushes`: w−1 piezas de medio, no w | 1 → 0 | — |
| `render()`: paso de 8 px por bloque (P24), tablas `_2` y tuberías por pantalla (P28), página del bug de Nintendo (P21) | invisibles para `m16diff`; 33.5 % → 25.5 % de píxeles | P21, P24, P28 |

**Lección:** `m16diff` al 100 % **no basta**. Los bloques con capa 2 detrás son
"no identificables" y ahí se escondían las pendientes en escalera, la boca de la
tubería diagonal y el color de las tuberías. Después de `m16diff` hay que
**mirar** los recortes apilados de todo el nivel (5 tiras de 1024 px).

### Herramientas de comparación (2026-09-22)

Todas en `port-amiga/tools/`. La cadena completa es:

```
m16diff.py     <- LA ÚTIL: nuestra grilla Map16 vs la leída de la referencia
  m16find.py   <- dado un bloque de la referencia, qué índice Map16 lo reproduce
    gridread.py  <- dado un bloque, qué TILE de qué GFX reproduce cada cuadrante
  crop_ref.py  <- recortes lado a lado para mirar con los ojos
  cmp_ref.py   <- métrica de píxeles (con --bits 5 y --mask none)
  m16vs.py     <- referencia vs una entrada Map16 concreta, ampliado
```

**`m16diff.py` es la que hay que correr primero.** Construye un índice inverso
"firma de píxeles → índices Map16 que la producen" y luego, bloque a bloque,
dice exactamente *"en la columna 8, fila 21, esperaba `$159` y tenemos `$000`"*.
Eso convierte "algo se ve mal" en una lista de trabajo concreta. Salida actual:

```
bloques comparables : 6111
  correctos         : 6111 (100.0%)
  erroneos          : 0
  no identificables : 2529 (capa de fondo encima)
```

Construye un índice de firmas **por `pantalla & 3`**, porque las tuberías
cambian de paleta según la pantalla (P28).

**Trampa de `m16diff`:** un bloque de la referencia que es cielo puro coincide
con las entradas Map16 **totalmente transparentes** (`$0C7`..`$0CA`). Como en
nuestro `Level.M` el `0` es el centinela de "vacío", hay que tratarlo como
acierto cuando la referencia también es cielo — si no, salen 5000 falsos errores
y la métrica da 17 %. (Y ojo: `Map16 $000` NO está vacío, son los tiles
`$70`-`$73` a paleta 7.)

**Trampa de espacio de color (importante):** la referencia expande 5→8 bits con
`v << 3` y nuestro `palmod.snes_to_rgb8` usa replicación de bits
(`v<<3 | v>>2`). A 8 bits **todo** difiere por 1..7 unidades. **Todas las
comparaciones van a 5 bits** (`c >> 3`). Esto ya está por defecto en `cmp_ref`
(`--bits 5`) y en `m16find`/`m16diff`.

**Tuberías (antes "diferencia abierta", hoy CERRADA — P28):** el color de las
tuberías `$133`-`$13A` depende de la **pantalla** (`MAP16AppTable`). En
Yoshi's Island 1 las de la pantalla 7 son lavanda, igual que en la referencia.

## 8b. El layout de paletas de SMW (RESUELTO)

Reconstruido emulando `LoadPalette` (`game.s:5039`) y verificado: el color
de fondo de Yoshi's Island 1 sale `$5D80` = rgb(0,99,189), el celeste
clásico. Implementado en `tools/palette.py`.

### Las dos rutinas

```
LoadCol8Pal(value, X):                 ; game.s:5145
    escribe `value` en X, X+$20, ..., X+$E0   (8 filas seguidas)

LoadColors(m0, m4, m6, m8):            ; game.s:5157
    s = m0 ; base = m4
    repetir m8+1 veces:
        d = base
        copiar m6+1 palabras: CGRAM[d] = bank[s] ; s += 1 ; d += 2
        base += $20                    ; una fila de 16 colores
```

Claves que hay que tener presentes:

- `m4` es un **offset en BYTES** dentro del shadow de CGRAM (`wm_Palette`,
  `COL_DATA 256` = 512 B). Color *n* vive en el byte `n*2`.
- `m0` **avanza contiguamente** entre pasadas; el destino es el que salta.
  Por eso `PALETTE_Objects` declara 36 palabras pero la rutina lee 60: las
  otras 24 viven tras las etiquetas `DATA_B298/B2A4/B2BC` que hay en medio.
  **Hay que leer `palettes.a` en orden, no por etiquetas.**
- `DATA_00ABD3` (`game.s:5026`) es una tabla de offsets en bytes a
  sub-paletas dentro de un blob: `$00,$18,…,$A8` (paso 12 palabras) para los
  8 primeros, `$00,$14,$28,$3C` (paso 10) para los 4 últimos.
- Los índices de paleta del header del nivel son **3 bits** (0-7), no 4:
  `FgPal = byte3 & 7`, `SprPal = (byte3>>3) & 7`, `BgPal = byte0>>5`,
  `BgCol = byte1>>5`.

### A dónde va cada cosa

| Destino | Fuente |
|---|---|
| color 1 de paletas BG 0-7 | `$7FDD` (LoadCol8Pal) |
| color 1 de paletas SPR 0-7 | `$7FFF` (LoadCol8Pal) |
| BG 0-1, col 2-7 | `PALETTE_Background + 12·BgPal` |
| BG 0-1, col 8-15 | `PALETTE_Layer3` |
| BG 2-3, col 2-7 | `PALETTE_Foreground + off(FgPal)` |
| BG 4-7, col 2-7 | `PALETTE_Objects` grupos 0-3 |
| SPR 0-5, col 2-7 | `PALETTE_Objects` grupos 4-9 |
| SPR 6-7, col 2-7 | `PALETTE_Sprites + off(SprPal)` |
| pal 2,3,4 col 9-14 | `PALETTE_YoshiBerry` |
| pal 9,10,11 col 9-14 | `PALETTE_YoshiBerry` |
| SPR 0 col 7-15 | `PALETTE_Mario/Luigi` (fuera de LoadPalette, ver P10) |

Resultado en Yoshi's Island 1 (header `33 40 08 80 27`): paleta 5 = hierba
(tostado/verdes), paleta 6 = bloques `?` (marrón/naranja/amarillo), paleta
10 = monedas y `?` como sprite. Volcado completo en `work/cgram_swatch.png`.

### Consecuencia para el port

SMW usa **128 colores** en pantalla; la Amiga tiene 32 como máximo y el demo
va a 16. Por eso D1 es una decisión de diseño, no un detalle: hay que
**fusionar** paletas. Candidatos para Yoshi's Island 1:

- terreno + fondo: BG 5 (hierba) + BG 1 (cielo) → ~13 colores
- objetos: BG 6 (`?` blocks) → +8 colores

Estrategia recomendada: 16 colores fijos para el nivel, y **partir el copper**
a media pantalla para el HUD (barra de estado con su propia paleta), que es
justo lo que hace la SNES con CGRAM.
