# Plan técnico: optimización, lo que falta y más allá de YI1

> **Movido textual el 2026-10-05 desde `docs/plan-tecnico.md` §9, §10 y §11**, con los
> mismos números de sección: una referencia "`docs/plan-tecnico.md` §10.6" es "§10.6 de este
> fichero". Es **referencia de cómo hacer cada cosa**, escrita el 2026-09-30:
> los números de estado que aparecen son de esa fecha. Lo vigente está en
> `ROADMAP.md` §1-§2 (estado y presupuesto) y en `PROXIMO.md` (qué sigue).
> Las menciones a "§1", "§2", "§8" dentro de este texto son del `ROADMAP.md`
> (las §2, §3 y §8 conservan su número; el §1 viejo está en
> `docs/archivo/roadmap-2026-10-05.md`).

---

## 9. Optimización: plan e ideas (2026-09-30)

> **Ver también `docs/investigacion-ports.md` (2026-10-03):** qué hicieron
> otros ports y juegos de A500 con estos mismos problemas, con tarjetas
> nuevas (O5, V1-V3, L4, L5, G0, E2). Corrige §9.6: la cola de blits por
> interrupción no ganó en una A500 de serie (medido por AmiGalaga).

**Método (siempre):** medir el peor frame y **dónde** ocurre → cambiar
**una** cosa → verificar la semántica (`regress.py`; el C con `abcheck.py`;
`scroll.s` con `scrollsim.py --ret` + `imgdiff.py`) → medir en cycle-exact
(`regress.py --emu`). Se optimiza el **peor frame**, no la media: el frame
que no entra en 20 ms es el que se nota.

**Regla de conversión** (medida en la 8.2 y en la 6.4): en la A500, con el
DMA de 6 planos, un trabajo cuesta ~1,3-1,4 veces lo que da Musashi.
O sea, **~1 000-1 100 ciclos de Musashi por cada 1 % de frame** en la
Amiga (un frame PAL son 141 876 ciclos; en la parte visible de cada línea
el DMA de planos se lleva la mitad de las ranuras pares).

### 9.0 Dónde estamos y a dónde hay que llegar

Peor frame por partes (el del juego entero sin medir: es el paso O1):

| parte | peor frame hoy | dónde | objetivo | falta |
|---|---|---|---|---|
| scroll a la ida (`build_mid` + columna) | 78,8 % (FS-UAE, 4 px/frame) | s = 4584 (postes de la meta) | ≤ 25 % | −54 puntos |
| scroll a la vuelta | 94,8 % en Musashi (≈ 125 % en la Amiga, **estimado**) | s = 2832 | ≤ 25 % | −100 puntos |
| lógica con sprites (`level_frame`) | 45 896 ciclos en Musashi ≈ 45 % | frame 9714 (2 pirañas, Rex, `$8E`, `$C7`) | ≤ 40 % | −6 000 ciclos |
| Mario en sprites (`mspr_draw`) | ~10 400 ciclos ≈ 7,3 % | cada cambio de pose | ≤ 3 % | −4 000 ciclos |
| sprites del nivel (9.2) | sin hacer | — | ≤ 8 % | diseñarlo barato (9.5) |
| HUD / audio | sin hacer | — | ≤ 2 % / ≤ 3 % | — |
| **margen** | — | — | **≥ 10 %** | — |

La suma de los objetivos da 81 % + margen. Hoy el peor caso pasa del
130 %. **Lo que manda es el scroll**; la lógica está cerca.

### 9.1 Paso 0: medir el frame entero (O1-O3)

Sin esto se optimiza a ciegas; además es la **6b.6 (compuerta D1)**.

- **O1. `game.s -DBENCH`:** timer A de CIA-B al principio y al final de
  cada parte (entrada, `level_frame`, `mspr_draw`, `scroll_frame`:
  columna, `build_mid`, lista), **por frame**, en el replay. Se guardan el
  peor frame de cada parte y el del total, con su frame y su s, y se
  escriben en pantalla como bits (el método de `bench.s`), con un lector
  `tools/game_read.py --auto`. Enganchar a `regress.py --emu game`.
- **O2. Escenarios de estrés con snesorc:** `oracle_yi1` no recorre los
  peores casos. Guiones `.orc` nuevos:
  - la cámara volviendo a toda velocidad sobre s ≈ 2600-2900 y 4100-4800,
    las zonas caras del scroll;
  - Banzai + 4 Rex + Mario a la vez en pantalla;
  - las 2 pirañas del frame 9714 con Mario corriendo.

  Pasarlos por `m68kverify.py --replay` → `game.s -DREPLAY -DBENCH`.
- **O3. En `regress.py`:** los ciclos del peor frame por parte en Musashi
  (`gamecheck.py --engine musashi`, que tiene que aprender a correr
  también `scroll_frame`) y el scroll en los **dos sentidos**
  (`scrollprof.py -D RETURN=4864 --stopx 0`). Hoy `-DBENCH` solo mide la
  ida (P72).

### 9.2 Scroll: `build_mid` (lo más grande)

Reparto del peor frame de la ida (s = 4580, 76 850 ciclos en Musashi, ver
Etapa 6.4): 55 líneas reescritas enteras, 276 cargas (~124 ciclos cada
una) + ~520 por línea + ~7 800 para recorrer las 108 líneas de LNS.
Por qué se reescriben:

| motivo | líneas |
|---|---|
| una carga "tarde" (se reescribe en **todos** los frames, P50) | 24 |
| entra una carga por la derecha | 25 |
| caduca una carga | 6 |

