# Decisiones: los datos medidos

> Movido textual desde `AGENTS.md` §9 el 2026-10-03. La tabla de decisiones
> (D1-D16) y la lista de sprites de D3 siguen en `AGENTS.md` §9.

---

### D8/D9 — datos medidos (2026-09-22)

| medida | valor |
|---|---|
| colores CGRAM distintos que usa la capa 1 en todo el nivel | **38** + el cielo |
| máximo en una ventana de 2 pantallas (lo que se ve a la vez) | **31** |
| colores de la referencia (capa 1 + capa 2 + sprites) por ventana de 320 px, >16 px | **20 a 41** |

O sea: **solo el terreno ya llena 32 colores**; 16 (la vieja opción B) está
lejos del 1:1. Antes de elegir D8 hay que averiguar **cómo se mueve la capa 2
en este nivel** (si va a otra velocidad que la capa 1, la opción (b) deja de ser
1:1) leyendo la configuración de scroll del nivel en `lv_read.s`.

### Etapa 4 — resultados (2026-09-22)

#### 1. Cómo se mueve la capa 2 en Yoshi's Island 1 (sin hardware)

`levels/tables.a:DATA_05F000[$105]` = `%0101 1011` → ajuste de scroll 5 →
`L2HorzScrollSettings[5] = 2` (`map_l1.s:45`) → en `player.s:5396`,
**`Bg2HOfs = Bg1HOfs >> 1`: paralaje a media velocidad**. Vertical:
`L2VertScrollSettings[5] = 2`, también a media velocidad. El fondo es
`Layer2Mountains` (`Layer2Ptrs`, fila 100-107).

#### 2. Colores (medidos sobre nuestro render y la referencia)

| medida | valor | consecuencia |
|---|---|---|
| capa 1, colores por línea (ancho completo del nivel) | **22** | necesita 5 planos por sí sola |
| capa 2, colores con peso (incluye el cielo) | **~8** | cabe en 3 planos |
| vista de cámara real (256×224), capa 1 + capa 2 + sprites, por **línea** | **25** | cabe en 31 |
| ídem, por **pantalla** | **40** | hace falta recargar paleta por bandas con el copper |

#### 3. Blitter en la A500 (`player/bench.s`, `a500.uae`, cycle-exact)

Medido por la propia Amiga con el timer A de CIA-B (709379 Hz), 32
repeticiones por carga, con **5 planos entrelazados en pantalla a 320 px**
(peor caso: con 256 px de ancho hay menos contención). Calibración: 14210
ticks/frame contra 14188 teóricos (+0.16 %). Máximo ≈ media en todas las
cargas: la medida es estable.

| carga | BLTPRI off | BLTPRI on |
|---|---|---|
| W1: columna nueva (14 bloques, cada 16 px de scroll) | 5.51 ms · 27 % frame | 4.86 ms · 24 % |
| W2: **recomponer toda la pantalla** (fondo 336×224 + 160 bloques) | 69.3 ms · **346 %** | 58.1 ms · **290 %** |
| W3: bobs (Banzai Bill 64×64 + 4 Rex 16×32, restaurar + dibujar) | 12.6 ms · 63 % | 9.4 ms · 47 % |

| presupuesto por frame a 50 Hz | BLTPRI off | BLTPRI on |
|---|---|---|
| sin paralaje, scroll 1 px/frame + bobs | 64 % | **48 %** |
| sin paralaje, scroll 3 px/frame (carrera) + bobs | 68 % | **51 %** |
| paralaje recomponiendo todo + bobs | 408 % | 337 % → ni a 16.7 Hz |

Deducido de W1 contra W3 (mismos tipos de blit, distinto número): **cada blit
cuesta ~42 µs de CPU** en preparación y espera, además de los datos (P31).

#### 4. Qué opciones de D8 quedan

