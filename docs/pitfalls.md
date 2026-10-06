# Pitfalls conocidos (texto completo)

> Movido textual desde `AGENTS.md` §8 el 2026-10-03. El índice de una línea por
> trampa sigue en `AGENTS.md` §8. Una trampa nueva va aquí y en el índice.

---

## 8. Pitfalls conocidos

**P1 — El layout de paletas de SMW no es un array 8×16. ✅ RESUELTO.**
`PALETTE_Sprites` en `palettes/palettes.a` tiene solo 42 palabras, no 128:
está empaquetado para la rutina de subida. **No asumas
`paletas[n*16:(n+1)*16`.** La solución completa está en §8b y en
`tools/palette.py`, que emula `LoadPalette` y reconstruye el CGRAM exacto.

**P2 — El blitter tiene prioridad sobre la CPU y la "roba" ciclos.**
Usa el bit *blitter nasty* (DMACON `$0400`) solo cuando necesites el blit
terminado ya. Si no, deja que la CPU siga y sincroniza en el VBL.

**P3 — Las listas de copper deben estar en chip RAM y alineadas a 4 bytes.**
El registro `COP1LC` ignora los bits bajos.

**P4 — Los punteros de bitplane deben ser múltiplos de 2.**
El bit 0 se ignora silenciosamente. Un fallo aquí produce un desplazamiento
de 1 píxel que no se ve hasta que algo se sale de pantalla.

**P5 — Los back-references de LC_LZ2 apuntan a offsets ABSOLUTOS** en el
buffer de salida y pueden solaparse consigo mismos. Hay que copiar byte a
byte, no con `memcpy`. Ya está resuelto en `smw2amiga.py`.

**P6 — `chr.lz2` no es lo que dice la documentación.** Es 4bpp, no 3bpp.
Ya resuelto en la tabla de §5. Corregido además su contenido: **no son
"objetos comunes" sino los tiles del jugador** (Mario/Luigi) más el huevo de
Yoshi. Se ve la cara de Mario al renderizarlo.

**P9 — `document/graphics.txt` usa IDs de fichero, no nombres.**
El mapeo `chr`/`spr-N`/`obj-N`/… → ID es por *propósito*, no secuencial:
`obj-1` = ID 07 (ghost house) pero `obj-2` = ID 14 (tubería/moneda), y
`obj-3` = ID 15 (suelo de hierba). No hay atajo: hay que mirar
`levels/*.a` (`.INCBIN`) y `graphics.s` para mapear cada nombre.

**P10 — La paleta del jugador no viene de `LoadPalette`.**
`CODE_00B03E` (game.s:5527) copia `PALETTE_Mario` (10 colores) a
`wm_PaletteCopy` **empezando en el color 134** (CGRAM `$86`), y el sprite se
dibuja con la paleta de sprites 0 (colores 128-143). Esta nota decía 135:
con 135 la gorra sale rosa y el overol violeta (visto en la Amiga el
2026-09-27, 6b.4); con 134, gorra roja y overol azul. Ver
`tools/mkmario.py` y `build_player_palette()` en `tools/mkdemo.py`.

**P7 — Las muestras de audio en Paula son PCM de 8 bits FIRMADO.**
BRR es ADPCM de 4 bits sin signo explícito. Cuidado con el sesgo DC.

**P9b — El buffer Map16 guarda ÍNDICES Map16, no tile numbers.**
`wm_Map16BlkPtrL/H` (a pesar del nombre "Ptr") contiene índices de 9 bits que
hay que resolver con `tilemaps/*.bin` para obtener tile + **paleta**. Si los
tratas como tile numbers y les aplicas la paleta 0 te sale el gradiente del
cielo en vez del terreno. Costó un render entero descubrirlo. Ver §5b.

**P10b — El índice Map16 incluye el bit de página.**
`BlockIsPage1/2` no son "flags": escriben el **byte alto** del índice. El
índice real es `valor | (page << 8)`, o sea 0..511. Los ficheros de rango
cubren exactamente 0x000-0x1FF por eso.

**P11 — El orden de los bloques GFX está invertido respecto a la lista.**
`OBJECTGFXLIST[t*4 + 0]` va a VRAM $0000, `+1` a $0800, `+2` a $1000 y `+3` a
$1800, porque el bucle hace `LDA OBJECTGFXLIST,Y / STA m4,X` con X de 3 a 0.
Con tileset 7 (obj-2, obj-5, bg-3, obj-3) el bloque 0 es obj-2 y el 2 es bg-3.

**P12 — Las 4 palabras de una entrada Map16 van en column-major, no raster.**
`word0=TL`, `word1=BL`, `word2=TR`, `word3=BR`. Con el orden raster las
tuberías salen "garbled" (esa fue exactamente la queja de Az). Se ve al
instante con `tools/m16sheet.py --order row|col`. Ver §5b.

**P13 — El cuadrante vacío es la palabra `$0000`, no `tile == 0`.**
Filtrar con `if tile == 0: continue` borra cuadrantes legítimos que usan el
tile 0 (la boquilla de tubería, por ejemplo) y deja huecos negros en el medio
del gráfico. Hay que mirar la palabra entera (`Map16.get_raw()`).

**P14 — El color de fondo del nivel no está en `cgram[0]`.**
`LoadPalette` (game.s:5039) calcula el color de cielo con
`PALETTE_Sky[wm_LvHeadBgCol]` y lo **devuelve aparte** (`wm_LvBgColor`); no lo
escribe en el CGRAM. `cgram[0]` queda a 0. Usar `cgram[0]` como fondo pinta el
cielo de negro. `palette.build_cgram()` devuelve `(cgram, bg_color)` — hay que
usar el segundo.

**P15 — Los handlers de objeto no comparten la página.**
Cada rutina llama a `BlockIsPage1` o `BlockIsPage2` según el tile. Los
arbustos (`CODE_0DB5B7`) usan **Page1** → índices `$073/$074/$079`, que caen en
la zona *específica del estilo* (`set_N/073-0FF.bin`), no en la común. Copiar
la página de memoria o asumir que "todo va a la página 2" da gráficos de otro
tileset.

**P16 — Los handlers NO escriben todos con `CODE_0DA95B`.**
El escritor que avanza columna (`w()`) es solo para las filas de terreno y las
tuberías. Muchos objetos escriben con `STA [ptr],Y` puro (columna fija) y bajan
con `CODE_0DA97D` (`down()`): *Midway/Goal point* (`CODE_0DB224`),
*Yoshi Coin* (`CODE_0DB2CA`) y *Vert. Pipe/Bone/Log* (`CODE_0DB51F`) son así.
Si les metés `w()` te corren **una columna por fila** y el objeto aparece como
una escalera diagonal gigante. Fue exactamente el bug que mandó el poste de
meta a la pantalla 19 y bajó el score de 43.75 % a 49.4 %.

**P17 — `down_left`/`down_right` cambian de PANTALLA al dar la vuelta.**
`CODE_0DA992` (`down_left`) hace `Y -= $10`; si la columna era 0, el resultado
es negativo y el `BPL` de `_0DA97D` no se toma: el puntero retrocede `$B0` y
`DEC wm_MirrorScrnNum`. O sea **col 0 → col 15 de la pantalla ANTERIOR**.
`down_right` (`CODE_0DA9B4`) hace lo simétrico: col 15 → col 0 de la siguiente.
Usar `(col ± 1) % 16` deja la escritura en la pantalla equivocada — verificado
contra la referencia: la tubería diagonal que arranca en la pantalla 8 aterriza
en la **columna 15 de la pantalla 7**.

**P18 — `DATA_0DB72F` y compañía son ÍNDICES Map16, no tile numbers.**
La tabla de la tubería diagonal (`tiles.s`, `DATA_0DB72F`) es
`C4 C5 C7 EC ED C6 C7 EE 59 5A EF C7 EE 59 5B 5C` y se escribe con
`BlockIsPage2` → los índices reales son `$1C4, $1C5, $1C7, $1EC, $1ED, $1C6,
$1EE, $159, $15A, $1EF, $15B, $15C`. Igual pasa con `DATA_0DEB93`
(`tiles4.s:289`): es la casa de Yoshi en índices Map16, no el nivel.
De ahí sale que `$159`-`$15C` (en `set_0`) sean las piezas de la tubería
diagonal y `$15D`-`$160` las variantes de la tubería recta.

