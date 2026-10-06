# Etapas: el paso a paso (2026-09-26)

> **ARCHIVADO el 2026-10-05.** Lo pendiente de cada etapa, más nuevo, está en
> `docs/plan-tecnico.md` §10 y en las tarjetas de `SUBAGENTES.md`; el estado,
> en `ROADMAP.md` §1. Los "§" de abajo son del ROADMAP de entonces
> (`docs/archivo/roadmap-2026-10-05.md`).
>
> Movido textual desde `ROADMAP.md` §5 el 2026-10-03. Estado actual: `ROADMAP.md`
> §1.2; lo pendiente, más nuevo, en `ROADMAP.md` §10.

---

## 5. Etapas

Formato de cada paso: **Dónde** · **Qué hacer** · **Hecho cuando**.

### Etapa 0 — Consolidar el WIP

**Dónde:** cloud. **Objetivo:** que la cabeza de la rama no tenga nada sin
verificar.

0.1 **Entorno.** `sh tools/setup_cloud.sh`. Correr §1.5 y anotar los números.
**Hecho cuando** §1.3 se reproduce, salvo lo que el WIP cambió.
**HECHO el 2026-09-26** (setup en ~2 min la primera vez, ROM con CRC32
`B19ED489`).

0.2 **Optimización de los subagentes** (`45e3857`: `manim.c`, `mario.c`,
`mcam.c`, `mcoll.c`, `mgfx.c`, `msprite.c`, `smwmac.h`).
- `marioverify` en los 7 modos tiene que dar lo mismo que en §1.3.
- `sh tools/logicbench_build.sh` (se para si hay una referencia absoluta);
  después `m68kverify --engine musashi --mode loop` (37) y `--mode loop
  --sprites` (4). Anotar los ciclos medios contra 31 100 / 44 400.
- Medir: `sh tools/fsuae_shot.sh work/logicbench.adf work/logicbench.png 30
  && python3 tools/logicbench_read.py --shot work/logicbench.png --auto`.
- Si algo no cuadra, bisecar por fichero (`git checkout bb66d2c --
  player/<f>.c`) y quedarse con lo que pasa.

**Hecho cuando** la verificación es idéntica, los ciclos bajan y la nueva
base de ciclos queda anotada en §1.3.
**HECHO el 2026-09-26:**
- `regress.py`: los 7 modos del PC dan exactamente la base y los cruces
  PC = 68000 cuadran.
- `abcheck.py bb66d2c` y `--sprites`: semántica IGUAL. Ciclos de media −17 %
  (31 124 → 25 909) y −19 % con sprites (44 364 → 35 779); peor frame −10 %
  y −18 %.
- FS-UAE: 26,5 % / 26,9 %, antes 31,6 % / 32,9 %.

Queda de esta etapa: los commits siguen llamándose "WIP" en el historial;
no hace falta reescribirlo, basta con esta nota.

0.3 **`scroll.s` del WIP** (escaneo de `wake` por bloques de 16 líneas con
`gmin_a/b`; `blit_steps`, la columna repartida en `BLITS`=4 pasos por frame).
- Imagen: `python3 tools/regress.py --quick --emu scrollimg` hace todo
  esto. A mano, para `X` en 500, 1000, 1700, 2500, 3500 y 4500 (la espera
  tiene que ser ≥ 50 + X/100 s: AROS tarda ~35 s en arrancar y el scroll va
  a 2 px por frame; con 60 s fijos, 3500 y 4500 se capturan antes de
  llegar):
  ```bash
  ~/vbcc/bin/vasmm68k_mot -Fbin -m68000 -I player -DSTOPX=X -o work/scroll.bin player/scroll.s
  python3 tools/mkadf.py --boot work/boot.bin --stage2 work/scroll.bin --data work/yi1_s.dat --out work/scroll.adf
  sh tools/fsuae_shot.sh work/scroll.adf work/scroll.png $((50 + X / 100))
  python3 tools/scroll_check.py --shot work/scroll.png --s X --mid
  ```
- Coste: `-DBENCH -DSPEED=4` y `scroll_read.py --auto`, o directamente
  `regress.py --emu scrollbench`. Mirar la **media y el máximo**; el
  máximo sale con la s donde ocurrió.
- Si la imagen empeora: `git checkout f21a2e3 -- player/scroll.s`.

**Hecho cuando** los fallos que no explica un vecino son iguales o menores
que en §1.3 y el coste baja, o el cambio queda revertido con el motivo
escrito.
**Estado el 2026-09-26:**
- **Imagen: igual a la base** en las 6 x (§1.3).
- **Coste:** media 25,2 %, contra ~36 % antes. No se compara 1:1: con
  `blit_steps` casi todos los frames cuentan como "con columna".
- **Falta — un pico de 307 % (61 ms) en s = 4504.** No es el primer frame:
  el banco ya descarta los 8 primeros (`BSKIP`) y guarda la s del peor
  frame (w8/w9, lo imprime `scroll_read.py`). Para cerrar:
  1. armar con `-DBENCH -DSTOPX=4520` y ver si se repite;
  2. perfilar ese frame en Musashi, con el listado `-L` de `scroll.s`;
  3. sospechosos: la rama "columna a medias: terminarla" (`moveq #99,d7`)
     y un recálculo completo de `build_mid`.

  Hasta explicarlo, el pico cuenta en el presupuesto.

**CERRADA el 2026-09-27 (PC):** el pico no es un bug. `tools/scrollprof.py`
(Musashi, el cuerpo real de `frame`) da 218 % solo de CPU en s = 4504, y
el 99 % es `build_mid`. En x = 4816-4856 del nivel hay un **borde vertical
de color en 144 líneas** (765 cargas); cuando entra por la derecha,
`build_mid` reconstruye ~140 líneas enteras (~2 200 ciclos cada una: recorre
todas las cargas de la línea, hasta 52) en 2-3 frames seguidos. No es el
único: a 2 px/frame hay **403 frames** cuyo trabajo pasa del comienzo de la
pantalla siguiente (s ≈ 1590-1970, 2630-2700, 4230-4680); el banco solo
mostraba el máximo. Confirmado en WinUAE KS 1.2: 309,9 % en s = 4504. El
arreglo es de la 6.4: reconstruir solo lo que cambia (agregar la carga que
entra, no rehacer la línea) y repartir entre frames.