| opción | colores capa 1 | paralaje | coste | veredicto |
|---|---|---|---|---|
| (a) dual playfield | **7** (necesita 22) | sí | barato | ✗ por color |
| recomponer todo cada frame | 22 | sí | 290-346 % de frame | ✗ por tiempo |
| split por copper (DPF arriba, 5 planos abajo) | ≤ 7 arriba, 22 abajo | solo arriba del corte | barato | con el corte en la fila 15 (el más bajo que deja ≤7 colores arriba) **el 79 % de la capa 2 visible queda debajo, sin paralaje** |
| **(b) fondo pre-compuesto, sin paralaje** | 22 | **no**: el fondo se mueve con el terreno | 48-68 % de frame con bobs | ✓ viable a 50 Hz |

Con el hardware del OCS **no hay forma medida de tener a la vez los colores de
la capa 1 y el paralaje de la capa 2**. La pérdida de fidelidad hay que
elegirla: colores (DPF) o movimiento del fondo (b).

#### 5. Cómo lo hicieron otros juegos del OCS (investigado 2026-09-23)

Fuentes: hilo de Lemon Amiga `viewtopic.php?t=8512` ("Parallax on the Amiga"),
Codetapper *Sprite Tricks* (Brian the Lion, Risky Woods, R-Type 2, Jim Power,
Videokid, Beast, Agony) y la entrevista de Codetapper a **Chris Sorrell**
(James Pond 1/2). Ningún juego del OCS tiene un primer plano de 31 colores
**y** un fondo con paralaje: todos bajan el primer plano a 3 o 4 planos.

| técnica | juegos | primer plano | fondo | paralaje H |
|---|---|---|---|---|
| dual playfield + barras de copper | Lionheart, Kid Chaos, Beast, Agony | 7 + copper | 7 + copper | gratis (`BPLCON1` PF2) |
| **4 planos + 5.º plano de fondo**, paleta 16-31 = copia de 0-15 | James Pond 1 y 2 | 15 + copper | **1 color + copper** (0/16) | ver paridad ↓ |
| sprites detrás del playfield, recolocados por copper | Risky Woods, R-Type 2 (patrón de 64 px, 15 colores); Brian the Lion (el copper escribe `SPRxDATA` cada 8 px, 2 colores) | 15 (4 planos) | según el truco | gratis (`SPRxPOS`) |

**Paridad de planos.** `BPLCON1` tiene un retardo para los planos impares
(1, 3, 5) y otro para los pares (2, 4). En un solo playfield, el plano de fondo
siempre comparte retardo con planos del primer plano. Por eso el paralaje H fino
del 5.º plano **no sale del hardware**: hay que redibujarlo o desplazarlo con
el blitter. Sorrell: el plano 5 de Robocod "se redibuja entero cada 16 px de
scroll", y el paralaje horizontal "no llegué a hacerlo". El vertical sí es
gratis (mover `BPL5PT`). Coste de un blit de desplazamiento de 1 plano:
**sin medir**, se mide con `bench.s`.

**Sprites.** Todas estas variantes necesitan un primer plano de 4 planos. Con 5
planos los sprites pisan los colores 16-31 (P32) y el 5.º plano le roba ranuras
al copper, que ya no llega a una escritura cada 8 px como en Brian the Lion.
Risky Woods y R-Type 2 repiten un patrón de 64 px, y las montañas de SMW no son
periódicas a 64 px.

#### 6. Colores re-medidos por ventana de cámara (2026-09-23)

El "22" de arriba es por línea **a lo ancho de todo el nivel**. Dentro de lo que
se ve (256 px), sobre `work/level_final.png`:

| medida (capa 1, sin el cielo) | valor |
|---|---|
| máx. colores por línea en cualquier ventana de 256 px | **17** |
| líneas con ≤ 15 en cualquier ventana | 428 / 432 |
| líneas con ≤ 7 en cualquier ventana | 307 / 432 (las que fallan: filas 14-23 de bloques, terreno) |
| capa 2 (referencia donde la capa 1 es cielo), píxeles exactos con 1 / 3 / 7 colores por línea | 45 % / 81 % / 98 % |

Simulación (`work/d8_dpf_sim.png`, `d8_cmp_b.png`, `d8_cmp_c.png`):

- **DPF, paleta fija por línea**: rompe la pantalla 7 (bloques de cemento y
  tuberías lavanda/gris pasan a marrón). Con la paleta **siguiendo a la
  cámara**, las tuberías y los bloques siguen perdiendo sombreado. **DPF no es
  1:1 para la capa 1.**