**P19 — La capa de fondo (layer 2) no la dibujamos, y domina la métrica.**
Cielo, pilares, nubes y la plataforma blanca detrás de los arbustos viven en
la capa 2, que **no está implementada**. Por eso el diff de píxeles de imagen
completa está clavado en ~33.5 % y no se mueve aunque arregles el primer plano.
**Para medir el primer plano usá la métrica de bloques Map16 (`m16diff.py`),
no el diff de píxeles.**

**P20 — `--mask mine` NO es comparable entre versiones nuestras.**
El denominador cambia según cuánto dibujemos (321 k → 380 k píxeles), así que
un porcentaje "mejor" puede ser solo un denominador más chico. **Para comparar
dos versiones nuestras, siempre `--mask none`.** `--mask mine` sirve solo para
inspeccionar el primer plano contra la referencia.

**P21 — El bug de Nintendo en `CODE_0DB7AA` hay que REPRODUCIRLO (corregido 2026-09-22).**
La rama izquierda de la cornisa diagonal hace `LDA.W BlockIsPage1` donde debería
ir un `JSR` (el decomp lo marca con `; FIX SHOULD BE JSR NINTENDO`).
`BlockIsPage1/2` **no son un "modo"**: hacen `STA [wm_Map16BlkPtrH],Y`, o sea
escriben el byte alto en la celda actual. Sin la llamada, la celda **conserva la
página que ya tenía** (vacía → 0 → `Map16 $0A1`, la cima de la colina). La
versión anterior de este pitfall decía "la página queda en 2 → `$1A1`": era
falso, y dibujaba un saliente de hierba en la cima de todas las colinas. En
`Level.put()` se modela con `page=None`.

**P22 — El color de la MONEDA DE YOSHI es una animación de paleta, no $7C3F.**
`CODE_00A418` (game.s:4148) corre **todos los frames** y hace:
```
LDA #$64 / STA CGADD            ; $64 = palabra $32 = paleta 6, color 4
LDA wm_FrameB / AND #$1C / LSR  ; -> 0,2,4,...,14
TAY / LDA PALETTE_Flashing,Y / STA CGDATAW
```
O sea: el color 4 de la paleta 6 **no** es el `$7C3F` (magenta) que carga
`PALETTE_Objects` (palettes.a:58), sino que se **pisa cada frame** con un valor
de `PALETTE_Flashing` (palettes.a:157, fila *Yellow*). Los 8 pasos son
`$02DF $27FF $73FF $27FF $01BF $001B $0018 $001F`.
La referencia de SNES capturó el paso 1 (`$27FF`). Sin esto la moneda sale
**magenta**. Implementado en `palette.build_cgram(..., coin_frame=1)` →
`palette.COIN_ANIM` / `COIN_ANIM_REF`, así lo heredan todas las herramientas.
Detectado con el barrido "colores de la referencia que no están en nuestro
CGRAM": `$27FF` aparecía exactamente 400 px = 4 monedas × 100 px, en las
pantallas 1, 5, 11 y 18 (justo donde el nivel tiene monedas).

**P23 — La moneda de Yoshi también anima sus TILES.**
`CODE_00A390` (game.s:4096) hace DMA a VRAM desde `wm_GfxAnimFrame1/2/3` y
termina en `_00A418`. O sea que las palabras de Map16 `$02D`/`$02E` de
`set_0`/`000-072.bin` son **solo el frame 0** de la animación; la forma que
captura la referencia es otro frame. Consecuencia práctica: **`m16find`/
`m16diff` nunca van a identificar el bloque de la moneda** (diferencia de
forma, no de geometría). No es un bug de posición: la moneda está en el tile
correcto (verificado: el `$27FF` de la referencia cae exactamente en
`(11,3,14)`, que es el `y=14` del objeto).

**P24 — `render()` dibujaba con paso de 8 px por bloque (corregido 2026-09-22).**
`BW = lv.W * 8` y `ox = gx * 8 + ...`, pero un bloque Map16 mide 16×16. Con
`--scale 2` la imagen salía de 5120 px (parecía alineada con la referencia),
pero cada bloque pisaba la mitad derecha e inferior del anterior: **solo se veía
el cuadrante superior izquierdo de cada bloque, ampliado 2×**. En tierra y
césped uniformes no se nota; en pendientes convierte la diagonal en escalera.
Ahora el paso es 16 y `--scale 1` (el defecto) da los 5120×432 alineados.

**P25 — `restore()` NO devuelve el cursor al punto guardado.**
`CODE_0DA6B1`/`CODE_0DA6BA` guardan y reponen **solo el puntero de pantalla**
(`m4/m5`). La fila y la columna base viven en `wm_BlockSubScrPos`, y
`CODE_0DA97D`/`0DA992`/`0DA9B4` las **reescriben** (bajar una fila es
permanente). Modelar `restore()` como "volver a (pantalla, fila, col)" hacía que
todos los bucles `save/restore/down` reescribieran la misma fila: pendientes
huecas, cornisas deformes. Además, cuando `down_left`/`down_right` cruzan de
pantalla, `CODE_0DA9D6`/`0DA9EF` mueven también la copia guardada. Y alguna
rutina hace `STY wm_BlockSubScrPos` a mano (`set_pos()`). Tabla completa en §5b.

**P26 — Una celda vacía vale `$25` en el ROM, no 0.**
El buffer se inicializa con el bloque en blanco `$025`, y las mezclas
(`CODE_0DB84E`, `CODE_0DB114`) comparan con `CMP #$25`. Nuestro `Level` usa la
palabra 0 como vacío, así que `_low_at()` traduce 0 → `$25`. Sin eso,
`CODE_0DB84E` suma +2 donde el ROM no suma nada.

**P27 — Leer las tablas `.DB` del handler ANTES de contar bucles.**
Tres de los errores de esta sesión eran de conteo (`DEC m0 / BNE` vs `BPL`, un
`y += 1` incondicional). Transcribir instrucción por instrucción, con el estado
de `m0`, `X` e `Y` anotado, y no "por la forma" del objeto.

**P28 — El ROM reapunta entradas Map16 según el tileset y la PANTALLA.**
Dos sustituciones que `map16.py` no hacía (ahora sí, `Map16(..., tileset=t)` y
`get(idx, screen)`):
1. Tilesets 0 y 7 (`lv_read.s:283`): `$1C4`-`$1C7` y `$1EC`-`$1EF` pasan a
   `1C4-1C7_2.bin`/`1EC-1EF_2.bin` (`DATA_0D8A70`). Son la **boca de la tubería
   diagonal**; las tablas normales son pendientes de tierra.
2. Tuberías `$133`-`$13A` (`MAP16AppTable`, `lv_read.s:805`): al subir la
   columna `c` se elige la variante `(c >> 4) & 3`, o sea **pantalla & 3** →
   paleta 3 / 5 (verde) / 6 / 7 (lavanda). Esto **cierra D7**. El puerto tiene
   que reproducirlo en el conversor de nivel (resolver el color por pantalla al
   generar el tilemap de Amiga).

**P29 — El "slow RAM" de la A501 comparte el bus del chipset.**
`$C00000` no es fast RAM: cuelga del bus de chip y la CPU espera los mismos
ciclos que roban el DMA de bitplanes, el copper y el blitter (por eso se llama
*slow*). Moverle el código **libera chip RAM, pero no lo acelera**. Hoy el stage
2 corre en chip RAM (trackdisk en KS 1.x solo lee a chip); la etapa 4 tiene que
medir la CPU con el código donde vaya a vivir y con los planos y bobs reales
activos. R2 sigue valiendo: el chipset no *lee* de `$C00000`.

**P30 — `tools/shot.ps1` sin `-Exact` no sirve para medir.**
Sin la opción usa `cpu_speed=max` e `immediate_blits=true`: la imagen es
correcta, los tiempos son falsos. `-Exact` usa la temporización de `a500.uae`.
Verificado el 2026-09-22: el ADF arranca en KS 1.2 con temporización real y la
captura coincide al 100 % con el oráculo del PC.

**P31 — Cada blit cuesta ~42 µs de CPU además de los datos.**
Medido en la etapa 4 (W1 contra W3, `bench.s`): preparar los registros y
esperar a que el blitter termine, con el código en chip RAM, cuesta unos 42 µs
por blit. 160 bloques sueltos de 16×16 son ~6.7 ms solo de eso. Preferir
**pocos blits grandes** (una columna entera de una vez, bloques de pantalla
entrelazada en un solo blit de h×5 filas) y no esperar al blitter entre blits
si la CPU tiene otra cosa que hacer. `BLTPRI` (blitter nasty) ahorra un 12-25 %
**solo** mientras la CPU no tiene nada que hacer (P2).

