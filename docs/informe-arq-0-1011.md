# ARQ-0 — la vara, la medida de partida y las palancas grandes

2026-10-11. Tarjeta `docs/instrucciones-arq-0.md` (D17). Pasos 0, 1 y 2
medidos. P3 (la espiral) quedó sin prototipo: depende de lo que se elija
para P1/P2. **Nada integrado al vivo**: el hash sigue en `33f2250a…`
(recompilado y comparado). La única línea nueva del juego es una sonda
opt-in `-DARQ_5PL` en `scroll.s`, que solo cambia `BPLCON0`. **La
elección es del usuario (§5).**

## 1. Paso 0 — la vara: `tools/arq_diff.py`

Compara una captura de WinUAE con la pantalla de la SNES del mismo frame
del oráculo (`snesorc --shots`). Usa el formato de directorio de
`sweep_cmp.py` (o un par suelto) y la alineación fila Amiga = fila
SNES − 1 (P128). Da:

- **% de píxeles distintos** con el color de 12 bits: la base 1:1 es la
  SNES cuantizada a 12 bits.
- **CIEDE2000 por píxel**, sobre el color mostrado: media, p99, máximo y
  **área con ΔE ≥ 2**. El umbral es un parámetro (`--thr`).
- **El piso de 12 bits**, como dato: el ΔE entre la SNES de 15 bits y la
  cuantizada.
- **Una imagen SNES | Amiga | mapa de ΔE** por foto. Colores del mapa:
  azul < 2, amarillo 2-5, naranja 5-15, magenta ≥ 15.

La barra de estado (filas 0-39, sin portar, D11) se informa aparte. Las
métricas "juego" la excluyen. Las capturas con la ventana minimizada se
rechazan (P135).

**Puertas cumplidas:**

- `--selftest`: siete pares de la tabla de Sharma (2005) a 10⁻⁴, una foto
  contra sí misma y un píxel cambiado.
- `--gate` en las dos barridas (126 fotos cada una): el recuento de
  12 bits es el de `sweep_cmp` en todas. Las fotos exactas según
  `sweep_cmp` dan ΔE 0 y área 0: 50 en la del 10/10, 66 en la de hoy.

### Línea base (master de hoy, replay yi1, una foto por segundo, WinUAE cycle-exact)

| medida, zona de juego | SW1 del 10/10 | **hoy** |
|---|---:|---:|
| fotos exactas | 50 / 126 | **66 / 126** |
| píxeles distintos (media) | 0,97 % | **0,56 %** |
| ΔE medio | 0,44 | **0,29** |
| área ΔE ≥ 2, media por foto | 457 px | **264 px** |
| área ΔE ≥ 2, peor foto | 10.705 px (k2449, fuera de sincronía) | **3.617 px** (k1049) |

En las peores fotos de hoy lo que pesa son objetos sin dibujar: el
Banzai Bill (k699-k1099, tarjeta BANZAI) y la moneda de Yoshi con otro
tono (P22). Imágenes: `work/arq0/base_yi1/img/`. Datos:
`work/arq0/base_yi1/arq_diff.json`.

**Piso de 12 bits:** pasar la paleta de 15 a 12 bits ya cuesta un
**ΔE medio de 1,71** sobre toda la pantalla. Redondear en lugar de
truncar da lo mismo (1,71). El mejor color de 12 bits por ΔE bajaría a
1,54, casi todo por el blanco azulado (29,30,31): 6,1 → 4,6. Es un límite
del hardware y no lo mueve ningún recorte del port.

**Umbral "se nota" = ΔE ≥ 2: a confirmar por el usuario** con las
imágenes (decisión pendiente, §5).

## 2. Paso 1 — medida de partida, BENCH WinUAE cycle-exact

Replay BM1 (`bm_build.sh`, G5L + CUSHION), `-DREPLAY -DBENCH`, master
`e66b326`. Cada captura se comprobó con el número de frames del replay.

- **Meta:** el replay de yi1 no llega a la meta. Su cámara no pasa de
  s ≈ 2.280 y termina en la tubería. Se usó `oracle_goal` recortado antes
  del frame 3961 (`work/arq0/oracle_goal_cut.bin`, 2.508 frames, 0
  resincronizaciones). Ahí Mario toca la meta y empieza la caminata
  final, que no está portada. Recorre hasta s = 4.717, o sea que pasa por
  los postes (P81). El replay entero no entra en el disco: 970.752 B
  contra 901.120 B, con 590 resincronizaciones.