- **Robocod (4+1)**, paleta siguiendo a la cámara: capa 1 **idéntica** en la
  misma ventana. Precio: el fondo queda en 1 color por línea más el cielo
  (las montañas pasan a siluetas con degradado), y la paleta por línea tiene
  que cambiar con la cámara en X. Eso obliga a re-indexar los bloques por zona
  en el conversor. Sin prototipar.
- **Render del nivel entero con (c)** (2026-09-23): `work/d8_c_nivel.png`,
  comparado con (b) en `d8_b_vs_c.png` y `d8_b_vs_c_zoom.png`, ambos sin
  sprites. El fondo limpio se reconstruye con la moda de sus 10 repeticiones
  (período 512 px, 97.8 % de coincidencia). Terreno: 1 píxel distinto en todo
  el nivel. Fondo con el color de mínimo error por línea: **14 % de píxeles
  exactos**. Montañas, nubes y pilares se funden en una sola masa celeste por
  franja, sin contornos, sin sombreado y sin los puntos.

#### 7. Dos ideas más, medidas sobre los datos (2026-09-23)

- **Recomponer solo los bloques cuyo fondo cambia** (5 planos, fondo que se
  mueve 1 px): **90-115 de 224 bloques** por paso. W2 (160 bloques) ya costaba
  290 %. ✗
- **DPF + el copper cambiando colores a mitad de línea.** Es asignación de
  registros: 7 índices por línea y cada color vive entre su primer y su último
  uso. Si se puede reasignar un índice en un hueco de 16 px, **las 432 líneas
  caben en 7 colores vivos**. Con huecos de 32 px ya no caben 79 líneas. Pero
  una línea de cámara llega a necesitar **29 cargas de color**, y con 6 planos
  en lowres el copper da aprox. 1 MOVE cada 16 px, unas 16 por línea de 256 px
  (**estimado, sin medir**). Sería la única vía hacia la capa 1 1:1 **y** el
  fondo a 7 colores con paralaje. Queda sin cerrar hasta simularla con las
  restricciones reales del copper.

#### 8. Opción (d): DPF + recarga de colores a mitad de línea — simulada y medida (2026-09-23)

**Simulación** (`tools/dpfsplit.py`): índices de la capa 1 asignados **fijos
por posición del nivel** (coloreo de intervalos con 7 registros y derrame al
color más cercano). Por frame, el copper carga en el borrado el color inicial
de cada índice y a mitad de línea los que cambian, en ranuras cada 16 px con
±8 px de margen. Si una carga no entra, ese tramo se ve con el color anterior.
Capa 2: fondo limpio de período 512, con ≤ 7 colores por línea salvo una
línea que tiene 8.

| medida (gap 48, margen 8, cámara cada 1 px) | valor |
|---|---|
| capa 1, derrame fijo | 330 px de 359 010 (0.09 %) |
| capa 1, cargas que no entran | 0.010 % de los píxeles vistos; peor encuadre 114 px |
| cargas a mitad de línea | máx. 11 por línea (hay ~20 ranuras en 320 px) |
| cargas en el borrado (capa 1 + capa 2, solo lo que cambia) | máx. **8** (presupuesto 14); 0 líneas-frame por encima |
| peor frame, cargas a mitad de línea | 456 en 89 líneas |
| variantes de bloque por índices | 244 (22 KB + máscara) |
| nivel entero, (d) contra (b) | **346 px distintos de 2.2 M** |

Robusto: con gap 32-64 y margen 4-16 el error queda siempre < 0.2 %.
Renders: `work/d8d_g48m8_nivel.png`, `d8d_g48m8_worst.png`,
`d8d_g48m8_err.png` y `d8_b_vs_d.png`.

**Medida en la Amiga** (`player/copbench.s` + `tools/copbench_read.py`,
`a500.uae` cycle-exact, fetch de 336 px, DMA de sprites encendido):

| modo | separación entre MOVE en pantalla |
|---|---|
| 4 planos | 8 px (= Brian the Lion, calibración) |
| 5 planos | 8/12/12 px (~10.7) |
| **DPF 6 planos** | **16 px** (el supuesto de la simulación ✓) |