0.4 **Los ~5 px del copper** (`WOFS`=8, un parche empírico). Leer lo que
dejó el subagente (`copcal_fine.py` y el diff de `copcal.s`/`copcal.py` en
`45e3857`). Si no hay conclusión, repetir el experimento: bandas con
`BPLCON1` a 0, 7 y 15 y un contenido de rayas de 1 px (`-DPATTERN`), y
comparar dónde cae el MOVE respecto de los píxeles del contenido y del borde
de la DIW. **Hecho cuando** hay una explicación y una fórmula en `scroll.s`
(y un **P42**), o `WOFS` queda documentado como empírico con la medida que
lo respalda.

**Pista nueva (2026-09-26):** dos builds de `scroll.s` que solo difieren
en la posición de las variables (`V_SIZE` 80 → 92, sin tocar el código que
dibuja) dan en x = 1700 3 fallos limpios más, con el mismo origen de ajuste
(91 → 94), y en x = 4500 125 → 127; en x = 1000 la captura es idéntica. Una
imagen que depende de la disposición en memoria apunta a una carrera de
tiempos entre la CPU y el copper, la misma familia que los ~5 px. Probar
con `imgdiff.py` sobre dos builds con relleno distinto (`ds.b` de más antes
de `vars`).

**CERRADA el 2026-09-27 (PC):** explicado y arreglado, sin `WOFS`.
- **P42:** con 6 planos el WAIT tiene rejilla de 8 px (h = `$40` y `$42`
  caen igual). Medido en WinUAE con `copcal.s -DPATTERN` + `COPCAL_FINE=1`:
  x = 8·⌊(h − `$38`)/4⌋ − 1. El modelo viejo fallaba 5 px con h ≡ 2 (mod 4).
  `BPLCON1` y el fetch se comportan como supone `scroll.s`. `TXOFS` no se
  usaba: borrado.
- Mirando en movimiento, el usuario vio **objetos que salen por la
  izquierda pintados con los colores del siguiente** (s = 846, 1936). Tres
  causas más, arregladas: **P43** (el borrado deja el copper libre ~60 px
  antes de x = 0: la primera carga de la línea va con WAIT), **P44** (los
  derrames de la etapa 5 alargan el tramo: `mkscroll.py`) y **P45** (una
  carga cortada por `LASTX` no bajaba el `vu`).
- La pista de la disposición en memoria (91 → 94) queda explicada por P42:
  cambiar el código cambia la fase de los WAIT en la rejilla.
- Herramientas nuevas: `tools/scrollsim.py` (la lista del copper de cada
  frame, simulada con el modelo medido, contra el render del PC),
  `tools/scrollprof.py` (ciclos por frame y por rutina de `scroll.s` en
  Musashi), `tools/shots6.ps1` (capturas de WinUAE en varias x, con
  reintentos) y `scroll_check.py --sc 2` (capturas de WinUAE ×2, sin el
  borroneo de FS-UAE).
- Queda (6.x): los postes de la meta (s ≈ 4540-4580) tienen más cambios de
  color de los que el copper alcanza (ancho de banda), y los 72 px de
  x = 3500 (iguales antes y después: no son del copper; sin investigar).

0.5 **HECHA:** commit sin "WIP" (rama `etapa0-cierre`). §1 actualizado.

### Etapa 6 — Terminar el scroll

**Dónde:** cloud; 6.5 en la PC. **Parte de:** `player/scroll.s`,
`tools/mkscroll.py` y el formato `yi1_s.dat` (documentado en la cabecera de
`mkscroll.py`).

6.1 **Pantalla de 256 px** (D10).
- DIW centrada, por ejemplo `DIWSTRT $2CA1` / `DIWSTOP $0CA1`, y fetch
  `DDFSTRT $40` (una palabra antes de `$48`) / `DDFSTOP $C0`. **Comprobar
  estos valores con una captura antes de construir encima.**
- `mkscroll.py`: `VIS = 256`. Recalibrar el modelo del copper (`HOFS`,
  `XKNEE`, `HKNEE`, `LASTX`, `BLANKH`) con `copcal.s` + `copcal.py gen/read`
  en la pantalla nueva, porque el borrado horizontal queda más largo.
- Confirmar con una captura que el sprite 7 tiene DMA. Después, volver a
  correr `oamstudy.py`, `d8demote.py` y `copsim.py` con el número real de
  columnas.

**Hecho cuando** `scroll_check` da lo mismo o menos que a 320 px, el coste
queda re-medido y las simulaciones de sprites están re-corridas y anotadas.

**HECHA el 2026-09-27 (PC, WinUAE KS 1.2):**
- `scroll.s` y las herramientas llevan `VIS` (256 por defecto; `-DVIS=320`
  arma la pantalla vieja **byte a byte igual** a la de antes). DIW
  `$2CA1`/`$0CA1`, fetch `$40`/`$C0`, 17 palabras por línea; los valores
  del roadmap eran correctos.
- Copper recalibrado (**P46**): la misma rejilla con h − `$48`,
  x = 8·⌊(h − `$48`)/4⌋ − 1 hasta h = `$C0` (x = 239); después `$C4` → 243,
  `$C8` → 247, `$CC` → 251, `$CE` → 255 (macro `TAILH`). El borrado sigue
  terminando antes de x = 0 (P43).
- Imagen, `scroll_check --mid --sc 2 --w 256`, fallos que no explica un
  vecino: 500: 0, 846: 1, 1000: 0, 1700: 0, 1936: 0, 2500: 0, 3500: 72,
  4500: 75 (a 320: 0, 0, 0, 0, 0, 0, 72, 54; en 4500 la ventana ve otra
  parte del nivel). `scrollsim --speed 2`: 14 868 px mal en todo el
  recorrido (320: 19 586).