- **Rex:** `stress_sprites` y `hills2`.

Columnas: picos de cada parte en % del frame. Son de fotos distintas y
no se suman.

| tramo | fotos perdidas | racha | total medio | level_frame | build_mid | resto scroll | columns | mspr_draw |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| normal (yi1) | 217/6312 (3,44 %) | 2 | 94,9 % | 32,7 % | 109,0 % | 132,5 % | 20,1 % | 8,0 % |
| vuelta (stress_back) | **1128/4126 (27,3 %)** | **28** | 108,4 % | 61,3 % | 227,2 % | 149,2 % | **285,3 %** | 10,1 % |
| meta (goal recortado) | 581/2507 (23,2 %) | **22** | 104,3 % | 57,4 % | 164,0 % | 140,9 % | **238,6 %** | 10,2 % |
| Rex (stress_sprites) | 397/1914 (20,7 %) | 5 | 105,0 % | 58,2 % | 96,7 % | 122,3 % | 25,6 % | 10,6 % |
| Rex (hills2) | 686/2835 (24,2 %) | 5 | 108,8 % | 57,2 % | 128,1 % | 132,4 % | 27,8 % | 10,8 % |

Leídos con `python work/arq0/table.py`. Capturas en `work/arq0/b_*/`.

**Hallazgo — el master empeoró desde el informe P123 (10/10, `6797dd0`):**

| replay | P123 (10/10) | hoy |
|---|---|---|
| yi1 | 14/6312, racha 1 | 217/6312, racha 2 |
| stress_back | 387/4126, racha 5 | 1128/4126, racha 28 |
| stress_sprites | 98/1914, racha 3 | 397/1914, racha 5 |

- **yi1:** las 217 coinciden con el control que midió G7 esa misma tarde
  (`informe-g7-1010.md`). La subida está entre `6797dd0` y la sesión G7.
  **La tabla de ROADMAP §2 (14/6312) estaba vieja.**
- **Vuelta y meta:** `columns` tiene un pico de 285 % / 239 % con 6
  planos que desaparece con 5 (23 %). Rachas de 28 y 22 fotos son medio
  segundo de imagen congelada.
- **Sin atribuir:** no se hizo bisect. Candidatos: SW-A/B (bloques, D_MAP
  desde las columnas), los objetos de G4-B y la regla de 2 por foto.

**Traza VBTRACE de yi1** (`work/arq0/vt_yi1/vbtrace.log`):

- **124 fotos salteadas.** La sonda difiere del BENCH: no tiene los
  sellos.
- **Agrupadas en rachas:** frames 1124-1236, 3306-3453, 4039-4266 y
  4559-4711, con la cámara en s ≈ 290, 1.550-1.650, 1.850-1.900 y
  1.975-2.030.

## 3. Paso 2 — las palancas

### P1 — 5 planos (PF2 de 2 planos)

**(a) Colores de la capa 2 por línea, en todas las cámaras.**

- **Base:** la capa 2 de YI1 son 7 colores más el cielo, que sale por
  transparencia.
- **Recuento:** en el 67 % de los pares (línea, ventana de 256 px) se ven
  **más de 3** (el 28 % usa los 7). 154 de las 320 filas con capa 2 llegan
  a 7 en alguna ventana.
- **Veredicto: no caben en 3.**

**(b) El mejor reparto de 3 colores, medido con la vara:**

| reparto | ΔE medio en la capa 2 | área ΔE ≥ 2 |
|---|---:|---:|
| terna fija por fila (el periodo de 512) | 1,36 | 14,6 % de la capa 2 |
| terna por fila y por ventana de cámara | 1,10 | 18 % en la peor ventana |
| **en pantalla** (oculta por la capa 1, parallax, zona de juego) | 1,82 | **4.464 px por foto de media**, mediana 4.641, peor 7.063 (s = 3.328) |

- **Contra la base:** es **17 veces** la diferencia visible de hoy (264
  px), y en *todas* las fotos.
- **Qué se pierde:** el sombreado y los contornos de las colinas, con
  rayas horizontales donde cambia la terna.
- **Imágenes:** `work/arq0/p1_pantalla_s1528.png` (mediana),
  `p1_pantalla_s3328.png` (peor) y `p1_capa2_x136.png` (la capa 2 sola).

**(c) BENCH A/B, sonda `-DARQ_5PL`:**