A la vuelta, casi todo se reescribe en cada paso (P72). Ideas, de más
barata a más cara:

- **S1. Las cargas "tarde", arregladas en origen.** Son 34, en
  x ≈ 4817-4861 (los postes de la meta), y cada una fuerza su línea unos 128
  frames seguidos.
  - (a) Clasificación fija, con la línea canónica (P71) y la h en celdas de
    8 px: la línea se reescribe cada 8 px de s, no en cada frame.
  - (b) En `mkleveld.py`/`mkscroll.py`, repartir los registros cerca de los
    postes para que las ventanas se puedan cumplir. Si hace falta, aceptar
    un derrame de 1 px donde no se ve (P44).
  - (c) Dibujar los postes con 2 sprites de hardware adosados (15
    colores). En la meta casi no hay enemigos: saca esas cargas del copper.
  - Estimado: −20-30 % del peor frame de la ida.
- **S2. Recorrer LNS por grupos de 16 líneas** con el mínimo de cada grupo
  (el `gmin_a/b` del WIP viejo): de ~7 800 a ~1 000 ciclos en los frames en
  que casi no cambia nada.
- **S3. Escribir cada cambio una sola vez.** Hoy cada lista (A y B) tiene
  su sombra (`V_LSA`/`V_LSB`) y **cada línea que cambia se reescribe dos
  veces**: en la lista de este frame y en la del siguiente. Como un
  segmento vale para un intervalo de s, las dos listas pueden compartirlo:
  un pool con 2 ranuras por línea; la que cambia se escribe en la ranura
  libre y las dos listas se reenganchan (2 palabras cada una). La trampa:
  el salto al segmento siguiente está **dentro** del segmento, así que
  compartirlo obliga a sacar los saltos a una "columna vertebral" por
  lista, que gasta MOVE del copper en el borrado. Medir primero con
  `copcal` si entran (P39, P43, P46). Estimado: hasta −50 % de
  `build_mid` en régimen.
- **S4. Editar en el sitio en vez de reescribir la línea** (el diseño de
  `tools/wip64/`): rebase (solo el byte h de cada WAIT), append y truncado
  por la derecha. En el modelo: ida 48,6 → 38 %, vuelta 78,8 → 56 %. La
  imagen queda igual por construcción si la clasificación "tarde" es fija.
- **S5. Repartir entre frames con un presupuesto.** Cada evento tiene una
  holgura de b + 6 px, así que no hace falta atenderlo en el frame en que
  aparece. Una cola por plazo (EDF) con un tope de ciclos por frame: lo
  urgente primero, el resto después. Aplana el pico hacia la media (hoy
  14,9 % a la ida). Las cargas muertas se neutralizan en el sitio (el MOVE
  pasa a `$1FE`) en vez de reescribir.
- **S6. Un plan por sentido.** El plan pone las cargas lo antes posible
  (a ≈ 0), así que sirve hacia la derecha y casi nada hacia la izquierda
  (P72). Un segundo plan con las cargas lo más tarde posible (ALAP) para
  cuando la cámara va a la izquierda, o las cargas en el centro de su
  ventana para los dos sentidos. Cuesta otro MLD en slow RAM.
- **S7. Menos cargas desde el origen.** Cada carga que no existe ahorra
  CPU y ranuras del copper. Mejor asignación de registros en
  `mkleveld.py` (intervalos que se reusan, preferir el registro que ya
  tiene el color) y más variantes de bloque. Hoy son 244; quedan ~117 KB
  de chip. Medir antes la distribución de cargas por línea visible.
- **S8. El blitter copia los segmentos.** Si las palabras del copper de
  cada segmento están precalculadas en chip, un blit A → D las copia
  mientras la CPU corre la lógica; la CPU solo parchea las h. Evaluarlo
  después de S3-S5: depende de cuánta chip haga falta.

**Recurso E13 (2026-10-06):** cambiar `BPLCON2` por franja permite alterar
la prioridad entre playfields y sprites (Lionheart, Beast, Jim Power;
`docs/investigacion-ports.md` §19.3). No hay un caso confirmado en YI1:
no se abre implementación hasta que una comparación 1:1 lo requiera.

Orden propuesto: S1a + S2 (baratas) → S4 → S5 → S3 → S6. Hecho cuando el
máximo es ≤ 25 % **en los dos sentidos** y en los escenarios de O2, con
`scrollsim.py --ret` (≤ 9282 px, ida = vuelta) y las capturas de las 6 x
sin empeorar.

### 9.3 Lógica (`level_frame` con sprites)

Perfil del 2026-09-30 (`PROF=1 sh tools/logicbench_build.sh &&
python3 tools/m68kprof.py --sprites --worst 5`), en ciclos propios por
frame, sin inline:

| función | media | peor frame real (9709) |
|---|---|---|
| `mario_E2BD` (gráficos de Mario) | 3 970 (12 %) | 4 020 |
| `f44d_asm` (sondas, 5,5 por frame) | 3 060 | 2 740 |
| `spr_tile_asm` | 890 | **2 300** |
| `sprite_run` (temporizadores, ~500 por ranura) | 980 | **2 020** |
| `camera_F6DB` | 1 720 | 1 810 |
| `eb77` / `sprites_all` / `f636` / `mario_D5F2` | 1 030-1 350 cada una | 1 040-1 540 |
| `f7f4_c` (scroll vertical hacia arriba: el asm cae al C) | 510 | **1 390** |
| `spr_obj_interact` / `spr_obj_vert` / `sprite_main` / `jumping_piranha` | 470-550 | 1 050-1 250 cada una |