- Coste, `-DBENCH -DSPEED=4`: media **22,1 %** (320: 27,3 %), máx. 278,5 %
  en s = 4568 (320: 320,6 %). Musashi: 26 813 ciclos de media (320:
  30 963). A 2 px/frame, 433 frames pasan del frame (320: 487).
- **Sprite 7 con DMA: sí.** `scroll.s -DSPRTEST` dibuja los 8 sprites: a
  256 px se ven los 8 (4 columnas adosadas); a 320, solo 0-5.
- `oamstudy`, `d8demote` y `copsim` dan lo mismo que lo anotado en
  `AGENTS.md` §9 (ya modelaban 256 px y 4 columnas; ahora la premisa está
  medida): 2310 líneas piden 5-6 columnas, 45 de 2500 frames sin resolver
  con un bob, 1916 cargas de la capa 1 que no entran. El borrado no es el
  límite (como mucho 9 MOVE); `--hbl` no cambia nada.

6.2 **Cámara en las dos direcciones.** Hoy `lo_tab`, `vu` y la lista de
cambios de color (`CHG`) solo avanzan.
- Guardar en `CHG` también el valor anterior (o repetir los cambios al
  revés).
- Dibujar la columna nueva por el borde izquierdo.
- Hacer que las sombras de `build_mid` (`vu`, `wake`) valgan también cuando
  `s` baja.
- Prueba: recorrer 0 → 4800 → 0 y comparar las capturas de ida y de vuelta
  en la misma x: tienen que ser idénticas.

**Hecho cuando** la ida y la vuelta dan la misma imagen en 6 puntos.

**HECHA el 2026-09-27 (PC, WinUAE KS 1.2), con una salvedad de 1 píxel:**
- `build_mid` reescrito: las cargas a mitad de línea se planifican en
  `mkscroll.py` **en coordenadas del nivel** (MLD, 12 bytes: clase, x,
  MOVE, a, b) y la Amiga solo copia, por línea, las que caen en
  `[s, s + LASTX]`. Lo escrito queda fijo en pantalla y vale mientras
  `s0 + a <= s < s0 + b` (intervalo por carga); la línea se reescribe cuando
  deja de valer, cuando entra o sale una carga, o cuando la cámara vuelve.
  Solo se miran las líneas de la lista `LNS[s >> 4]`. No depende de la
  dirección.
- `CHG` guarda también el color viejo (se deshace al volver); las columnas
  nuevas entran por el lado hacia el que va la cámara; `-DRETURN=r` y
  `-DS0=n` para probar.
- Simulación (`scrollsim.py`, 2 px/frame): 9282 px mal en todo el nivel
  (antes 14 868); ida y vuelta **idénticas en los 2431 frames** (tras P50).
- Coste (Musashi, CPU sin DMA): media **9,9 %**, peor **54,1 %** (s = 4580);
  antes 22,1 % / 278 % en WinUAE. A 4 px/frame, 13,4 % / 59,2 %.
- Capturas de WinUAE a ida y vuelta (`shots6.ps1 -Extra`, `work/r62f2`,
  `work/r62b2`): idénticas en 500, 1000, 2500, 3500 y 4500; en **1700
  difiere 1 píxel** (línea 174, x = 244): P51, el copper es más rápido
  después de `DDFSTOP` y el modelo no lo tiene. `scroll_check` (fallos que
  no explica un vecino): 0 / 0 / 43-44 / 0 / 72 / 45.

6.3 **Conectar la cámara del port (`mcam.c`) — modo replay.** El scroll deja
de avanzar solo: lo mueve `Bg1HOfs`, calculado por `level_frame()` a partir
del joypad **grabado en el oráculo** (`$15-$18` de `oracle_yi1.txt`, metido
en el ADF). Es la primera prueba de lazo cerrado en la Amiga.
- En el frame N, capturar y comparar con el esperado del PC para la cámara
  `$1A-$1B` del oráculo en N.
- Ventana vertical: en la partida la cámara no se movió nunca en Y (192).
  Confirmar con el ajuste de scroll vertical del header (byte 4, bits 4-5) y
  `lv_scroll.s` si en Yoshi's Island 1 puede moverse. Si puede, dejar el
  soporte vertical para el final y documentarlo.

**Hecho cuando** la Amiga sigue la partida grabada y las capturas coinciden
con el esperado en al menos 5 frames repartidos por el nivel.

**HECHA el 2026-09-27 (PC, WinUAE KS 1.2):**
- `player/game.s`: un solo binario con el C (`level_frame`, datos a menos
  de 32 KB de `binstart`, P36) y `scroll.s` como biblioteca (`SCROLL_LIB`:
  `scroll_init` / `scroll_frame`). Cada frame, desde la línea `$110`:
  entrada → `level_frame` → Mario (6b.4) → `scroll_frame` con
  s = `Bg1HOfs`. El binario se copia solo a la slow RAM (todo es relativo
  al PC o a `a4`) y libera la chip: no entraba en 512 KB. Build:
  `sh tools/game_build.sh` (`GDEFS`, `OUT`).
- `-DREPLAY`: `m68kverify.py --mode loop --sprites --replay` escribe
  `work/yi1_replay.bin`: el tramo 5145-11457 (6313 frames) con el joypad y
  las mismas resincronizaciones del lazo cerrado del PC (RUN 6177, SYNC 3,
  SKIP 129, RUNSYNC 4). La Amiga hace exactamente eso.
- `tools/gamecheck.py`: el binario del juego en Unicorn, frame a frame:
  **0 diferencias** con el oráculo en los 6177 RUN. La cámara recorre 0-2492
  y vuelve (el vertical queda en 192 toda la partida). **Corregido el
  2026-09-30:** el header de YI1 **sí** tiene scroll vertical
  (`wm_VertScrollHead` = 2); `lvparse.py` leía mal el byte 4 (P77, §10.2b).
