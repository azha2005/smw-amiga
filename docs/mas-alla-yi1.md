# Más allá de YI1

> Movido textual desde `ROADMAP.md` §11 el 2026-10-03.

---

## 11. Más allá de YI1: otro nivel y la lógica extra del juego

Esto **no** está en el alcance de hoy (`AGENTS.md` §1: un nivel). Queda
escrito para cuando YI1 esté terminado, y para no cerrar puertas mientras
tanto: las decisiones de las etapas 6b.1, 9.2 y 11 tienen que dejar sitio
para esto.

### 11.1 Qué es de YI1 y qué es genérico

| pieza | hoy | para otro nivel |
|---|---|---|
| handlers de objetos (capa 1) | los que usa YI1, 1:1 | `lvparse.py --dump` del nivel nuevo: transcribir los que falten (mismo método, P16-P27) |
| tileset, Map16, paletas | tileset 7, `set_0`, `MAP16AppTable` | genérico en `mklvl.py`/`map16.py`/`palette.py`, pero **probado solo con YI1** |
| capa 2 | `Layer2Mountains`, paralaje a media velocidad | `mkbg.py` tiene que leer el fondo y el ajuste de scroll del nivel (`DATA_05F000`) |
| scroll vertical | ventana fija, líneas 192-415; YI1 lo necesita poco (10.2b) | `world_1/3` sigue a Mario todo el tiempo (`wm_VertScrollHead` = 1). Es el trabajo más grande (11.3) |
| colores (formato (d)) | 7 registros por línea de PF1 + cargas a mitad de línea | por nivel: medir primero con `dpfsplit.py` (derrames, cargas por línea) |
| sprites | los 11 tipos de YI1 | cada tipo nuevo se porta y se graba (9.1). Algunos son motores enteros: **Yoshi**, plataformas, agua |
| Mario | chico, grande, fuego | la **capa** (pluma) es un motor aparte (`MARIO_UNSUP_CAPE`); nadar (`WATER`), trepar (`CLIMB`) |
| herramientas | nombres y constantes fijos: `yi1_*.dat`, `LEVEL = "3340088027"` en `mkmario.py`, 20 pantallas, la ventana Y | un **descriptor de nivel** que lean todas (11.2) |

### 11.2 El proceso, paso a paso

0. **Elegir el nivel** con una tabla de viabilidad. De cada nivel, con
   `lvparse.py` y un recuento de `spr.lv`: pantallas, modo, tileset, scroll
   vertical, capa 2, sprites nuevos y si aparecen Yoshi o la capa. Hoy, en
   el mundo 1:

   | nivel (carpeta) | pantallas | modo | tileset | scroll V (`wm_VertScrollHead`) | sprites en `spr.lv` | comentario |
   |---|---|---|---|---|---|---|
   | `world_1/1` (YI1) | 20 + 2 | 0 | 7 | 2 (en algunos casos) | 11 tipos | el de hoy |
   | `yellow_switch` | 3 + 3 | 0 | 4 | 0 (no hay) | `$3E` ×1 | el más chico con juego: el interruptor del palacio (`MARIO_UNSUP_TILE`) |
   | `world_1/2` | 20 + 2 | 0 | 0 | 2 (como YI1) | `$00`, `$01`, `$05`×8, `$3E`, `$4D`×2, `$4E`×3, `$4F`, `$7B`, `$91`×2, `$B9`×2, `$DA`, `$DB`×2 | Koopas y caparazones (reusa P4), otro tileset; confirmar si sale Yoshi de un bloque |
   | `world_1/3` | 21 + 2 | 0 | 0 | **1 (sigue a Mario)** | `$05`×2, `$09`, `$0B`×4, `$55`×2, `$57`×2, `$59`×3, `$5A`×5, `$5F`×8, `$7B`, `$B9`×2 | scroll vertical de verdad y muchos sprites de plataforma |
   | `world_1/4` | 11 + 2 + 4 | 0 | 8 | 0 (la subzona de 4 pantallas: 2) | `$05`×3, `$15`×2, `$18`, `$3E`, `$47`×3, `$5D`×13, `$A4`×9, `$DB` | 13 + 9 sprites de dos tipos nuevos: ver qué son |
   | `castle_1` | 8 + 4 + 1 | 0 / 0 / 11 | 1 / 1 / 0 | 0 / 3 / 0 | 7 tipos + jefe | modo 11 y un jefe: al final |

   Los nombres de los sprites están en la tabla de punteros de
   `sprite_1-main.s`; la carpeta no es el número de nivel, así que hay que
   confirmar cuál es cuál con el translevel.
   Los valores salen de `lvparse.py` **después** de arreglar la lectura del
   byte 4 (P77).
   **Recomendación:** después de YI1, `world_1/2` (reusa casi todo: el
   mismo modo de scroll vertical que YI1, que ya estará hecho por 10.2b, y
   Koopas) o `yellow_switch` (chico, para probar la generalización barata).