(El frame 4437 cuesta 53 818 porque paga `probe_init`, 21 454 ciclos: no
es un frame del juego, P64.)

Ideas, por ganancia estimada en el peor frame (hacen falta −6 000):

- **L1. Ensamblador a mano** (el C queda de referencia, como en la 8.2):
  - la rama hacia arriba de `f7f4`: −1 000 en los frames en que Mario sube;
  - `sprite_run` + el despacho de `sprite_main`: −1 000-1 500 con varios
    sprites vivos;
  - `mario_E2BD`: −1 500-2 000 en todos los frames;
  - `spr_obj_interact`/`spr_obj_vert`/`spr_spr_interact` y
    `jumping_piranha`.
- **L2. Descartes rápidos:** `spr_spr_interact` es O(n²): descartar por
  |dx| antes de la caja completa. Lo mismo con el contacto con Mario
  (`DefaultInteractR` en C). Casi siempre están lejos.
- **L3. Estado nativo** de los campos calientes de Mario (8.2, paso 2):
  ≤ 5-8 % estimado. Queda para el final: toca todo el C.
- Verificar cada paso con `abcheck.py <base> --sprites` (semántica IGUAL) y
  con `regress.py`, que corre los cruces de la RAM entera (`--cross`); el
  vbcc de cloud compila mal cosas que gcc compila bien (P38, P62).

Hecho cuando el peor frame con sprites da ≤ 40 % en cycle-exact
(`logicbench -DWORST`) y en los escenarios de O2.

### 9.4 Mario en sprites (`mspr_draw`, 7,3 %)

Medido en el replay (6313 frames): la pose dibujada (punteros de tiles
`wm_0D85` + la OAM relativa) cambia en el **33,5 %** de los frames, y hay
**987** combinaciones distintas.

- **M1. No redibujar si la pose no cambió:** solo SPRxPOS/SPRxCTL. −66 %
  de media. **No** baja el peor frame, que es un cambio de pose.
- **M2. Precalcular todas las poses:** 987 × ~544 B ≈ 530 KB: no entra en
  chip. Descartado.
- **M3. Caché LRU de N poses** en chip (16 × 544 B ≈ 9 KB): ayuda a la
  media (el ciclo de caminar repite 3 poses), no al peor frame.
- **M4. Bajar el coste del dibujo en sí:** perfilar `mspr_draw` por
  etiquetas (como `scrollprof.py --zones`) y atacar lo que salga: filas
  vacías, entradas que se tapan entre sí, el camino del volteo. Objetivo:
  ≤ 3 %.
- **M5. Hacerlo fuera de la pantalla:** es trabajo de bus puro. Hacerlo en
  las 88 líneas sin DMA de planos lo abarata ~1,3×.

### 9.5 Sprites del nivel (9.2): baratos desde el diseño

- Frames **precalculados** por pose (Rex, Banzai, piraña, Koopa...) en chip,
  listos para el DMA de sprites. La CPU solo escribe las palabras de
  control y los punteros; nada de dibujar por CPU.
- Reusar un canal en vertical sin copper: después de la última línea de un
  objeto van las palabras de control del siguiente (0 MOVE).
- Colores 17-31 recargados por el copper solo donde cambian (filas de
  color precalculadas por pose, `copsim.py`).
- Asignador de columnas con coste acotado: ≤ ~10 objetos en pantalla,
  ordenados por Y una vez por frame (inserción: casi ordenados de un frame
  al siguiente).
- Bobs en PF1 solo en el caso raro de `d8demote` (1,8 % de los frames).
- Medir con O1 desde el primer día. Objetivo ≤ 8 %.

### 9.6 Organización del frame y DMA

- Hay **88 líneas sin DMA de planos** (el 28 % del frame). Ahí la CPU va a
  velocidad completa: el trabajo de bus puro (copiar segmentos del copper,
  `mspr_draw`) rinde más ahí. Medir cada trabajo en las dos franjas (método
  de `bench2.s`) y ordenar el frame según eso.
- El blitter trabaja en paralelo: columna nueva y bobs en una cola servida
  por la interrupción del blitter. Nunca esperar a que termine un blit si
  la CPU tiene otra cosa que hacer (P31). `BLTPRI` solo mientras la CPU
  espera (P2).
- Mover código a `$C00000` libera chip pero **no acelera** (P29).
- Si D1 termina en "dibujar a 25 Hz": la lógica sigue a 50 y el scroll se
  calcula cada 2 frames, pero con el doble de desplazamiento por paso. El
  pico de `build_mid` no se divide por 2 automáticamente: medirlo con O1.

### 9.7 Técnicas del 68000 y de vbcc (lo que ya sirvió)

1. **Estado nativo, no `ram[]` byte a byte:** `R16()` son 2 lecturas + `lsl`
   + `or` (~50 ciclos) contra 12 de un `move.w d16(a4),Dn`.
2. **`int` es de 32 bits en vbcc:** los `u8` se promocionan con
   `ext`/`and.l #$FF`. Intermedios en `u16`/`s16`; revisar
   `work/cc/<f>.code.s` buscando `ext.l`, `and.l`, `mulu` y llamadas al
   runtime.
3. **Nada de `mulu`/`divu` en caliente** (38-140 ciclos): tablas o
   desplazamientos.
