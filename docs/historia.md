# Historia: handoffs y planes superados

> Movido textual el 2026-10-03 desde `AGENTS.md` (los handoffs del 2026-09-24 y la
> tabla de etapas original de §10) y desde `ROADMAP.md` §1 (el día a día de las
> olas 1-3). Es historial: lo vigente está en `ROADMAP.md`. Sirve para saber
> por qué algo es como es y con qué números se decidió.

---

## AGENTS.md: handoffs del 2026-09-24

## Dónde quedó el trabajo (2026-09-24, tarde)

> Superado por `ROADMAP.md` §1 (handoff del 2026-09-26). Se deja como detalle
> de lo medido y de los comandos.

**Etapa 8: el frame entero del jugador está portado y verificado contra el
oráculo**, en el PC y en el binario 68000 real. Todo corre en Claude cloud
(ver más abajo).

| parte | fichero | rutinas del ROM | verificación |
|---|---|---|---|
| 8a física | `player/mario.c` | `D5F2`, `D062`, `D7E4` | `marioverify` (modo 8a) |
| 8b colisión con la capa 1 | `player/mcoll.c` | `CD24`: `DC2D`, `E92B` (sondas, pendientes, bloques), `F595`; `GenerateTile`; bloques que rebotan `CODE_028752` / `CODE_02902D` | `marioverify ... full` |
| frame del jugador + animación | `player/manim.c` | `C500` (temporizadores), `ResetAni`, scroll L/R `CDDD`, `CEB1` | `marioverify ... full` |
| gráficos de Mario | `player/mgfx.c` | `E2BD`, `E45D`, `F636` | `marioverify ... gfx` |
| cámara + frame de nivel | `player/mcam.c`, `level_frame()` en `manim.c` | `F6DB` (`F7F4`, `F8AB`), principio de `01808C`, orden de `A295` | `marioverify ... loop` |