**P32 — Con 5 planos los sprites de hardware comparten los colores 16-31.**
Los sprites del OCS usan COLOR17-19, 21-23, 25-27 y 29-31, que con 5 planos son
también colores del playfield. Poner a Mario en sprites de hardware **no suma
colores**: salen del mismo presupuesto de 31 por línea (D9).

**P33 — `wm_BlockXPos` guarda la Y y `wm_BlockYPos` la X.**
Los nombres del desensamblado están cambiados (`CODE_00F44D` pone la X de
Mario + desplazamiento en `wm_BlockYPos`). Lo mismo con `wm_BounceSprXLo`
(guarda la Y) y `wm_BounceSprYLo` (la X). En el port se transcribe tal cual,
con un comentario donde importa; "arreglar" los nombres rompe la
correspondencia con el ROM.

**P34 — Golpear un bloque cambia el MAPA después, en la fase de sprites.**
`CODE_028752` crea un "sprite de rebote" (4 ranuras, `wm_BounceSpr*`) y es
`CODE_02902D`, después de Mario, quien pone el bloque en sólido invisible
(`$152`) y, al terminar, el bloque final. Un bloque giratorio (`$11E`) queda
en `$048` (**atravesable**) durante 255 frames. Sin portar esto, Mario choca
con bloques que en el juego ya se pueden atravesar (fue la mayor fuente de
fallos de la 8b). Además, en los golpes de costado el rebote cambia la
`SpeedX` de Mario.

**P35 — Los gráficos de Mario se calculan ANTES que su física.**
`CODE_00A295`: cámara (`F6DB`) → `E2BD` (gráficos, con la posición del frame
anterior y la cámara nueva; calcula `MarioScrPosX/Y`) → `C47E` (física; la
colisión usa esas `MarioScrPosX/Y`) → sprites. Verificar los gráficos con el
estado del mismo frame da un frame de desfase.

**P36 — vbcc `-sd`: los datos tienen que estar a menos de 32 KB de `a4`.**
Cada dato se direcciona `simbolo(a4)` con desplazamiento de 16 bits y
`a4 = binstart`. `logicbench_build.sh` parte cada `.s` de vbcc en datos y
código e incluye primero todos los datos; el código y el mapa quedan
detrás y el arnés los llama con `binstart + desplazamiento` (un `bsr`
tampoco llega a más de 32 KB). Además, las etiquetas locales de vbcc
(`l12`...) se repiten entre ficheros: el build les pone un prefijo.

**P37 — vbcc incorpora en línea las funciones `static`.**
Con `-O=991` no dejan símbolo: un perfil por símbolo global atribuye sus
ciclos al global anterior. Para perfilar, `PROF=1 sh
tools/logicbench_build.sh` arma una variante sin inline y sin `static`
(`work/prof/`). **No** sirve para medir la 8d.

**P38 — vbcc `-O=991` puede sumar dos veces la base de un puntero.**
`u8 *p = ram + x; if (p[wm_SpriteDecTbl1]) p[wm_SpriteDecTbl1]--;` salió
como `lea 5440+_ram(a4),a1` + `add.l d0,a1` y después `subq.b #1,5440(a1)`
(y `tst.b 5452(a1)` para la tabla siguiente): cada byte, al doble de
desplazamiento. gcc lo compila bien, así que **`marioverify` no lo ve**: lo
vio `m68kverify` (el frame llegaba al tope de 10 M ciclos). Arreglo: el
puntero apunta a la primera tabla y los índices son relativos
(`p[wm_X - wm_SpriteDecTbl1]`). **Después de cada cambio en C, correr
`m68kverify` con el binario del 68000, no solo `marioverify`.**

**P39 — En DPF, un WAIT del copper gasta una ranura igual que un MOVE.**
Con 6 planos el copper tiene una ranura cada 16 px (§9 punto 8), y el
WAIT también la ocupa. Una simulación que cuente solo los MOVE (como
`dpfsplit.py`/`render_d.py`) promete cargas de color que la Amiga no
puede hacer: con 4-5 registros cambiando en 47 px, las cargas se retrasan
en cadena. Para cargas seguidas, un solo WAIT y después MOVE (con relleno
donde no hay carga).

**P40 — En 68000, `(An,Dn.w)` suma el índice CON signo.**
Una lista del copper de 224 × 220 bytes pasa de 32 767 en la línea 149:
con `(a1,d1.w)` las escrituras caen 64 KB antes (en `scroll.s`, las de la
lista B aterrizaban justo en la A, que por eso se veía bien). Para
desplazamientos que pueden pasar de 32 KB: `moveq #0,d1` + `move.w` +
`(a1,d1.l)`. Lo mismo con un array de registros de 16 bytes indexado por
un número de registro de más de 2047.

**P41 — Una captura de FS-UAE con tiempo fijo puede no estar donde se cree.**
AROS tarda ~35 s en arrancar y `scroll.s` avanza 2 px por frame: con 60 s de
espera, `-DSTOPX=3500` y `4500` se capturaban **antes de llegar** y
`scroll_check` daba ~35 000 fallos (la imagen era de otra parte del nivel).
Esperar **≥ 50 + STOPX/100 s**. `tools/regress.py` ya lo hace, y avisa si
una captura difiere en más del 20 % (posición equivocada, no fallo de
imagen). Descubierto el 2026-09-26; ver `ROADMAP.md` §8. En WinUAE con
KS 1.2 pasa lo mismo: `tools/shots6.ps1` espera 25 + STOPX/100 s.

**P42 — En DPF de 6 planos, el WAIT del copper tiene rejilla de 8 px, no de 4.**
Medido en WinUAE (`copcal.s -DPATTERN`, `COPCAL_FINE=1`, h de a 2): el
MOVE después de `WAIT h` cambia el color en
**x = 8·⌊(h − $38)/4⌋ − 1** hasta h = `$D0` (x = 303), y después en
x = 303 + (h − `$D0`). `h = $40` y `$42` dan los dos x = 15; `$44` y `$46`,
x = 23. Con 6 planos el copper solo tiene una ranura cada 4 cc. `BPLCON1`
no mueve el cambio, y con `BPLCON1` = 0 el píxel 0 de la palabra cae justo
en el borde de la DIW (el scroll de `scroll.s` es correcto). `copcal` solo
había medido h múltiplos de 8 (error de 1 px) y el modelo x = 2·(h − $38)
fallaba por **5 px** con h ≡ 2 (mod 4): era el adelanto "sin explicar" que
tapaba `WOFS` = 8. Para caer en x ≥ objetivo: q = (objetivo + 8) >> 3,
h = $38 + 4q (cabecera de `scroll.s`). Además, como el camino rápido de
`build_mid` mueve el WAIT con la cámara y su fase en la rejilla cambia, los
MOVE sin WAIT que lo siguen se deciden con la **cota inferior** (el
objetivo), no con la x real de ese frame.

**P43 — El borrado deja al copper libre ~60 px ANTES de x = 0.**
El borrado de la línea L empieza en (L − 1, `$E2`): en el borrado
horizontal no hay DMA de planos y los 7 MOVE terminan mucho antes de x = 0.
`build_mid` suponía T = 0 al empezar las cargas de la línea: una carga
cuyo tramo anterior todavía se veía en x = 1..40 salía sin WAIT (o con 1-2
MOVE de relleno) y caía **antes de x = 0**. Síntoma: los objetos que salen
por la izquierda se pintan con los colores del objeto siguiente (tubo
diagonal con franjas de tierra en s = 846, caja de piedras verde en
s = 1936; lo vio el usuario en movimiento). Las capturas con el scroll
parado en las 6 x de siempre no lo veían porque ahí no hay un objeto
saliendo por el borde. Arreglo: T = `TLINE` (−64) al empezar la línea, así
la primera carga de cada línea lleva WAIT. `tools/scrollsim.py` simula la
lista del copper en **cada frame** del recorrido con este modelo (T0 = −56).