- **Qué hace:** solo cambia `BPLCON0` a 5 planos. La imagen de la capa 2
  sale mal; los tiempos (DMA de planos, CPU, blitter) son los reales.
- **Qué no incluye:** el costo de recargar 3 colores por fila. La
  ganancia real sería un poco menor.

| tramo | 6 planos (hoy) | 5 planos | build_mid pico | total pico |
|---|---|---|---|---|
| normal | 217 (3,44 %), racha 2 | **93 (1,47 %), racha 1** | 109 → 93 % | 216 → 175 % |
| vuelta | 1128 (27,3 %), racha 28 | **772 (18,7 %), racha 5** | 227 → 155 % | 428 → 315 % |
| meta | 581 (23,2 %), racha 22 | **342 (13,6 %), racha 5** | 164 → 146 % | 439 → 306 % |
| Rex (sprites) | 397 (20,7 %), racha 5 | **267 (14,0 %), racha 3** | 97 → 65 % | 274 → 229 % |
| Rex (hills2) | 686 (24,2 %), racha 5 | **447 (15,8 %), racha 3** | 128 → 96 % | 280 → 223 % |

- **Cuánto gana:** −32 % a −57 % de fotos perdidas y corta las rachas
  largas.
- **Qué no alcanza:** D1 no cierra en ningún tramo (mínimo ≤ 0,1 %,
  racha 1). La lógica sola sigue en 52-55 % en los tramos de estrés.

### P2 — menos trabajo del copper por frame

**(a) Plan del PF1 precalculado por posición de cámara.**

- **Cómo se calculó:** recorriendo el MLD de `yi1_s.dat` con la regla de
  validez de `build_mid` (intervalos [s0 + a, s0 + b), entrada por la
  derecha, cargas tarde en celdas de 8 px).
- **Cuánto ocupa:** **8.607 intervalos y 7.404 segmentos distintos, ≈ 199
  KB**.
- **Dónde tendría que ir:** el copper los lee, así que en chip, que tiene
  17-40 KB libres. Aun como fuente para la CPU no entran en slow: el vivo
  tiene 61 KB libres.
- **Las líneas más caras:** la 171 y la 187 (367 intervalos), en la zona
  de los postes.
- **Veredicto: no entra en memoria.** Una variante con caché por línea y
  saltos del copper (`COPJMP2`) cuesta unos 5 MOVE por línea en el hueco
  entre filas, que ya está al límite (P111). Sin medir; no se propone.

**(b) Paleta optimizada que fusione colores de la capa 1.**

- **Modelo:** reproduce los eventos de hoy (9.951 intervalos contra
  9.963).
- **Resultado:** los **27 colores de la capa 1 están todos a ΔE ≥ 2 entre
  sí**. Fundir los que "no se notan" no quita ni una carga.

| umbral de fusión | colores | intervalos de carga | píxeles recoloreados |
|---|---:|---:|---:|
| ΔE < 2 | 27 | 9.951 (−0 %) | 0 |
| ΔE < 3 | 26 | 9.907 (−0,4 %) | 0,03 % |
| ΔE < 12 | 20 | 9.179 (−8 %) | 3,7 % |
| ΔE < 20 | 11 | 7.925 (−20 %) | 13,7 % |

- **Por qué no rinde:** las cargas no vienen de colores parecidos. Vienen
  de los mismos colores que reaparecen a lo largo de la fila cuando hay
  más de 7 a la vista.
- **Veredicto: sin ganancia invisible.**

### P3 — la espiral

- **Sin prototipo.** S11 midió que en la vuelta, con 3 listas, se
  reescriben ≈ 90 líneas por visita. Cada lista llega 36-48 px más a la
  izquierda y la ventana de validez de una línea es de ≈ 13 px.
- **Palancas que quedan:** menos listas (va contra el colchón aceptado en
  D1) o menos fotos omitidas (que es lo que hace P1).
- **Lo primero, de todos modos:** las rachas de 28/22 de hoy vienen con
  el pico de `columns` que se fue con 5 planos. Antes de P3 hay que
  entender ese pico (§4).

## 4. Lectura

1. **La palanca que más rinde (P1) es la única que se ve**, en todas las
   fotos y 17 veces por encima de la diferencia de hoy. No cumple "que no
   se note" con la vara propuesta.
2. **P2 en sus dos formas no da ganancia que valga:** (a) no entra en
   memoria; (b) no hay colores fundibles sin que se note.