- Capturas (`tools/shots63.ps1`, `-DSTOPF`): frames 6000 / 7000 / 8000 /
  9000 / 10000 / 11000 → fallos que no explica un vecino **0 / 0 / 0 / 0 /
  0 / 6** (el 11000, con la cámara volviendo).
- Coste de la lógica en el juego (Musashi, sin DMA): media 20,9 %, peor
  29,3 % del frame.

6.4 **Bajar el coste a ≤ 25 %** en el peor frame con columna. Primero,
el pico de s = 4504 (Etapa 0.3). Ideas
anotadas en `AGENTS.md`: `blit_steps` (0.3); en `build_mid`, tablas en vez de
`mulu` y no reescribir las h si `s` no cambió; un solo WAIT por cadena de
cargas (P39). Perfil con `m68kverify.MusashiCPU` y el listado `-L`: el
script de perfil por zonas se perdió con el contenedor y hay que rehacerlo
en `tools/`, no en `/tmp`. **Hecho cuando** `scroll_read.py` da ≤ 25 % de
máximo sin empeorar la imagen.

**Estado al 2026-09-27: NO hecha.** Con el `build_mid` de 6.2 el peor frame
bajó de 278 % (WinUAE) a **54,1 %** (Musashi, cota inferior; en WinUAE sin
medir todavía con `-DBENCH`). Media 9,9 %. 172 de 2432 frames (a 2 px)
pasan del 25 %, en s ≈ 900, 1700-2000, 2600-2700 y 4100-4800.
- Perfil del peor frame (s = 4580, `scrollprof.py --at`): **`build_mid` es
  el 95 %**: reescribe 55 de las 108 líneas con cargas, 276 cargas. Cada
  carga cuesta ~130 ciclos (copiar el MOVE, el intervalo de validez con
  máx./mín., la clase) y cada línea reescrita ~450 más. El bucle ya está
  cerca del mínimo: pulirlo da < 10 %.
- **Hay que reescribir menos líneas.** Las cargas no tienen intervalos
  "sueltos" (ancho b − a: mediana 256, pero 5 % < 43) y casi todo el coste
  del peor frame es "entra una carga por la derecha" (38 de 52 líneas en
  s = 4580). Ideas medidas en simulación (`skipsim*.py`, scratchpad de la
  sesión): añadir por la derecha sin reescribir la línea (−4 % del máximo);
  reescribir desde la primera carga que deja de valer (y desde su WAIT);
  WAIT propio para las cargas de la cola (P51, arregla también 1 px).

**Estado al 2026-09-30 (cloud): sigue sin hacer, con el problema medido.**
- Herramientas: `scrollprof.py --zones` (ciclos por etiqueta de un frame,
  el perfil que se había perdido) y `scrollsim.py --ret` (ida y vuelta,
  compara la imagen simulada en cada s).
- Peor frame de la ida (s = 4580, 76 850 ciclos en Musashi): `build_mid`
  ~95 %, 55 líneas reescritas y 276 cargas (~124 ciclos por carga, ~520 por
  línea, ~7,8 k para recorrer las 108 líneas de LNS). Por qué se reescriben:
  24 líneas por una carga "tarde" (en **todos** los frames, P50; 34 cargas
  tarde en x ≈ 4817-4861, los postes de la meta), 25 porque entra una carga
  por la derecha y 6 porque caduca una.
- **La vuelta es peor que la ida** (P72): media 36,6 %, máx. 94,8 %.
- Probado y descartado: reescrituras completas con validez por ventana
  (modelo: ida máx. 48,6 %, vuelta 78,8 %). En la Amiga salió **peor**
  (máx. 97,6 %: ~330 ciclos por carga) y la ida y la vuelta diferían en
  s = 4684-4780 (P71).
- Siguiente: `tools/wip64/build_mid_incremental.s` (rebase de la h de cada
  WAIT en el sitio, append y truncado por la derecha; en el modelo, ida 38 %
  y vuelta 56 %); para los eventos en bordes verticales, repartirlos entre
  frames (holgura b + 6 px) y neutralizar las cargas muertas en el sitio
  (MOVE a `$1FE`); el recorrido de LNS por grupos de 16 líneas. Modelos en
  `tools/wip64/midsim*.py`.
- FS-UAE: `scroll_check.py` buscaba el origen solo hasta x = 200 (320 px);
  a 256 px daba ~30 % de fallos falsos. Arreglado.

6.5 **PC:** capturas de WinUAE `-Exact` **sin reescalar** en los 6 puntos
contra el esperado del PC, y arranque en KS 1.2.

### Etapa 7 — Capa 2 contra la referencia

**Dónde:** PC.
- `python tools/render_d.py` → `work/yi1_d_nivel.png` (imagen ideal, sin
  paralaje, igual que el mapa estático de la referencia).
- `cmp_ref.py --mine work/yi1_d_nivel.png --mask none --bits 4`. Los colores
  del blob están cuantizados a 12 bits: a 5 bits difiere todo.
- Recortes apilados de todo el nivel (5 tiras de 1024 px) con `crop_ref.py`.

**Hecho cuando** el diff baja del 25,52 % (el valor solo con la capa 1), lo
que queda cae debajo de sprites o es cuantización, y a la vista las montañas,
las nubes y los pilares coinciden.

### Etapa 8 — Mario: cerrar la 8c y bajar el coste

8.1 **Sesión de grabación única** (PC + usuario). Juntar todo lo que hace
falta grabar:
- **Colinas (8c):** a toda carrera en las dos direcciones, parado sobre la
  pendiente, deslizándose y saltando sobre pendientes.
- **Sprites (9):** pisar y tocar cada tipo de D3. Dejar que un Banzai Bill
  cruce la pantalla, que la piraña salga con Mario al lado de la tubería,
  pelear con el Chuck, patear el caparazón rojo y cortar la cinta de meta.