4. **Punteros que avanzan** (`(An)+`, 8 ciclos) en vez de `d8(An,Dn)` (14),
   con P38 y P62 en mente.
5. Lo caliente en variables locales (registros); las tablas de la ROM
   pasadas a palabras nativas una vez; desenrollar los bucles de vueltas
   fijas; `movem.l` para copiar bloques (la lista del copper: 38 % con un
   bucle, 15 % con `movem`).
6. **Asm a mano solo en lo que el perfil pone arriba**, con la misma
   interfaz que el C, que queda de referencia y para los casos raros.
7. Una palabra en dirección impar cuelga el 68000 (`even`, `cnop 0,2`).
   Los desplazamientos de más de 32 KB van con `(An,Dn.l)` (P40). `tst` y
   `eor` no aceptan `(pc)` ni memoria de origen (P73).

### 9.8 Qué NO hacer

- Cambiar la semántica para ganar ciclos: saltarse sprites, simplificar la
  física o la cámara. Rompe el 1:1, y está bien que el verificador lo marque.
- Tomar Musashi como coste real, o medir con la config rápida (P30).
- Optimizar sin perfil, o por la media en vez de por el peor frame.
- Dar por buena una optimización del scroll probada en un solo sentido
  (P72) o solo en `oracle_yi1` (P69).

---

## 10. Todo lo que falta, y cómo lo haría (2026-09-30)

> Decisiones del usuario del mismo día: D1 = 50 Hz haciendo todo lo
> posible, D15 = se acepta la velocidad PAL, D16 = la zona de la tubería
> entra. Donde abajo dice "decisión [usuario]" o "recomendación", ya está
> decidido así.

La lista completa hasta el ADF final, en el orden en que lo haría. Para
cada punto: **qué falta**, **cómo lo haría** (con las alternativas y por qué
elijo una), los **riesgos**, **cómo se verifica** y las **tarjetas** de
`SUBAGENTES.md` que lo parten. Los detalles de optimización están en §9;
los pasos originales de cada etapa, en §5.

### 10.1 La compuerta D1: medir el juego entero (6b.6)

- **Falta:** nadie midió el peor frame del juego integrado. Solo hay
  medidas por partes, y sumadas pasan del 130 % (§9.0).
- **Cómo lo haría:** `game.s -DBENCH` con el timer A de CIA-B en modo
  continuo (709 379 Hz: ~14 190 ticks por frame, cabe en 16 bits), leído en
  las fronteras de cada parte. Se guarda el máximo de cada parte con su
  frame y su s, y un contador de **frames que se pasan** (el VBL siguiente
  ya llegó). El resultado se pinta al final como en `bench.s`. Se corre
  sobre el replay y sobre escenarios de estrés grabados con snesorc (la
  cámara volviendo sobre las zonas caras, Banzai + 4 Rex, las 2 pirañas).
- **Mi recomendación para D1**, a confirmar con los números: **50 Hz**. Las
  medias entran de sobra (scroll ~15 %, lógica ~25 %, Mario 7 %). Los picos
  son estructurales: son eventos de `build_mid` que se pueden repartir entre
  frames (§9.2 S5) y unas pocas rutinas de la lógica. Dibujar a 25 Hz queda
  de reserva si la 6.4 no baja del 40 %.
- **Además:** qué pasa cuando un frame se pasa igual. Hoy se pierde un VBL
  y se ve un tirón. Con el EDF de S5, lo no urgente se pospone solo; lo
  urgente (lógica, cargas que caducan) siempre entra primero.
- **Verificación:** con `-DBENCH`, el binario sin el banco sale igual byte a
  byte; los máximos caen en frames que se pueden explicar con el perfil.
- **Tarjetas:** O1, O3, R6, O4.

### 10.2 El scroll a ≤ 25 % (6.4)

- **Falta:** todo. Ida 78,8 % y vuelta ~125 % (estimado).
- **Cómo lo haría** (detalle en §9.2), en este orden:
  1. las cargas "tarde" de los postes de la meta, que hoy obligan a
     reescribir 24 líneas en cada frame;
  2. recorrer LNS por grupos de 16 líneas;
  3. edición en el sitio (rebase de la h, append y truncado por la
     derecha);
  4. EDF con presupuesto;
  5. segmentos compartidos entre las dos listas, si el copper tiene
     ranuras en el borrado;
  6. un plan por sentido.

  Del 1 al 4 se puede hacer sin tocar el formato del copper.
- **Riesgos:** romper la ida = vuelta (P71). Por eso `scrollsim.py --ret`
  va en cada paso. El copper después de `DDFSTOP` (P51) va a 8 px por
  MOVE desde x = 239: está en `scrollsim.advance()` y en `build_mid`.
- **Verificación:** la puerta común de las tarjetas S.
- **Tarjetas:** S1a, S2, S4, S5, S3, S6, S7, E1.

### 10.2b La cámara vertical en YI1 — **nuevo, hallado el 2026-09-30**

- **El hecho:** YI1 **sí** tiene scroll vertical. Su cabecera trae
  `wm_VertScrollHead` = 2 ("solo en algunos casos", `CODE_00F82A`), que es
  lo que hay en `$1412` en todos los frames del nivel. `lvparse.py` leía mal
  el byte 4 y decía 0 (P77, arreglado), y `oracle_yi1` nunca movió la
  cámara. En las grabaciones de snesorc, `Bg1VOfs` baja de `$C0` a `$BC`
  durante 36 frames (`normal`) y 51 (`diagpipe`).