3. **El master de hoy cuesta mucho más que el del 10/10:** 15× las fotos
   perdidas en yi1, 3-4× en el estrés y rachas de 28. Es lo único grande
   que se puede bajar sin tocar la fidelidad. Encontrar qué lo subió es
   barato: bisect con BENCH entre `6797dd0` y hoy, en serie o con slots
   (P135).
4. **Ni con 5 planos se llega a D1 en el estrés:** la lógica sola ocupa
   52-61 % del frame.

## 5. Para que decida el usuario

- **D-A (la vara):** ¿ΔE ≥ 2 es "se nota"? Mirar
  `work/arq0/base_yi1/img/` y `work/arq0/p1_pantalla_*.png`.
- **D-B (P1):** ¿5 planos con la capa 2 en 3 colores por fila (imágenes
  arriba) a cambio de −32 a −57 % de fotos perdidas? Recomendación: **no
  por ahora**. Primero recuperar lo que se perdió desde el 10/10 (punto
  4.3), que no cuesta imagen, y volver a medir.
- **D-C (el contrato):** se escribe con la elección, como dice la tarjeta.
  Sin elección no hay contrato.

### Decisiones del usuario (2026-10-11, después de este informe)

- **D-A: la vara es ΔE ≥ 2**, vista la página de calibración (escalones de
  color, SNES a 12 bits, diferencias reales y P1). **Tolerancia: ΔE hasta 3
  no le molesta al usuario si da beneficios claros**; se informa aparte el
  área ΔE ≥ 3 cuando un recorte la use.
- **D-B: P1 (5 planos) vale**, pero antes hay que buscar un truco visual que
  acerque la capa 2 de 3 colores por fila a la original (P1-V).
- D-C (el contrato) se escribe cuando P1-V cierre.

### P1-V — trucos visuales para la capa 2 de 3 colores (en curso, 2026-10-11)

Medido sin hardware (sobre `work/yi1_d.dat`, la capa 1 tapa, paralaje
x0 = s/2, zona de juego de 184 filas). Área con ΔE ≥ 2 por foto; 76
encuadres. Referencias: **port de hoy 264 px**, **P1 tal cual 4.462 px**.
En los 12 bits todos los escalones de estos colores pasan de ΔE 3, así que
el área con ΔE ≥ 3 es la misma (la tolerancia de D-A no cambia nada acá).

| variante | media | mediana | peor | qué cuesta |
|---|---|---|---|---|
| V0 terna fija por fila (P1) | 4.462 | 4.569 | 7.063 | nada |
| V1 terna por fila y ventana de la cámara | 3.586 | 3.466 | 6.929 | recarga por fila |
| V2 V1 + COLOR00 como 4º color donde no se ve el cielo | 3.525 | 3.383 | 6.733 | ídem |
| V3 V2 eligiendo con lo visible | 3.306 | 3.254 | 6.545 | cálculo por frame |
| V4 V3 + tramado | 3.336 (por píxel) | — | — | no ayuda: 4.613 vs 4.649 en la vista 2×2 |
| cortes fijos en pantalla, ≤ 2 por fila (bloques de 32 px), elección por x0 | 645 | 446 | 1.527 | tabla de 512 × 184 entradas ≈ 2,4 MB: **no entra** |
| **cortes anclados a la capa 2, tramos ≥ 64 px**, rejilla del copper 8 px | **461** | **446** | **1.162** | **tabla de 8.365 B** (4,9 tramos por fila); ≤ 4 cortes visibles por fila |
| ídem, tramos ≥ 96 px (≤ 3 cortes) | 1.036 | 966 | 2.126 | tabla 6.673 B |
| ídem, tramos ≥ 128 px (≤ 2 cortes) | 1.351 | 1.195 | 2.499 | tabla 5.368 B |

Corte anclado: cada fila del mapa de 512 px de la capa 2 se parte en tramos
(programación dinámica sobre bloques de 16 px), cada uno con su terna (+
COLOR00 si el tramo no tiene cielo). En pantalla el copper hace WAIT en
`(inicio − x0) mod 512` redondeado a 8 px y 3-4 MOVE de color. La tabla no
depende de la cámara ni del número de frame: una lista de tramos por fila.

Lectura: los trucos de paleta solos dan −25 %. **Los cortes de paleta a
mitad de fila son el truco que sirve**: con tramos de 64 px queda en 461
px por foto, 1,7× el port de hoy (contra 17× de P1 sin trucos). Lo que
queda se ve en el contorno oscuro de las colinas de adelante y en algún
brillo suelto (`work/arq0/de2/p1va_1528_*.png`, `p1va_3328_*.png`).