- **Power-ups (D12):** agarrar cada uno; con la flor, disparar.
- **Muerte, punto medio y meta** (12).
- **HUD (10):** hoy el grabador no guarda los contadores (vidas `$0DBE`,
  monedas `$0DBF`, tiempo desde `$0F31`, puntuación desde `$0F34`...). Agregarlos a
  `tools/oambot.lua` **respetando los límites** (V6). Direcciones exactas en
  `equates/memory.i`.
- **Audio (11):** grabar el audio de `smwrecomp` a WAV en la misma partida.

Pasos: probar el grabador (`oamrec.py --test 10`); grabar con `python
tools/oamrec.py --out work/oracle_<nombre>.txt`, **nunca** encima de
`oracle_yi1`; después `oracle2bin.py --inp ... --out ...` y `marioverify
<bin> full` / `loop`. Commitear los `.txt` (V4).

**Desde el 2026-09-30 se graba en cloud, sin el usuario** (P67, P68):
`sh tools/snesorc_setup.sh` clona snesrev/smw (commit fijo) fuera del repo
y compila `work/snesorc`, que corre la ROM (U) en su emulador con los
parches de snesrev deshechos. Un guion `.orc` (`tools/snesorc/`: `N
RIGHT+Y`, `until w$0094>=07B0 max 600 RIGHT+Y`, `assert`, `include`...)
arranca desde el encendido (`boot_yi1.orc` llega a YI1 en el frame 1452) y
vuelca el mismo formato que `oamrec.py`. `sh tools/snesorc_make.sh`
regenera los `.txt` y corre `marioverify`; `--replay` valida el generador
contra `oracle_yi1` (6871/6871 líneas idénticas). Limitaciones: sin
guardar/cargar estado (4000 frames tardan < 1 s), y cambiar una línea de un
guion mueve el RNG y los tiempos de lo que sigue (los `assert` lo detectan).
Lo único que sigue pidiendo la PC es el audio de referencia (11).

**Hecho cuando** las grabaciones están en git y la 8c da 100 % en los frames
de pendiente, o los fallos quedan listados por causa.

8.2 **Optimizar la lógica en C nativo** (cloud; el usuario ya eligió este
camino). Red de seguridad: V1 en cada commit.
1. Perfil: `PROF=1 sh tools/logicbench_build.sh && python3 tools/m68kprof.py
   --sprites`. `m68kprof` no tiene tope: si el binario se cuelga (P38), no
   termina nunca. Probar antes con `m68kverify`.
2. **Estado de Mario en variables nativas.** El coste de fondo es emular la
   WRAM byte a byte: cada valor de 16 bits son 2 lecturas + `lsl` + `or`,
   ~50 ciclos. El método:
   - un accesor (macro en `smwmac.h`) por cada campo caliente: posición,
     subpíxel, velocidades y flags de `$77`/`$72`;
   - en un commit por grupo, el almacenamiento del campo pasa de `ram[]` a
     una variable nativa big-endian;
   - todos los lectores, sprites incluidos, van por el accesor;
   - el verificador sincroniza `ram[]` ↔ variables en la frontera del frame,
     y solo en los builds de verificación.
3. Si el C no alcanza: las sondas de colisión (`f44d`/`f461`/`f545`, ~28 %
   de `level_frame`) en ensamblador a mano, verificadas con `m68kverify`.
4. **No optimizar `e45d`** (OAM de Mario, ~12 % de `level_frame`): en la Amiga Mario no usa
   OAM. En la 6b se reemplaza por la elección directa del frame de sprite.
   La versión OAM queda para el modo `gfx` del verificador.
5. Medir el **peor frame con sprites en cycle-exact**. Hace falta extender
   `logicbench`: meter `spr.lv` en el arnés (apuntar `_spr_level`),
   `level_sprites = 1` y un estado del oráculo con Rex a la vista.

**Hecho cuando** la lógica con sprites da ≤ 40 % en el peor frame (FS-UAE,
DPF encendido) y V1 es idéntica.

**HECHA el 2026-09-27 (PC).** Resultado, WinUAE KS 1.2 a 256 px:
- **Peor frame con sprites** (frame 7901, `logicbench -DWORST`):
  **40,1 %** medido, con ~0,4 % del propio banco (la entrada por
  `callframe`): **~39,7 %** real. Objetivo: ≤ 40 %. Semántica idéntica
  en todo (V1: `regress.py`, `abcheck.py` IGUAL en cada paso).
- **Sin sprites (8d):** 20,2 % corriendo / 20,5 % saltando (antes 25,8 /
  26,3 % a 256 px; 28,3 / 28,8 % a 320).
- Musashi, peor frame con sprites: 52 816 → **40 956** (−22,5 %); media
  con sprites 35 938 → 28 598.

Qué se hizo, por orden de ganancia:
1. **`NOOAM`** (el build de la Amiga no escribe la OAM: sin `ClearOam` ni
   las 4 entradas de Mario; quedan sus efectos en `HidePlayer`/`m4-m6`):
   −8 % en el peor frame, −11,6 % de media. `logicbench_build.sh` compila
   con `CDEFS=-DNOOAM` por defecto; el PC (modo `gfx`) sigue con la OAM.
2. **Ensamblador a mano, `player/logic68k.s`:** `spr_tile`, `f44d`,
   `spr_pos_axis` (con `addx`), `get_draw_info`, `camera_F6DB`, `f7f4`,
   `spr_mario_contact`, `rex_main`, `spr_update_pos`. Cada rutina
   reemplaza a la de C **solo** en el build de la Amiga (vbcc sin
   `NOASM`); el C queda como referencia y para los casos raros (el asm
   salta al C con los mismos argumentos). Las direcciones salen de
   `work/cc/smwram.i` (generado de `smwram.h`, `smwtab.h` y el enum de
   `mario.h`); las tablas de la ROM se leen por puntero
   (`logic68k_init`), nada de la ROM en el asm (R9).
3. C: `sprite_load_level` sin recorrer el nivel, `f04d` con tabla,
   `init_sprite_tables` desenrollado, `spr_tile` sin MULU.