**P46 — A 256 px (DIW `$2CA1`, fetch `$40`-`$C0`) el copper es otro modelo.**
Medido en WinUAE (`copcal.s -DW256 -DPATTERN`, `COPCAL_W256=1..3`): la
rejilla de 8 px de P42 corrida a h − `$48` (x = 8·⌊(h − `$48`)/4⌋ − 1)
hasta h = `$C0` (x = 239) y, al terminar el fetch, `$C4` → 243,
`$C8` → 247, `$CC` → 251, `$CE` → 255; desde `$D0` ya está fuera de la
pantalla. **Cada cambio de DIW o de fetch pide recalibrar** con `copcal`.

**P47 — vbcc también emite direcciones absolutas sin avisar al tomar la
dirección de un array `static` o al inicializar un puntero.**
`p = tabla;` sale `move.l #msprite_l12,...` y `const u8 *p = tabla;` deja
`dc.l` con la dirección del ensamblado: el binario se carga en cualquier
sitio y esas direcciones están mal (en Musashi, `BASE` = `$10000`).
`logicbench_build.sh` ahora también para con las etiquetas locales
(`msprite_l34`). Arreglo: asignar en tiempo de ejecución con un índice
que vbcc no puede plegar (`tabla + logic68k_zero`, un `u8` que vale 0):
así usa `lea l12(a4)`. Lo mismo con el vbcc de 2022 al desenrollar
escrituras repetidas a la misma tabla (`move.l #5718+_ram,d2`).

**P48 — En el banco, lo que va delante de los datos del C los corre.**
`logicbench -DWORST` metía 10 KB de estado delante de los `.data.s` del
C: los datos pasaban de 32 KB de `a4` (P36) y el frame salía otro sin
ningún error. Los datos grandes del arnés van al **final** del binario
(después del mapa) y se llegan con `a4 + (etiqueta - binstart)`.

**P49 — `logicbench`: una carga que toca `a4` tiene que guardarlo.**
`measure` usa `a4` = CUSTOM; una carga que lo pone en `binstart` y no lo
restaura cuelga el banco (la captura sale sin resultados). `copystate`
lo guarda; `copyworst` tuvo que hacerlo también.

**P50 — `build_mid`: una carga que no vale ni en la s en que se escribe.**
Las cargas que "llegan tarde" (o temprano) en el plan tienen un intervalo
`[s0 + a, s0 + b)` que no contiene `s0`. Si solo se corrige `vu = s + 1`,
al avanzar la línea se reescribe cada frame, pero al volver vale lo
escrito antes (`vl = s0 + a` queda por debajo): la ida y la vuelta dan
imágenes distintas (19 frames, 2 px cada uno). Hay que forzar las dos
cotas: `vl = s`, `vu = s + 1`.

**P51 — Después de `DDFSTOP` el copper va más rápido (8 px por MOVE desde x = 239 a 256 px; arreglado 2026-10-05).**
El modelo (`scrollsim.py`, `mkscroll.py`) pone cada MOVE encadenado a 16 px
del anterior, que es lo que pasa con los 6 planos leyendo. Al final de la
línea (h >= `$C0` a 256 px) el DMA de planos termina y el MOVE cae antes:
en la captura de 1700 a la vuelta, un WAIT en `$BD` (x = 231) + un MOVE
detrás cambió el color en x <= 244, no en 247. Afecta a las cadenas que
cruzan x ~ 232-255. Para arreglarlo: medir esa zona con `copcal.s` y
meterla en el modelo, o poner un WAIT propio a cada carga en la cola.

2026-10-05: la validación SX lo volvió a ver en s = 1700 (seis píxeles
alternantes, verdes adelantados sobre x = 247-249). Con 256 px, el MOVE
siguiente a x = 239 avanza 8 px, no 16 (`scrollsim.advance()`). Con ese
modelo, `scrollsim` sobre el `scroll.s` anterior predice línea por línea
los 43 píxeles de la captura de la vuelta a 1700.

**Arreglo (`0361736`).** El plan de `mkscroll.py` sigue en 16 px; lo
corrige `build_mid`/`bm_left` al escribir. Solo falla una carga encadenada
cuya anterior cae de verdad en x >= 239: `((x_WAIT - s0) | 7) + x - x_WAIT
>= 255` (el WAIT de `htab` cae en `x | 7`). Clase 1 -> un relleno (exacto;
**un WAIT gasta dos ranuras y cae 8 px tarde**); clases 2/3 -> WAIT propio;
tardes 5 -> 6, 6/7 -> 4. Convertir todas las de x - s > `XKNEE` (el primer
intento) empeoraba la ida y rompía ida = vuelta. `d2 = s0 + 248` filtra el
caso común. Resultado: `scrollsim` 5119 px / 134 frames, igual frame a
frame que antes con el modelo viejo, ida = vuelta 1215/1215; capturas SX
1700 ida y vuelta 0 px (`docs/validacion-sx.md`). Coste: `build_mid` máx.
75 816 -> 80 868 ciclos (+6,7 %). Solo medido a 256 px: a 320 el binario
no cambia y el modelo no se extrapola.

**P52 — `game.s`: el código del juego queda a más de 32 KB de `binstart`.**
Los datos del C van primero (P36) y detrás el código del C y de
`scroll.s`: `entry`, `mario_draw` y compañía quedan más allá de 32 KB, y
`lea binstart(pc)` / `bra.w entry` / `move.l hdr_data_len(pc)` dan
"displacement out of range". Se usa el macro `GETBASE An` (`lea` a una
etiqueta local + `sub.l #etiqueta-binstart`) y la cabecera salta con
`lea binstart(pc)` + `add.l #entry-binstart` + `jmp`. Lo mismo con los
datos grandes del final: al meter GFX32 delante del replay,
`lea replay(pc)` dejó de llegar. Un `ifgt cdata1-binstart-$7ffe` + `fail`
avisa si los datos del C pasan de 32 KB.

**P53 — `mspr_draw` destruye d2.** `mario_draw` guardaba en d2 el buffer
de sprites de la lista y después de `bsr mspr_draw` escribía los punteros
con ese d2: Mario salía como un garabato al pie de la pantalla (los
punteros de sprites apuntaban a basura). Ahora `movem.l d2/a2` alrededor.
Las rutinas a mano documentan los registros que destruyen: leerlo.

**P54 — vbcc y el dibujo genérico: 300 000 ciclos.** `mario_sprite()` en C
(lienzo `[linea][columna][plano][byte]`, índices `int`, bucles genéricos)
costaba ~301 000 ciclos por frame (212 %): unas 37 000 instrucciones. El
C queda como referencia y para los casos raros; el caso de siempre va en
`mspr68k.s` con `MOVEP.W`: en un tile de 4 bpp de la SNES la fila r tiene
los planos 0-1 en la palabra 2r y los 2-3 en 16 + 2r, y `movep.w d,0(a)` /
`movep.w d,1(a)` reparte los bytes del tile izquierdo y del derecho en las
palabras DATA/DATB de los sprites sin convertir nada (~10 400 ciclos,
7,3 %). Volteo horizontal: `gfx32f.bin` (bytes al revés) y L/R cambiados.

**P55 — "Recién apretado" contra la RAM del juego (RESUELTO 2026-09-30).**
`game.s` en vivo calculaba `$16 = $15 nuevo & ~$15 viejo` con el `$15` de
`ram[]`. Ahora `pad_convert` hace lo mismo que `ControllerUpdate` de SMW
(P60). Ojo: en el port solo `no_buttons()` borra `$15-$18`, y solo al
morir, así que esto **no** explica los dobles saltos que vio el usuario.
Sospechas, sin confirmar: el joystick de un botón (arreglado, P60) y los
rebotes sobre Rex que se simulan pero no se dibujan.

**P56 — La herramienta Bash rompe las barras invertidas en los heredoc.**
`\1` de los macros de vasm, `\n` de las cadenas de C y `\x01` de Python
llegaron como caracteres de control o saltos de línea reales (varias veces,
en las dos sesiones del 2026-09-27; el `\1` roto fue un chr(1) invisible
que hizo fallar un `Edit` después). Los scripts con barras se escriben con
la herramienta de escritura de ficheros, no con `cat <<EOF`, o se usa
`chr(92)`.

**P57 — Capturas ×2 de WinUAE: muestrear el centro del píxel.** Con el
origen de la pantalla en (130, 69) de la captura, el píxel (x, y) de la
Amiga es (131 + 2x, 70 + 2y). Tomando la esquina (130 + 2x) salen miles de
"fallos" en todos los bordes (`game_check.py` dio 7566 así; 0 al
arreglarlo).