### P1-V medido: los cortes se comen la ganancia (2026-10-11)

El usuario: "medí la ganancia, y si es así lo acepto", y después dio
libertad creativa para modificar el plano. Medido:

**La cuenta.** P1 gana porque deja de leer el plano 6: 17 palabras de DMA por
línea (`FETCHW`). Cada palabra de copper compite por el mismo bus. Los cortes
de 64 px gastan **16,3 palabras por línea** (WAIT + 2 por color que cambia,
`p1v_anchor.py --dma`); hay que sumarles el borrado que repone la paleta del
primer tramo en cada línea, y la CPU que los mueve con la cámara.

**La medida (BENCH, WinUAE cycle-exact).** La sonda `-DARQ_CUTN=K` agrega K
MOVE nulos por línea detrás del borrado (solo el DMA, sin la CPU: es la
mejor cota posible para los cortes). Las bandas `-DARQ_BANDS` ponen 5 planos
fuera de las filas [B1, B2) con un MOVE de `BPLCON0` en el borrado (sin CPU
por frame: la ventana vertical es fija). Fotos perdidas (racha):

| tramo | hoy | P1 | P1 + 8 MOVE (cortes de 64 px) | bandas 0-16 + 208-223 | bandas 0-16 + 192-223 | bandas 0-29 + 192-223 | bandas 0-47 + 192-223 |
|---|---|---|---|---|---|---|---|
| yi1 | 217 (2) | 93 (1) | 191 (2) | 195 (2) | 184 (2) | 173 (2) | 164 (2) |
| back | 1128 (28) | 772 (5) | 1009 (25) | 1041 (24) | 1003 (7) | 1002 (22) | 968 (22) |
| sprites | 397 (5) | 267 (3) | 364 (4) | 375 (5) | 366 (5) | 356 (5) | 345 (4) |
| hills2 | 686 (5) | 447 (3) | 620 (5) | 644 (5) | 627 (4) | 610 (5) | 593 (4) |
| goal | 581 (22) | 342 (5) | 447 (7) | 460 (7) | 450 (7) | 439 (7) | 428 (7) |
| **imagen, ΔE ≥ 2 por foto** | 264 | 4.462 | ≈ 460-490 | **≈ 4** | 23 | 119 | 333 |

(La racha de back es inestable entre variantes: 24 / 7 / 22 / 22. El área
de las bandas es la media por foto sobre las 224 filas, sin el HUD encima.
Con la banda de abajo desde la fila 192, el error se concentra en los huecos
del suelo por donde se ve una colina: hasta 535 px en esas fotos (sombreado
plano y una raya en la fila 192), `work/arq0/de2/p1vb_17_192_3328_*.png`.
Desde la 208 no hay huecos: ≈ 4 px.)

Lectura:

- **Los cortes no sirven.** Aun sin su CPU, conservan del 20 al 55 % de la
  ganancia de P1, menos que las bandas, y gastan copper en cada línea.
- **Las bandas son la variante que sirve**, sin CPU por frame y con 2
  MOVE de `BPLCON0`. Las filas de arriba (cielo y nubes, bajo el HUD) y las
  del suelo admiten 3 colores + COLOR00 casi sin diferencia. Bandas 0-16 +
  192-223 (49 filas): 23 px por foto de media y del 25 al 55 % de la ganancia
  de P1 (la racha de goal baja de 22 a 7), pero se nota en los huecos del
  suelo. **Bandas 0-16 + 208-223 (33 filas): ≈ 4 px, invisible**, y del 17 al
  24 % de la ganancia (51 % en goal, racha 22 → 7). Bandas 0-47 + 192-223 (80 filas):
  333 px, del 39 al 64 %.
- **El resto de la ganancia está en las filas de las colinas.** Ahí la capa 2
  tiene 7 colores por fila, y ningún truco de paleta las lleva a 3 sin
  verse: 3.900 px por foto o más (curva en `tools/arq0/p1v_mix.py`). Con
  cortes se arregla la imagen, pero el copper se come el ahorro.
