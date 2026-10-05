# AGENTS.md — Manual de implementación del port-demo SMW → Amiga 500

> Este fichero define **cómo trabajar** en este proyecto. Es el contrato entre
> quien implementa (persona o agente de IA) y el hardware objetivo.
> El análisis de viabilidad original (el *porqué* de la primera versión del
> plan) está en **`docs/plan-original.md`** (antes `PLAN.md`).
>
> **Qué hacer ahora y en qué orden: `ROADMAP.md`** (plan a futuro por etapas
> y handoff vigente).
>
> **Cómo repartirlo entre subagentes: `SUBAGENTES.md`** (tarjetas de todo lo
> que falta, con nivel, puerta y ficheros que tocan).
>
> **El detalle de referencia vive en `docs/`** (compactado el 2026-10-03; nada
> se borró, se movió textual): `formato-nivel.md` (antes §5, §5b, §5c y §8b),
> `pitfalls.md` (el texto completo de §8), `decisiones-medidas.md` (los datos
> de §9: D8/D9 y "Etapa 4 — resultados"), `historia.md` (los handoffs viejos
> y la tabla de etapas original) e `investigacion-ports.md` (qué hicieron otros
> ports y juegos de A500).

---

## 1. Objetivo

Port-demo **jugable** del nivel **"Yoshi's Island 1"** (nivel `105`,
`world_1/1/`) de Super Mario World a **Commodore Amiga 500 PAL con 1 MB**
(512 KB chip + 512 KB A501).

Entregable: un **ADF booteable** (bootblock propio, KS 1.2) que toma la máquina y muestra el nivel
con Mario controlable, scroll, **los enemigos reales del nivel** (D3), HUD y música.

**Criterio de fidelidad: lo más cercano posible a 1:1 con la SNES.** Una
métrica que pasa no es "hecho" si a la vista hay una diferencia.

**No** es un emulador de SNES. **No** es un port completo del juego.
Es una reimplementación de un nivel usando los datos del decompilado.

---

## 2. Reglas duras (NO negociables)

Violar cualquiera de estas invalida la implementación.

| # | Regla | Consecuencia si se viola |
|---|---|---|
| R1 | **Solo PAL** (320×256, 50 Hz) | En NTSC (320×200) no caben las 224 líneas |
| R2 | **Slow RAM ($C00000) es solo para la CPU** | El chipset NO la ve. Nunca pongas ahí bitplanes, tilesets, muestras de audio ni listas de copper |
| R3 | **Presupuesto de chip RAM: 512 KB** | Todo lo que toque el chipset vive aquí |
| R4 | **Máximo 32 colores** (5 planos). Nunca EHB | EHB fuerza la mitad superior a media intensidad |
| R5 | **El scroll horizontal fino es `BPLCON1` (0-15 px); el grueso, `BPLxPT` (16 px)** | Ver "R5 en detalle": NO hay que re-blitear el playfield para mover 1 px |
| R6 | **Máximo 8 sprites de hardware**, 16 px de ancho, 3 colores | Los sprites de juego van por blitter |
| R7 | **Ancho de banda del blitter ≈ 3,5 MB/s, compartido** con la CPU y el DMA de audio | Asume que solo dispondrás del 60-70% |
| R8 | **Máximo 4 canales de audio** | Música: 2-3 canales. Efectos: 1-2 |
| R9 | **Nunca redistribuir** la ROM ni los assets derivados | Es material con copyright |

### R5 en detalle — CORREGIDO el 2026-09-22