- **Qué pasa hoy en la Amiga:** `game.s` y `scroll.s` **no leen**
  `Bg1VOfs`; la ventana está fija en las líneas 192-415. Cuando la cámara
  sube, Mario (dibujado con la posición de pantalla que calcula el ROM) se
  corre respecto del fondo tantos píxeles como suba la cámara: se ve
  hundirse o flotar.
- **Cuánto puede subir:** sin medir. Solo se vio hasta 4 px. Un guion de
  estrés de snesorc (saltos a toda carrera desde lo alto de las tuberías y
  de los Rex) da el mínimo real de `Bg1VOfs`. Hacia abajo el límite es
  `$C0` (el `limit` de `f7f4`).
- **Cómo lo haría (barato, porque el movimiento es chico y raro):**
  - **Datos:** extender la ventana de `mkscroll.py` K líneas hacia arriba
    (las del mínimo medido). Cada línea de más cuesta ~320 B de `L2B` y lo
    proporcional de las tablas de CPU.
  - **PF1 y PF2:** sumar (cam_y − 192) filas a los punteros de planos; PF2
    con la mitad (`Bg2VOfs = Bg1VOfs >> 1`, el paralaje vertical de
    YI1). Es gratis.
  - **El copper:** que los segmentos queden **indexados por línea del
    nivel**, no de pantalla. El contenido (las cargas de color) depende de
    la línea del nivel y de s, no de cam_y; lo único que depende de cam_y
    es la **v de los WAIT** de cada segmento. Al cambiar cam_y se parchean
    esas v (224 × 2 palabras, del orden de 3 000 ciclos, **estimado**) y se
    mueven el principio y el final de la cadena. No hay que reescribir
    ninguna carga.
  - Es el mismo paso que prepara el scroll vertical de otros niveles
    (11.3).
- **Verificación:** `scroll_check.py` con cam_y ≠ 192, y capturas del replay
  de `oracle_normal` en los frames 2672-2707.
- **Tarjetas:** R6 (`stress_vert.orc`, el guion de estrés vertical) y S8.

### 10.3 La lógica a ≤ 40 % (8.2, segunda ronda)

- **Falta:** −6 000 ciclos en el peor frame (45 896 → ~40 000 en Musashi).
- **Cómo lo haría:** ensamblador en lo que marca el perfil:
  - la rama hacia arriba de `f7f4`, que hoy cae al C;
  - `sprite_run` entero;
  - `mario_E2BD`;
  - las interacciones.

  Más descartes rápidos por |dx| en las colisiones sprite-sprite y
  sprite-Mario. El estado nativo de Mario (8.2 paso 2) solo si con eso no
  alcanza: toca todo el C y el beneficio estimado es ≤ 5-8 %.
- **Riesgos:** el vbcc de cloud compila mal cosas que gcc compila bien (P38,
  P62). Los cruces de RAM entera de `regress.py` y `gamecheck.py --spr` son
  obligatorios.
- **Tarjetas:** L1a-L1d, L2, L3.

### 10.4 Las pendientes (8c)

- **Falta:** la colina grande de x = `$AE0` (pendiente hacia el otro lado,
  con 5 Rex encima).
- **Cómo lo haría:** un guion de snesorc (a toda carrera en los dos
  sentidos, parado, deslizándose y saltando); `marioverify full` clasifica
  los fallos por causa y los de pendiente se arreglan en `mcoll.c`
  transcribiendo la rutina de la pendiente que falte. Las colinas 1-4 ya dan
  2154/2154.
- **Tarjetas:** R1 (y un M para lo que falle).

### 10.5 Los sprites que faltan: lógica (9.1)

- **Falta:**
  - Clappin' Chuck `$95`;
  - caparazones: el rojo `$DB`, y el Koopa `$02` con caparazón;
  - la cinta de meta `$7B`;
  - lo que sale de los bloques: seta, flor, estrella, 1-UP y enredadera
    (el giratorio "estrella 2/1-UP/enredadera" lo decide el ROM según el
    estado); la luna 3-UP; el champiñón invisible dando la vida;
  - las **bolas de fuego**, que son sprites extendidos (`ex_sprite.s`);
  - las monedas que salen de los bloques y los sprites de puntos;
  - las monedas de Yoshi, contadas (la 5.ª da 1-UP);
  - la caja de reserva;
  - las animaciones de Mario por `$71`: crecer, encoger, morir, la
    estrella.

  Además, dos diferencias chicas: el Koopa `$BD` en el primer frame del
  nivel y un nacimiento de la piraña en `diagpipe`.
- **Cómo lo haría:**
  - **Cada sprite en su fichero** (`player/spr_*.c`, tarjeta I1), así se
    trabaja en paralelo.
  - Transcripción instrucción por instrucción, como el Rex.
  - Para cada objeto, primero la grabación con snesorc y después el port
    contra esa grabación.
  - Los sprites extendidos y las animaciones de `$71` son motores propios
    del ROM (`ex_sprite.s`, la tabla de `$71` en `player.s`): se portan
    enteros, no solo el caso que se ve, porque la flor, la estrella y la
    muerte los usan.
  - El orden: lo que hoy **congela el juego en vivo** primero (el modo
    diagnóstico dice cuál aparece más), después lo que falta para
    terminar el nivel (la meta).
- **Riesgos:** el coste. Cada sprite activo suma ~1 000-2 500 ciclos en el
  peor frame (el perfil de §9.3). Medir con O1 a medida que entran.