**P58 — En vivo, lo no portado congela el juego y lo explica (2026-09-30).**
`level_frame` pone `mario_unsupported` y no sigue cuando Mario entra en algo
que el port no tiene (animaciones, meta, tuberías, capa 2, tiles
especiales...). En el replay eso lo tapan las resincronizaciones; en vivo,
`game.s` entra en el **modo diagnóstico**: congela la imagen, muestra el
motivo, el frame, la X/Y, `$71` y el Map16 bajo los pies en una franja
debajo de la pantalla, y con ESPACIO pasa a una página con el historial
del joypad desde el principio del nivel en una rejilla de bits. Desde una
captura de esa página, `tools/diag_read.py --shot X.png --repro` reproduce
la partida en el PC (Unicorn) y dice en qué frame y por qué se paró.
RETURN, Z, A o el botón vuelven a empezar. El daño con Mario grande sigue
sin animación: grande → chico con `wm_PlayerHurtTimer = $7F`.

**P59 — Un WAIT del copper en la línea 255 con h ≥ ~`$E0` no llega nunca.**
El copper evalúa esa h con V ya en `$00` (línea 256) y se queda parado
hasta el frame siguiente, sin ningún error visible. `scroll.s` perdía así
las líneas 212-223 (el borrado del segmento 212 esperaba en (`$FF`, `$E2`)).
Usar **un solo** `WAIT $FFDF`: un segundo `$FFDF` detrás también cae después
de la vuelta. Arreglo: `WAIT $FFDF` + `MOVE $1FE,0`, mismo tamaño de
segmento. `scrollsim.py` no lo ve porque supone que corren todos los
segmentos. Para ver hasta dónde llega el copper: un `MOVE COLOR00` con otro
color en cada segmento y mirar el borde.

**P60 — `ControllerUpdate` de SMW (`game.s:708`).** "Recién apretado" =
nuevo AND NOT anterior, contra copias **propias** (`wm_JoyDisP1L/H`), no
contra `$15/$17`. Además `$15 = (JOY1L & $C0) | JOY1H`: el bit 7 es B|A y
el 6 es Y|X, así que A suma a B y X suma a Y. Para reconstruir el mando
crudo con A o X apretados hacen falta `$16/$18` y el frame siguiente. Un
joystick de un botón que cambia A↔B según arriba tiene que fijar el botón
mientras no se suelta: si no, soltar arriba da un B nuevo (otro salto).

**P61 — `build_sign` se calcula en `entry` ANTES de escribir los punteros
del C** (`_map16_lo`...). Un arnés que los escriba primero (`gamesim.py`)
saca otra firma del binario.

**P62 — El vbcc de cloud también compila mal código que esquiva P38.**
(1) Con `u8 *p = &RX8(wm_SpriteXLo, x)` y `p[t - wm_SpriteXLo]`, vbcc cargó
la base de otra tabla y todas las lecturas salieron mal; en
`m68kverify --sprites` pasaba de 0 a 1 resincronización, casi por
casualidad. (2) En `mario_sprite`, `u8 *o = mario_oam + 4 * e; prop = o[3]`
dejó `o + 3` en el registro y leyó `o[0..2]` desde ahí: `put8` escribía
fuera de `cv`, encima del código de `mcoll` (el asm cae a ese C en 1 frame
del replay: en la Amiga ese frame pisaba código). El vbcc de la PC (2022)
no falla en los mismos sitios. Los que lo ven: `m68kverify --cross` (la RAM
entera contra el C del PC, lo corre `regress.py`) y `gamecheck.py --spr`.
Arreglo: leer los bytes a variables locales.

**P63 — `Scc` después de un `MOVE` lee un C ya borrado.** `MOVE` pone C a 0
(X no). El acarreo de un `add` hay que tomarlo con `scs` inmediatamente
después. Era el fallo de `spr_pos_axis_asm` (Mario sobre el bloque `?`
volador se corría 1 px cada 4 frames en la Amiga); lo encontró `--cross`.

**P64 — El máximo de ciclos de `m68kverify` era una inicialización.** El
primer `level_frame` de cada corrida pagaba `probe_init` (~21 000 ciclos) y
ese era el "peor frame" (4438). Ahora lo paga `level_start_sprites`. Mirar
siempre en qué frame cae el máximo.

**P65 — Los sprites que ya están al empezar un tramo los crea la carga del
nivel.** `CODE_02A751` (`CODE_02ABF2` + `CODE_02ACA1` + una pasada de
`CODE_01808C`) corre antes del primer frame grabado. Marcarlos como
"cargados" hacía que no existieran nunca (el Koopa deslizante). En el port:
`sprite_level_start` + `level_start_sprites`; en `game.s`, el op LEVEL (4)
del replay y `live_start`.

**P66 — Congelamientos que pone un sprite.** Cuando un sprite congela el
juego (HurtMario pone `SpritesLocked = $2F`), en ese frame los sprites de
ranuras anteriores ya corrieron y los de las posteriores no; en el frame
en que se descongela vuelven a correr todos. Saltarse esos frames en el
verificador desfasa un frame a los sprites.

**P67 — La ROM que emula snesrev/smw NO es la original.** Fuerza el acarreo
en 46 ADC/SBC y aplica ~20 arreglos de bugs (`$00E3FB` pone a cero
`$0C/$0D` en los gráficos de Mario). Para un oráculo hay que deshacer esos
parches: `work/snesorc` lo hace por defecto (`--mode rom`) y así reproduce
`oracle_yi1` (smwrecomp) línea a línea, 6871/6871.

**P68 — El oráculo se toma antes del NMI y el mando se lee en el NMI.** La
entrada del frame k de un guion `.orc` aparece en los `$15-$18` del registro
k+1. Además `_NoButtons` borra `$15-$18` en el frame en que empieza una
animación (entrar en una tubería): la grabación pierde el botón real, y en
`oracle_yi1` (frame 11425) hubo que deducirlo.

**P69 — Lo que el oráculo no recorre puede estar mal aunque todo dé 100 %.**
`f7f4` (`CODE_00F82A`) hacía `return` donde el ROM hace
`STX wm_EnableVertScroll` y sigue con el scroll vertical (con X != 0: pared,
planeo, trepar, globo, nube, Yoshi con alas, nadar volando); además
`CODE_00F875` corre también con el scroll vertical ya habilitado.
`oracle_yi1` nunca movió la cámara en vertical; lo mostraron las
grabaciones de snesorc (4 resincronizaciones por `Bg1VOfs` en `normal` y
`diagpipe`). Antes de dar un camino por verificado, comprobar que el
oráculo pasa por él; si no, grabarlo con snesorc.

**P70 — Las "colinas" de YI1 son cornisas.** Solo son sólidos los 3 bloques
de pendiente; la cima `$0A1` y el lado derecho `$0A6` no lo son, y por
dentro se pasa.

**P71 — Una carga "tarde" que vale con la base desplazada rompe la
ida = vuelta.** Si "válida o canónica" depende de qué cargas se
escribieron, y eso depende de la dirección o de la historia, la imagen de
una misma s cambia (línea 178, x = 4828, a = −11, b = −5: 41 frames
distintos). Regla: "tarde" (a > 0 o b ≤ 0) es una clasificación fija, y una
línea con una tarde viva es canónica (s0 = s).

**P72 — La base de `build_mid` hace el scroll asimétrico.** El plan pone las
cargas lo antes posible (a ≈ 0): valen b px hacia la derecha y casi 0 hacia
la izquierda, así que yendo a la izquierda cada línea con cargas visibles
se reescribe en cada paso. Musashi, 2 px/frame: ida media 9,9 % y máx.
54,1 %; **vuelta media 36,6 % y máx. 94,8 %** (s = 2832), con 1400 de 2432
frames por encima del 25 %. `scroll.s -DBENCH` solo mide la ida: medir las
dos (`scrollprof.py -D RETURN=4864 --stopx 0`).

**P73 — `tst` con `(pc)` no existe en el 68000.** vasm lo rechaza con
`-m68000`: leer con `move.b x(pc),d0`. Tampoco `eor` con origen en memoria
(`eor.w (a0)+,d0` no ensambla): `EOR` solo acepta `Dn` como origen.