1. **Generalizar las herramientas (una sola vez).** Un descriptor por nivel
   (`levels/<nombre>.json`: rutas de `obj*.lv`/`spr.lv`, cabecera, ventana
   de cámara, nombres de salida) que lean `mklvl`, `mkbg`, `mkd8in`,
   `mkleveld`, `mkscroll`, `mkmapbin`, `mkmario`, `smwgen` y los
   verificadores. Buscar con `grep` las constantes de YI1 (`yi1_`, `105`,
   `3340088027`, `192`, `20 * 0x1B0`...). Criterio: con el descriptor de
   YI1, **todo sale igual byte a byte** (`regress.py --level`).
2. **Capa 1 1:1:** `mklvl.py` + `m16diff.py` contra el mapa del nivel de
   SNESMaps (§5c de `AGENTS.md`: el mismo método; la referencia la tiene
   que bajar el usuario, en la PC). Objetivo: 100 % de bloques.
3. **Capa 2:** `mkbg.py` con el fondo y el paralaje del nivel.
4. **Formato (d):** `mkd8in` → `mkleveld`. Mirar derrames, cargas por línea
   y `scrollsim`: si un nivel pide más de lo que el copper da, se sabe acá
   y no en la Amiga.
5. **`mkscroll` → `<nivel>_s.dat`**, y `scroll.s` parametrizado por el
   descriptor (ancho, ventana).
6. **Sprites nuevos** (9.1 + 9.2): un guion de snesorc por tipo, el port
   contra la grabación y los frames precalculados.
7. **Música** (11): la captura del DSP del tema del nivel.
8. **Oráculo del nivel:** un guion de snesorc que llegue (por el mapa o con
   `poke` del translevel) y lo juegue de punta a punta; `marioverify
   full/loop/game` con su mapa (`mkmapbin` por descriptor).
9. **Integración:** la tabla de niveles del juego, la carga entre niveles
   (11.4) y el paso de uno a otro (salir por la meta → el siguiente).

### 11.3 El scroll vertical (el trabajo más grande de otro nivel)

El scroll de hoy está hecho sobre una ventana fija de 224 líneas (192-415
del nivel). YI1 se mueve poco y rara vez (10.2b, que resuelve el caso
chico); un nivel como `world_1/3` sigue a Mario todo el tiempo. Con scroll
vertical de verdad:

- **PF1:** buffer circular también en vertical (filas de bloques nuevas por
  arriba o por abajo, como las columnas) y el reenganche vertical por
  copper: cambiar `BPL1PT`-`BPL5PT` en la línea donde da la vuelta.
- **Colores por línea:** el plan de cargas de `mkscroll` está en
  coordenadas del nivel (x, y). Con la cámara en Y, la línea de pantalla L
  muestra la línea del nivel L + cam_y, así que la lista del copper se
  rearma entera cuando cambia cam_y: **todas las líneas cambian**. Idea
  (la de 10.2b, llevada a todo el nivel): segmentos indexados por línea
  del nivel, en los que solo cambia la v de los WAIT, en un pool que cubra
  la ventana más un margen arriba y abajo, que se rellena por la fila que
  entra (como las columnas de PF1). Se combina con los "segmentos
  compartidos" de §9.2 S3.
- **PF2:** su propio paralaje vertical (mover `BPL2/4/6PT`: gratis).
- Probarlo primero en YI1 con 10.2b, antes de ir a un nivel nuevo.

### 11.4 Cargar entre niveles

Hoy todo se lee con `trackdisk` antes de tomar la máquina (D13). Con varios
niveles hay que leer del disco **con la máquina tomada**:

- **(a) Loader por hardware (lo que hacen los juegos):** `DSKLEN`/`DSKPT`,
  una pista por vez al buffer, decodificar el MFM (CPU o blitter) y
  descomprimir. Es lo más robusto, permite música y una pantalla de carga
  animada mientras lee, y funciona igual en KS 1.2 y 1.3. Es trabajo de
  nivel F, con el riesgo de las diferencias entre disqueteras reales.