- **Verificación:** `marioverify <grabación> game` con
  `sprite XX: seguidos N exactos N` y 0 resincronizaciones.
- **Tarjetas:** R2-R5, I1, P1-P10.

### 10.6 Los sprites que faltan: dibujo (9.2)

- **G2 revisado y auditado el 2026-10-06:** [diseño e interfaces](diseno-9.2.md),
  prueba offline en `informe-g2.md`: 64528 B DMA y 72716 B tablas para el lote acotado.
  G8 escribe OAM de Rex y rutinas compartidas en el PC; G3a convierte las
  fichas (227/227 poses en las grabaciones actuales). Los enemigos todavía
  **no se ven** en la Amiga: faltan G3 final, G4/G6, G5/G9 y G7.
- **Decisiones de implementación:** OAM en la lógica en su fase original;
  foto de O5 ampliada con OAM/cámara/pertenencia a ranura en slow RAM;
  cuatro parejas adosadas, descontando las una o dos de Mario; Banzai
  siempre bob; desbordes con destino explícito, sin descartarlos.
- **Reuso:** PT + POS/CTL por copper, conforme a la medida G0 a 256 px.
  Contar hasta 8 MOVE por pareja (6 si los punteros comparten banco de
  64 KiB). El encadenado queda como alternativa por objeto; no asumir
  válida la ventana de una línea a partir del modelo de 320 px.
- **Color:** G3 debe remapear los índices de cada paleta a COLOR17-31,
  respetando los de Mario. La unión de 11 colores medida con poses de
  referencia no verifica todas las poses. Autoprueba de píxeles y tamaño
  de las variantes antes de aprobar el banco de 64 KiB.
- **Bobs:** segundo PF1 (+59 136 B), para conservar la imagen publicada
  cuando O5 repite un frame. G7 restaura y dibuja en el buffer libre, y
  publica al terminar los blits. Los casos sin color exacto de
  `d8demote.py` siguen pendientes.
- **Memoria:** vivo opt-in + banco G2: 466760 B chip proyectados.
  Con banco máximo, PF1 doble y audio: 592440 B; C2/C4 sacan 135468 B CPU
  de chip, dejando 67312 B para bobs, HUD y listas. Slow: tablas ≤98304 B,
  trabajo ≤32768 B y fotos 2376 B; con vivo y C2/C4 quedan 4248 B al tope.
  Auditar el binario/loader concreto, incluido el pico de carga.
- **Puertas:** OAM real del 68000 contra grabaciones; asignación y píxeles
  reconstruidos exactos; capturas contra la OAM; `memmap`; coste de lógica
  con OAM ≤40 %, preparación de sprites ≤8 %, ticks/fotos perdidos O5
  medidos en cycle-exact. Detalle y comandos en el diseño y sus informes.
- **Tarjetas:** G0, G3-G9, C2/C4; Z1, H1 y A1/A2 según sus dependencias.

### 10.7 Carga y memoria (6b.1)

- **Falta:** el loader definitivo, el enlazado absoluto (vlink), la
  compresión y un mapa de memoria que alcance para todo.
- **La cuenta de la chip** (hoy ≈ 395 KB de 512):
  - `yi1_s.dat` son 223 600 B y hoy van **enteros a chip**. De eso, el
    chipset solo lee `BLK` (23 424, el blitter) y `L2B` (71 232, el DMA de
    planos). `MAP`, `INI`, `CHG`, `L2P`, `MLX`, `MLD` y `LNS` (129 000 B)
    los lee solo la CPU.
  - Moverlos a `$C00000` (D13) deja la chip en **≈ 266 KB**, con sitio
    para el audio (≤ 64 KB), los gráficos de sprites (< 30 KB), el HUD y la
    zona de la tubería (10.10).
  - **Sin esto no entra todo**: 395 + 64 + 30 ya pasa de 490 KB.
- **Cómo lo haría:**
  1. partir `yi1_s.dat` en una parte de chip y otra de CPU (`mkscroll.py`
     ya sabe dónde empieza cada sección);
  2. `memmap.py` que compruebe el mapa desde el listado;
  3. vlink con direcciones fijas: se van P36/P52 y los `GETBASE`;
  4. compresión LZ solo si el tiempo de carga lo pide. El ADF va por el
     46 % y leer 412 KB con trackdisk tarda del orden de 15-20 s
     (**estimado**; medirlo).

  Todo se carga con `trackdisk` mientras el SO vive (D13); después de tomar
  la máquina no hay que leer del disco.
- **Riesgos:** que el binario enlazado en absoluto rompa las herramientas
  que lo cargan en `BASE` (`m68kverify`, `gamecheck`, `gamesim`, `abcheck`):
  tarjeta E3.
- **Tarjetas:** C1-C5, E3.

### 10.8 HUD, caja de mensajes y pausa (10)

- **Falta:** la barra de estado, **las 2 cajas de mensaje** del nivel (la
  lógica del sprite `$B9` está, pero el texto no se muestra) y la pausa.
- **H1 medido el 2026-10-05:** `docs/medida-hud.md` cuantifica la máscara
  inicial y la banda conservadora. Hay cruces con PF1 (hasta 6 píxeles
  en 9216; 16 en 9472 al incluir la línea 36). H2/H3 deben conservar
  ese terreno al componer la tinta; la alineación raster exacta sigue pendiente.