DPF 6 planos, pantalla de 320 px: **35 MOVE por línea**, de las que **14-15
caen entre el borde derecho y el izquierdo** de la línea siguiente.

Trampa encontrada al medir: en un WAIT, `or.w #$0f01,d0` también toca la
línea (byte alto). Para la posición h hay que usar `or.w #$000f`.

**Sin medir / abierto** (en orden de riesgo):
1. **Bobs (enemigos) en la capa 1**: necesitan índices libres en sus líneas.
   Los sprites de hardware quedan libres con los colores 16-31 (en DPF no
   los usa nadie): Mario puede ir 1:1 en un sprite adosado de 15 colores.
   Rex y Banzai Bill no entran todos en 8 sprites. Sin estudiar.
2. **CPU para regenerar la lista del copper**: 456 cargas en el peor frame;
   a 60-100 ciclos cada una, 20-32 % de frame (**estimado**).
3. Blitter: la capa 1 son 3 planos (antes 5) y la capa 2 no se blitea, pero
   6 planos le roban más ciclos durante la pantalla. Hay que re-medir W1/W3
   en DPF.
4. Chip RAM de la capa 2: 832 px (512 + pantalla) × ~328 líneas × 3 planos
   ≈ 100 KB.

#### 9. Opción (d): los objetos, con una partida real (2026-09-23)

**Datos**: el usuario jugó Yoshi's Island 1 en `smwrecomp` mientras
`tools/oamrec.py` + `tools/oambot.lua` grababan por el puerto Lua TCP la OAM
visible, la cámara y las ranuras de sprites de cada frame:
`work/oam_yi1.txt`, 2500 frames de translevel $29 sin huecos. Trampas del
protocolo, medidas: **cada valor devuelto se corta a 1024 caracteres, van
como máximo 16 valores por respuesta y hay una sola conexión a la vez** (una
segunda conexión rompe la primera). El mensaje de la intro también es modo $14
(translevel 0).

**Modelo Amiga**: 8 canales de 16 px, que dan 4 columnas adosadas de 15
colores (17-31) u 8 de 3 colores (cada par comparte 3). El copper corre cada
columna entre líneas (`SPRxPOS`) y recarga los colores 17-31 por línea.

| medida (`tools/oamstudy.py`, `tools/d8objs.py`, `tools/d8demote.py`) | valor |
|---|---|
| líneas con sprites que caben en ≤ 4 columnas | 98.3 % (2310 de 138 629 piden 5-6) |
| quién pide 5-6 columnas | siempre Banzai Bill (4) + Mario, a veces + Rex: 130 frames (5 %) |
| colores por línea de 16 px: Mario / Rex / Banzai / Piranha / Chuck | 4 / 6 / 6 / 5 / 7 |
| peor unión de una línea de Mario con una de cualquier enemigo | 11 (≤ 15 ✓) |
| Banzai en pares sin adosar (≤ 3 colores por franja de 32 px) | ✗: 42-63 de 63 líneas tienen más |
| líneas de 5-6 columnas que se resuelven pasando un objeto a bob en PF1 | 77.7 % (Banzai 61.6 %, Rex 25.8 %, Mario 21.6 %) |
| **frames que quedan con alguna línea sin resolver** | **45 de 2500 (1.8 %)** |

Contando los colores por paleta entera (Mario 11 + enemigo 7) salía que el
33 % de los frames se pasaba de 15. Contando por línea, que es lo que carga
el copper, no se pasa nunca.

**Diseño que sale de esto**: Mario y los enemigos van en sprites adosados, y
el copper recarga los colores 17-31 por línea. Cuando un Banzai Bill comparte
líneas con Mario y un Rex, uno de los tres (casi siempre el Banzai, que vuela
por aire donde el terreno deja registros libres) pasa a bob en PF1. En el
1.8 % restante el bob usa el color más cercano.

**Sin medir**: cuántas MOVE por línea piden las recargas de colores de los
sprites y de los bobs (hay ~6 libres en el borrado y ~9 a mitad de línea
después de la capa 1). Las filas de color de Rex y Banzai salen de la pose
de la referencia, no de cada frame.