Resultados (`work/oracle_yi1.txt`, 6547 pares de frames de Yoshi's Island 1):

- **`full`: 6510 / 6547 pares exactos en 24 campos** (posición, subpíxel,
  velocidades, `$77`, suelo, `$72`, pendientes, dirección, agachado, carrera,
  giro, `FrameB`, pose, paso, temporizadores de animación, capa). De N+1 solo
  se toman las **entradas**: joypad, `FrameA` y la cámara (`$1A-$1D`, que
  todavía no está portada). Los 37 que fallan son **todos contacto con
  sprites** (etapa 9): 23 sobre un sprite sólido y 14 al pisar o golpear un
  enemigo (`SpeedY` = `$D0` / `$10`).
- **`gfx`: 6869 / 6869 frames con la OAM de Mario y `MarioScrPosX/Y`
  exactas** (13 432 entradas de OAM en 6718 frames con Mario visible).
- **`loop` (lazo cerrado): el port reproduce la partida él solo**, desde el
  primer frame de cada tramo y recibiendo **solo el joypad** (la cámara, el
  `FrameA`, todo lo demás lo calcula). Tramo más largo: **1240 frames
  seguidos idénticos** (~25 s). Se resincroniza 37 veces en 6547 frames:
  exactamente los contactos con sprites. El binario 68000 da lo mismo.
- Las pendientes de la partida (42 frames que antes fallaban) ya salen
  exactas: buena parte de la **8c** está hecha, pero falta la grabación de
  las colinas para darla por cerrada.
- **El binario 68000 de vbcc da exactamente lo mismo que el C del PC**
  (`tools/m68kverify.py`, Unicorn y Musashi).

Coste estimado de un frame de nivel sin sprites (`level_frame`: cámara,
`E2BD`, jugador, bloques) en un 68000 **sin esperas de DMA** (Musashi):
**34 529 ciclos de media = 24,3 % de un frame PAL; peor frame 38 712 =
27,3 %**. Solo el jugador (`E2BD` + `mario_player` + `blocks_update`): 26 674
de media (18,8 %). Con
el DMA de 6 planos será más. Dónde se va (`tools/m68kprof.py`): las sondas
de colisión (`f44d` + `f461` + `f545`, 5,5 por frame) ≈ 28 %, las 4 entradas
de OAM (`e45d`) ≈ 12 %, `E2BD` ≈ 9 %, los bucles de temporizadores de
`mario_player` ≈ 8 %. Es código "emulador" (valores de 16 bits armados byte
a byte en `ram[]` little-endian): hay margen de optimización, y el
verificador asegura que no se rompe nada.

**8d, MEDIDA (2026-09-24, en cloud con FS-UAE cycle-exact):** un frame de
nivel sin sprites (`level_frame`: cámara + gráficos + jugador + bloques),
con la pantalla DPF de 6 planos encendida y el código en chip RAM:

| estado | ticks CIA | ciclos | % de un frame PAL |
|---|---|---|---|
| corriendo (frame 5410) | 4857 | ~48 600 | **34,2 %** |
| empieza un salto (frame 10983) | 5065 | ~50 700 | **35,6 %** |

Musashi, sin DMA, estimaba 24,3 % de media: el resto es contención (DMA de
6 planos, código en chip RAM).

Primera ronda de optimización (sin cambiar la semántica: el verificador en
PC y en 68000 sigue exacto): tablas del ROM con índice de 8 bits
(`T8X`/`T16X`), temporizadores y OAM por puntero, las sondas pasan X/Y en
variables. **Queda en 31,6 % corriendo y 32,9 % saltando** (Musashi: 31 972
ciclos, −7,4 %). Lo que queda ya no son descuidos: es el precio de emular la
RAM de la SNES byte a byte (cada valor de 16 bits son 2 lecturas + `lsl` +
`or`, ~50 ciclos) y de las tablas leídas de a bytes.

**Implicación para D1 (decisión del usuario):** el presupuesto conservador
del peor frame de vídeo era 58 % (§9 punto 10); con el jugador (~33 %) ya
son ~91 %, y faltan los sprites (etapa 9: 18 Rex, Banzai Bill...). A 50 Hz
no entra sin una optimización de otro nivel. Opciones: (1) reescribir las
rutinas calientes con el estado de Mario en variables nativas del 68000 (y
seguir verificando contra el oráculo), (2) bajar a 25 Hz (lógica cada 2
frames: la previsión de §9 D1), (3) ensamblador a mano en las sondas y la
OAM. Mover el código a slow RAM no ayuda (P29). Se repite con:

```bash
sh tools/logicbench_build.sh && sh tools/fsuae_shot.sh work/logicbench.adf work/logicbench.png 30
python3 tools/logicbench_read.py --shot work/logicbench.png --auto
```

**FS-UAE en cloud (`tools/fsuae_shot.sh`) sustituye a WinUAE para medir.**
A500 por defecto de FS-UAE = cycle-exact (`cpu_cycle_exact`,
`blitter_cycle_exact`, `cpu_speed=real`, `immediate_blits=false`), 512 KB
chip + 512 KB slow; sin Kickstart propio usa el AROS que trae dentro, que
arranca nuestro bootblock (lo que se mide toma la máquina después).
Validación: `bench2.s` da W1 5,5-6,2 %, W2 38,1 %, W3 47,5/33,7 %, contra
5,6-6,4 / 38,1 / 47,6-33,8 % en WinUAE; la calibración, 14 210 ticks por
frame, es la misma. Las capturas salen a ×2,125: los `*_read.py` tienen
`--auto`, que encuentra la rejilla de bits por las palabras de sincronía.
**Lo que no sirve para probar en FS-UAE+AROS: el arranque en KS 1.2.**

**Después (todo se puede hacer en cloud):**

1. Optimizar el frame del jugador con el verificador como red (`marioverify
   full/loop`, `m68kverify`) y midiendo con FS-UAE: sondas de colisión,
   `e45d`, temporizadores, cámara.
2. Etapa 6: el scroll en la Amiga con el blob de la etapa 5
   (`work/yi1_d.dat`, formato en la cabecera de `tools/mkleveld.py`) y la
   cámara ya portada (`player/mcam.c`).
3. Etapa 9 (sprites): son los 37 frames que faltan en `full` y `loop`.
4. 8c: el usuario graba las colinas (ver el grabador más abajo).

**En Claude cloud, primero correr `sh tools/setup_cloud.sh`** (~15 s). Deja
todo listo para compilar **y verificar**:

- vasm y vbcc para el 68000, desde espejos de GitHub (la red del entorno no
  deja bajar de `sun.hasenbraten.de` ni de `phoenix.owl.de`);
- las librerías de Python (numpy, pillow, scipy);
- el fuente de SMW, clonado desde https://github.com/galaxyhaxz/smw-src en
  `../../smw-src-master`, que es donde lo busca `smwgen.py`;
- **la ROM (U), ensamblada desde ese fuente** en `work/smw.sfc`: WLA-DX del
  2016-07-29 (misma fecha que el `wla-65816.exe` de smw-src) con `DL` en
  `.ENUM`, más `tools/smwsrc_wla.py`, que traduce las etiquetas `@` y el
  `.ASC "...\n"` de la WLA modificada. El script comprueba **CRC32
  `B19ED489`** = Super Mario World (U) [!];
- `player/gen/*`, el mapa `work/yi1_map16.bin` (`tools/mkmapbin.py`),
  `work/oracle_yi1.bin` + `work/oracle_yi1_oam.bin`, `work/marioverify` (y
  `work/mvtrace`, con traza de las sondas) y los estados de `logicbench`;
- Unicorn y machine68k (Musashi) para `tools/m68kverify.py` y
  `tools/m68kprof.py`.

Comprobaciones (todas en cloud):

```bash
work/marioverify work/oracle_yi1.bin            # 8a sola (modo híbrido antiguo)
work/marioverify work/oracle_yi1.bin full       # frame del jugador: 6510/6547
work/marioverify work/oracle_yi1.bin gfx        # gráficos de Mario: 6869/6869
work/marioverify work/oracle_yi1.bin loop       # lazo cerrado: 37 resincronizaciones (sprites)
work/marioverify work/oracle_yi1.bin sprload    # cargador de sprites: 20/20
work/marioverify work/oracle_yi1.bin sprloop    # Rex en lazo cerrado: 2411/2412
work/marioverify work/oracle_yi1.bin game       # Mario + Rex: 26 resincronizaciones, tramo 2711
python3 tools/m68kverify.py --engine musashi --mode loop   # lo mismo en 68000 + ciclos
python3 tools/mkbg.py && python3 tools/mkd8in.py && python3 tools/mkleveld.py && python3 tools/render_d.py
FULL_FRAME=11180 work/mvtrace work/oracle_yi1.bin full   # un frame, con las sondas
sh tools/logicbench_build.sh                    # (VBCC=~/vbcc) binario 68000 + ADF
python3 tools/m68kverify.py --engine musashi    # el binario 68000 contra el oráculo + ciclos
PROF=1 sh tools/logicbench_build.sh && python3 tools/m68kprof.py   # perfil por función
```

Comprobado el 2026-09-24 en cloud: `marioverify` (modo 8a) da exactamente
los números del handoff de la PC (2989/3497 en el aire, 2962/3050 en el
suelo) y `logicbench_build.sh` arma el ADF.

**Qué no está en git y cómo recuperarlo** (regla R9):

- `work/` no se versiona (salvo `oracle_*.txt` y `oam_*.txt`): ahí van la
  ROM, los `.bin` del oráculo, los ADF y los renders.
- `player/gen/smwrom00.c` tampoco. Se regenera con `python tools/smwgen.py`,
  que necesita la ROM (U).
- En Claude cloud no hay WinUAE, ni KS 1.2, ni `smwrecomp`: se compila, se
  verifica contra el oráculo y **se mide con FS-UAE + AROS**; lo que queda
  para la PC local es grabar partidas (8c: las colinas) y probar el
  arranque en KS 1.2.
- El grabador tiene límites que ya costaron partidas: 1024 caracteres por
  valor, 16 valores por respuesta y una sola conexión TCP. **Probar siempre
  el grabador antes de pedirle al usuario que juegue.**

## Handoff cloud → sesión local (2026-09-24) — para el agente en la PC

Esta sesión de Claude cloud trabajó en la rama `claude/agents-md-x4v1di`.
Antes de nada: `git fetch && git checkout claude/agents-md-x4v1di` (o
mergearla), y leer "Dónde quedó el trabajo" justo arriba.

**Actualización (2026-09-24, 14:10 UTC) — optimización (cierre de sesión, LEER PRIMERO)**

Hecho y **commiteado**:
- `build_mid`: las cargas a mitad de línea quedan **fijas en pantalla**
  mientras valen (`vu` = mínimo de `principio del tramo nuevo − x − VMARG`,
  `wake` = `vu`; sin camino rápido por frame). Musashi: **29 800 → 16 300
  ciclos** por frame, imagen igual o mejor (fallos que no se explican por
  un vecino: 1000: 31, 1700: 91, 2500: 46, 4500: 127).

En el árbol **SIN commitear** (`player/scroll.s`; ensambla, **sin
verificar en imagen ni medir en FS-UAE**):
- escaneo de `wake` por bloques de 16 líneas con su mínimo (`gmin_a/b`):
  Musashi 16 300 → **13 400** ciclos;
- `blit_steps`: la columna nueva repartida entre frames (`BLITS` = 4 pasos
  por frame; paso 14 = la segunda copia). Busca bajar el pico de los
  frames con columna (hoy 42 % contra 33 %). `blit_column` quedó sin uso.
- Para cerrarlo: `scroll_check.py --mid` en x = 1000/1700/2500/4500 y
  `-DBENCH -DSPEED=4` + `scroll_read.py --auto`; si todo está bien,
  commit. Perfil por zonas de `build_mid` en Musashi: el script estaba en
  `/tmp/b/me_prof.py` (se pierde con el contenedor; rehacerlo con
  `tools/m68kverify.MusashiCPU` y el listado `-L`).

**Dos subagentes quedaron trabajando al cerrar** (sus cambios están en el
árbol, **sin commitear y sin revisar**):
1. Optimización del frame de Mario + sprites en C (`player/manim.c`,
   `mario.c`, `mcam.c`, `mcoll.c`, `mgfx.c`, `msprite.c`, `smwmac.h`).
   Criterio de aceptación: `marioverify` full/gfx/loop/game/sprloop
   idénticos a la base (full 3557/3573 2953/2974, gfx 6869/6869, loop 37,
   game 1 resincronización) y `m68kverify --mode loop` (37) y
   `--sprites` (4) iguales; base de ciclos: 31 100 / 44 400 (Musashi).
   **Revisar con `git diff` y correr todo eso antes de commitear**; si algo
   no cuadra, `git checkout` de esos ficheros.
2. La causa del adelanto de ~5 px de las cargas con WAIT en el scroll
   (hoy tapado con `WOFS` = 8), con `player/copcal.s` + `tools/copcal.py`
   (modificados en el árbol): hipótesis, el retardo de `BPLCON1` o la
   escala de la captura. Si no dejó conclusión, repetir el experimento
   (bandas con distinto `BPLCON1` y contenido de franjas de 1 px).

**Actualización (2026-09-24, 13:40 UTC) — etapa 6: copper calibrado, franja arreglada**

1. **Calibración del copper** (`player/copcal.s` + `tools/copcal.py`, en la
   pantalla del scroll: DPF de 6 planos, fetch `$30`-`$D0`, sin sprites):

   | medida | valor |
   |---|---|
   | h → x de pantalla (WAIT + MOVE, copper libre) | x = 2·(h − `$38`) hasta h = `$D0` (x = 303); después **1 px por h** (`$D4` → 307, `$DC` → 315, `$E0` ya fuera) |
   | MOVE seguidos | uno cada 16 px |
   | un WAIT, aunque ya haya pasado | **32 px** (WAIT + MOVE = 48 px) |
   | borrado de 2 WAIT + 14 MOVE en (v, `$07`) | termina en x ≈ 64-79 |
   | borrado en (v−1, `$E2`): 7 MOVE / 14 MOVE | termina antes de x = 0 / en x ≈ 32 |

   `copcal.py gen` genera `work/copcal_lines.i`; con `COPCAL_RIGHT=1`,
   las pruebas del borde derecho.
2. **`scroll.s` con ese modelo:** `HOFS` = `$38` (antes `$40`: todo caía 16
   px tarde), con el quiebre de x > 304; la h se redondea **hacia arriba**
   (va de 4 en 4 px; redondear hacia abajo escribía hasta 3 px antes de
   que termine el tramo anterior); borrado en (v−1, `$E2`) con los 7 de PF1
   y **solo los de PF2 que cambian**; cargas colocadas con el tiempo T del
   copper (MOVE si ya se puede, 1-2 MOVE de relleno a `$1FE` si falta ≤ 32
   px, WAIT si no); ninguna carga después de x = 316.
3. **`mkscroll.py` planifica** las cargas por plazo con el mismo modelo (2 de
   3409 llegan tarde) y guarda la x planificada: MLD de 16 bytes.
4. **Tres bugs de verdad** (P40): `apply_colors` indexaba con 16 bits con
   signo (desde la línea 149 las escrituras de la lista B caían en la A);
   al ordenar por x planificada, las cargas caducadas detrás de una viva
   se seguían emitiendo; y "la línea tenía cargas" contaba solo los WAIT
   (las líneas con cargas sin WAIT no se limpiaban).

Fallos limpios contra el esperado, en 6 puntos del nivel (FS-UAE):

| x | antes | ahora |
|---|---|---|
| 500 | — | 132 (0,18 %) |
| 1000 | 268 | **45 (0,06 %)** |
| 1700 | 1025 (la franja) | **116 (0,16 %)** |
| 2500 | — | **52 (0,07 %)** |
| 3500 | — | 163 (0,23 %) |
| 4500 | — | 635 (0,89 %): a la vista iguales; son bordes verticales de las montañas de la capa 2 (muestreo de la captura ×2,125) |

Descontando el muestreo (`scroll_check.py` imprime también los fallos que
no se explican por un vecino, ±1 px, ±1 línea): 500 → 74, 1000 → 45,
1700 → 113, 2500 → 18, 3500 → 72, 4500 → 172. **Todos < 0,25 %.** Lo que
queda son marcas sueltas en bordes de tubería y escalón.

Coste (`-DBENCH`): 33,9 % sin columna, 42,5 % con columna (igual que antes).

**Después (13:58):** el usuario vio en la captura de x = 4500 la piedra
gris sin su esquina y marcas de colores en la tierra, junto al escalón.
Causa: **en el scroll, las cargas con WAIT caían ~5 px antes** de lo que
dice `copcal` (el tramo anterior todavía se veía). Sin explicar (¿el
retardo de `BPLCON1`? ¿escala de la captura?); corregido de forma empírica
con `WOFS` = 8 (los WAIT, 8 px más tarde): la piedra sale entera y queda
un solo punto en la tierra. Fallos que no se explican por un vecino:
1700 → 98, 2500 → 44, 4500 → 126. **Pendiente:** entender los 5 px con
`copcal` a distintos retardos de `BPLCON1`.
También: `build_mid` no hace nada si la cámara no se movió desde la
última vez que se escribió esa lista, y tablas L·SEG / L·SHSZ en vez de
`mulu` (coste con scroll continuo: 33 % / 42 %, casi igual).
**Criterio del usuario: priorizar lo que se nota a simple vista**; el
magenta del fondo en `scroll_check` es casi todo reescalado.

**Siguiente (etapa 6):** bajar el coste de `build_mid`; cámara hacia la izquierda;
conectar `mcam.c`. Para dar la imagen por cerrada, comparar en la PC con
capturas de WinUAE sin reescalar (el ×2,125 de FS-UAE ensucia los bordes).

**Actualización (2026-09-24, 13:00 UTC) — etapa 6, segunda hora**

1. **Cargas de color a mitad de línea: hechas.** `mkscroll.py` guarda por
   línea las cargas en coordenadas del nivel (MLX/MLD). En `scroll.s`
   cada línea es un **segmento** de copper de 172 bytes y largo variable:
   2 WAIT + 14 MOVE del borrado + hasta 12 cargas (WAIT + MOVE) + salto
   al segmento siguiente (`COP2LCH`/`COP2LCL`/`COPJMP2`), así los huecos
   no le cuestan tiempo al copper. Dos listas: la CPU escribe una mientras
   se ve la otra y cambia `COP1LC`. Una carga a menos de 16 px de la
   anterior va sin WAIT: en DPF el copper tiene una ranura cada 16 px y
   **un WAIT gasta ranuras igual que un MOVE**. Sin eso la tercera carga
   seguida llegaba tarde (líneas sueltas de otro color en las pendientes).
   `scroll_check.py` cuenta ahora los **fallos limpios** (color OCS exacto
   y distinto; las mezclas son del reescalado de la captura): **273 px
   (0,38 %) contra el esperado con las cargas**, 952 contra el de solo
   borrado.
2. **Columna nueva por blitter: hecha** (`blit_column`): un blit por
   bloque (1 palabra × 48 filas: 16 líneas × 3 planos a `ROWB1`) y la
   segunda copia de una vez (1 × 672). Misma imagen que con la CPU. El
   dibujo inicial sigue con la CPU (el SO todavía es dueño del blitter).
3. **Coste medido** (`-DBENCH`, CIA-B, FS-UAE cycle-exact, 4 px/frame,
   1200 frames; `tools/scroll_read.py --auto`):

   | versión | sin columna, media | con columna, media |
   |---|---|---|
   | sin `build_mid` (`-DNOMID`) | 1,2 % | 7,1 % |
   | `build_mid` recalculando todo cada frame | 83,5 % | 104,2 % |
   | + atajo de líneas sin cargas (`nxt`) | **73,2 %** | **90,1 %** |

   El máximo (~250 %) es el primer frame (`lo_tab` avanza desde 0).
   Musashi (sin DMA): `build_mid` = ~72 000 ciclos de media; en x=1004,
   224 líneas, 66 por el camino completo, ~760 ciclos cada una. **Es
   CPU, no contención.** Con esto el scroll no entra en 50 Hz junto al
   jugador.

**Después, en la misma hora (13:00 UTC):**

- **`build_mid` incremental: hecho.** Por lista y por línea una sombra:
  `vu` (hasta qué `s` vale la estructura: sale la carga más vieja, entra
  una por la derecha o empieza a verse una saltada) y, por cada WAIT, su
  posición en el segmento y su x objetivo; con `s < vu` solo se
  recalculan las h. Más un array `wake[L]` por lista (0 si la línea tiene
  cargas escritas, `vu` si no) que un bucle mínimo recorre para entrar
  solo en las líneas que hacen falta (~26 de 224).
- La columna nueva va **lo primero** del frame, en el borrado vertical:
  ahí el blitter tiene el bus, y la copia de 672 filas corre mientras la
  CPU hace `build_mid`.
- Objetivo de cada carga: **fin del tramo anterior + 5 px** (`TXOFS`), no
  el centro de la ventana. Si cambian varios registros juntos, cada MOVE
  llega 16 px después del anterior.

| `build_mid` | Musashi (sin DMA) | FS-UAE, sin columna | con columna |
|---|---|---|---|
| recalcular todo | ~80 000 ciclos | 83,5 % | 104,2 % |
| + atajo de líneas sin cargas | ~72 000 | 73,2 % | 90,1 % |
| incremental (sombras) | ~37 000 | 35,0 % | 52,9 % |
| + columna primero | — | 35,0 % | 44,7 % |
| + `wake` | ~29 000 | **33,0 %** | **43,1 %** |

Imagen: x = 1000 → **268 px de fallo limpio (0,37 %)**; x = 1700 →
**1025 px (1,43 %)**, casi todo en una **franja de ~16 líneas justo encima
del suelo**: la parte de abajo de las tuberías lavanda sale verde, el
arbusto gris, la base de los bloques de cemento mal. **No es del camino
incremental**: la versión que recalcula todo da lo mismo (1093 px). Ahí
tres registros cambian dentro de una ventana estrecha (~27 px entre el
arbusto y la tubería). Sospechas, sin comprobar:
1. la colocación de las cargas no hace el reparto por plazo en ranuras de
   16 px que usan `dpfsplit.py`/`render_d.py` (para ellos solo falla el
   0,018 %): hay que precalcularlo en `mkscroll.py` y guardar la x
   objetivo en MLD;
2. el borrado (2 WAIT + 14 MOVE) empieza en h = `$07` de cada línea. En
   DPF el copper solo tiene libres 14-15 MOVE entre el borde derecho y el
   izquierdo (§9 punto 8), y así pierde el tramo del borde derecho de la
   línea anterior: las últimas cargas del borrado caen ya dentro de la
   pantalla.

**Causa de la franja, encontrada (13:05):** en la línea 182 (x = 1700), entre
x = 66 y x = 113 (47 px de ventana) tienen que cambiar 4-5 registros. En
DPF el copper tiene **una ranura cada 16 px y un WAIT gasta una ranura
igual que un MOVE**: WAIT + 4 MOVE = 5 ranuras ≈ 80 px > 47. Las cargas se
retrasan en cadena (el `$88C` del registro 2 aparece en x = 255 en vez de
115). **`dpfsplit.py`/`render_d.py` solo contaban los MOVE, no los WAIT**:
por eso daban 0,018 % de fallos. Es un error del modelo de la etapa 5,
no del scroll. (Probado y descartado: empezar el borrado al final de la
línea anterior, WAIT (v−1, `$E2`): no cambia nada.)

Dos salidas:
- **(a)** Un flujo de MOVE **sin WAIT intermedios**: después del primer
  WAIT, cada carga en su ranura de 16 px, con MOVE de relleno a un
  registro inocuo donde no hay carga. Cada carga cuesta una ranura, como
  suponía la simulación. Las posiciones relativas no cambian con la
  cámara (solo la fase `s mod 16` y lo que entra o sale por los bordes),
  así que encaja con las sombras de `build_mid`.
- **(b)** Rehacer el reparto de registros de `dpfsplit.py` contando los
  WAIT, y volver a simular antes de tocar la Amiga.

Probado y descartado (13:07, revertido): planificar las cargas por plazo
(EDF en ranuras de 16 px, como `dpfsplit`) en `mkscroll.py` y ordenar MLD
por la x planificada. Con el modelo "1 ranura por carga" solo quedaban 3
cargas tarde en todo el nivel, pero en la Amiga x = 1700 **empeoró** (1335
px contra 1025). O sea: **el modelo de tiempos del copper no está
calibrado** (dónde cae de verdad cada MOVE respecto a la h del WAIT,
`HOFS`, cuánto cuesta un WAIT intercalado en medio de una cadena). Antes
de (a) o (b) hay que **medirlo** con una prueba de copper (como
`copbench.s`): una línea con WAIT + N MOVE de color y ver en la captura
dónde cambia cada uno.

**Siguiente (etapa 6), en orden:**
- Calibrar el copper (arriba) y después la franja: (a) o (b). Comprobar varias x con
  `scroll_check.py --mid`, no solo 1000 y 1700.
- Bajar el 33 % de `build_mid`: tablas de desplazamientos por línea en vez
  de los dos `mulu` de cada visita, y no volver a escribir las h de los
  WAIT cuando `s` no cambió (Mario quieto).
- Cámara hacia la izquierda (`lo_tab`, `vu` y la lista de cambios solo
  avanzan) y conectar `mcam.c`.

**Lo que había escrito antes de hacerlo (referencia):**
- **`build_mid` incremental.** Entre dos frames, el conjunto de cargas de
  una línea solo cambia cuando la cámara cruza un umbral (una carga entra
  por la derecha, sale por la izquierda o se pega al borde). Si no, todas
  sus h bajan lo mismo (`Δs/2`). Guardar por lista y por línea (primera y
  última carga, s de la última escritura) y, si no cambió, solo restar a
  las palabras WAIT (~20 ciclos por carga, sin tocar MOVE ni salto).
  De media hay 24 líneas y 70 cargas a la vista.
- Baratos: guardar la x objetivo de cada carga en MLD (ahorra el cálculo),
  no reescribir el salto si el número de cargas no cambió.
- Cámara hacia la izquierda (`lo_tab` y la lista de cambios solo avanzan)
  y conectar `mcam.c`.

```bash
~/vbcc/bin/vasmm68k_mot -Fbin -m68000 -I player -DBENCH -DSPEED=4 -o work/scrollb.bin player/scroll.s
python3 tools/mkadf.py --boot work/boot.bin --stage2 work/scrollb.bin --data work/yi1_s.dat --out work/scrollb.adf
sh tools/fsuae_shot.sh work/scrollb.adf work/scrollb.png 70
python3 tools/scroll_read.py --shot work/scrollb.png --auto
```

**Actualización (2026-09-24, 12:05 UTC) — etapa 6, primer prototipo (media hora)**

- `tools/mkscroll.py`: de `work/yi1_d.dat` a `work/yi1_s.dat` (126 KB, en
  el orden de la Amiga). Ventana vertical fija, líneas 192-415: la cámara
  no se mueve en Y en toda la partida (`Bg1VOfs` = `Bg2VOfs` = 192).
  Colores de la capa 1: el valor de cada registro en el borrado solo
  cambia cuando la cámara pasa el final de un evento → **lista de 3409
  cambios ordenada por x**, que la Amiga aplica a la lista del copper
  según avanza (barato: un puntero que avanza).
- `player/scroll.s`: toma la máquina como `demo.s` y se desplaza sola a 2
  px/frame hasta `STOPX` (`-DSTOPX=n`). PF1: buffer circular de 22
  columnas escrito dos veces (704 px, 3 planos entrelazados); puntero =
  palabra `(s-1)>>4`, retardo `(-s)&15` (con `DDFSTRT $30` la fórmula de
  R5 da 1 px de desfase; esta no). PF2: bitmap de 848 px (512 + 336) a
  `s/2`: paralaje por hardware. Lista del copper: 64 bytes por línea (2
  WAIT + 7 + 7 MOVE; el segundo WAIT es el `$FFDF` en la línea 256).
  La columna nueva la copia **la CPU** (~24 000 ciclos cada 16 px): el
  definitivo va por blitter.
- Verificado en FS-UAE (`STOPX=1000`, 60 s de captura: con AROS tarda en
  arrancar, a los 30 s todavía no llegó) con `tools/scroll_check.py`,
  contra el frame esperado con el mismo modelo (paralaje + solo borrado):
  **~6-7 % de píxeles distintos, todos bordes de 1 px y puntos de la
  tierra del reescalado ×2,125 de la captura**; a la vista son idénticos.
  Ojo: la imagen "ideal" de `render_d.py` / `yi1_d_nivel.png` pone la capa
  2 a la misma velocidad que la 1 (sin paralaje): no sirve de esperado
  para el scroll.
- Falta (en orden): las cargas de mitad de línea (sin ellas, franjas de
  color en las pendientes y en los bloques; `scroll_check.py --mid` es el
  esperado final); la columna por blitter; la lista del copper por
  segmentos encadenados (§9 punto 10); medir el coste por frame; conectar
  la cámara de `mcam.c` en vez del avance automático.

```bash
python3 tools/mkscroll.py
~/vbcc/bin/vasmm68k_mot -Fbin -m68000 -I player -DSTOPX=1000 -o work/scroll.bin player/scroll.s
python3 tools/mkadf.py --boot work/boot.bin --stage2 work/scroll.bin --data work/yi1_s.dat --out work/scroll.adf
sh tools/fsuae_shot.sh work/scroll.adf work/scroll.png 60
python3 tools/scroll_check.py --shot work/scroll.png --s 1000
```

**Actualización (2026-09-24, 07:00 UTC) — cierre de la hora de trabajo**

Sobre lo de 06:25 (abajo), en esta última media hora:

- **Sprites nuevos**: bloque `?` volador (`$83`, sólido, golpe desde
  abajo) y `CODE_019386` (sprite sobre un tile de pendiente ≥ `$D8`: sube
  1 px y repite `CODE_0192C9`). Antes, en las colinas, cortaba el
  seguimiento del Rex.
- `marioverify ... game` adopta los Rex vivos del oráculo que nacieron
  antes del tramo (`GAME_NOADOPT=1` lo apaga, `GAME_SHOW=1` imprime los
  campos distintos). **Resincronizaciones de Mario: 26 → 1** (la que queda
  es el frame 5322: pisotón al Koopa sin caparazón `$02`, sin portar).
  **Rex exactos 3192/3194**; `sprloop` 2593/2594.
- **Los sprites ya están en el binario del 68000**: `msprite.c` entra en
  `logicbench_build.sh` y en el arnés; `level_frame` corre las 12
  ranuras (`sprite_run`) y el cargador si `level_sprites = 1` (apagado
  por defecto: `logicbench` y la 8d miden lo mismo que antes).
- `m68kverify.py --mode loop --sprites` (lazo cerrado del binario 68000
  con TODOS los sprites en el port: los sin portar no hacen nada) y
  `m68kprof.py --sprites`. Medido en Musashi (sin DMA), antes de
  optimizar el motor de sprites: **media 48 054 ciclos por frame (33,9 %
  de un frame PAL), p99 67 420, máx. 68 638 (48,4 %)**; sin sprites, 31 056
  (21,9 %). Mario: 4 resincronizaciones en 6547 frames (en `game` hay 1,
  porque allí los sprites sin portar se copian del oráculo).
- Perfil con sprites (`m68kprof.py --sprites`): `sprite_run` se llevaba
  6120 ciclos/frame (510 por ranura), casi todo del bucle de los 7
  temporizadores sobre una tabla de direcciones. Desenrollado: **48 054 →
  44 364 ciclos de media (31,3 %), máx. 64 752 (45,6 %)**, con el mismo
  resultado. La primera versión la compiló mal vbcc (P38).
  Sin sprites: 31 124 (+68 por el `tst` de `level_sprites`).
- Trampa de `m68kprof.py`: va instrucción a instrucción y **no tiene
  tope**. Si el binario se cuelga (P38), no termina nunca. Probar antes
  con `m68kverify.py`, que corta a los 10 M ciclos.

**Siguiente (en este orden):**
1. Seguir con el perfil de sprites (`PROF=1 sh tools/logicbench_build.sh
   && python tools/m68kprof.py --sprites`): `level_frame` pasó de 2708 a
   3944 ciclos propios (bucle de 12 ranuras + cargador en línea),
   `spr_tile` 947, `get_draw_info` 673.
2. Koopa sin caparazón (`$02`, sale del `$BD`): es la última
   resincronización de `game` (frame 5322). Después Banzai Bill (`$9F`),
   piraña saltarina (`$4F`), Chuck (`$95`).
3. Medir `level_frame` con `level_sprites = 1` en FS-UAE/WinUAE: hace
   falta meter `spr.lv` en el arnés (hoy solo `m68kverify`/`m68kprof`
   lo cargan en memoria y apuntan `_spr_level`) y un estado del oráculo
   con Rex a la vista.

**Actualización (2026-09-24, 06:25 UTC) — pasos 1 y 2 del plan de D1**

El usuario eligió: optimizar en C nativo verificando contra el oráculo
(paso 1) y escribir los sprites directamente así (paso 2). Estado:

- **Paso 1 (nativo, primera parte):** sondas de colisión con tablas
  nativas y atajo de `F545`; cámara con variables locales. Musashi:
  31 972 → 30 848 ciclos por `level_frame`. Todo sigue exacto. **Falta** la
  parte grande: el estado de Mario en variables nativas (ver "Implicación
  para D1"), medir con FS-UAE después de cada paso.
- **Paso 2 (sprites), `player/msprite.c`:**
  - cargador `LoadSprFromLevel`: `marioverify ... sprload` → **20/20
    nacimientos exactos** (ranura, número, X, Y) y ninguno de más;
  - motor mínimo: `InitSpriteTables`, temporizadores, `HandleSprite`
    (init + main), `SubUpdateSprPos`, colisión con el nivel
    (`CODE_019140`, nivel horizontal de capa 1), `GetDrawInfo` (flags),
    `SubOffscreen`, contacto Mario-sprite (`MarioSprInteract`, cajas,
    `CheckForContact`), `BoostMarioSpeed`, choque sprite-sprite (estado 8
    contra 8) y **el Rex completo**;
  - `marioverify ... sprloop` (los Rex que nacen a la vista corren solos;
    Mario y la cámara son entradas): **2411/2412 Rex-frames exactos**, los
    pisotones, el doble pisotón y la muerte con giro incluidos; los 11
    rebotes de Mario sobre esos Rex coinciden con el oráculo;
  - `marioverify ... game` (Mario desde el joypad + los Rex del port en el
    mismo frame): resincronizaciones de Mario **37 → 26**; tramo más largo
    **1240 → 2711 frames idénticos** (~54 s). Lo que queda: 23 frames
    parado sobre la **caja de mensaje** (`$B9`, sprite sólido), y 3
    rebotes: Koopa sin caparazón (`$02`, frame 5322), bloque `?` volador
    (`$83`, 6393) y un Rex que ya estaba al empezar el tramo (6909).
  - Tablas de otros bancos: `tools/smwtabx.py` → `player/gen/smwtabx.h`
    (generado, no se versiona). `smwgen.py` ahora lee también las tablas
    de sprites (`INSTANCEOF` en `memory.i`): `smwram.h` cambió.
  - Trampas nuevas: en `CODE_01A56D` el `ROL` guarda el **carry** de la
    resta (sin préstamo), no el signo; `RexSpinKill` pasa a estado 4 (no a
    0); al resincronizar un sprite hay que copiar también la fracción
    (`SpriteXAcc`/`YAcc`, grabadas) y deducir la dirección (no grabada).
  - **Los sprites todavía no están en `logicbench`** ni medidos en la
    Amiga: `level_frame` no los llama (los llama el verificador). Siguiente:
    caja de mensaje, bloque `?` volador, Koopa, Banzai Bill, piraña; meter
    los sprites en `level_frame` y medir con FS-UAE.

**Qué cambió (resumen; el detalle está arriba y en §8 P33-P37):**
- 8b, animación, gráficos de Mario y cámara portados y verificados:
  `player/mcoll.c`, `manim.c`, `mgfx.c`, `mcam.c`, `smwmac.h`.
  `marioverify` tiene los modos `full`, `gfx`, `loop` y `fulldump`.
- `logicbench` ahora mide `level_frame` (cámara + gráficos + jugador +
  bloques) y lleva el mapa del nivel dentro (`work/yi1_map16.bin`, lo
  genera `tools/mkmapbin.py`). `logicbench_build.sh` compila 5 ficheros
  C, parte datos/código y **se para si hay referencias absolutas**.
- Etapa 5: `tools/mkbg.py` (capa 2 desde el ROM), `mkd8in.py`,
  `mkleveld.py` → `work/yi1_d.dat`, `render_d.py`.
- 8d medida en cloud con FS-UAE + AROS: **31,6 % / 32,9 % de un frame**.

**Qué hay que hacer en la PC (lo que cloud no puede):**
1. **Confirmar la 8d en WinUAE con KS 1.2** (la de cloud es FS-UAE + AROS):
   ```bash
   python tools/mkmapbin.py
   gcc -O2 -Iplayer -o work/marioverify tools/marioverify.c player/mario.c player/mcoll.c player/manim.c player/mgfx.c player/mcam.c player/msprite.c player/gen/smwrom00.c
   work/marioverify work/oracle_yi1.bin fulldump 5410 work/cc/state_run.bin
   work/marioverify work/oracle_yi1.bin fulldump 10983 work/cc/state_jump.bin
   python tools/smwgen.py && python tools/smwtabx.py
   sh tools/logicbench_build.sh
   ```
   ```powershell
   .\tools\shot.ps1 -Exact -Adf work\logicbench.adf -Out work\logicbench.png -Wait 80
   ```
   ```bash
   python tools/logicbench_read.py        # esperado: ~31,6 % y ~32,9 %
   ```
   Si difiere de FS-UAE en más de 1 punto, anotarlo: la validación con
   `bench2.s` dio los mismos números en los dos emuladores.
   Esto también prueba que el ADF **arranca en KS 1.2** con el binario de
   58 KB (en cloud solo se probó con AROS).
2. **Etapa 5 contra la referencia**: `cmp_ref.py` / recortes apilados de
   `work/yi1_d_nivel.png` contra `SuperMarioWorldMap02.png` (la de cloud
   se comparó con la imagen ideal sacada del ROM, no con la referencia).
   Ojo: los colores del blob están cuantizados a 12 bits (OCS); comparar a
   4 bits por canal o esperar diferencias de 1 bit en todo.
3. **8c: grabar las colinas** (a toda carrera en las dos direcciones,
   parado encima, deslizándose, saltando) con `tools/oamrec.py --out` a un
   fichero **distinto** de `oracle_yi1`. **Probar el grabador antes** de
   pedirle al usuario que juegue (límites de 1024 caracteres, 16 valores y
   una sola conexión). Después: `oracle2bin.py --inp ... --out ...` y
   `marioverify <bin> full` / `loop` (el mapa es el mismo nivel).
4. Esperar la **decisión del usuario sobre D1** (ver "Implicación para D1"
   arriba) antes de empezar la etapa 9: define si los sprites se portan al
   estilo byte a byte (fácil de verificar, lento) o en C nativo pensado
   para el 68000.

**Diferencias de entorno a tener en cuenta en la PC:**
- `tools/mkd8in.py`, `mkleveld.py`, `render_d.py` y `dpfsplit.py` usan
  **numpy**, y el Python local (§6) no lo tiene: instalarlo o correrlos en
  cloud. `m68kverify.py` / `m68kprof.py` necesitan `unicorn` y
  `machine68k` (pip).
- `logicbench_build.sh` llama a `python tools/mkmapbin.py` si falta el
  mapa: necesita `../../smw-src-master` como siempre.
- `work/smw.sfc` en cloud es la ROM **ensamblada desde el fuente** (CRC32
  `B19ED489`, idéntica a la (U)); en la PC se sigue usando la del usuario.
- Los `*_read.py` aceptan `--auto` (capturas con otra escala, p. ej.
  FS-UAE); sin la opción siguen leyendo las capturas de `shot.ps1` como
  antes.

## AGENTS.md §10: la tabla de etapas original (2026-09-22)

## 10. Roadmap

> El plan detallado de lo que falta (pasos, criterios de hecho, presupuesto del
> frame y decisiones D10-D14) está en `ROADMAP.md`.

Reordenado el 2026-09-22 con un criterio: **primero se mide en el hardware lo
que puede tumbar el proyecto, después se pule la fidelidad.** La versión
anterior dejaba perfecto el fondo en el PC (2c) antes de saber en qué formato
iba a existir en la Amiga, y ponía la prueba de rendimiento en cuarto lugar.

### Hecho

| Etapa | Contenido | Criterio | Estado |
|---|---|---|---|
| 1 | Pipeline de assets | 52/52 ficheros + round-trip OK + PNG verificados | **HECHO** |
| 1b | Paletas reales | CGRAM reconstruido emulando `LoadPalette` | **HECHO** |
| 2 | Parsear `.lv` → buffer Map16 | Volcar el nivel 105 como imagen legible | **HECHO** |
| 2b | Capa 1 1:1 | 92/92 objetos, `m16diff` 100 % **y** inspección visual del nivel entero | **HECHO** — 6111/6111; solo difieren píxeles bajo sprites |
| 3 | Esqueleto Amiga | ADF arranca (KS 1.2) y muestra el tileset estático | **HECHO**, pero **sin medida válida**: los "49.9 fps" son de la config rápida. Se re-mide en la etapa 4 |

### Pendiente

| Etapa | Contenido | Criterio de "hecho" | Cierra |
|---|---|---|---|
| **4** | **Prueba de viabilidad en `a500.uae`** (cycle-exact) | Tabla de costes medida en la Amiga + cómo se mueve la capa 2 | **HECHO** (2026-09-22) — ver "Etapa 4 — resultados" en §9. Cerró D1 y D9; D8 queda para el usuario con los datos. El scroll del **nivel real** no se hizo aquí (hace falta el conversor de la etapa 5): pasa a la etapa 6. `player/bench.s` + `tools/bench_read.py` |
| 5 | **Conversor de nivel → Amiga, formato (d)** | Capa 1: 3 planos con la asignación de índices de `dpfsplit.py` (244 variantes de bloque) + tablas del copper por línea del nivel (cargas en el borrado y a mitad de línea con su ventana). Capa 2: bitmap de 3 planos de período 512 px + paleta por línea. `render_dat.py` renderiza el blob en el PC aplicando las tablas y se compara contra `d8d_g48m8_nivel.png` y la referencia con `cmp_ref.py` | **HECHO en cloud** (2026-09-24): `tools/mkd8in.py` → `tools/mkleveld.py` → `work/yi1_d.dat` (199 KB) → `tools/render_d.py`. Todo sale de los datos del ROM (la capa 2 también: `tools/mkbg.py`). Colores cuantizados a 12 bits (OCS) antes de repartir registros. 244 bloques, 9575 eventos, derrame 357 px (0,1 %). El render **solo desde el blob** = la imagen ideal (0 px distintos); moviendo la cámara cada 4 px, 0,018 % de píxeles mal (peor encuadre 132 px). **Falta en la PC**: `cmp_ref.py` contra `SuperMarioWorldMap02.png` |
| 6 | Scroll del nivel real en la Amiga | PF1 con `BPLCON1` bits 0-3 + columna nueva; PF2 con bits 4-7 a media velocidad (paralaje); lista del copper por frame (segmentos por línea encadenados, §9 punto 10). Recorre las 20 pantallas a 50 Hz; captura de WinUAE = render del PC en varios puntos; coste medido con el método de `bench2.s` | **Primer prototipo** (2026-09-24, cloud): `tools/mkscroll.py` → `work/yi1_s.dat`, `player/scroll.s` (ver el handoff). Nivel real en DPF, PF1 con buffer circular + columna nueva, PF2 con paralaje por hardware, colores por línea con cargas en el borrado **y a mitad de línea** (segmentos de copper encadenados, dos listas, `build_mid` incremental), columna nueva por blitter. Fallos limpios contra el esperado: 0,37 % en x = 1000, 1,43 % en x = 1700 (una franja sobre el suelo; arreglada: copper calibrado + tres bugs, ver el handoff de las 13:40): hoy 0,06-0,23 % en 5 de 6 puntos. **Coste medido: 33 % de un frame sin columna, 43 % con columna.** Falta: la franja, bajar el coste, cámara hacia la izquierda y conectar `mcam.c` |
| 7 | **Capa 2** | En (d) la hacen las etapas 5 y 6 (PF2 con scroll por hardware). Queda la verificación: recortes apilados contra `SuperMarioWorldMap02.png`, el diff tiene que bajar del 25.5 % | — |
| 8 | **Mario**, por partes verificadas bit a bit contra el oráculo `work/oracle_yi1.txt` (partida real grabada en `smwrecomp`: joypad + WRAM `$0000-$00FF` y `$13C0-$14FF` + OAM por frame): **8a** velocidad horizontal, gravedad y saltos; **8b** colisiones con bloques (en SMW el "acts like" es el propio índice Map16); **8c** pendientes de 45° (hace falta grabar las colinas: a toda carrera, en las dos direcciones, parado encima y deslizándose); **8d** coste medido en la Amiga | Cada parte: el estado de Mario del port = el del oráculo en todos los frames de sus tramos | **8a, 8b, animación, gráficos y cámara HECHOS** (2026-09-24): 6510/6547 pares exactos, los 37 restantes son sprites (etapa 9); OAM 6869/6869; lazo cerrado solo con el joypad. 8c: las pendientes de la partida salen exactas, falta la grabación de las colinas. **8d medida: 31,6-32,9 % de un frame** (FS-UAE cycle-exact, tras la 1.ª optimización) |
| 9 | **Sprites del nivel** (D3): Rex, Banzai Bill, Jumping Piranha; después Chuck, Sliding Koopa, bloque volador, Info Box, meta | Aparecen en las posiciones de `spr.lv` y se comportan como en la SNES | — |
| 10 | HUD | Barra de estado con su propia paleta (copper) | — |
| 11 | Audio (D5) | Música del nivel + efectos, 4 canales | — |
| 12 | Pulido | Muerte, punto medio, meta, transiciones | — |

**La etapa 4 decide el proyecto.** Su resultado puede cambiar las etapas 5-7
(formato de los bloques, paleta, cómo se dibuja el fondo). Por eso va antes que
cualquier trabajo de fidelidad nuevo.

## ROADMAP: el día a día del 2026-09-30 al 2026-10-01

- **Ola 3 (2026-10-01, PC Windows):** integradas C1 (`tools/memmap.py`:
  0 violaciones; chip 401,6 KB en vivo, 135 KB de datos solo de CPU
  candidatos a slow, 10.7; sin A501 no entra), P6 (`spr_powerup.c`, la seta
  `$74`; `mcoll.c` `bounce_spawn` llama a `powerup_from_block`, el bloque `?`
  ya da la seta), L1b+L1d (`sprite_run`, `spr_spr_interact`,
  `spr_obj_interact`, `spr_obj_vert` llano y `jumping_piranha` en asm:
  `level_frame.max` 42 418 → 39 026; L2 en C no ganó), P8 (`$71` = 1, 2, 4,
  9 en `manim.c`, `mario_hurt`, la estrella contra el Rex; `game.s`
  `diag_cause` congela recién al terminar la muerte, `GameMode` `$0B`/`$15`:
  falta el reinicio del nivel, Z1), SX paso 1 (`bm_left`: `scroll.vuelta.max`
  135 498 → 114 112, media 36 133 → 19 837) y RC (`pw_c7`, `pw_bloques`,
  `pw_1up`; los "!" de YI1 no son sólidos). Musashi después de todo:
  `game.total.max` 122 900 (≈ 87 % sin DMA), media 40 438. **Siguiente:**
  SX paso 2 (diferir las cargas por la derecha: ida ~71k → ~58k según
  `midsim5`), O4 (informe D1 con WinUAE), Z1 (reinicio del nivel tras la
  muerte), P7 (bolas de fuego), P9/P10 (monedas del bloque, caja de
  reserva), RC: `pw_3up` (parece pedir capa) y la moneda de Yoshi 4.
  **SX paso 2 integrado** (diferir por la derecha, con desfase fijo de
  8 px en las líneas impares para no amontonarlas): `scroll.ida.max`
  86 688 → 80 492, a 2 px 77,5k → 60,6k; `game.total.max` 118 724.
  **Faltan las capturas de WinUAE** contra master (ida 500-4500 y una a
  la vuelta); `shot.ps1` no es seguro en paralelo dentro del mismo
  worktree (`work\shot.uae` fijo). El pico a 4 px (s 4580-4672) pide S5/S7.
  Tarjetas nuevas por lo aprendido de reassembler (OutRun y Sonic en la
  Amiga; SUBAGENTES §5): **A0/A8** (referencia de audio = registro del
  DSP de `snesorc`, auditoría nota por nota) y **X1** (estudio: borrador de
  C desde el 65816 con `tools/x65c.py`, medido regenerando Rex, Chuck y
  caparazones).
  Cruce de los oráculos snesorc contra el binario 68000 en `regress.py`
  (hoy solo `marioverify` en el PC; ver P92).
- **Ola 2 (2026-10-01, PC Windows; cerrada por uso):** integradas I2
  (`levels/yi1.json` + `tools/lvdesc.py`; falta en `mkscroll.py` y
  `mkmario.py`), O3 (`regress.py` guarda `game.<parte>.max/.media` en
  Musashi y `scroll.ida/vuelta.*`; `--shots DIR` lee `game_bench.png`),
  P1+P2 (eran del verificador: alinear el primer registro de snesorc por
  `$1404`, y liberar el índice del sprite que sale cuando otro nace en su
  ranura), P3 Chuck (`spr_chuck.c`, 450/450), P4 caparazones
  (`spr_shell.c`, `shells` 527/527 y 0 resincronizaciones), P5 cinta de la
  meta (`spr_goal.c`, 138/211/417; `goalhit.orc` nuevo), L1c (`mario_E2BD`
  en asm: `level_frame` media −8 %; `tools/e2bd_fuzz.py`; `lint_port` A1
  vigila las tablas de las que depende) y MA1 (`mspr_draw` con caché por
  pose: media −60 %; si otra rutina escribe `g_spra`/`g_sprb`, llamar a
  `mspr_inval`). Medida del juego entero en WinUAE con S1a+S2 (antes de
  L1c y MA1): peor `build_mid` 85,4 % (s = 1825), `level_frame` 34,6 %,
  total 127 %, media 44,8 %, 359 frames pasados. En Musashi, después de
  todo: `game.total.max` 135 290 (≈ 95 % del frame, sin DMA), media
  45 828. **Quedan en ramas sin integrar** (revisar, repetir la puerta e
  integrar): `wt/s4` (S4, `build_mid` en el sitio, opus), `wt/ra`
  (`pipe`, `stress_vert` con `Bg1VOfs` mínimo `$81`, `stress_sprites`,
  `stress_back`) y `wt/rb` (`pw_medio` y lo que haya llegado): **las tres ya
  integradas al cierre** (RA: `stress_back` llega de `$1240` a x `$0500`; RB:
  `pw_yoshicoin` 3 de 4, `goal_low`, `goal_miss`; sin grabar: estrella/1-UP,
  `$C7`, bloques `!`, 3-UP). **S4 no entró en `scroll.s`: la edición en el
  sitio SUBE el pico** (ida 77 498 → 105 496 en s = 4580; la media de la
  vuelta sí baja 51 939 → 16 482): cada edición cuesta ~1000 ciclos por línea
  contra 413 + 124 por carga de reescribir. Quedan `tools/wip64/s4_inplace.diff`
  y `tools/wip64/midsim5.py` (modelo de eventos que reproduce los conteos del
  asm). Siguiente para el scroll, según el modelo: **a la izquierda, base menor**
  (s0 = max(s + 1 − min b, x_última − LASTX), con pista del min b; recorrido
  duplicado por sentido para que la ida no cambie): vuelta peor 133k → 77,5k
  (2 px); y **diferir la carga que entra por la derecha** hasta que su tramo se
  ve (holgura de S5): ida peor ~71k → ~62k a 2 px. El pico de la ida a 4 px solo
  baja con S5 (EDF) o con menos cargas (S7). Después:
  O4 (informe y decisión D1 con el usuario), y el resto de la ola 2/3.
  En Windows, `regress.py` no arma `work/libport.so` (los cruces de RAM):
  `gcc -shared -O2 -DNOOAM -Iplayer -o work/libport.so player/mario.c
  player/mcoll.c player/manim.c player/mgfx.c player/mcam.c
  player/msprite.c player/mspr.c player/spr_*.c player/gen/smwrom00.c`.
  WinUAE: `winuae_lock.ps1` es un semáforo de 3 lugares.
- **Ola 1 (2026-09-30, tarde, en la PC Windows; parcial, cerrada por uso):**
  integradas L1a, I1, O1 (6b.6 medida) y S1a+S2, y 9 grabaciones nuevas
  (ver 8.1 en §1.2). Worktrees con `tools/wt_new.sh` y las adaptaciones de
  P82. Queda de la ola 1: las grabaciones de la lista de 8.1 y volver a
  medir el juego entero con O1 sobre el scroll de S1a+S2
  (`GDEFS="-DREPLAY -DBENCH" OUT=work/bench sh tools/game_build.sh`, captura
  con `shot.ps1 -Exact -Wait 220` por `winuae_lock.ps1`, `game_read.py
  --auto`). Notas para R9 (`pipe.orc`): la tubería del frame 11425 de
  `oracle_yi1` está en x `$780`-`$79F` (boca en y `$160`), al fondo de la
  caja de cemento de `$770`/`$7A0`, con dos bloques giratorios encima (y
  `$140`); con Mario chico, salto con giro para romperlos y DOWN cerca de
  x `$787`. `diagpipe.orc` no sirve de modelo (tuberías diagonales).
  Modelos de subagente preferidos por el usuario: optimización → Opus
  (medium), grabaciones → Sonnet (low), el resto → Sonnet (high).
- **Hecho el 2026-09-30:** los oráculos en cloud, la 9.1 sin
  resincronizaciones en `game`, la 6b.7 y tres bugs que ningún verificador
  veía (P59, P62, P69). La 6.4 no se cerró: se midió y se entendió (P71,
  P72) y el diseño quedó en `tools/wip64/`.
- **Siguiente, en orden:**
  1. **6b.6, compuerta D1 [usuario]:** medir el peor frame del juego
     integrado en FS-UAE. Con lo medido por partes (lógica con sprites
     ~45 %, scroll hasta 79 % a la ida y 95 % a la vuelta en Musashi, Mario
     7 %) el peor caso **pasa del 100 %**: preparar las opciones de §2 con
     números y preguntar.
  2. **La cámara vertical de YI1 (§10.2b, hallado al final de la sesión):**
     el nivel sí scrollea en vertical y la Amiga no lo lee; Mario se corre
     respecto del fondo cuando la cámara sube.
  3. **6.4:** terminar `tools/wip64/build_mid_incremental.s` (rebase en el
     sitio, append y truncado por la derecha; clasificación "tarde" fija),
     medir **ida y vuelta** con `scrollprof.py` y verificar con
     `scrollsim.py --ret` (9282 px, ida = vuelta).
  4. **9.1:** Chuck `$95` (x `$12A0`), caparazón rojo `$DB` (x `$D10`), cinta
     de meta `$7B` (x `$12E0`), seta `$74` y el resto de D12; cada uno con su
     grabación de snesorc (un guion `.orc` que llegue hasta ahí).
  5. **9.2:** dibujar los sprites del nivel (hoy hay Rex invisibles que
     Mario pisa: parece un doble salto).
  6. Sueltos, **sin comprobar**: en las 4 grabaciones de snesorc, el Koopa
     deslizante `$BD` difiere 1 frame justo al empezar el nivel (frame
     1455, ranura 7, `$AA` = SpeedY: port 0, ROM 3); en `diagpipe`,
     `sprload` da 31/33 (la ROM mete la piraña `$4F` en la ranura que un Rex
     deja libre en el mismo frame; el port no).
- Para retomar: `sh tools/setup_cloud.sh && python3 tools/regress.py`.
- Todo lo que falta, con cómo lo haría: §10. Otro nivel, partidas
  guardadas, pantalla de carga: §11. En tarjetas para subagentes:
  `SUBAGENTES.md` (olas 1-6; la ola 1 no depende de la compuerta D1).
- Decisiones del usuario del 2026-09-30: **D1 = 50 Hz, todo lo posible**;
  **D15 = se acepta el 83 %**; **D16 = la zona de la tubería entra**.

## AGENTS.md: la cabecera anterior (hasta el 2026-10-03)

# AGENTS.md — Manual de implementación del port-demo SMW → Amiga 500

> Este fichero define **cómo trabajar** en este proyecto. Es el contrato entre
> quien implementa (persona o agente de IA) y el hardware objetivo.
> Para el *porqué* de cada decisión, lee primero **`PLAN.md`**.
>
> **Qué hacer ahora y en qué orden: `ROADMAP.md`** (plan a futuro por etapas
> y handoff vigente, 2026-09-30). Las secciones "Dónde quedó el trabajo" y
> "Handoff cloud → sesión local" de abajo son el detalle histórico del
> 2026-09-24.
>
> **Cómo repartirlo entre subagentes: `SUBAGENTES.md`** (tarjetas de todo lo
> que falta, con nivel, puerta y ficheros que tocan).