- **Cómo lo haría:**
  - **Barra (D11, overlay).** H1 detecta terreno en esas líneas, por lo
    que H2/H3 deben probar una composición por máscara de blitter que
    conserve PF1, con colores y scroll coordinados mediante el copper.
    PF2 sigue con su paralaje. Falta demostrar la paleta de hasta 7 colores
    y su coste con O5; un bitmap fijo que sustituya toda la banda perdería
    los cruces medidos. Los dígitos se actualizan cuando cambian, aunque
    hay que conservar la tinta al restaurar el terreno bajo el HUD.
  - **Cajas de mensaje.** En YI1 son solo 2 textos, que están en
    `strings/level_messages.a`. Los **renderizaría offline** a dos bitmaps
    con la fuente `gb-1`. En la Amiga, mostrar uno es cambiar punteros y
    colores en el copper en las líneas de la ventana, con el juego
    congelado como en la SNES. La animación de apertura se hace creciendo
    esas líneas frame a frame (`dialog.s` dice cuántas).
  - **Pausa.** Start congela la lógica (la rutina del ROM) y baja el
    volumen de la música.
- **Verificación:** `marioverify hud` contra los contadores grabados (R7);
  capturas de la barra y de la caja contra la referencia.
- **Tarjetas:** H1-H5, R7 (y una H6 para las cajas de mensaje, que se
  agrega cuando esté H3).

### 10.9 Audio (11)

- **Falta:** registro DSP, secuencias y reproducción. A1 convierte y
  verifica muestras contra el DSP; R8 WAV y escucha siguen pendientes.
- **Números:**
  - inventario A1 medido el 2026-10-06: las 20 muestras de
    `mw_e10/sound/samples` suman 28440 B BRR y 50560 B PCM8, con
    14976 B de margen frente a 65536 B (`docs/informe-a1.md`). Esto
    sustituye la estimación histórica de 92 KB BRR / 164 KB PCM, que no
    describe ese directorio. No demuestra que audio y las otras reservas
    quepan juntos en chip; además, 12/13 loops cambian entre vueltas por
    el historial BRR, que A3/A4 deben representar (P105);
  - música: el tema del nivel está en `sound/music1`; las secuencias son de
    N-SPC.
- **Cómo lo haría** (el cambio más grande respecto de la idea original de
  D5): **no escribir un intérprete de N-SPC**, sino **capturar las
  escrituras al DSP** con snesorc (el SPC700 emulado de snesrev), tick a
  tick, mientras suena el tema. Por voz:
  - la fuente de la muestra (SRCN), la altura (P), el volumen y la
    envolvente (ADSR/GAIN), y los KON/KOFF;
  - la altura se pasa a periodo de Paula y la envolvente a una tabla de
    volumen por tick;
  - las 8 voces se reparten en 3 canales por prioridad (melodía, bajo,
    percusión), robando la voz cuando otra calla;
  - se captura un bucle del tema;
  - los efectos igual: se dispara cada uno solo, escribiendo en los
    puertos de sonido (`$1DF9-$1DFC`), y se graba lo que hace el DSP.

  El 68000 solo recorre flujos de eventos por tick (timer de CIA): es
  casi nada de CPU, y exacto en tiempo y en altura. Lo que se pierde (eco,
  filtros, modulación entre voces) D5 ya lo daba por perdido.
- **Riesgos:** voces que no caben en 3 canales en los momentos densos del
  tema (medir en la captura cuántas suenan a la vez); el periodo mínimo de
  Paula (124) para las notas agudas de muestras con mucha frecuencia de
  muestreo.
- **Verificación:** render offline de los eventos contra el WAV de snesorc
  (R8): notas a ±1 tick y ±5 cents; en FS-UAE, a oído.
- **Tarjetas:** R8, A1-A7 (A2 y A3 cambian: "capturar el DSP" en vez de
  "leer N-SPC").

### 10.10 La zona de la tubería (`obj-1.lv`) — **nuevo**

- **Qué es:** el nivel tiene una segunda zona: `obj-1.lv`, 2 pantallas,
  tileset 3, música 1, con nubes, monedas y tuberías. Se llega por una
  tubería: en `oracle_yi1`, Mario entra en una en el frame 11425 (P68). El
  nivel tiene una salida de pantalla (pantalla 18, destino `$CB`).
- **Falta:** todo: la conversión de la zona, entrar y salir por tubería,
  la transición y el regreso.
- **Cómo lo haría:**
  - generalizar la cadena del nivel (`mklvl` → `mkd8in` → `mkleveld` →
    `mkscroll`) para que reciba el nivel como parámetro, y generar
    `yi1b_s.dat`. Son 2 pantallas: poca memoria;
  - en la Amiga, la transición es un fundido, cambiar los punteros del
    scroll (otra `yi1_s`), la paleta y la cámara, y seguir;
  - la lógica: las animaciones de tubería de `$71` y la carga de la
    subzona (cabecera, sprites si los hay, posición de entrada) del ROM;
  - grabarlo con snesorc (el camino de `oracle_yi1` hasta la tubería).
- **Decisión [usuario] (D16):** entra en el alcance si "Yoshi's Island 1"
  quiere decir el nivel entero (criterio 1:1: sí). Si no, la tubería se
  queda cerrada.
- **Tarjetas:** R9 (grabación), I2 (descriptor de nivel), T1 (conversión),
  T2 (lógica de tubería), T3 (transición en la Amiga).

### 10.11 Pulido y final del nivel (12)