**P74 — Tablas grandes dentro de `scroll.s` rompen `game.s`.** `scroll.s`
va en medio del binario del juego: 64 KB de `ds.b` dejan `bsr scroll_init`
y los `lea (pc)` fuera de ±32 KB (P52). Pedirlas con `AllocMem` en
`scroll_init`, que corre con el SO vivo en los dos programas.

**P75 — `-DSTOPF` cuenta desde el primer frame del replay, no es el frame
del oráculo.** El replay empieza en 5145: para capturar el frame F del
oráculo, `-DSTOPF=F-5145` (como `shots63.ps1`). Con `STOPF=6000` la
captura se toma antes de llegar y `game_check` da miles de fallos.

**P76 — `fsuae_shot.sh` en paralelo.** Varias corridas a la vez necesitan
`FSUAE_BASE` y `FSUAE_DISPLAY` distintos, y aun así Xvfb puede no estar
listo en los 2 s que espera el script ("unable to open display"). Correrlas
de a una.

**P77 — `lvparse.py` leía mal los bytes 2 y 4 de la cabecera (arreglado
2026-09-30), y YI1 SÍ tiene scroll vertical.** El byte 4 es `IIVVZZZZ`
(`lv_read.s`: tileset `& $0F`, item memory bits 6-7, `wm_VertScrollHead` =
bits 4-5, con 3 → 0 y sin scroll horizontal). `lvparse` tomaba 5 bits de
tileset y el bit 7 como "scroll vertical", y en el byte 2 metía la
prioridad de la capa 3 en la música. De ahí salió "el header de YI1 no
tiene scroll vertical": vale **2** ("solo en algunos casos",
`CODE_00F82A`), y en las grabaciones de snesorc la cámara sube hasta 4 px
(`Bg1VOfs` = `$BC`). La Amiga no lee `Bg1VOfs` (`docs/plan-tecnico.md` §10.2b). Para las
cabeceras, la fuente de verdad es `lv_read.s`.

**P78 — vbcc y los `spr_*.c` (I1, 2026-09-30).** Tres reglas para un
sprite en fichero propio: (1) las tablas `static const` de
`gen/smwtab*.h` se emiten aunque no se usen: incluirlas en un `spr_*.c`
metió 16,5 KB de datos duplicados y rompe P36; `msprite.h` no las incluye
y un `spr_*.c` las incluye solo si las usa (`spr_rex.c`: bajo
`#ifndef LOGIC68K`). (2) Un helper `static` en un header se emite una vez
por fichero que lo incluye (+124 B cada uno): los helpers compartidos son
extern en `msprite.c`. (3) Todos los `.s` van a un solo vasm plano: dos
`static` con el mismo nombre en distintos `.c` chocan; los nombres son
únicos en todo el C. `logicbench_build.sh` anexa los `spr_*` a
`msprite.data.s`/`msprite.code.s` porque `game.s` y `logicbench.s`
incluyen por nombre.

**P79 — `cmp.b`/`bhs` es sin signo, y un registro reusado arrastra valor
(L1a).** En `_f7f4` hacia arriba, con `wm_OnYoshi` y `YoshiHasWings` < 2
hay que poner `d5` a 0 antes de mirar el nado (`.swim: moveq #0,d5`); si
no, queda el 1 de `YoshiHasWings` y se habilita el scroll vertical.

**P80 — `game.s -DBENCH` (O1).** `-DBENCH` en `game.s` activa también los
bloques `ifd BENCH` de `scroll.s` (`readtimer`, `res`...): las etiquetas
del bench del juego llevan prefijo `gb_`. Cada sello de CIA cuesta 33
ticks (~330 ciclos): `gb_init` lo calibra y se resta. `tst.w label(pc)` no
existe en 68000 (`move.w label(pc),d0`). **`gb_scroll_frame` es una copia
del cuerpo de `scroll_frame`**: si cambia el cuerpo en `scroll.s`, cambiar
la copia o el bench mide otra cosa (reemplazarla por marcas dentro de
`scroll.s` cuando se pueda tocar). `game_read.py --auto` ignora el marco
de la ventana de WinUAE; `bench_read.py` no.

**P81 — El pico de los postes de la meta no baja agrupando (S1a+S2).** Las
cargas "tarde" de los postes son un borde vertical: todas cruzan su celda
de 8 px en el mismo frame en que entran por la derecha las cargas de los
mismos postes, y a 4 px/frame cada lista avanza 8 px por escritura y
cruza siempre. Un agregado por grupo de LNS solo compensa si no cuesta
nada al reescribir (a la vuelta casi todo se reescribe, P72): por eso el
agregado se calcula solo en grupos fríos y hasta la primera reescritura, y
el indicador es `a4`. S2 ahorra en los frames tranquilos (LNS 5494 → 806
ciclos en s = 1000) y **cuesta ~120 ciclos por grupo cuando todos se
reescriben**: el peor frame subió 0,5-1,9 puntos (aceptado el 2026-09-30:
se recupera con S4/S5). `(d8,pc,Xn)` llega a ±127 bytes: `celltab` va
dentro del código de `build_mid`, detrás de un `bra`.

**P82 — La PC Windows (2026-09-30).** (1) `/c/msys64/ucrt64/bin` primero
en el PATH: si no, gcc llamado desde Python sale con 1 sin mensaje
(choque de DLLs con `/mingw64/bin`). (2) `python3` es el stub de
WindowsApps: `python` y `PY=python`. (3) La base de la PC es
`tools/baseline_pc.json` (`regress.py --baseline tools/baseline_pc.json`;
el vbcc de 2022 da otros ciclos). (4) No hay FS-UAE: capturas con
`tools/shot.ps1 -Exact`, `shots6.ps1`, `shots63.ps1`, **de a un WinUAE
por vez** (`C:\Users\JC\Downloads\sma\winuae_lock.ps1 <script> <args>`,
fuera del repo: las esperas son en segundos de reloj). (5) Con capturas
de WinUAE: `scroll_check.py --sc 2` (la escala por defecto es la de
FS-UAE y da 60 % de fallos falsos) e `imgdiff.py --crop 130,69,642,517`
(la barra de título y de estado cambian). (6) `scrollprof.py` escribe
siempre `work/scrollprof.bin`: de a una corrida. (7) `core.autocrlf=true`:
los `.orc` y `oracle_*.txt` salen en CRLF y `snesorc --replay` lee 0
registros; pasarlos a LF para correr snesorc (`snesorc_make.sh` ya quita
los `\r` de lo que genera). (8) snesrev está en
`C:/msys64/home/JC/.cache/snesrev-smw`: un `snesorc.exe` suelto necesita
`SNESORC_ASSETS=C:/msys64/home/JC/.cache/snesrev-smw/smw_assets.dat`
(`snesorc_make.sh` lo exporta solo). SDL2 y `make` están instalados con
pacman de msys2.

**P83 — Guiones de snesorc.** Un `until` que ya se cumple no espera: el
`N BOTONES` siguiente corre con Mario en el aire y no salta (empezar los
saltos con `until $0072==00`). `until w$0094<=X` también se cumple
después de morir (el nivel vuelve a x = `$000D`): comprobar además
`assert $0100==14`. Cruzar la cinta de la meta (`$12DB`-`$12E0`) termina
el nivel y ya no se puede volver. El Chuck (x `$12A0`) mata a Mario si va
andando: saltarlo desde x ≥ `$1260` con salto largo.

**P84 — La cámara vertical de YI1 solo se mueve con `$13F1`
(`wm_EnableVertScroll`) ≠ 0**, y en YI1 lo pone `$149F`
(`wm_GlideTimer`, ~80 tras un salto a plena carrera): un salto normal no
la mueve. Con él activo, la cámara sigue a Mario a 3 px/frame hasta
dejarlo a ~100 px del borde de arriba y vuelve sola a `$C0`. Mínimo visto
de `Bg1VOfs`: `$AF` (`oracle_chuck`). Para S8, `stress_vert` todavía no
está grabado.

**P85 — Datos de sprites de las grabaciones.** El caparazón rojo `$DB` de
`spr.lv` aparece en las ranuras como sprite `$05`. En `$19`, 03 es la flor
de fuego y 02 la capa. La flor `$75` se queda encima del bloque `?` (no
cae); el cabezazo tiene que dar con x + 8 dentro del bloque. El Chuck
sobrevive a los pisotones (su HP está en `$1500`+, fuera del registro). Un
Banzai que pasa por la x de Mario lo mata si Mario salta dentro de su caja.
El pozo de x `$C10`-`$C5F` atrapa a los sprites (un caparazón rebota ahí
para siempre). El `$C7` de x `$0660` se convierte en `$74` sin que Mario
lo toque (`oracle_chuck`, frame 2568).