Probado y descartado: flags de vbcc (igual o semántica rota, P38);
partir `sprite_run` para hacer los temporizadores en asm (vbcc deja de
incorporar el despacho y sale peor). Queda sin ensamblador, si hiciera
falta margen: `spr_obj_vert`, `spr_obj_interact`, `spr_spr_interact`,
`eb77`, `f636`, `e92b`, `sprite_run` entero.

**Estado intermedio (histórico):**
- **Dónde estamos.** `logicbench -DVIS256` (la pantalla de la 6.1) en WinUAE
  KS 1.2: 25,8 % corriendo / 26,3 % saltando. Factor WinUAE/Musashi del
  mismo trabajo: **1,39** a 256 px (1,50 a 320). Peor frame con sprites en
  Musashi: 51 354 ciclos → **~50 % estimado** en la Amiga. Objetivo 40 %:
  falta **~−20 %** en el peor frame (≤ ~40 800 ciclos en Musashi).
  El paso 5 (medir el peor frame con sprites directamente en cycle-exact)
  sigue pendiente; esto es una estimación con el factor medido.
- **Perfil** (`m68kprof.py --sprites --every 1 --worst N --at F --hot N`):
  **plano**, ninguna instrucción pasa del 1 %. Por familia: `move` con
  `ram[]` 17 %, `movem`+`jsr`/`rts` ~15 % (llamadas; el build real
  incorpora en línea parte), `and.l #255` y desplazamientos ~14 %
  (promoción de `u8` a `int`). El peor frame persistente (7856-7996) es
  de sprites: `spr_tile` (colisión de sprites con bloques, NO es OAM),
  `sprite_load_level`, `spr_pos_axis`, `get_draw_info`, `rex_main`,
  interacciones; el peor absoluto (9670) es un frame con aparición.
- **Hecho:** `sprite_load_level` sin recorrer el nivel (−2,2 %),
  `init_sprite_tables` desenrollado, `spr_tile` sin MULU (−0,6 %). Peor
  frame con sprites 52 816 → **51 354** (−2,8 %), semántica IGUAL.
- **Descartado:** flags de vbcc. `-speed`, `-inline-size`,
  `-maxoptpasses`, `-unroll-size` dan el mismo binario; `-O=1023`/`4095`
  cambian la semántica (433 resincronizaciones en vez de 37: P38).
- **Lo que queda, por tamaño estimado:**
  1. **OAM fuera del build de la Amiga** (lo que la 6b.4/9.2 reemplaza):
     solo las escrituras directas a `$200-$46F` son el 4,6 % de la media
     (casi todo `ClearOam`); con `e45d` y los gráficos de sprites, ~8-12 %.
     El verificador (`gfx`) sigue con la OAM. Es diseño de la 6b.4: se
     consulta antes.
  2. **Ensamblador a mano** en `f44d`/`f461` (sondas), `spr_tile` y
     `camera_F6DB` (paso 3): ~12 000 ciclos del peor frame; a la mitad,
     ~−12 %.
  3. **Estado nativo** (paso 2): el perfil dice que las rearmadas de 16
     bits ya son pocas; ganancia estimada ≤ 5-8 %.
  Con 1 + 2 se llega; con micro-optimizaciones de C (0,5-2 % cada una)
  no.

### Etapa 6b — Integración: el primer ADF jugable

**Dónde:** cloud; arranque en KS 1.2 en la PC. **Objetivo:** un solo
binario que tome la máquina, cargue el nivel y cada frame lea el joystick,
corra `level_frame()`, mueva el scroll y dibuje a Mario.

6b.1 **Carga y memoria (D13).** Inventario de la chip RAM, estimado a partir
de las constantes actuales (320 px):

| bloque | bytes |
|---|---|
| PF1 circular | 59 136 |
| 2 listas del copper | ~98 800 |
| `yi1_s.dat` | ~126 KB |
| código + datos del C | ~58 KB |

Unos 340 KB antes de sprites y audio. En `yi1_s.dat`, `BLK` y `L2B` las lee
el chipset y se quedan en chip; `MAP`, `CHG`, `MLX`, `MLD` e `INI` las lee
solo la CPU y van a slow RAM.

Pasos, con el esquema de D13 (§3):
1. `tools/mkgame.py` (nuevo): parte los datos en secciones "chip" y "CPU",
   las comprime y escribe la tabla de carga (dirección destino, tamaño,
   alineación), que el loader recorre.
2. Script de enlace de vlink con las direcciones fijas.
3. Loader nuevo (`player/loader.s`), que reemplaza la carga de `demo.s` y
   `scroll.s`, y `tools/mkadf.py` extendido para varios bloques.
4. `tools/memmap.py` (§8.2) comprueba el mapa.

**Hecho cuando** hay un mapa de memoria escrito en `AGENTS.md` §4, con
cifras medidas, el loader lo respeta, el tiempo de carga está medido y
V1 pasa sobre el binario enlazado en absoluto.

6b.2 **Bucle del frame.** Latencia de un frame, como la SNES, que sube en el
NMI lo que calculó el frame anterior:

```
VBL: cambiar a la lista del copper preparada → lanzar el blit de la columna
     → leer la entrada → level_frame() (cámara, Mario, sprites)
     → preparar la lista siguiente (build_mid, punteros de planos y sprites) → esperar el VBL
```

Juntar `scroll.s` y el arnés del C, enlazados en absoluto con vlink (D13).
`m68kverify`/`abcheck` tienen que aprender a cargar el binario en su
dirección fija, en vez de en `BASE`. Después de juntarlos, correr V1 sobre
el binario nuevo.

6b.3 **Entrada (D14), teclado primero.**
- **Teclado.** Al tomar la máquina, el SO ya no lee el teclado: hace falta
  un manejador propio.
  - Interrupción de nivel 2 (`PORTS`, CIA-A `ICR` bit `SP`).
  - Leer `CIA-A SDR`; el código raw es `~byte` rotado un bit a la derecha
    (`not.b` + `ror.b #1`); el bit 7 = tecla soltada.
  - **Handshake:** poner `CIA-A CRA` bit 6 (`SPMODE` salida) durante
    ≥ 85 µs (unas 2 líneas; medir con `VHPOSR`, no con un bucle) y volverlo
    a entrada. Sin handshake, el teclado reintenta y se pierden teclas.
  - Mantener un mapa de 128 bits de teclas apretadas.