#### 10. Opción (d): copper completo, CPU y blitter — simulado y medido (2026-09-23)

**Copper con todo junto** (`tools/copsim.py`, los 2500 frames de la partida,
560 000 líneas): capa 1 + capa 2 + colores de sprites + `SPRxPOS`.

| medida | peor línea | presupuesto |
|---|---|---|
| MOVE en el borrado | 9 | 14 |
| ranuras a mitad de línea | 10 | 16 (256 px) |
| cargas que no entran | 1916 en 492 frames: **todas de la capa 1** (las ventanas estrechas del punto 8); sprites y fondo no suman fallos | — |
| entradas por frame | media 432, máx. 857 (3.4 KB) | — |

Aproximación: las filas de color de Mario salen del bloque 16x32 con más
píxeles de su hoja de gráficos, no de su pose en cada frame.

**Medido en la Amiga** (`player/bench2.s` y sus variantes `bench2v.s` y
`bench2m.s`, `tools/bench2_read.py`, `a500.uae` cycle-exact, DPF 6 planos en
pantalla: capa 1 de 3 planos entrelazados + capa 2 de 3):

| carga | durante la pantalla | después de la última línea visible |
|---|---|---|
| W1 columna nueva, 14 bloques de 3 planos, copia directa | 5.6-6.4 % | 9.0-9.3 % |
| W2 lista del copper del peor frame, bucle por línea (224 WAIT + 633 MOVE) | **38.1 %** | 30.9 % |
| W2 misma lista copiada en bloque con `movem` | — | **15.1 %** |
| W3 bobs Banzai + 4 Rex, 3 planos (BLTPRI off / on) | 47.6 / 33.8 % | 26.2 / 22.7 % |

Con 5 planos (etapa 4) la columna costaba 27 % y los bobs 63/47 %: en DPF el
blitter trabaja con 3 planos y no compone el fondo.

**Lectura**:
- Lo que pesa en la lista del copper es la **CPU** (~52 ciclos por entrada,
  casi todo de la vuelta por línea), no la contención (+20 %).
- En la partida la cámara **no se movió nunca en vertical** y en horizontal
  se movió en el 57 % de los frames. Entre un frame y el siguiente solo
  cambian las líneas con cargas a mitad de línea (~19) y las que tienen
  sprites (~55).
- Diseño propuesto (**sin medir**): un segmento de copper por línea,
  encadenado con `COP2LCL` + `COPJMP2` (2 MOVE; `COP2LCH` fijo si toda la
  lista está en el mismo banco de 64 KB). Cada segmento tiene dos copias:
  la CPU reescribe solo las líneas que cambian, en la copia libre, y cambia
  el puntero de la línea anterior. Estimado: ~75 líneas × ~150 ciclos ≈ 8 %
  de frame.
- En (d) los enemigos van en sprites de hardware; W3 solo pesa en los
  frames que pasan un objeto a bob (punto 9).

**Presupuesto del peor frame, conservador** (BLTPRI encendido): lista del
copper 15 % (en bloque) + bobs 34 % + columna 9 % ≈ **58 %**, sin contar la
lógica del juego (etapas 8-9, sin medir), que es el siguiente riesgo.

Conclusión: los trucos de la época **confirman** el veredicto de D8, que no hay
1:1 de las dos capas con paralaje en el OCS. Además dejan una tercera opción
concreta: **(c) Robocod**, con la capa 1 1:1 y paralaje H+V real a cambio de
un fondo de 1 color por línea.

### D7 — cómo se cerró

La hipótesis "selección de paleta que no encontramos" era la buena, pero no es
por nivel sino **por pantalla**: `MAP16AppTable` (`lv_read.s:805`) tiene cuatro
versiones de las entradas `$133`-`$13A`, idénticas salvo la paleta (3, 5, 6, 7),
y el cargador de columnas elige `(columna >> 4) & 3`. Las tuberías de la
pantalla 7 de Yoshi's Island 1 caen en la variante 3 = paleta 7 = lavanda, que
es lo que muestra la referencia. Detalle en P28.