- **Z1 implementado el 2026-10-05:** animación de muerte normal y regreso
  al inicio conservando vidas y estado persistente; O5 y KS 1.2 cycle-exact
  verificados. Carga 300,19 ms, reaparición en 411. Ver `docs/validacion-z1.md`.
- **Falta:**
  - reaparecer en el punto medio si se pasó; ese caso sigue en diagnóstico;
  - el **punto medio**: el objeto `Midway/Goal point` + `Midway point
    rope` del nivel; al tocarlo, marca y Mario grande;
  - la **meta**: la cinta, "course clear", la cuenta de puntos
    (`lv_end_seq.s`) y el fundido;
  - el tiempo agotado;
  - los fundidos de entrada y salida;
  - Mario detrás del poste de la meta.
- **Cómo lo haría:**
  - **Fundidos:** el OCS no tiene brillo global, así que hay que
    reescribir todos los colores. Durante un fundido la lógica está parada
    y sobra CPU: se regeneran los MOVE de color de las dos listas con una
    tabla de 16 pasos por componente.
  - **Mario detrás del poste:** `BPLCON2` por línea con el copper (la
    prioridad es por playfield, no por píxel: en esas líneas Mario queda
    detrás de toda la capa 1, que en la meta es casi solo el poste).
  - **Muerte, punto medio y meta:** son rutinas del ROM que se transcriben
    contra grabaciones de snesorc, como todo lo demás.
- **Tarjetas:** Z1-Z6, R4, R5.

### 10.12 La velocidad: 50 Hz contra 60 — **decisión nueva (D15) [usuario]**

- **El hecho:** el port corre **un frame de lógica del ROM (U), que es
  NTSC, por cada frame PAL**. El juego va a 50/60 = **83 % de la velocidad
  de la SNES americana**, igual que les pasaba a los juegos PAL de SNES
  que no se ajustaban. La música no cambia de tempo, porque el tick sale
  de un timer de CIA (D5).
- **Opciones:**
  - (a) aceptarlo, como la SNES PAL; es lo que hay hoy y no cuesta nada;
  - (b) correr 6 frames de lógica cada 5 de pantalla: +20 % de CPU de
    lógica, que hoy no hay;
  - (c) ajustar la física: rompe el 1:1 con el oráculo.
- **Mi recomendación:** (a), y dejarlo escrito.

### 10.13 Hardware real y pruebas finales

- **Falta:** que el juego corra alguna vez en una A500 de verdad.
- **Riesgos, ordenados:**
  - el handshake del teclado (medido en WinUAE, no en un 8520 real);
  - la temporización del copper (calibrada en WinUAE: WinUAE cycle-exact es
    muy fiel, pero conviene una captura real de `copcal`);
  - la detección de la A501 (P8);
  - la lectura del disco en KS 1.2/1.3.
- **Cómo lo haría:** un ADF de diagnóstico con `copcal`, el teclado
  mostrando los códigos y `logicbench`, para que el usuario le saque una
  foto a la pantalla. El modo diagnóstico del juego (P58) sirve también
  para los fallos en el hardware real: una foto de la página 2 alcanza
  para reproducirlo.
- **Tarjetas:** U1-U4, Z7.

### 10.14 Verificación continua

- **Falta:**
  - el replay completo **hasta la meta** como prueba de `regress.py`: hoy
    `oracle_yi1` se corta antes;
  - una grabación de snesorc que cubra todo el nivel de punta a punta;
  - las métricas del frame entero (O3).
- **Idea, sin decidir:** correr `setup_cloud.sh` + `regress.py` en GitHub
  Actions en cada push. La ROM se arma desde el fuente público y no se
  publica nada derivado de ella, pero se arma en máquinas de GitHub.
  **[usuario]**: consultar antes, por R9.
- **Tarjetas:** Z8, O3.

### 10.15 Orden global

Las decisiones están tomadas (D1 = 50 Hz haciendo todo lo posible, D15 =
velocidad PAL, D16 = la zona de la tubería entra). El orden va en **8 olas**,
descritas una por una en `SUBAGENTES.md` §3 (tarjetas, entrega, criterio de
cierre, sesiones) y resumidas en §1.8:

1. medir el frame entero y grabar todo lo que falta;
2. y 3. 50 Hz: el scroll y la lógica, y los diseños del dibujo y del audio;
4. motores: copper definitivo + cámara vertical (10.2b), vlink,
   conversores, el resto de la lógica de sprites, la zona de la tubería en
   datos;
5. integraciones: enemigos en pantalla, loader, HUD, música;
6. el juego completo: muerte, punto medio, meta, zona de la tubería,
   replay hasta la meta;
7. segunda ronda de 50 Hz con todo junto;
8. cierre: KS 1.2/1.3, arreglos, ADF final.

Total: 12-15 sesiones con las olas en paralelo; 16-20 si hay que
serializar.

Cómo repartirlo entre subagentes (niveles, tarjetas, protocolo):
`SUBAGENTES.md`.

---

## 11. Más allá de YI1: otro nivel y la lógica extra del juego

Fuera del alcance de hoy. Textual en **`docs/mas-alla-yi1.md`**:

- 11.1 Qué es de YI1 y qué es genérico
- 11.2 El proceso, paso a paso
- 11.3 El scroll vertical (el trabajo más grande de otro nivel)
- 11.4 Cargar entre niveles
- 11.5 Pantalla de carga, título y demo
- 11.6 Partidas guardadas
- 11.7 Otros extras (baratos, cuando haya tiempo)
- 11.8 Cosas que conviene decidir YA pensando en esto