- Asignación de §3 (D14) en una tabla.
- **Joystick** (alternativa): `JOY1DAT`, fuego en CIA-A `PRA` bit 7 y 2.º
  botón en `POTGO`/`POTINP`; se combina con el teclado con un OR.
- Convertir al formato de la SNES en `$15-$18`: `JoyPadA/B` = mantenido y
  `JoyFrameA/B` = recién apretado (`nuevo & ~anterior`), que es lo que
  espera el port.
- Teclas de depuración reservadas, que no usa el juego: pausa por frames y
  modo replay.

6b.4 **Mario en sprites de hardware.**
- Herramienta nueva `tools/mkmario.py`: toma las poses que aparecen en el
  oráculo (el modo `gfx` da los tiles de cada frame) y los tiles de `chr` a
  4 bpp, y genera frames de **sprites adosados** (16 colores) con las
  versiones volteadas precalculadas: el hardware no voltea.
- Comprobar el ancho máximo de las poses. Si alguna pasa de 16 px, usar un
  segundo par de sprites.
- La paleta de Mario (P10) va a los colores 17-31, cuantizados a 12 bits.
  En DPF esos colores no los usa nadie.
- Ajustar `BPLCON2` (`PF1P`/`PF2P`) para que los sprites queden delante de
  las dos capas. Hoy vale `$0000` porque no hay sprites.

6b.5 **Verificación.** El modo replay de la 6.3 + Mario: la captura del
frame N tiene que coincidir con el render del PC para la cámara y la OAM de
Mario del oráculo en N. Extender `scroll_check.py` o escribir
`game_check.py`.

6b.6 **Medida.** Peor frame del juego integrado, con `-DBENCH` y FS-UAE →
**compuerta D1** (§2).

**Estado al 2026-09-27 (en curso):**
- 6b.1: el juego carga con el loader de siempre (`boot.s` + `mkadf.py`):
  binario (~180 KB) a slow RAM y `yi1_s.dat` a chip. Sin compresión ni
  vlink todavía.
- 6b.2: hecho en `game.s` (arriba, 6.3). Latencia de un frame: la lista del
  copper, los punteros de sprites y la paleta de Mario de un frame se ven
  juntos.
- 6b.3: `game.s` sin `-DREPLAY` = en vivo. Teclado por la interrupción de
  nivel 2 (handshake de >= 2 líneas con `VHPOSR`), tabla D14 (`keytab`),
  joystick del puerto 2 (botón 1 = B, arriba + botón = A, botón 2 = Y), OR
  de los dos → `$15-$18`. Lo que el port no tiene (animaciones de Mario,
  meta, tuberías...) congela el frame: a los 1,5 s el nivel vuelve a
  empezar (se guardan al cargar los datos del C y el mapa). Daño sin
  animación: grande → chico con invulnerabilidad; chico → reinicio.
  **Sin probar con teclas en el emulador todavía.**
- 6b.4: `mgfx.c` (NOOAM) deja las 4 entradas de Mario en `mario_oam` /
  `mario_osz` y la paleta en `mario_pal`; `player/mspr.c` (referencia) y
  `player/mspr68k.s` (el caso de siempre, con `MOVEP.W`, ~10 400 ciclos =
  7,3 %) arman dos parejas de sprites adosados desde GFX32
  (`tools/mkmario.py`: `gfx32.bin`, `gfx32f.bin` volteado, `mario_pal.bin`).
  `marioverify mspr` (PC, `-DNOOAM`): OAM = oráculo y sprites = render de
  referencia en 6869/6869; `gamecheck.py --spr`: vbcc y asm = referencia en
  6184/6184 (el asm fue al C 1 vez). Coste extra de la lógica por llenar
  `mario_oam`: ~2 300 ciclos (Musashi, peor frame con sprites 43 280).
- 6b.5: `tools/game_check.py` (fondo + Mario contra la captura).

**Hecho cuando** el ADF se juega con joystick en FS-UAE y en WinUAE con
KS 1.2, el replay coincide con el oráculo y el presupuesto está medido y
presentado al usuario.

### Etapa 9 — Sprites del nivel

9.1 **Lógica** (cloud; en paralelo con la 6 y la 8.2).
- Orden (D3, por frecuencia y porque destraba la verificación):
  1. Koopa sin caparazón (`$02`, sale del Sliding Koopa `$BD`): es la última
     resincronización de `game`;
  2. Banzai Bill (`$9F`);
  3. Jumping Piranha (`$4F`);
  4. Clappin' Chuck (`$95`);
  5. caparazón rojo (`$DB` → `$05`, estado 9);
  6. cinta de meta (`$7B`);
  7. warp hole (`$8E`) y champiñón invisible (`$C7`);
  8. lo que sale de los bloques (D12, §3): seta, flor y **bolas de fuego**
     (`MARIO_UNSUP_FIRE`), estrella (invencibilidad + música), 1-UP, luna
     3-UP, champiñón invisible, monedas, monedas de Yoshi y puntos. Más la
     caja de reserva y el crecer / encoger de Mario (animación `$71`, hoy
     "sin física normal").
- Método (P27): transcribir `sprite_*.s` instrucción por instrucción, sobre
  `ram[]` como el Rex; tablas de otros bancos con `tools/smwtabx.py`.
- Verificar con `marioverify game` / `sprloop` y `m68kverify --sprites`
  (V1). Trampas conocidas de la 9: `ROL` del carry en `CODE_01A56D`,
  `RexSpinKill` pasa a estado 4 y no a 0, y al resincronizar hay que copiar
  también `SpriteXAcc`/`YAcc`.
- Si la grabación no cubre el comportamiento de algún sprite, pedirlo en la
  sesión única (8.1), no en una aparte.