- **Otra fuente de DMA sin costo de imagen: la dieta de copper.** El copper
  fijo de cada línea son 24 palabras, más que las 17 del plano 6: 2 WAIT
  (el segundo es un relleno histórico de la etapa 6, cuando el primero
  cruzaba la línea 255), 7 MOVE de borrado de la capa 1 y el salto al
  segmento siguiente (3 MOVE). Del borrado solo hacen falta 2,1 MOVE por
  línea en promedio (colores que cambian respecto del final de la línea
  anterior). Estimado, sin medir: saltar el WAIT repetido, 2 palabras;
  omitir `COP2LCH` cuando el banco no cambia, 2; compactar el borrado y
  saltar el resto, ~6 netas. Unas 10 palabras por línea, cerca del 60 % del
  plano 6, sin tocar la imagen. Toca `apply_colors` (posición fija por
  registro, CHG de `mkscroll.py`), `build_mid` y la búsqueda del salto de
  G5L (`$0084`).

### ARQ-C paso 1 medido (2026-10-11)

Los saltos al segmento siguiente entran en el segundo WAIT (`SEGIN` = 4 en
`scroll.s`; el segmento que cruza la 255 lleva el MOVE nulo primero; el fin
de lista va en `SEGIN` y `CL_SIZE` crece 4 B). 2 palabras de copper por
línea menos, imagen igual (regresión completa OK). Fotos perdidas (racha),
6 planos: yi1 217 → 213 (2), back 1128 → 1090 (25), sprites 397 → 393 (5),
hills2 686 → 677 (6), meta 581 → 484 (7). Vivo: SHA `425b658a…`.

### Decisión (libertad creativa del usuario, 2026-10-11)

El usuario dio libertad para modificar el plano buscando el mayor parecido
con la mayor ganancia. Con lo medido:

1. **Los cortes de paleta no se adoptan**: no conservan la ganancia.
2. **Primero, la dieta de copper (tarjeta ARQ-C)**: es la palanca estimada
   más grande (~10 palabras por línea) y no cambia la imagen. Se mide con
   BENCH antes de seguir.
3. **Después, las bandas de 5 planos 0-16 + 208-223 (P1-B)**: invisibles
   (≈ 4 px por foto) y medidas del 17 al 24 % de la ganancia de P1 (51 % en
   goal). Hace falta convertir esas filas de la capa 2 a 2 planos con su
   paleta, mover sus datos del plano 6 para que el puntero (que no avanza en
   las filas de 5 planos) quede alineado, y verificar con `arq_diff` en
   WinUAE.
4. **Las filas de las colinas a 5 planos (P1 entero) quedan para el
   usuario**: es lo único que cambia la imagen de forma visible (≈ 3.900
   px por foto más).
5. El contrato del frame (D-C) se escribe con lo que dejen ARQ-C y P1-B.

Herramientas: `p1v_pareto.py` (cortes optimizados con costo de copper),
`p1v_rows.py` (5 planos por fila, imágenes de bandas `--bands B1 B2 --img
s`), `p1v_mix.py` (mezcla por fila), `build_cut.sh` (`K=8` o
`BANDS=17,192`), `table.py c8 bd17_192 ...`.

## 6. Reproducir

Todo en `tools/arq0/` (scripts de esta medida; escriben en `work/arq0/`):

```
python tools/arq_diff.py --selftest
python tools/arq_diff.py --dir work/arq0/yi1b --gate
python tools/arq_diff.py --dir work/arq0/yi1b --out work/arq0/base_yi1
python tools/arq0/quant.py          # piso de 12 bits
python tools/arq0/p1a.py            # P1 (a)(b)
python tools/arq0/p1screen.py       # P1 en pantalla + imagenes
python tools/arq0/p2a.py            # P2 (a)
python tools/arq0/p2b.py            # P2 (b)
sh tools/arq0/build_base.sh         # builds BENCH de partida (b_*); goal recortado: ver §2
sh tools/arq0/shots_par.sh b_yi1:260 b_back:200 b_goal:170   # capturas en paralelo, una copia de shot.ps1 por slot (P135)
python tools/arq0/table.py
python tools/arq0/p1v.py --step 64           # P1-V: V0-V3
python tools/arq0/p1v_dither.py              # P1-V: V4 (tramado)
python tools/arq0/p1v_split.py               # P1-V: cortes fijos en pantalla
python tools/arq0/p1v_anchor.py --step 50 --minseg 64   # P1-V: cortes anclados (--img s ... para imagenes)
```

El oraculo recortado se rehace con los primeros 2.508 registros de 584 B
de `work/oracle_goal.bin` (frames 1453-3960). Los builds `-DARQ_5PL` son
los mismos con `GDEFS="-DREPLAY -DBENCH -DARQ_5PL"` y `OUT=work/arq0/p5_<tramo>`.