- **(b) Devolverle la máquina al SO para cargar:** restaurar
  interrupciones, DMA y la vista, leer con `trackdisk` y volver a tomarla.
  Es más simple, pero lento y frágil (el SO se quedó sin su chip RAM).
- **Recomendación:** (a), con un formato de disco propio: una tabla de
  pistas en el bootblock y cada nivel comprimido en pistas enteras.
- **Espacio en el disco:** YI1 ocupa hoy 412 KB (46 % del ADF). Sin
  comprimir entra como mucho un nivel más; comprimido (~50 %, estimado),
  3-4. Más allá, un segundo disco (DF1 o pedir el cambio).
- **Memoria:** un solo nivel residente. El código común queda en slow RAM
  (~190 KB hoy, y crece con cada tipo de sprite). La parte de CPU del nivel
  (~130 KB, 10.7) y la de chip (~95 KB: `BLK` + `L2B`) se cargan por nivel,
  junto con las muestras de su música.

### 11.5 Pantalla de carga, título y demo

- **Pantalla de carga:** una imagen fija de 5 planos (el logo "Nintendo
  Presents" de `spr-1` o el título, renderizados offline con las
  herramientas de la etapa 1) y una barra de progreso con el copper (un
  color que avanza por línea, sin CPU). Con el loader por hardware (11.4),
  además música desde la interrupción del VBL mientras lee.
- **Título:** la pantalla de título de SMW son capas 1/2/3 + sprites; una
  versión fija renderizada offline alcanza.
- **Demo de atracción:** en la SNES, el título corre partidas grabadas. El
  port ya tiene el **modo replay** (`-DREPLAY`): el título puede reproducir
  `yi1_replay.bin` o una grabación de snesorc tal cual, sin código nuevo de
  lógica.

### 11.6 Partidas guardadas

- **Qué guarda SMW:** 3 ficheros en la SRAM, con los niveles pasados y los
  eventos del mapa, los palacios, las monedas de Yoshi por nivel y una suma
  de control; se guarda al pasar castillos, casas fantasma y palacios. Las
  vidas no se guardan. El formato y las direcciones están en el fuente
  (buscar la rutina de guardado en `game.s`/`map.s`).
- **Cómo lo haría en la Amiga:**
  - **(a) Un sector reservado del disco**, con el mismo contenido que la
    SRAM y su suma de control. Escribir por hardware con la máquina tomada
    (codificar el MFM + `DSKLEN` de escritura), que es delicado; o
    devolver la máquina al SO un momento y escribir con `trackdisk`, lo más
    seguro para una escritura de 1 sector. Hace falta que el disco no esté
    protegido contra escritura; si lo está, avisar y seguir.
  - **(b) Contraseñas:** sin escribir en el disco; cabe todo en pocos
    caracteres para un mundo, y no hay riesgo de corromper el disco.
  - Recomendación: (b) mientras haya pocos niveles; (a) si se llega a un
    mundo entero.
- **El mapa (overworld)** es otro motor entero (capas propias, el Mario del
  mapa, caminos, eventos). Para unos pocos niveles alcanza una **pantalla
  de selección** fija; el mapa de verdad solo si el proyecto crece a un
  mundo.

### 11.7 Otros extras (baratos, cuando haya tiempo)

- **Pausa con opciones:** reasignar teclas (la tabla `keytab` de D14) y
  elegir teclado o joystick.
- **Game over y continuar:** la lógica del ROM, con el contador de vidas.
- **Marcador de tiempo real y "estadísticas":** fuera del 1:1; solo si el
  usuario lo pide.

### 11.8 Cosas que conviene decidir YA pensando en esto

- **6b.1 (vlink y mapa de memoria):** separar desde el principio lo común
  (código, Mario, HUD) de lo que es de cada nivel (bloques, capa 2, plan
  del copper, gráficos de sus sprites, muestras), en regiones de memoria
  distintas.
- **9.2 (sprites):** gráficos precalculados **por tipo de sprite**, con una
  tabla de tipos cargada por nivel; nada fijo al Rex.
- **11 (audio):** los eventos y las muestras **por tema**, con las muestras
  compartidas (efectos) aparte.
- **Herramientas:** cada herramienta nueva que se escriba para YI1 recibe
  ya el nivel como parámetro, aunque hoy solo haya uno.