**Hecho cuando** `game` da 0 resincronizaciones, o solo por eventos
documentados como fuera de alcance.

**Estado al 2026-09-30:** portados y verificados `$BD`, `$02` (sin la
parte de caparazones), `$9F`, `$4F`, `$8E` y `$C7`, más el contacto por
defecto con Mario (pisotón, salto con giro, daño), los estados 2-4,
`GetDrawInfoBnk1`, `FlipSpriteDir`, las pendientes empinadas y la carga de
los sprites al empezar el nivel (P65). `game` da 0 resincronizaciones en
`oracle_yi1` y en las 4 grabaciones de snesorc; `regress.py` cuenta los
frames exactos por tipo de sprite (`pc.game.spr_XX.*`). Sin verificar:
Banzai pisado, `$02` con caparazones, salto con giro sobre el Koopa, tocar
el `$C7`. Sin portar: Chuck (`$95`, nunca aparece en `oracle_yi1`: grabarlo
con snesorc), caparazón rojo, cinta de meta y los power-ups.

9.2 **Dibujo en la Amiga** (cloud; diseño de D8 (d), `AGENTS.md` §9 puntos 9
y 10).
1. **Antes de programar**, volver a correr `oamstudy.py`, `d8demote.py` y
   `copsim.py` con el número real de columnas (6.1) y la pantalla final.
2. Conversor: gráficos de cada sprite (Rex y Banzai en el GFX `20`) →
   frames de sprites adosados, más la versión bob con máscara. Paleta por
   fila de cada objeto.
3. Asignador por frame (CPU): objetos → columnas por franja de líneas. El
   copper recoloca `SPRxPOS` entre líneas y recarga los colores 17-31 por
   línea. Si una línea pide más columnas de las que hay, un objeto pasa a
   bob en PF1: casi siempre el Banzai (`d8demote`). `copsim.py` es la
   implementación de referencia: la salida de la Amiga se compara contra la
   suya.
4. Bobs en PF1: se restauran desde `BLK`. Ojo con el buffer circular: un bob
   que cruza el reenganche tiene que ir a las dos copias.
5. Verificar: el replay contra el esperado con la OAM de `oam_yi1.txt`.
   Medir el peor frame: Banzai + 4 Rex + Mario.

**Hecho cuando** los objetos se ven 1:1 en las capturas del replay y el
coste entra en §2.

### Etapa 10 — HUD

1. Medir en `yi1_d` con la cámara Y final cuántas líneas ocupa el HUD de la
   SNES y si en ellas aparece alguna vez la capa 1. Si aparece, buscar una
   variante que conserve el overlay antes de consultar (D11). Por ejemplo:
   el HUD en PF1 con los colores 1-7 del HUD y la capa 1 de esas líneas
   compuesta en el mismo bitmap, que es barato si son pocas líneas.
2. Overlay (D11): en esas líneas, el copper apunta PF1 a un bitmap fijo del
   HUD (retardo de PF1 = 0, colores 1-7 del HUD) y PF2 sigue igual. Gráficos
   de la barra: tiles de capa 3 a 2 bpp (los `gb-*`; `gb-1` es el juego de
   caracteres). Los números y la reserva se blitean solo cuando cambian.
3. Lógica: portar la actualización de la barra de `game.s` (tiempo,
   monedas, vidas, puntuación, monedas de Yoshi, estrellas, reserva).
   Verificar contra los contadores de la grabación 8.1.

**Hecho cuando** la barra coincide con la referencia y con los contadores
grabados, y el coste es ≤ 2 %.

### Etapa 11 — Audio (D5)

1. `tools/brr2pcm.py`: BRR (ADPCM) → PCM de 8 bits **con signo** (P7), sin
   sesgo DC. Verificar contra el WAV de `smwrecomp` (8.1).
2. D5: convertir offline las secuencias de `sound/` (N-SPC) a un formato
   compacto de eventos con los efectos ya resueltos:
   - notas con periodo de Paula precalculado;
   - glissando y vibrato como tablas de deltas por tick;
   - envolvente ADSR como tabla de volumen por tick.

   El secuenciador 68000 solo recorre eventos y escribe `AUDxPER`/`AUDxVOL`/
   `AUDxLC`/`AUDxLEN`: nada de mezcla ni de cálculo por muestra. El tick sale
   de un timer de CIA, no del VBL: el tempo del SPC700 no depende de 50/60 Hz.
3. 8 voces → 3 de música + 1 de efectos. Elegir las voces por prioridad en
   cada tema (y la de la estrella). El eco no existe: se omite. Cuando suena
   un efecto, la voz de música que comparte canal se silencia, como en la
   SNES con prioridades.
4. Efectos: el port ya escribe los disparadores (`wm_SoundCh1/2/3`, por
   ejemplo en `mario.c`): engancharlos ahí.
5. Presupuesto: ≤ 64 KB de muestras en chip RAM y **≤ 3 %** de CPU
   (medido con el método de `bench2.s`).

**Hecho cuando** el tema del nivel y los efectos principales (salto,
moneda, pisotón, power-up, 1-UP) suenan reconocibles contra el WAV de
referencia, con el coste medido.

### Etapa 12 — Pulido y entrega

- Muerte y reinicio, punto medio, cinta de meta y secuencia final, tiempo
  agotado, transiciones con fundido por copper.
- Si alguna tubería del nivel es entrable (mirar las salidas de pantalla
  del nivel), su transición.
- Prioridad sprite/capa 1 donde la SNES pone a Mario detrás, por ejemplo
  el poste de la meta.
- ADF final: bootblock propio + loader de todas las pistas, ≤ 880 KB.
  Probado en WinUAE con KS 1.2 y 1.3, y en hardware real si el usuario
  quiere (opcional).
- R9: el ADF lleva material derivado de la ROM; es de uso personal y no se
  distribuye.

**Hecho cuando** se puede jugar el nivel de principio a fin en la
configuración objetivo, a la frecuencia que fijó D1, y `AGENTS.md` §10 queda
cerrado.