**P86 — Verificadores contra snesorc (P1, P2, P4).** El primer registro de
`oracle_yi1` (y de la partida del port) es el último frame del mosaico
(`$1404` ≠ 0); el de un guion de snesorc con `rec on` tras `until
$0100==14` ya tiene el primer frame del nivel corrido (`$1404` = 0): una
pasada de sprites más. Un cambio en `level_start_sprites` se prueba contra
`oracle_yi1` Y contra snesorc. El cargador puede reusar una ranura en el
mismo frame en que un sprite sale de pantalla: `sprload` libera el índice
del saliente también con `sj == 1`. Un sprite que nace directo en estado 9
(el caparazón `$DB`) es un nacimiento, no se copia del oráculo (si no, el
port lo duplica). La RAM por encima de `$14FF` (`wm_SprObjStatus`,
`wm_SpriteSlopeTbl`, `wm_MirBlkCheck`, `wm_SprOnTileXLo`...) no está en
el oráculo: un arnés que reponga la RAM desde el oráculo la arrastra.

**P87 — Transcribir sprites (P3, P4, P5).** `SubHorzPos`/`SubVertPos` del
banco 2 usan `wm_MarioXPos/YPos` ya movidos; el `sub_horiz_pos` de
`msprite.c` usa `wm_PlayerXPosLv` (el del frame anterior): no se
intercambian. `GetDrawInfo2` lejano hace `PLA PLA RTS` (en el port:
`get_draw_info` devuelve 0). La ROM lee fuera de tablas (`DATA_02C73D` con
Y = 6 lee `DATA_02C743[0]`): emularlo. En `CODE_01A5DA` el `STA
SpriteStatus,Y` después de `JSR CODE_01A77C` mata al que corre, no al
otro. Una variable local `m0`..`m15` choca con los `#define` de
`smwram.h`. Cada `spr_*.c` nuevo: tablas en su bloque `#elif
defined(SMWTABX_<X>)` de `smwtabx.py`, una línea en `sprite_main` (y en el
init de `sprite_run`), su bloque al final de `msprite.h`, el número en
`game_ported` de `marioverify.c`, su oráculo en `SNESORC` de `regress.py`.

**P88 — asm del 68000 con vasm (L1c, MA1).** `lea d8(An,Dn.w)` solo admite
desplazamiento de 8 bits con signo; `movem.l regs,(An)+` no existe; en
rutinas largas las ramas `.s` se salen de rango. Una macro definida dentro
de un `ifnd` falso falla si su cuerpo tiene `ifeq`/`else`: las macros van
fuera. El asm de `mario_E2BD` depende de propiedades de tablas de la ROM
que vigila `lint_port.py` A1: si cambia el generador de `smwrom00.c`,
mirar A1 antes que el asm. `mspr_draw` tiene caché por pose (MA1): quien
escriba `g_spra`/`g_sprb` llama a `mspr_inval`.

**P89 — Editar las listas del copper en el sitio no conviene en el 68000
(S4).** Cada edición cuesta ~1000 ciclos por línea (buscar, rango de bases,
vl/vu) contra 413 + 124 por carga de reescribir entera, y en el borde de
los postes igual se reescribe la mitad: el pico de la ida subió 77 498 →
105 496. Lo que baja el pico (modelo `tools/wip64/midsim5.py`, que
reproduce los conteos del asm): elegir la base menor yendo a la izquierda
y diferir las cargas por su holgura b. Una carga que ya salió por la
izquierda no daña la imagen pero ocupa copper al principio de la línea y
obliga a s0 ≤ x[klo].

**P90 — Guiones de snesorc, más (P5, RB).** Las condiciones de `until` leen
un byte de WRAM: "y ≥ `$150`" de un sprite es `until $14D7==01` y después
`until $00DB>=50`. Un `poke` después de un `until` que ya se cumplió dentro
de un bloque `N BOTONES` largo llega tarde sin error. La Y real de Mario es
`$D3`/`$D1`; el oráculo graba `$0096` (poner las dos). El contador de
monedas de Yoshi es `$1420`. La cinta de la meta la corta cualquier
contacto mientras esté por encima de los pies de Mario. En Windows,
`regress.py` no arma `work/libport.so` (los cruces de RAM): `gcc -shared
-O2 -DNOOAM -Iplayer -o work/libport.so <el C del port> player/spr_*.c
player/gen/smwrom00.c`. `level_final.png` (lo leen `mkbg`/`mkd8in`) no lo
genera la cadena: `mklvl.py --out work/level_final.png`.

**P91 — El binario del juego y el arnés de Musashi (ola 3).**
`gamecheck.py --engine musashi` carga el binario en `V.BASE` = `$10000` y
los datos del scroll en `DATA`: con P6+P8+L1b el binario llegó a `$4025C`
y pisaba `DATA = $40000` (3825 frames distintos solo con el scroll; con
`--no-scroll` y con Unicorn, 0). Ahora `DATA = $48000` y `gamecheck` corta
si se vuelve a pasar. Si un fallo aparece solo con la suma de varias
ramas, mirar primero el tamaño.

**P92 — Lo que `regress.py` no cruza (L1b).** Los oráculos de snesorc
(`orc.*`) los corre `marioverify` en el PC, es decir el C: un asm de
`logic68k.s` que rompa chuck, shells o goal solo lo ve `m68kverify --mode
loop --sprites --cross work/libport.so --oracle work/oracle_<n>.bin`. La
tolerancia de ciclos (0,2 %) deja pasar como OK subidas de 35-85 ciclos.
En `logic68k.s`, `bxx.s` entre bloques grandes se pasa de ±127 B; una
rutina C se puede llamar con `bra` (tail call) si el asm no tocó la pila
ni d2-d7/a2-a6.

**P93 — Animaciones de Mario y el juego en vivo (P8).** `StarPowerTimer`
lo baja `mgfx.c` (CODE_00E2BD), no el jugador. El poke de snesorc entre
dos frames aparece como un arranque de la estrella sin sprite (el
verificador lo toma como entrada). `GiveMarioMushroom` escribe
`$1496` (`ExecutePtr` preserva Y). `diag_cause` de `game.s` decide qué
congela en vivo: al portar una animación de `$71`, agregarla ahí o el
juego se congela con ella.

**P94 — vasm: una etiqueta global corta las locales (SX).** Una etiqueta
global en medio de una rutina deja fuera de alcance sus `.x`: por eso
`bm_left` es rutina aparte con su `.done`. Capturas de WinUAE a la vuelta
(`-DRETURN`): esperar ~25 + (2·RETURN − x)/100 s con margen; con menos,
master todavía no llegó y la imagen sale distinta.

**P95 — Grabaciones (RC).** Los "!" de YI1 (Map16 `$6B`) son de contorno
punteado, no sólidos. El Map16 se regenera con `tools/mkmapbin.py --out`
(un `work/yi1_map16.bin` todo `$25` está vacío). Un buscador no debe
escribir el guion de salida sobre el que lee como prefijo. Nombres de
oráculo: mirar `tools/snesorc/` antes de grabar (RC y P8 hicieron dos
`pw_estrella` distintos; el de RC quedó como `pw_1up`).

**P96 — El factor del DMA no es uniforme (O1 en WinUAE, 2026-10-04).**
Contra Musashi: `level_frame` ×1,03, `build_mid`/`mspr_draw`/resto del
scroll ×1,45, la columna (blitter) ×3,2; el total del peor frame ×1,30, la
media ×1,07. Presupuestar la lógica a ×1,05 y el scroll y el dibujo a ×1,5,
no un ×1,3 global (`docs/informe-d1.md` §5).

**P97 — O5, el render desacoplado (ola 3).** (1) La foto no puede escribir
el buffer de sprites de la lista **publicada** todavía no puesta: la COPER
(línea 272) corre entre la publicación y la VERTB que la pone. Ocupados =
{publicada si hay, si no la que se ve; la del render}; excluir solo la que
se ve adelanta a Mario un frame respecto a la cámara (P35) siempre. (2) La
lógica empieza en la línea 272 (COPER), no en la 0 (VERTB): en la 0 el DMA
de planos sube `level_frame` de 28,2 a 33,9 % y la media de 29,3 a 37,2 %.
(3) asmlint no sigue un cambio de pila (`move.l (sp),sp`): va en una
rutina sin cabecera (`dc_logstk`). (4) `gamecheck.py` con un binario
`-DBENCH` se cae en Unicorn (`gb_rt` lee el CIA): usar uno sin `-DBENCH`.
(5) El cuerpo de `dc_loop` es otra copia de `scroll_frame` (como
`gb_scroll_frame`, P80): si cambia uno, cambiar las tres. (6) Supone que en
la línea 272 el DMA ya no lee los sprites de la imagen: vale mientras
ningún sprite baje de la línea 268.