> **La versión anterior de esta regla era falsa** ("el scroll por hardware NO
> existe; para mover 1 px hay que re-blitear el playfield entero"). Todo el
> análisis de D1 (opciones A/B/C, 16 colores a 25 Hz) partía de ahí.

El OCS **sí** tiene scroll horizontal fino por hardware:

```
BPLCON1 ($DFF102)  bits 0-3 = retardo PF1 (0..15 px), bits 4-7 = PF2
BPLxPT             desplazamiento grueso, en palabras (16 px)
DDFSTRT            se adelanta una palabra ($0030 en vez de $0038) para
                   leer los 16 px extra que el retardo va a meter en pantalla
BPLxMOD            = ancho_buffer - ancho_visible - 2

scroll_x:  BPLxPT = base + (scroll_x >> 4) * 2
           BPLCON1 = (15 - (scroll_x & 15)) * $11
```

Todo eso lo escribe el copper una vez por frame: **mover la imagen 1 px cuesta
cero ciclos de blitter.** Lo único que hay que blitear es la **columna de
bloques nueva** que entra por el borde: 14 bloques de 16×16 cada 16 px de
scroll, o sea menos de 1 bloque por frame a velocidad de carrera. Es la técnica
estándar de los plataformas de Amiga a 50 Hz.

Consecuencias que hay que cerrar en la etapa 4, la prueba de viabilidad (no están decididas):

- **Buffer de playfield**: un buffer circular más ancho que la pantalla (p.ej.
  pantalla + 32 px, con la columna nueva escrita dos veces o con reenganche por
  copper), en vez de redibujar.
- **DDFSTRT=$0030 quita el sprite de hardware 7** (el fetch extra usa su slot
  de DMA). Quedan 7 sprites.
- **Sprites de hardware "attached"**: dos sprites acoplados dan **15 colores**
  a 16 px de ancho. Mario puede ir por hardware y liberar al blitter (R6 dice
  "3 colores", que es solo el modo no acoplado).
- **5 planos en lowres no roban ciclos de CPU apreciables** (6 sí). 32 colores
  a 50 Hz es plausible; lo que cuesta blitter son los **bobs** (enemigos) y su
  restauración, con doble buffer.

**D1 se cerró con la etapa 4** (medido en cycle-exact): 1 px / 5 planos /
50 Hz, con scroll + 5 bobs en el 48-68 % del frame. Ver §9, "Etapa 4 —
resultados".

---

## 3. Material de partida

```
C:/Users/JC/Downloads/sma/
├── smw-src-master/          <-- ÚNICO con código fuente. Tu activo principal.
│   ├── project/mw_e10/
│   │   ├── player.s         5.702 líneas  fisica de Mario  <-- tablas clave
│   │   ├── game.s           5.557 líneas  bucle principal, HUD
│   │   ├── sprite_1-main.s  6.019 líneas  motor de sprites
│   │   ├── sprite_2-clus.s  6.932 líneas  enemigos
│   │   ├── sprite_3-1.s     7.056 líneas  enemigos
│   │   ├── lv_scroll.s      1.797 líneas  scroll de nivel
│   │   ├── tiles.s          3.403 líneas  colisiones con tiles
│   │   ├── graphics/*.lz2   52 ficheros   graficos LC_LZ2
│   │   ├── palettes/*.a     paletas BGR555
│   │   └── levels/data/     niveles YA DESCOMPRIMIDOS (.lv)
│   └── document/            ram_map.txt, graphics.txt, bug_fixes.txt
├── smwre/                   solo .exe (snesrev/smw)  - SIN FUENTES
├── smwrecomp/               solo .exe (mstan/...)    - SIN FUENTES
└── port-amiga/              <-- ESTE PROYECTO
    ├── .gitignore           repo git: solo codigo y docs; nada derivado de la ROM (R9)
    ├── AGENTS.md            este fichero
    ├── docs/                plan original, formato del nivel, pitfalls, medidas, historia
    ├── build.ps1            build / shot / run / clean (bootblock + ADF + WinUAE)
    ├── a500.uae             config CYCLE-EXACT de referencia para medir
    ├── player/              boot.s (bootblock), demo.s (stage 2), exec.i
    ├── tools/               pipeline de assets, nivel y comparacion (ver §5c)
    ├── assets-out/          salida generada
    └── work/                renders, capturas, ADF (todo regenerable)
```

**Aviso:** `smwre/` y `smwrecomp/` son binarios precompilados sin código.
No intentes extraer lógica de ellos. Si los necesitas, clona sus repositorios
(`snesrev/smw`, `mstan/SuperMarioWorldRecomp`) por separado.

**Nivel objetivo:**
```
smw-src-master/project/mw_e10/levels/data/world_1/1/
  obj.lv    283 B   objetos del nivel (formato de 3 bytes)
  obj-1.lv   55 B   objetos secundarios
  spr.lv    104 B   posiciones de sprites/enemigos iniciales
```

---

## 4. Mapa de memoria objetivo

```
$000000 - $07FFFF   CHIP RAM (512 KB)   <- accesible por CPU, blitter,
                                            copper, Denise y Paula
$BFD000 - $BFDFFF   CIA-A
$BFE001 - $BFEFFF   CIA-B
$C00000 - $C7FFFF   SLOW RAM (512 KB)   <- SOLO CPU (expansion A501)
$DC0000             reloj RTC (no existe en A500)
$DFF000 - $DFF1FF   registros de los chips custom
$F80000             Kickstart ROM (no la usaremos: bootblock propio)
```

### Reparto dentro de nuestro programa

**Chip RAM (presupuesto 512 KB, planificado ~168 KB):**

| Bloque | Bytes | Alineación |
|---|---|---|
| Playfield 272×224 × 4 planos (margen de scroll) | 30.464 | 8 bytes |
| Barra de estado 320×32 × 2 planos | 2.560 | 8 bytes |
| Tiles del jugador (`chr`, 744 tiles × 32 B — es Mario, no objetos, P6) | 23.808 | 8 bytes |
| Tileset del nivel (tileset 7 = `obj-2`+`obj-5`+`bg-3`+`obj-3`, 512 tiles; mejor **pre-renderizado a bloques Map16 de 16×16**: la capa 1 usa **80 bloques únicos** (medido) × 128 B a 4 planos) | 10.240 | 8 bytes |
| **Segundo playfield para doble buffer de bobs** (no estaba presupuestado) | 30.464 | 8 bytes |
| Gráficos de sprites + máscaras | ~33.000 | 8 bytes |
| Muestras de audio (PCM 8 bits) | ~64.000 | 2 bytes |
| Listas de copper + punteros + tablas | ~10.000 | 4 bytes |

**Slow RAM (512 KB, uso libre):**

| Bloque | Bytes |
|---|---|
| Código 68000 (hoy corre en chip; moverlo aquí libera chip RAM pero **no lo acelera**, P29) | ~60.000 |
| Tilemap del nivel (16×16 celdas) | ~4.000 |
| Tablas de objetos y sprites | ~8.000 |
| Tablas de física 8.8 | ~2.000 |
| Buffers de descompresión / trabajo | ~32.000 |

**Regla de oro:** si el blitter o el copper tienen que leerlo, va en chip RAM.
Sin excepciones.

### Mapa medido del juego (`player/game.s`, 2026-09-27)

Lo de arriba era el plan; esto es lo que usa hoy el primer ADF jugable.
**Hace falta la expansión A501**: el binario solo, más los datos del scroll,
PF1 y las dos listas no entran en 512 KB de chip.

| dónde | bloque | bytes |
|---|---|---|
| chip | `yi1_s.dat` (bloques, capa 2, colores, plan del copper; `D_*`) | 223 600 |
| chip | PF1: buffer circular (`BUF1`) | 59 136 |
| chip | 2 listas del copper con `-DSPRITES` (`CL_SIZE` = 216 + 220 × 224 + 4) | 2 × 49 500 |
| chip | sprites de Mario: 2 buffers × 4 sprites × 84 palabras + nulo (12 B desde el 2026-10-03) | 1 356 |
| chip | pantallas del modo diagnóstico (`DG_SIZE`, P58) + 64 B por lista | 11 528 |
| chip | **total del juego** | **≈ 395 KB** |
| slow | el binario (se copia solo desde la chip de `boot.s`, que se libera); en vivo, con el historial del joypad del diagnóstico | 187 188 (replay: 181 916) |
| slow | copia de los datos del C y del mapa (reinicio del nivel, en vivo) | 11 748 + 17 280 |

Dentro del binario (`work/live/game.lst`): cabecera `A5PL` → datos del C
(`smwrom00` + `cdata0..cdata1` = `$401C-$6E00`: **tienen que quedar a
menos de 32 KB de `binstart`**, P36) → código del C, `logic68k.s`,
`mspr68k.s` → `scroll.s` (`SCROLL_LIB`) → código del juego (`entry` en
`$1101C`) → `map16` (17 280), `spr.lv`, `mario_pal.bin` (256),
`gfx32.bin` y `gfx32f.bin` (2 × 23 808), `yi1_replay.bin` (42 058). El ADF
ocupa 412 KB de 880 KB (46 %), medido el 2026-09-30.

---

## 5. Assets y formato del nivel (etapas 1-2 — HECHAS)

Detalle completo, textual: **`docs/formato-nivel.md`** (pipeline y
profundidades de color, formato `.lv`, Map16, tileset → GFX → VRAM, los 92
handlers, el cursor de bloques, los blends, la comparación contra
`SuperMarioWorldMap02.png` y sus herramientas, el layout de paletas).

Lo esencial:

- `tools/smw2amiga.py --all --selftest --planes 4` convierte los 52 `.lz2`
  (auto-test planar 52/52). Profundidades: `chr` y `boss-6` = 4 bpp, `gb-1..5`
  = 2, el resto 3 (P6). Verificar siempre mirando el PNG.
- El buffer del nivel guarda **índices Map16 de 9 bits** (`valor | página <<
  8`), no tiles (P9b, P10b). Las 4 palabras de una entrada van en
  column-major: TL, BL, TR, BR (P12); cuadrante vacío = palabra `$0000` (P13).
  Tileset 7 = obj-2 + obj-5 + bg-3 + obj-3, orden invertido (P11).
- Capa 1 1:1: `mklvl.py` + `m16diff.py` = **6111/6111** bloques. Comparar a
  5 bits y con `--mask none` (P20, P24).
- Paletas: `tools/palette.py` emula `LoadPalette`; el cielo no está en
  `cgram[0]` (P14); Mario desde el color 134 (P10); la moneda de Yoshi es una
  animación de paleta (P22).

---

## 6. Toolchain (la que se usa de verdad)

> Corregido el 2026-09-22: esta sección describía un flujo que el proyecto no
> usa (hunks + `xdftool` con **FFS**, `fs-uae`, Kickstart 1.3). Un disquete FFS
> **no arranca en Kickstart 1.x**, y el usuario solo tiene **KS 1.2**.

| pieza | ruta / valor |
|---|---|
| Ensamblador | `C:\Users\JC\vbcc\bin\vasmm68k_mot.exe` — `-Fbin -m68000 -no-opt` |
| C (cuando haga falta) | vbcc `+kick13` (sin libc; ver §7) |
| Python | `C:/Users/JC/.workbuddy-ai/binaries/python/envs/default/Scripts/python.exe` (Pillow, **sin numpy**) |
| Emulador | WinUAE `C:\Program Files\WinUAE\winuae64.exe` |
| Kickstart | **1.2**, `C:\Users\JC\Downloads\amivideo\kick12.rom` |

**Arranque:** sin AmigaDOS ni hunks (`HUNK_RELOC32SHORT` da "error 121" en KS
1.x). `player/boot.s` es un bootblock propio que lee el stage 2 en crudo con
`trackdisk.device` a chip RAM y salta; `tools/mkadf.py` arma el ADF.

```powershell
.\build.ps1 build            # boot.bin + demo.bin + demo.dat -> work\smw.adf
.\build.ps1 shot             # build + WinUAE + captura PNG (config RAPIDA)
.\build.ps1 run              # build + WinUAE interactivo
```

**Banco de pruebas de rendimiento (etapa 4):**

```bash
vasmm68k_mot -Fbin -m68000 -no-opt -I player -o work/bench.bin player/bench.s
python tools/mkadf.py --boot work/boot.bin --stage2 work/bench.bin --out work/bench.adf
```
```powershell
.\tools\shot.ps1 -Exact -Adf work\bench.adf -Out work\bench.png -Wait 80
```
```bash
python tools/bench_read.py --shot work/bench.png    # tabla en ms / lineas / % de frame
```

La Amiga mide con el timer A de CIA-B y escribe los resultados en pantalla como
bits; `bench_read.py` los decodifica y comprueba dos palabras de sincronía.
Para medir algo nuevo: añadir una rutina `workN` y una fila más.

**Dos configuraciones de emulador, con usos distintos:**

| config | para qué | por qué |
|---|---|---|
| `tools/shot.ps1` (y `build.ps1 shot`, que lo llama) | capturas y verificación visual | `cpu_speed=max`, `immediate_blits=true`: rápida, **tiempos falsos** |
| `tools/shot.ps1 -Exact` | capturas **con temporización real**; lo que hay que usar para medir | mismos valores que `a500.uae`: `cycle_exact=true`, `cpu_speed=real`, `immediate_blits=false` |
| `a500.uae` | sesiones interactivas en WinUAE (ROM y ADF se eligen a mano) | referencia de la config cycle-exact |

`shot.ps1` borra la captura anterior, espera a que la ventana tenga contenido y
sale con código 1 si no pudo capturar: `verify_shot.py` nunca compara una
imagen vieja.

Limitación del entorno: la herramienta PowerShell de este entorno no ejecuta
binarios nativos ni devuelve stdout. Compilar con bash (vasm + python) y usar
PowerShell solo para WinUAE + captura (`tools/shot.ps1`); los scripts escriben
logs en `work/*.log`.

> **"Arrancar sin Kickstart" no existe:** la A500 siempre arranca por el
> Kickstart de la ROM, que es quien carga el bootblock. Lo que hacemos es
> **tomar el control** después (`LoadView(0)`, `WaitTOF`, DMA propio). Lo que
> ocupa el SO en ese momento son decenas de KB, no ~256 KB, y se recupera al
> tomar la máquina.

---

## 7. Convenciones de código

### Reparto de responsabilidades

| Lenguaje | Para qué |
|---|---|
| **68000 asm** | rutinas de blitter, listas de copper, ISR del VBL, cambio de contexto |
| **C** | física, colisiones, IA de sprites, máquina de estados, HUD |

### Convenciones de ensamblador

- **ABI (la de vbcc/AmigaOS):** `d0/d1/a0/a1` son de trabajo y los destruye
  cualquier llamada; `d2-d7`/`a2-a6` los preserva quien los use. Vale para
  llamadas a librerías del sistema **y** para toda rutina asm llamada desde C.
  (Corregido 2026-09-22: esta sección decía "preservar `a2-a4`", que dejaba
  fuera `a5`/`a6`, y `demo.s` guardaba GfxBase en `a0` a través de `LoadView`.)
- **Registros con dueño en el código actual:** `a4` = `CUSTOM` (`$DFF000`),
  `a6` = ExecBase mientras se usa el SO; recargar siempre de `4.w`, nunca
  confiar en que sobrevivió. No reservar registros "globales" entre C y asm:
  vbcc usa `a5` de frame pointer y `a4` para el modelo small-data.
- El stack nunca baja de `$800`.
- Las direcciones de los chips custom se acceden vía `a4` con offset, nunca
  con literales absolutos.
- **El código no se acelera moviéndolo a `$C00000`** (P29).

### Convenciones de C

- Sin `malloc`. Sin libc completa. Solo lo que escribas.
- Tipos: `u8`, `s8`, `u16`, `s16`, `u32`, `s32`. Nada de `int` a secas.
- Punto fijo 8.8 para toda la física (igual que la SNES): `typedef s16 fix88;`
- Prohibido `float`/`double` — no hay FPU.

### Alineación (crítico)

- Bitplanes y tilesets: **8 bytes** (los blits son por palabra)
- Listas de copper: **4 bytes**
- Muestras de audio: **2 bytes**

### Estilo de comentarios

En español. Cada rutina de hardware (blitter/copper) lleva arriba:
```
; --- nombre_rutina ---
; entrada:  a0 = ...
; salida:   d0 = ...
; registros destruidos: d0-d3
; ciclos:   ~N (medido en emulador)
```

---

## 8. Pitfalls conocidos

Índice, una línea por trampa. **El texto completo (causa, síntoma, arreglo y
comandos) está en `docs/pitfalls.md`, textual**: leer ahí las del área que se
toca antes de cambiar nada. Una trampa nueva se agrega allí y aquí con el
número siguiente (**la próxima es P103**).

- **P1** El layout de paletas de SMW no es un array 8×16. ✅ RESUELTO
- **P2** El blitter tiene prioridad sobre la CPU y la "roba" ciclos
- **P3** Las listas de copper deben estar en chip RAM y alineadas a 4 bytes
- **P4** Los punteros de bitplane deben ser múltiplos de 2
- **P5** Los back-references de LC_LZ2 apuntan a offsets ABSOLUTOS
- **P6** `chr.lz2` no es lo que dice la documentación
- **P7** Las muestras de audio en Paula son PCM de 8 bits FIRMADO
- **P8** El slow RAM de la A501 no está disponible si el software lo desactiva
- **P9** `document/graphics.txt` usa IDs de fichero, no nombres
- **P9b** El buffer Map16 guarda ÍNDICES Map16, no tile numbers
- **P10** La paleta del jugador no viene de `LoadPalette`
- **P10b** El índice Map16 incluye el bit de página
- **P11** El orden de los bloques GFX está invertido respecto a la lista
- **P12** Las 4 palabras de una entrada Map16 van en column-major, no raster
- **P13** El cuadrante vacío es la palabra `$0000`, no `tile == 0`
- **P14** El color de fondo del nivel no está en `cgram[0]`
- **P15** Los handlers de objeto no comparten la página
- **P16** Los handlers NO escriben todos con `CODE_0DA95B`
- **P17** `down_left`/`down_right` cambian de PANTALLA al dar la vuelta
- **P18** `DATA_0DB72F` y compañía son ÍNDICES Map16, no tile numbers
- **P19** La capa de fondo (layer 2) no la dibujamos, y domina la métrica
- **P20** `--mask mine` NO es comparable entre versiones nuestras
- **P21** El bug de Nintendo en `CODE_0DB7AA` hay que REPRODUCIRLO (corregido 2026-09-22)
- **P22** El color de la MONEDA DE YOSHI es una animación de paleta, no $7C3F
- **P23** La moneda de Yoshi también anima sus TILES
- **P24** `render()` dibujaba con paso de 8 px por bloque (corregido 2026-09-22)
- **P25** `restore()` NO devuelve el cursor al punto guardado
- **P26** Una celda vacía vale `$25` en el ROM, no 0
- **P27** Leer las tablas `.DB` del handler ANTES de contar bucles
- **P28** El ROM reapunta entradas Map16 según el tileset y la PANTALLA
- **P29** El "slow RAM" de la A501 comparte el bus del chipset
- **P30** `tools/shot.ps1` sin `-Exact` no sirve para medir
- **P31** Cada blit cuesta ~42 µs de CPU además de los datos
- **P32** Con 5 planos los sprites de hardware comparten los colores 16-31
- **P33** `wm_BlockXPos` guarda la Y y `wm_BlockYPos` la X
- **P34** Golpear un bloque cambia el MAPA después, en la fase de sprites
- **P35** Los gráficos de Mario se calculan ANTES que su física
- **P36** vbcc `-sd`: los datos tienen que estar a menos de 32 KB de `a4`
- **P37** vbcc incorpora en línea las funciones `static`
- **P38** vbcc `-O=991` puede sumar dos veces la base de un puntero
- **P39** En DPF, un WAIT del copper gasta una ranura igual que un MOVE
- **P40** En 68000, `(An,Dn.w)` suma el índice CON signo
- **P41** Una captura de FS-UAE con tiempo fijo puede no estar donde se cree
- **P42** En DPF de 6 planos, el WAIT del copper tiene rejilla de 8 px, no de 4
- **P43** El borrado deja al copper libre ~60 px ANTES de x = 0
- **P44** Los "derrames" de la etapa 5 alargan el tramo anterior
- **P45** Una carga cortada por `LASTX` tiene que bajar el `vu` de la línea
- **P46** A 256 px (DIW `$2CA1`, fetch `$40`-`$C0`) el copper es otro modelo
- **P47** vbcc también emite direcciones absolutas sin avisar al tomar la dirección de un array `static` o al inicializar un puntero
- **P48** En el banco, lo que va delante de los datos del C los corre
- **P49** `logicbench`: una carga que toca `a4` tiene que guardarlo
- **P50** `build_mid`: una carga que no vale ni en la s en que se escribe
- **P51** Después de `DDFSTOP` el copper va más rápido (8 px por MOVE desde x = 239 a 256 px; arreglado 2026-10-05)
- **P52** `game.s`: el código del juego queda a más de 32 KB de `binstart`
- **P53** `mspr_draw` destruye d2
- **P54** vbcc y el dibujo genérico: 300 000 ciclos
- **P55** "Recién apretado" contra la RAM del juego (RESUELTO 2026-09-30)
- **P56** La herramienta Bash rompe las barras invertidas en los heredoc
- **P57** Capturas ×2 de WinUAE: muestrear el centro del píxel
- **P58** En vivo, lo no portado congela el juego y lo explica (2026-09-30)
- **P59** Un WAIT del copper en la línea 255 con h ≥ ~`$E0` no llega nunca
- **P60** `ControllerUpdate` de SMW (`game.s:708`)
- **P61** `build_sign` se calcula en `entry` ANTES de escribir los punteros del C
- **P62** El vbcc de cloud también compila mal código que esquiva P38
- **P63** `Scc` después de un `MOVE` lee un C ya borrado
- **P64** El máximo de ciclos de `m68kverify` era una inicialización
- **P65** Los sprites que ya están al empezar un tramo los crea la carga del nivel
- **P66** Congelamientos que pone un sprite
- **P67** La ROM que emula snesrev/smw NO es la original
- **P68** El oráculo se toma antes del NMI y el mando se lee en el NMI
- **P69** Lo que el oráculo no recorre puede estar mal aunque todo dé 100 %
- **P70** Las "colinas" de YI1 son cornisas
- **P71** Una carga "tarde" que vale con la base desplazada rompe la ida = vuelta
- **P72** La base de `build_mid` hace el scroll asimétrico
- **P73** `tst` con `(pc)` no existe en el 68000
- **P74** Tablas grandes dentro de `scroll.s` rompen `game.s`
- **P75** `-DSTOPF` cuenta desde el primer frame del replay, no es el frame del oráculo
- **P76** `fsuae_shot.sh` en paralelo
- **P77** `lvparse.py` leía mal los bytes 2 y 4 de la cabecera (arreglado 2026-09-30), y YI1 SÍ tiene scroll vertical
- **P78** vbcc y los `spr_*.c` (I1, 2026-09-30)
- **P79** `cmp.b`/`bhs` es sin signo, y un registro reusado arrastra valor (L1a)
- **P80** `game.s -DBENCH` (O1)
- **P81** El pico de los postes de la meta no baja agrupando (S1a+S2)
- **P82** La PC Windows (2026-09-30)
- **P83** Guiones de snesorc
- **P84** La cámara vertical de YI1 solo se mueve con `$13F1` (`wm_EnableVertScroll`) ≠ 0
- **P85** Datos de sprites de las grabaciones
- **P86** Verificadores contra snesorc (P1, P2, P4)
- **P87** Transcribir sprites (P3, P4, P5)
- **P88** asm del 68000 con vasm (L1c, MA1)
- **P89** Editar las listas del copper en el sitio no conviene en el 68000 (S4)
- **P90** Guiones de snesorc, más (P5, RB)
- **P91** El binario del juego y el arnés de Musashi (ola 3)
- **P92** Lo que `regress.py` no cruza (L1b)
- **P93** Animaciones de Mario y el juego en vivo (P8)
- **P94** vasm: una etiqueta global corta las locales (SX)
- **P95** Grabaciones (RC)
- **P96** El factor del DMA no es uniforme (O1 en WinUAE)
- **P97** O5, el render desacoplado: buffers de la foto, la lógica en la línea 272
- **P98** Rutinas de gráficos que escriben la OAM (G8)
- **P99** Gráficos de sprites: plano 3 del GFX 01, 16×16 y bit 8 (G3a)
- **P100** Columnas de sprite: 2-3 libres, el Rex mide 20 px (G1/G0)
- **P101** `poke` en snesorc no lo ve el port (R10)
- **P102** vasm relaja llamadas lejanas a absolutas; comprobar el listado (SPR_OAM)

---

## 9. Decisiones

| ID | Decisión | Opciones | Estado |
|---|---|---|---|
| D1 | Compromiso de scroll/color/frecuencia | **1 px (`BPLCON1`) / 5 planos, 31 colores / 50 Hz** | **cerrado** con la etapa 4: scroll + 5 bobs = 48-68 % del frame. **Confirmado por el usuario el 2026-09-30: 50 Hz, haciendo todo lo posible**; 25 Hz solo si agotada la optimización no entra (ROADMAP §3) |
| D2 | Nivel objetivo | **Yoshi's Island 1** (`world_1/1/`) | cerrado |
| **D3** | Enemigos del demo | Los que tiene el nivel de verdad (`spr.lv`, ver abajo). **Goomba y Koopa Troopa NO aparecen en Yoshi's Island 1** | **corregido** — mínimo: Rex + Banzai Bill + Jumping Piranha |
| D4 | Lenguaje principal | C para lógica + asm para hardware | cerrado |
| **D5** | Música | **secuenciador propio** sobre las secuencias N-SPC convertidas offline (no MOD), sin mezcla por CPU, 3 voces de música + 1 de efectos, ≤ 64 KB de muestras, ≤ 3 % de CPU | **cerrado** (usuario, 2026-09-26); detalle en `ROADMAP.md` §3 |
| D6 | Arranque | **bootblock propio** leyendo sectores crudos; funciona en KS 1.2 y 1.3 | cerrado |
| D7 | Color de las tuberías verticales | — | **cerrado**: depende de la pantalla (`MAP16AppTable`), ver P28 |
| **D8** | Cómo existe la capa 2 (fondo) en la Amiga | **(d) dual playfield + recarga de colores a mitad de línea con el copper**: capa 1 = PF1 (3 planos, índices fijos por línea del nivel), capa 2 = PF2 (3 planos, paralaje por hardware), Mario y enemigos = sprites de hardware con colores 17-31 recargados por línea, bob en PF1 cuando hay más de 4 columnas. Las demás opciones y sus medidas, en §9 "Etapa 4 — resultados" puntos 4-10 | **cerrado** (usuario, 2026-09-23) |
| D9 | Presupuesto de color | Vista real: **25 colores por línea, 40 por pantalla** (capas + sprites) | **cerrado**: 5 planos + paleta recargada por bandas con el copper. Ojo con P32 (los sprites comparten los colores 16-31) |
| **D10** | Ancho de pantalla | **256 px**, como la SNES (el scroll de hoy muestra 320) | **cerrado** (usuario, 2026-09-26): encuadre y aparición de enemigos 1:1, vuelve el sprite 7, 20 % menos de DMA |
| **D11** | HUD | **superpuesto (overlay)** con el copper sobre PF1 | **cerrado** (usuario, 2026-09-26), "si se puede": ver `ROADMAP.md` Etapa 10 |
| **D12** | Power-ups | **todos los de Yoshi's Island 1**: seta, flor + bolas de fuego, estrella, 1-UP, luna 3-UP, champiñón invisible (no hay pluma en el nivel) | **cerrado** (usuario, 2026-09-26) |
| **D13** | Carga y memoria | loader propio con `trackdisk`; lo que lee el chipset a chip RAM y el código y los datos de CPU a `$C00000`, todo en **direcciones fijas enlazadas en absoluto** (vlink) | **cerrado** (usuario, 2026-09-26); esquema en `ROADMAP.md` §3 |
| **D14** | Controles | **teclado primero** (flechas, Z = B, X = A, A = Y, S = X, Return = Start, Shift der. = Select), joystick como alternativa | **cerrado** (usuario, 2026-09-26) |
| **D15** | Velocidad (ROM NTSC en una Amiga PAL) | **se acepta el 83 %**, como la SNES PAL | **cerrado** (usuario, 2026-09-30), ROADMAP §10.12 |
| **D16** | Zona de la tubería (`obj-1.lv`, 2 pantallas) | **entra en el alcance** | **cerrado** (usuario, 2026-09-30), ROADMAP §10.10 |

### D3 — los sprites reales de Yoshi's Island 1

Leído de `levels/data/world_1/1/spr.lv` (registros de 3 bytes, byte 2 = nº de
sprite; nombres de `sprite_1-main.s`):

| sprite | nº | cuántos | nota |
|---|---|---|---|
| Rex | `$AB` | **18** | el enemigo del nivel |
| Banzai Bill | `$9F` | 4 | **64×64**: el bob más caro del proyecto |
| Jumping Piranha Plant | `$4F` | 3 | sale de las tuberías |
| Info Box | `$B9` | 2 | mensaje de texto |
| Clappin' Chuck | `$95` | 1 | |
| Sliding Koopa sin caparazón | `$BD` | 1 | |
| Bloque `?` volador (izquierda) | `$83` | 1 | |
| Bloques "warp hole" invisibles | `$8E` | 1 | sin gráfico |
| Champiñón invisible | `$C7` | 1 | sin gráfico |
| Caparazón de Koopa rojo, quieto | `$DB` | 1 | `sprite_2-clus.s:_02A971`: `$DA`-`$DF` se cargan con estado 9 y nº `id - $DA + 4` → `$05` (Red Koopa) |
| Cinta de meta | `$7B` | 1 | |

El gráfico de Rex y Banzai Bill es el GFX `20` (`graphics.txt:40`), no `spr-2`.

### Datos medidos de las decisiones

Textuales en **`docs/decisiones-medidas.md`**: "D8/D9 — datos medidos",
"Etapa 4 — resultados" (puntos 1-10: capa 2, colores, blitter, opciones de
D8, cómo lo hicieron otros juegos del OCS, la opción (d) simulada y medida,
objetos, copper, CPU y blitter) y "D7 — cómo se cerró". Las referencias
"AGENTS.md §9, etapa 4 punto N" del código apuntan ahí.

---

## 10. Roadmap

El plan vigente es **`ROADMAP.md`**. La tabla de etapas original de este
fichero (2026-09-22) y los handoffs del 2026-09-24 ("Dónde quedó el trabajo"
y "Handoff cloud → sesión local") están textuales en **`docs/historia.md`**.

---

## 11. Verificación (definición de "hecho")

Ninguna etapa se marca como completada sin **las tres**:

1. **Test automático.** Para assets: `smw2amiga.py --selftest` debe dar
   `Auto-test planar: TODO OK`. Para código: un test que compare el estado
   de la física contra los valores esperados de las tablas de `player.s`.
2. **Evidencia visual.** Captura del emulador (o PNG de la pipeline) donde se
   distinga claramente lo que se pretendía dibujar. **Y para el nivel, comparar
   1:1 contra `SuperMarioWorldMap02.png`** (ver §5c): mismo recorte apilado,
   referencia arriba, nuestro render abajo.
3. **Medida de rendimiento.** Cuando aplique, ciclos por frame medidos con el
   contador del emulador. No se acepta "parece que va fluido".
   **Solo vale una medida hecha con `a500.uae`** (`cycle_exact=true`,
   `cpu_speed=real`, `immediate_blits=false`). El `.uae` que genera
   `build.ps1` para las capturas usa `cpu_speed=max` e `immediate_blits=true`:
   sirve para ver la imagen, **no** para medir tiempos.

### Regla de diagnóstico (aprendida a la mala)

Si algo sale "garbled" pero **en la posición correcta**, el problema está en la
cadena de indirección (orden de cuadrantes, página, paleta, índice), **nunca**
en la geometría. No tocar el código de posiciones: aislar el objeto, renderizar
su tabla/entrada aislada y comparar. En esta sesión las tuberías estaban en el
lugar exacto y fallaban tres cosas distintas de la indirección a la vez.

### Comprobaciones rápidas

```bash
# ANTES DE CADA COMMIT (ROADMAP.md §8): reglas estáticas + regresión completa
python3 tools/lint_port.py && python3 tools/regress.py

# ¿la capa 1 sigue 1:1?  (regresion: tiene que dar 100 % y 0 erroneos)
$PY tools/mklvl.py --out work/level_final.png && $PY tools/m16diff.py
$PY tools/cmp_ref.py --mask none --bits 5      # hoy 25.52 %; baja solo con capa 2

# ¿cabe en chip RAM?
$PY -c "print('playfield', 272*224*4//8, 'B')"

# ¿el fichero convertido tiene el tamano esperado?
#   n_tiles * 8 filas * (cols*8/8) bytes * planos
```

---

## 12. Antipatrones prohibidos

- **Portar las 82.000 líneas de 65816.** No. Reimplementa el nivel 1.
- **Usar el CPU para dibujar píxeles.** Todo el dibujado va por blitter.
- **Poner gráficos en slow RAM.** El chipset no los verá (R2).
- **Asumir que existe scroll por hardware.** No existe (R5).
- **Asumir que el layout de paletas es un array plano.** No lo es (P1).
- **Usar `float`.** No hay FPU. Punto fijo 8.8.
- **Copiar código de `smwre`/`smwrecomp`.** No tienes sus fuentes.
- **Redistribuir assets derivados de la ROM.** (R9)

---

## 13. Nota legal

El decompilado exige poseer el juego original, y el propietario lo tiene.
Un port-demo personal no es un problema. Distribuir la ROM o los assets
convertidos (gráficos, música) **sí** sería redistribución de material con
copyright. Este proyecto es de uso personal.