**P98 — Rutinas de gráficos que escriben la OAM (G8).** `SprTilemapOffset`
solo cubre los sprites `$00-$53`: con `$83`, `$AB` en estado 4, `$B9` o
`$BD` la ROM lee lo que sigue a la tabla; en los portados ese tile se
sobrescribe siempre, pero el `$83` lo mostraría (sacarlo de la ROM antes de
engancharlo). La OAM grabada no trae la ranura: se compara por tramos
seguidos y orden relativo. Un Rex adoptado a mitad de tramo no tiene
`SpriteMiscTbl6` (no se graba): su pose puede diferir con la lógica exacta
(`oracle_pipe`). La nube del giro: atributos = `tile & $30`. `GetDrawInfoBnk1`
lejos cae en `_01A3CD` y escribe Y, m0 y m1; `Bnk3` no. La OAM grabada en el
registro N es la del frame N (sin desfase, medido). Desde el 2026-10-05,
`NOOAM+SPR_OAM` también funciona en el 68000: `rex_main_asm` llama a
`_rex_gfx` en la fase original. La limpieza incluye las 128 Y y las 12
cantidades, para que no queden fichas de frames anteriores. La OAM se
verifica con despachos del modo `game`, no con el `loop` que omite frames
animados/bloqueados. `spr_oam_first` es un desplazamiento en bytes desde
`$0300`, no un índice de ficha; `spr_oam_n` incluye las ocultas. Coste
integrado sin DMA: máximo de `level_frame` 39 026 → 46 718 ciclos
(+19,7 % relativo), media 28 588 → 32 692 (+14,4 %). Sigue opt-in hasta
medir DMA/O5. Evidencia y comandos: `docs/oam-amiga.md`.

**P99 — Gráficos de sprites (G3a).** `UploadGFXFile` deja el plano 3
distinto de 0 en las fichas 0, 1, 16 y 17 del GFX 01 (= bp0|bp1|bp2): no
basta con 3 bpp + plano 3 a 0. Un 16×16 de la OAM suma 1 en el nibble bajo
y 16 en el alto, cada uno con su vuelta. En la OAM (5 B) el bit 0 de `attr`
es el bit 8 del tile y el bit 0 de `hi` el bit 8 de X: sin él se pierden
las fichas 256-511. Las fichas de Mario se suben por DMA sobre el GFX 00.

**P100 — Columnas de sprite (G1/G0).** Las "4 columnas libres" ya incluían
a Mario: quedan 2 o 3 (Mario usa 2 cuando su caja pasa de 16 px). El Rex
mide 20 px (2 columnas) y el Chuck 24-32. Una pose compartida entre objetos
no lleva su Y/X: el copper reescribe también `SPRxPOS`/`SPRxCTL` (hasta 2
MOVE más por canal). G0 se midió a 256 px en WinUAE cycle-exact:
PT desde h=$80/$C0 de la línea anterior y POS/CTL desde h=$38 de VSTOP
dan poses compartidas exactas en ocho canales con carga sintética de color.
PT desde h=$D8 anterior llega tarde: no usar todo el borrado como ventana.
El encadenado con gap 1 también pasa. Copiar 1408 B chip→chip cuesta
7,47-7,52 % del frame durante el DMA de planos y 4,81-4,95 % en VBlank,
sin armado de listas/encabezados. El modelo de 320 px no sustituye esta
medida ni prueba las ventanas del copper real; `docs/medida-g0.md`.

**P101 — `poke` en snesorc no lo ve el port (R10).** La grabación guarda el
estado al final del frame: un `poke` sobre un sprite da 1 frame distinto
sin que el port ejecute el código que se quería cubrir. YI1 sí tiene
bloques giratorios (Map16 `$11E`). El `include` de un `.orc` es relativo al
guion: los guiones de búsqueda viven en `tools/snesorc`. Un Chuck solo
cuenta el pisotón fuera del estado 3.

**P102 — vasm relaja llamadas lejanas a absolutas (SPR_OAM).** Al crecer
el binario plano, una llamada fuera de ±32 KB puede ensamblarse como
`JSR/JMP` absoluto sin error. El juego se carga y se copia en otras bases:
ese destino sigue apuntando al offset original y salta a datos. El build
pequeño de logicbench puede pasar mientras el juego integrado falla.
La OAM descubrió el caso de `mcoll` → `_f44d_asm`; el detector encontró
también dos fallbacks asm→C ya absolutos en el build normal que los
oráculos no recorrían. No corregirlo aumentando el rango permitido ni
añadiendo nombres a una lista de excepciones.

`PICCALL/PICJUMP` calculan el destino desde una etiqueta PC cercana más
un delta de 32 bits, usando solo registros de trabajo. El puente del C
queda cerca de `mcoll`; los dos fallbacks usan PIC también por defecto.
`tools/piccheck.py`, llamado por los dos builds, inspecciona los opcodes
del listado y rechaza `4EB8/4EB9/4EF8/4EF9`, incluidas relajaciones de
`BRA/BSR`; un listado vacío falla. Las constantes `dc.l` no cuentan como
instrucciones. Verificar el binario integrado con `gamecheck --spr`, el
cruce de RAM/ABI y la regresión normal, sin actualizar baseline para
ocultar diferencias. Detalle y pruebas negativas: `docs/oam-amiga.md`.

**P103 — El bucle principal corre en modo usuario (Z1).** El bootblock
entra al juego conservando el modo usuario de Exec; las ISR sí ejecutan en
supervisor. Escribir `SR` para enmascarar interrupciones desde el bucle
principal provoca Guru `$80000008` en KS 1.2. El primer arnés de reinicio
corría en supervisor y dejó pasar ese defecto; la captura cycle-exact lo
detectó al terminar la primera muerte.

Para la carga atómica se guarda `INTENAR`, se borra MASTER en `INTENA`
vía `a4`, se reconstruyen RAM, mapa, PF1, listas y fotos, se reconocen las
peticiones VERTB/COPER acumuladas y se restaura la máscara original. No
retornar desde una ISR cambiando su pila ni publicar fotos a medio cargar.
`tools/restart_verify.py` ejecuta la transacción real en modo usuario y
comprueba retorno, modo CPU, INTENA y reanudación de O5. La captura de
reaparición y la medida de CIA-B están en `docs/validacion-z1.md`.

**P44 — Los "derrames" de la etapa 5 alargan el tramo anterior.**
`mkleveld.py` asigna los píxeles que quedan fuera de todo tramo al registro
que *todavía conserva* el color: después del fin de un tramo puede haber
píxeles de ese registro que necesitan el color viejo (línea 152, COLOR01:
tramo hasta x = 4571, píxel en 4579). `mkscroll.py` liberaba la carga en
el fin del tramo y el copper, legal según los datos, la ponía encima. Ahora
la carga (y el cambio del borrado) se libera después del último píxel del
registro antes del tramo nuevo. Coste: ventanas más cortas, más cargas con
WAIT (en el plan, 9 de 3409 no llegan, antes 2).

**P45 — Una carga cortada por `LASTX` tiene que bajar el `vu` de la línea.**
Si `.mv` abandonaba una carga con x > `LASTX` sin tocar el `vu`, la línea no
se volvía a mirar cuando la carga entraba en pantalla y las de detrás
quedaban sin escribir (s = 4346, línea 162: 4 de 6).

Con P42-P45 (`tools/scrollsim.py --speed 2`, todo el recorrido): 298 060 px
de la capa 1 con el color mal → **19 586** (−93 %), peor frame 5409 → 194
px. Lo que queda son los postes de la meta (muchos colores en pocos px:
ancho de banda del copper) y puntos sueltos.

**P8 — El slow RAM de la A501 no está disponible si el software lo desactiva.**
Algunas rutinas de arranque desactivan `/EXRAM`. Verifica que `$C00000`
responde antes de usarlo.
