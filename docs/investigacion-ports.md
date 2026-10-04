# Investigación: cómo resolvieron otros lo que nos frena (2026-10-03)

> Qué es: un relevamiento de ports, motores y juegos de Amiga 500 (y de
> otras máquinas cuando la idea se traslada) buscando soluciones a los
> problemas **abiertos** de este proyecto, sobre todo de **rendimiento**:
> el scroll con cargas de color (`build_mid`), la lógica del 65816 en el
> 68000, el dibujo de los sprites del nivel, el audio y la forma de medir.
> Es el mismo ejercicio que se hizo para el paralaje (`AGENTS.md` §9,
> "Etapa 4 — resultados", punto 5).
>
> Cómo leerlo: §1 es el resumen con lo que conviene hacer; §2-§8 el
> detalle por problema, con la fuente; §9 las tarjetas propuestas; §10 lo
> que se buscó y no sirvió (también es resultado); §11-§13 los hilos de
> EAB y lo de 65816/C/68000; §14 Coppershade y el código de juegos leído.
>
> Límite de la búsqueda: **English Amiga Board (eab.abime.net) no se pudo
> leer** (protección anti-bots); de sus hilos solo hay lo que muestran los
> buscadores. Varias respuestas buenas seguramente están ahí.

---

## 1. Resumen

| problema nuestro | quién lo resolvió y cómo | qué nos sirve | acción |
|---|---|---|---|
| El peor frame pasa del 100 % (D1, O4) | **Robocod** (Chris Sorrell): la lógica corre a 50 Hz fija por interrupción de timer y el bucle principal dibuja "lo antes que puede" las peticiones de render acumuladas | Una cuarta opción para el informe D1: **lógica siempre a 50 Hz, imagen que pierde un frame solo cuando no llega**. Ni 25 Hz fijos ni recortar | §2.1, tarjeta **O5** |
| Cola de blits por interrupción (ROADMAP §9.6) | **AmiGalaga** lo midió en una A500 de serie: la cola por interrupción **no gana** sin fast RAM, y con `BLTPRI` pierde | No implementar la cola sin medirla antes | §2.2, corrige §9.6 |
| Bobs con un solo buffer de PF1 (10.6) | **Battle Squadron**: borra y redibuja los bobs **detrás del haz**, en franjas de 1/3 de pantalla, sin doble buffer | Confirma la opción "detrás del haz" y ahorra los 59 KB del segundo buffer | §2.3 |
| `build_mid` (scroll a ≤ 25 %) | **Ningún juego** encontrado hace cargas de color a mitad de línea con scroll horizontal a esta densidad. Los que más copper usan (**Risky Woods**, 27 KB de lista) la tienen **precalculada** y por frame cambian un puñado de palabras | Confirma la dirección S3/S5/S6/S7 (que el cambio por frame no dependa del contenido), y S1c (postes con sprites) | §3 |
| Cámara vertical (§10.2b) y coste de escribir la lista | **Toni Wilen** (EAB): lista precalculada por línea del nivel, con WAIT solo horizontal, en la que se entra y se sale con `COPJMP`; **DanScott** (Chuck Rock 2): el blitter copia la lista del copper | Mover la cámara en vertical = 2-3 palabras; S8 tiene precedente comercial | §12.1 |
| Bucles del copper para líneas iguales (idea nueva) | Técnica del HRM y de las demos (WAIT enmascarado + `SKIP`) | **Medido en nuestros datos: no sirve** (solo ~12 % de líneas repetidas) | §3.3, descartado |
| `R16`/`W16` byte a byte (~50 ciclos) | Emuladores de Mega Drive/N64: **memoria "swizzled"** (XOR 1) o al revés; JOTD: memoria de la máquina original en una base fija | Un experimento barato: cambiar **solo** los macros de `smwmac.h` | §4.2, tarjeta **L4** |
| Traducción 65816 → C (X1) | **JOTD**, `6502to68k.py` (pública); **LLMario**: SMB traducido a C por un LLM y verificado **instrucción a instrucción contra un intérprete independiente con estados aleatorios** | Estructura del traductor y, sobre todo, el método de verificación | §4.1, §4.3 |
| Caminos que el oráculo no recorre (P69) | JOTD, `asmcoverage.py`: instrumenta cada rama y vuelca un mapa de bits de cobertura | `gcov` sobre `marioverify` con todos los oráculos: lista exacta de ramas sin verificar | §4.4, tarjeta **V2** |
| vbcc compila mal (P38, P62) | La comunidad considera el gcc de bebbo el que mejor código da para el 68000; Bartman trae gcc 15 | Probar el C del port con gcc: velocidad y, de paso, un segundo compilador como red | §4.5, tarjeta **L5** |
| Asignar columnas de sprites (9.2) | **ACE** (motor en C, PR #292), **Saint Dragon**, multiplexores del C64 (orden de Ocean) | Encadenar por DMA vs recargar por copper, ordenar con inserción continua, parpadear antes que desaparecer | §5 |
| Medir es lento y frágil (P41, P75, P76, P82, P94) | **AmiGalaga**: FS-UAE con Lua, sin ventana, ~9× tiempo real **con cycle-exact**, varios a la vez; lee la RAM por símbolos y mide en líneas de raster | Reemplazar las capturas con bits en pantalla y las esperas en segundos | §6.1, tarjeta **V1** |
| Rutinas asm que destruyen registros (P53) | AmiGalaga, `asmlint`: compara la cabecera de cada rutina con lo que el código toca | Adaptarlo a nuestras cabeceras (§7 de `AGENTS.md`) | §6.4, tarjeta **V3** |
| Audio ≤ 3 % (D5) | **LSP** (Light Speed Player): flujo precalculado de escrituras a Paula, **0,83 líneas** de media por tick. Un driver portado (AmiGalaga) cuesta 5-19 líneas por frame | Confirma el plan "capturar el DSP y reproducir un flujo" | §7 |
| Carga (C3) | LZ4 68k (el más rápido), ZX0, Shrinkler (2,5 KB/s: demasiado lento) | LZ4 si hace falta comprimir | §8 |
| Cargas de color a mitad de línea (`build_mid`) | **png2amiga** ("DPF + strips"): 20 MOVEs por línea cada 16 px en DPF de 6 planos, **calibrados en una OCS real**; Coppershade: con 6 planos un MOVE tarda 16 ciclos dentro del fetch | Confirma nuestro modelo (~14 en el borrado + ~20 visibles). Contrastar su `$E1` en la línea 255 con P59 | §14.1, §14.5 |
| Presupuesto del blitter | *Cheat Sheet* de Photon: ciclos por combinación de canales, 25 % de la línea libre con 6 planos | B como constante es más barato; los blits caros, durante el HUD | §14.3 |
| Restaurar el fondo de los bobs | **Knightmare**: restaura desde la otra copia que ya está en el buffer de scroll, sin buffer limpio aparte | Idea para el bob en PF1 (D8) | §14.7 |

---

## 2. El frame entero

### 2.1 Lógica a 50 Hz fija y render desacoplado (Robocod)

Chris Sorrell (James Pond 2 / Robocod, A500, 50 fps de objetivo):

> "the game-play logic actually ran at 50fps via a timer interrupt while
> the main game loop received buffered render requests which it would
> fulfill as quickly as it could."

Y Ronald Pieket Weeserik (Silkworm), sobre qué sacrificar: "knowing what
the game needs, but also what it doesn't need ... what the players will
see, and what they won't notice".

**Cómo se traslada.** Hoy un frame es lógica → Mario → scroll; si el
total pasa de 20 ms, se pierde el frame entero (la lógica también se
atrasa). Con el esquema de Robocod:

- `level_frame` + `mspr_draw` corren en cada VBL, siempre (hoy ≈ 28 % +
  7 %, por debajo del 40 % objetivo): el juego **nunca va más lento** y el
  1:1 con el oráculo no cambia (la lógica es la misma por frame).
- El scroll (`build_mid` + lista) corre en el bucle principal sobre una
  **foto** de la cámara. Si no terminó antes del VBL, se sigue mostrando
  la lista anterior.
- **La trampa:** Mario y los sprites se dibujan con posiciones de pantalla
  que dependen de la cámara (P35). La foto tiene que ser coherente:
  la lista y los punteros de los sprites que se muestran juntos tienen que
  ser del mismo frame lógico. O sea, el render toma `(cámara, OAM)` del
  mismo frame y publica los dos a la vez con el cambio de `COP1LC`.
- El efecto visible: en los frames caros (los postes de la meta a la
  vuelta) la imagen salta 2 frames de cámara en vez de 1; la física no.
  Es exactamente lo que hacía Robocod.

Silkworm suma una regla para los sprites: cuando no entran, **parpadean**
(se alternan entre frames) en vez de desaparecer. Sirve para el 1,8 % de
frames de `d8demote` (AGENTS §9 punto 9).

Esto es una **opción más para el informe D1 (O4)**, no una decisión:
quedan (1) seguir optimizando, (2) 25 Hz, (3) recortar, y **(4) lógica a
50 fija + imagen desacoplada**. Se mide con O1 contando cuántos frames de
imagen se pierden en el replay y en los escenarios de estrés.

### 2.2 La cola de blits por interrupción no gana en una A500 de serie

ROADMAP §9.6 propone "columna nueva y bobs en una cola servida por la
interrupción del blitter". AmiGalaga lo midió (`experiment-7`, misma
escena con sonido y 25 000 ciclos de "lógica", en líneas de raster, peor
frame entre paréntesis):

| máquina, bobs | espera, `BLTPRI` on | cola, `BLTPRI` on | espera, off | cola, off |
|---|---|---|---|---|
| A500 de serie, 10 | 238 (269) | 267 (301) | 268 (305) | 230 (254) |
| A500 de serie, 20 | 301 (325) | 352 (379) | 340 (376) | 317 (625) |
| 1 MB fast, 10 | 214 (241) | 185 (208) | 222 (250) | 179 (207) |

Conclusión de ellos: sin fast RAM la cola no es una ganancia clara (una
interrupción por blit y nada corriendo en paralelo), y **los marcos de
interrupción tienen que estar fuera de chip**: la pila de supervisor en
chip espera al blitter en cada acceso. Nuestro slow RAM **no es fast**
(P29): cuelga del mismo bus, así que lo esperable es el resultado de la
A500 de serie. **Antes de implementar la cola, medirla** igual que ellos
(misma escena, las cuatro combinaciones). Para la columna nueva (un solo
blit grande, P31) la cola no aporta nada.

### 2.3 Bobs con un solo buffer: detrás del haz (Battle Squadron)

Martin Pedersen (Battle Squadron): los enemigos se "borran y reimprimen"
en posiciones fijas del haz (1/3 y 2/3 de la pantalla), sin doble buffer,
lo que deja "about 1.5 frames to delete/print the bobs" y ahorra mucha
CPU. Es la opción "detrás del haz" de ROADMAP §10.6 para el Banzai en PF1:
confirma que funciona en un juego real a 50 Hz y evita los +59 KB del
segundo buffer. Coste de su música: "5-10 % of the raster time".

Otro dato: en Stardust el jugador va a 50 fps y las animaciones de fondo
a 25 (Atari-Forum). Para nosotros, el equivalente serían las animaciones
de tiles (moneda de Yoshi, bloques `?`, P22/P23), que no son lógica.

---

## 3. El scroll con cargas de color (`build_mid`)

### 3.1 Nadie lo hizo así; los que más copper usan, lo precalculan

Revisados: Shadow of the Beast, Risky Woods, Brian the Lion, Jim Power,
Lionheart, Hybris, Silkworm, Agony, Turrican 2 (Codetapper, Lemon Amiga,
entrevistas). Lo que hacen con el copper a mitad de línea:

| juego | qué cambia a mitad de línea | por frame |
|---|---|---|
| Shadow of the Beast | `COLOR00` en h fijas (`$40` y `$C0`) | nada: la h no depende del scroll |
| Risky Woods | 32 escrituras de sprites por línea, 231 líneas: **27 KB de lista** | lista precalculada; por frame cambian los punteros (32 B) o el bit 0 de `SPRxCTL` para el píxel impar |
| Hybris | colores por línea (~100 en pantalla) | vertical, no depende del scroll horizontal |
| png2amiga + Scorpion Engine | cambios de paleta por línea con un **presupuesto de cambios por línea** ajustable | fijos por línea; "suits horizontal levels" |
| Lionheart | copper sobre el playfield delantero para más colores (600+ en pantalla, cambiando de modo según el nivel) | por línea; aviso de la comunidad: los colores de los objetos se rompen cuando se mueven en vertical |

**Ninguno** pone cargas de color en coordenadas del nivel que se mueven
con el scroll horizontal, que es lo que hace `build_mid`. La lección
común: **el trabajo por frame tiene que ser O(pocas palabras),
independiente del contenido**; todo lo que depende de la posición en el
nivel va precalculado. Eso apoya, en este orden:

- **S1c** (postes de la meta con 2 sprites adosados): es literalmente lo
  que hacen Risky Woods y Brian the Lion, pasar al hardware de sprites lo
  que el copper no puede. Los postes son el peor frame de la ida (P81).
- **S7** (menos cargas desde el origen): png2amiga expone el número de
  cambios por línea como **un parámetro de calidad**; nosotros podemos
  hacer lo mismo en `mkleveld.py` (un tope de cargas por línea con el
  menor error visible, medido como en `cmp_ref.py`). Es la única palanca
  que baja el coste en todos los frames a la vez.
- **S3/S5/S6** (segmentos compartidos, EDF, plan por sentido): todas van a
  hacer el coste independiente del contenido. P89 ya mostró que editar en
  el sitio no lo es.
- **S8** (el blitter copia segmentos precalculados): es lo que hacen las
  demos de "copper chunky": la lista está armada y la CPU (o el blitter)
  solo escribe los valores. No hay un truco mejor escondido ahí.

**Confirmado en EAB** ("Copper horizontal waits", t=108695, 2021;
leído de una copia descargada a mano):

- Master484: "I don't know any 8-way scrolling games that would use
  horizontal copper changes on the X-axis to get more colors to the
  background. Even the technically most impressive games only use
  vertical coppers". Lo llama "a coders nightmare".
- roondar da las mismas ranuras que midió `copbench.s` (AGENTS §9 punto
  8): un cambio de color cada 8 px con 4 planos, 12 con 5 y 16 con 6; el
  WAIT con resolución de 4 px. Y avisa del coste que nos frena: "writing
  the correct colour data into a dynamic Copperlist using the CPU is
  likely going to cost a fairly big chunk of raster time. It may even end
  up costing more CPU/Copper DMA to set it all up this way than using an
  additional bitplane."
- Cómo lo hacen los que tienen más colores que planos (Kid Chaos, Shadow
  of the Beast, ambos en DPF; Pang): **cambios de paleta solo verticales,
  según la posición en el nivel**, con el diseño de niveles a favor: los
  bobs nunca comparten línea con la pared de colores cambiados, y los
  enemigos que sí la comparten son **sprites** (no les afectan los cambios
  de PF1). Pang cambia solo colores del fondo, así los objetos van a
  cualquier lado. Nosotros no podemos rediseñar el nivel (1:1), pero es el
  **plan B probado** para el informe D1: bandas verticales de paleta que
  cambian con la x de la cámara (cambios en el borrado, sin cargas a
  mitad de línea), aceptando colores aproximados donde no alcance; el
  error se mide con `cmp_ref.py` como en `AGENTS.md` §9 punto 6.

El aviso de Lionheart vale para D9/P32: si los colores 17-31 se recargan
por línea para los sprites, un sprite que se mueve en vertical cambia de
banda de colores. `copsim.py` ya lo modela por línea; hay que mantenerlo
cuando la 9.2 recargue colores.

### 3.2 La línea 255 y el WAIT (P59): confirmado en el HRM

El HRM (capítulo del copper, "A Copper Loop Example") documenta la misma
trampa por otro lado: **el bit 7 de la posición vertical no se puede
enmascarar** y "the Copper only checks for greater than or equal to"; su
ejemplo parte la lista en dos bucles (antes y después de la línea 128) y
termina con una espera infinita en `VP >= 255`. Es coherente con P59.

### 3.3 Bucles del copper para líneas iguales: medido, descartado

La idea (HRM y demos de copper chunky): un segmento con WAIT solo
horizontal (máscara vertical a 0) vale para cualquier línea; con `SKIP`
+ `COPJMP2` el copper lo repite N líneas y la CPU lo escribe **una** vez.
Si los postes de la meta (un borde vertical) dieran muchas líneas iguales,
bajaría el peor frame.

Medido sobre `work/yi1_s.dat` (cargas visibles por frame, con la x
relativa a la cámara, registro, color y clase; más la paleta de PF2 de la
línea), todas las s pares:

| | líneas con cargas | segmentos distintos |
|---|---|---|
| media | 57,4 | 50,5 |
| s = 4580 (peor de la ida) | 107 | 104 |
| s = 2832 (peor de la vuelta) | 130 | 122 |
| s = 1825 | 88 | 81 |

Solo ~12 % de las líneas repiten la anterior: el dibujo cambia línea a
línea incluso en los postes. **No compensa** (y el bit V7 obliga a partir
los bucles en la línea 128). El script quedó fuera del repo; se rehace en
20 líneas con el `load()` de `tools/wip64/midsim5.py`. Ojo: `yi1_s.dat`
era del 2026-09-30, antes de SX; el contenido de las cargas no cambió con
SX (solo el plan), así que la conclusión vale.

---

## 4. La lógica: el 65816 en el 68000

### 4.1 JOTD: transcodificar línea a línea, y a qué velocidad llega

Jean-François Fabre (JOTD) porta juegos de arcade a la A500
transcodificando el código original **instrucción por instrucción** a asm
del 68000 (Donkey Kong, Galaga, Pengo, Moon Patrol, Xevious, Ms. Pac-Man,
Bagman...). Sus conversores están en `github.com/jotd666/amiga68ktools`
(`tools/`): `z80268k.py`, **`6502to68k.py`** y `6809to68k.py`.

Cómo es `6502to68k.py` (leído, 1618 líneas), que es lo más parecido al
65816 que hay:

- registros fijos: A → `d0`, X → `d1`, Y → `d2`, más uno para el acarreo;
- **cada acceso a memoria pasa por un macro** (`GET_ADDRESS`,
  `GET_ADDRESS_X`) que el port implementa con la base de su mapa; y una
  pasada final que junta `GET_ADDRESS` + la operación en un solo acceso
  `(a0)` para la página cero, "guaranteed to be mapped";
- el acarreo del 6502 en `CMP`/`SBC` es el **inverso** del 68000: el
  conversor inserta `INVERT_XC_FLAGS` donde hace falta y, si puede,
  invierte la rama (`bcs` ↔ `bcc`), que es más barato;
- donde no puede decidir, deja `ERROR "review ..."` en el código: el
  resultado no compila hasta que alguien lo mira. Él mismo lo resume:
  "there are still a lot of manual fixes to apply (stack usage, carry
  operations)".

Resultados de velocidad, de sus READMEs: Donkey Kong y Ms. Pac-Man a
**50 fps** en una A500; Galaga "25 fps on bare amigas" (50 con
aceleradora); Moon Patrol 25 fps en OCS, con gráficos simplificados y sin
el fondo azul. O sea: **código de arcade de 3 MHz traducido 1:1 ya está
al límite de la A500**. SMW es más pesado. Confirma lo que hacemos: C de
referencia + asm a mano solo en lo que marca el perfil, y no un traductor
que lo haga todo.

Para **X1** (`tools/x65c.py`): copiar la estructura (macro de acceso a
memoria por modo de direccionamiento, marcas `review` donde el traductor
duda, pasada de optimización final) y emitir C en vez de asm. El 65816
agrega los modos M/X (8/16 bits), que hay que seguir por flujo como el
acarreo.

### 4.2 `R16` byte a byte: el truco de los emuladores (memoria "swizzled")

Hoy `smwmac.h` arma cada valor de 16 bits con 2 lecturas + `lsl` + `or`
(~50 ciclos contra 12 de un `move.w`, ROADMAP §9.7). Los emuladores que
corren una máquina de un endian en un host del otro (Mega Drive, 32X,
Saturn en PC; N64 con `^3`) guardan la memoria **con los bytes de cada
palabra intercambiados**: el byte de la dirección `a` vive en `a ^ 1`. Así
una palabra de la máquina original en una dirección **par** se lee con una
sola lectura nativa. Variante: la memoria entera **al revés**
(`mem[N - tamaño - a]`), que además sirve para 24 y 32 bits (los punteros
largos de SMW).

En el 68000 (big endian) sobre WRAM de la SNES (little endian):

| acceso | hoy | con XOR 1 |
|---|---|---|
| `R16(const)`, dirección par | 2 lecturas + `lsl` + `or` | `move.w` (la dirección se pliega en compilación) |
| `R16(const)`, dirección impar | ídem | ídem que hoy (el 68000 no lee palabras impares) |
| `R8(const)` | `move.b` | `move.b` (`const ^ 1` se pliega) |
| `RX8(tabla, x)` (tablas de sprites) | `move.b (a,x)` | hay que calcular `(tabla + x) ^ 1`: +1 `eor` por acceso, o recorrer las tablas con el índice ya permutado |

Lo atractivo: **el cambio está en un solo fichero** (los macros), el
verificador dice si algo se rompió, y abcheck dice si ganó. Lo que hay que
tocar además: el asm que indexa `_ram` directamente (`logic68k.s`,
`mario_E2BD`, `mspr68k.s`), los arneses que comparan con el oráculo
(desintercambiar al comparar) y cualquier `memcpy` sobre `ram[]`.

**Antes de hacer nada, medir** si gana: con un registro de snesorc,
contar los accesos de 16 bits por paridad de dirección y los accesos a
tablas indexadas de 8 bits. Si la mayoría de los de 16 bits caen en
direcciones pares (las variables de Mario `$94`, `$96`, `$7B`... lo son),
es la versión barata de la L3 ("estado nativo"), que ROADMAP estimaba en
5-8 % y "toca todo el C". Tarjeta **L4**.

**Medido el 2026-10-03: no conviene.** Contando cada acceso en los 6836
frames del modo `game` (copia instrumentada del C, `__builtin_constant_p`
para saber si la dirección es constante), por frame: 29 `R16` y 34 `W16`
en dirección constante par (los que ganarían ~30-38 ciclos), 274 `R8`/`W8`
constantes (igual que hoy), 90 `RX8` (+8-12 ciclos cada uno con el XOR) y
casi ningún acceso de 16 bits con dirección variable. Neto estimado: +1 350
ciclos de media (0,95 % del frame), +0,5-0,7 % en los frames con más
accesos, y **−2,7 %** en el peor (637 accesos de 8 bits con dirección
variable). Con ~110 sitios del asm, los arneses y los punteros a `ram[]`
por tocar, no se implementa.

### 4.3 Verificar una traducción: LLMario

`github.com/Wynplusplus/LLMario`: Super Mario Bros. traducido del 6502 a
C (10 320 funciones) **por un LLM**, y verificado con un **intérprete de
6502 independiente**: los dos parten del mismo estado (registros y 64 KB
de memoria **aleatorios**), avanzan instrucción a instrucción y se
comparan registros y memoria completa después de cada paso: "10,910
trials / 78,629 steps / 0 state mismatches". Una segunda sesión encontró 5
puntos de entrada que faltaban.

Para X1 y para los sprites que faltan: además de las partidas grabadas
(que solo recorren lo que se jugó, P69), probar cada rutina traducida
contra snesorc **desde estados aleatorios o mutados de los reales**. Es
lo que cubre los caminos que ningún oráculo pisa.

### 4.4 Cobertura: saber qué no está verificado (P69)

JOTD tiene `asmcoverage.py`: instrumenta cada rama del asm con un macro
que pone un bit en un mapa, y después se lee qué ramas nunca corrieron.
En nuestro caso es más fácil todavía, porque el C corre en el PC:
compilar `marioverify` con `gcc --coverage`, correr **todos** los
oráculos (`oracle_yi1` y los de snesorc) y mirar con `gcov` qué ramas de
`player/*.c` no se ejecutaron nunca. Eso convierte P69 ("lo que el
oráculo no recorre puede estar mal aunque todo dé 100 %") en una **lista
de trabajo**: cada rama sin cubrir pide un guion de snesorc o una prueba
aleatoria (§4.3). Tarjeta **V2**.

### 4.5 El compilador

vbcc compiló mal dos veces (P38, P62) y emite direcciones absolutas sin
avisar (P47). Lo que dice la comunidad
(bebbo, EAB, el benchmark de weblambdazero): el gcc 6 de bebbo para
AmigaOS "very likely generates the best code quality for the 68k of any
Amiga compiler ever"; vbcc compila rápido y da binarios chicos. La
extensión de Bartman (`vscode-amiga-debug`) trae gcc 15.

Propuesta (tarjeta **L5**): compilar el C del port con m68k-amigaos-gcc
`-O2 -m68000 -fomit-frame-pointer` y pasar `m68kverify` (semántica) y
Musashi (ciclos) contra el binario de vbcc. Si gcc gana, también da un
segundo compilador independiente: un fallo que aparece solo en uno de los
dos binarios es un fallo del compilador. Lo que hay que resolver: el
modelo de datos pequeños (P36, `a4`), las direcciones absolutas (P47) y
que `logicbench_build.sh` parte la salida de vbcc en datos y código.

---

## 5. Los sprites del nivel (9.2)

### 5.1 Encadenar por DMA o recargar por copper (ACE)

ACE (motor en C para OCS, `github.com/AmigaPorts/ACE`) discutió las dos
formas en el PR #292 ("Multiplexed sprites"):

- **encadenar por DMA**: las palabras de control del siguiente objeto van
  en el mismo flujo, ordenado por Y; "no copper work per element".
  Necesita **una línea libre** entre dos objetos del mismo canal. Dos
  buffers de DMA que siguen a los dos buffers del copper, y solo se
  copian los píxeles que cambiaron. Medido en una A500 PAL emulada: 93 %
  (shooter horizontal) y 75 % (vertical) de CPU en el pico, a 50 Hz;
- **recargar los registros con el copper**: "more flexible but costs
  copper and CPU time".

ROADMAP §10.6 eligió la segunda (un `SPRxPT` nuevo por copper, sin copiar
datos). El dato a favor de la primera: **nuestro copper es el recurso
escaso** (las 1916 cargas que no entran de `copsim.py` son todas de la
capa 1), y cada `SPRxPT` son 2 MOVE en líneas que ya están llenas. Con
frames precalculados por pose (9.5), "encadenar" se reduce a copiar ~270
B por objeto (o menos, si solo cambian los punteros de pose). **Medir las
dos** en las líneas más cargadas antes de elegir.

Saint Dragon usa la misma idea al extremo: "4 sprites are re-used to
create upwards of 20 player bullets by interleaving sprite control words"
(Codetapper).

### 5.2 Ordenar por Y: la ordenación de Ocean

Los multiplexores del C64 (Cadaver, codebase64) compararon burbuja,
"buscar el menor", cubetas Y/8 (rápido pero incorrecto), radix, y la
**inserción continua** ("Ocean sort"): un array de orden que **no se
reinicia** entre frames, así cada orden es la continuación del anterior.
Es la recomendada: casi O(n) porque los objetos se mueven poco entre
frames. Coincide con lo que ROADMAP §9.5 ya intuía ("inserción: casi
ordenados de un frame al siguiente"). Su regla de rechazo (comparar la Y
del nuevo con la del último del mismo canal físico) es la que hay que
aplicar para "una línea libre entre dos objetos".

### 5.3 Elegir qué va a sprite cada frame

Robocod: "the system would consider all the objects wanting to display
each frame, and would pick some of them to display using sprites", con
bandas fijas arriba y abajo y multiplexado en el medio. Es lo mismo que
el diseño (d) con `d8demote` (pasar un objeto a bob). Y Silkworm: si no
entran, parpadeo (§2.1).

---

## 6. Medir mejor

### 6.1 FS-UAE con Lua (AmiGalaga)

AmiGalaga (`github.com/mwulffn/AmiGalaga`, Galaga para A500 de serie,
también hecho con Claude Code: tiene `CLAUDE.md`) usa un fork de FS-UAE
con Lua (`github.com/mwulffn/fs-uae`) que:

- corre **sin ventana y a ~9× el tiempo real con cycle-exact encendido**
  ("that does not change what the Amiga does: a timing report comes out
  the same as at normal speed"), y varios a la vez (cada uno con su
  directorio y su puerto);
- desde Python: `mem.peek_u16`, `mem.read_range`, `mem.tap_write` /
  `tap_read` (vigilar escrituras o lecturas a una dirección),
  `dbg.bpset`, `dbg.exset` (excepciones = cuelgue, con registros),
  `dbg.load_symbols` (leer el estado por nombre), `emu.wait_frames`,
  `emu.cycles`, capturas, y meter joystick y teclado;
- mide **en líneas de raster por frame** directamente, sin escribir bits
  en pantalla;
- fija el commit del emulador y comprobó sus informes contra el FS-UAE
  publicado (sonido y lógica idénticos byte a byte; el tiempo, ±10-30
  líneas en medio millón).

Para nosotros reemplazaría el ciclo "ensamblar → ADF → WinUAE → esperar N
segundos → captura → decodificar bits" (`bench_read.py`,
`game_read.py`, `logicbench_read.py`) y las trampas P41, P75, P76, P82(4)
y P94. Y permite lo que hoy no podemos: **jugar el ADF real desde un
guion** y leer `ram[]` de la Amiga para cruzarla con el oráculo
(lo que hoy hace Musashi, pero con DMA). Riesgo: compilarlo (es un fork
de FS-UAE; en cloud es Linux, en la PC hace falta msys2) y validarlo
contra WinUAE con `bench2.s`, como se hizo con FS-UAE en 2026-09-24.
Tarjeta **V1**.

### 6.2 Perfilar con DMA

- **Bartman, `vscode-amiga-debug`**: perfilador por función **con los
  ciclos de DMA por línea** (blitter, planos, sprites, posición del haz)
  y una captura por frame, en A500 PAL. Está pensado para binarios de su
  gcc; con nuestro binario de vasm habría que darle los símbolos. Lo que
  más nos interesa es lo que Musashi no tiene: dónde se van los ciclos
  **con** la contención (la regla ×1,3 de §9).
- **JOTD, `profiler.s` + `profiler.py`**: perfilador por muestreo, mínimo:
  una interrupción (VBL o timer de CIA) guarda el PC interrumpido en un
  buffer; después se agrupan las direcciones. Se pega a `game.s` en una
  tarde y corre en cycle-exact (con el DMA). Complementa a `m68kprof.py`.

### 6.3 Calibrar el copper sin capturas

El depurador de WinUAE tiene un **depurador visual de DMA** (ciclo a ciclo
por línea: copper, planos, blitter, CPU; las esperas del copper con color
propio). Los modelos de P42, P46 y lo **sin medir** de P51 (el copper
después de `DDFSTOP`) se pueden leer ahí directamente en vez de con
`copcal.s` + captura + decodificación.

### 6.4 `asmlint` (AmiGalaga)

Lee el asm de vasm y comprueba que la cabecera de cada rutina (`In`,
`Out`, `Clobbers`) dice la verdad: un registro que la rutina cambia y no
declara es un error, y hereda los de las rutinas que llama. Es el bug de
P53 (`mspr_draw` destruía `d2`). Nuestras cabeceras (§7 de `AGENTS.md`,
"registros destruidos") tienen otro formato; adaptarlo es poco trabajo y
se engancha a `lint_port.py`. Tarjeta **V3**.

AmiGalaga encontró además que `clr` sobre un registro del chipset de solo
escritura **lee antes de escribir** en el 68000 (escribe basura un
instante). Revisado en `player/*.s`: no hay ningún `clr` sobre `CUSTOM`.

---

## 7. Audio (D5)

| reproductor | coste en una A500 PAL |
|---|---|
| **LSP** (Arnaud Carré): flujo precalculado de escrituras a Paula | **0,83 líneas** de media por tick, 2,27 de pico (modo normal); 0,46 en "insane" |
| driver de Galaga portado a Paula (AmiGalaga), a 121 Hz | 890-3500 ciclos por tick = **5-19 líneas por frame** |
| música de Battle Squadron | "5-10 % of the raster time" |

LSP es exactamente la arquitectura que eligió D5 tras reassembler:
"capturar lo que el driver le escribe al chip y reproducir un flujo". La
diferencia de coste con portar el driver es de un orden de magnitud. Con
LSP como referencia, el ≤ 3 % de D5 tiene margen: nuestro flujo (3 voces +
efectos, envolventes por tick) debería quedar en 1-2 líneas. El formato
y el reproductor de LSP (fuente abierta, `github.com/arnaud-carre/LSPlayer`,
con el modo CIA para tempo variable) son un buen punto de partida para
A3/A4, aunque el conversor de LSP lea MOD y el nuestro el registro del
DSP.

---

## 8. Carga y compresión (C3)

| compresor | descompresión en 68000 |
|---|---|
| LZ4 (`arnaud-carre/lz4-68k`, versión "fastest", 3,7 KB de código) | el más rápido; 4,45× UPX, 6,81× ARJ (medido en Atari ST) |
| ZX0 | decompresor de 80 bytes; un 64 KB en ~5 s |
| Shrinkler | ~350 ciclos por bit comprimido: **~2,5 KB/s** en A500 |

Si C3 hace falta (hoy el ADF va por el 46 %), LZ4: la lectura del
disco ya es lenta (~15-20 s estimados para 412 KB) y no conviene sumarle
un descompresor lento. Shrinkler solo para algo chico.

---

## 9. Tarjetas propuestas

Formato de `SUBAGENTES.md` (nivel · depende de · ficheros). Ninguna toca
la semántica sin pasar por `regress.py`.

| tarjeta | nivel | qué | hecho cuando |
|---|---|---|---|
| **O5** | M · O1 | Prototipo del render desacoplado (§2.1): `level_frame` en el VBL, scroll sobre una foto `(cámara, OAM)` del mismo frame; contar frames de imagen perdidos en el replay y en los `stress_*` | Número de frames perdidos y su distribución, para el informe D1 (O4) |
| **V1** | F · — | FS-UAE con Lua en cloud: arnés Python como `amiga.py`, medir `game.s -DBENCH` en líneas por frame y leer `ram[]` por símbolo | Mismos números que `game_read.py --auto` sobre la misma build (±1 %) y `bench2.s` como en 2026-09-24 |
| **V2** | B · — | `gcov` de `player/*.c` corriendo todos los oráculos en `marioverify` | `docs/cobertura.md` con las ramas sin cubrir, por fichero, y cuáles importan para YI1 — **hecha 2026-10-03** (`tools/coverage.py`) |
| **V3** | B · — | `asmlint` adaptado a las cabeceras de §7, en `lint_port.py` | Pasa sobre `player/*.s`; lo que encuentre, arreglado o anotado — **hecha 2026-10-03** (`tools/asmlint_port.py`) |
| **L4** | M · — | Medir con snesorc la paridad de los accesos de 16 bits y el peso de las tablas indexadas; si da, prototipo de `ram[]` con XOR 1 en `smwmac.h` | `abcheck.py` IGUAL y ciclos de `level_frame` (media y peor) contra la base — **medida y descartada 2026-10-03** (§4.2) |
| **L5** | M · — | El C del port con gcc moderno, `-m68000 -mshort -O2` (AmigaPorts, el de Bartman, o el gcc 15 de PeyloW; §13.3) | `m68kverify` igual que con vbcc; tabla de ciclos por función contra vbcc |
| **X0** | M · — | Antes de X1: generar en local el C de SMW con snesrecomp (§13.1) y medir cuánto sirve como borrador en un sprite ya portado | Informe: qué fracción de Rex o Chuck sale bien pasándolo a nuestros macros |
| **G0** | M · 9.5 | Medir encadenar por DMA vs `SPRxPT` por copper (§5.1) en las líneas más cargadas de `copsim.py` | Decisión con números para G1-G2 |
| **E2** | B · — | Antes de la cola de blits de §9.6, repetir el `experiment-7` de AmiGalaga con nuestra columna y un bob | Tabla con las cuatro combinaciones |

Para X1, sumar a su descripción: la estructura de `6502to68k.py` (§4.1)
y la verificación desde estados aleatorios de LLMario (§4.3).

---

## 10. Lo que se buscó y no sirvió

- **Bucles del copper** para líneas repetidas: medido, ~12 % (§3.3).
- **Un port de SNES a la A500 que corra la lógica original**: no
  encontrado. El único port comercial de consola a Amiga con entrevista
  técnica (El Rey León, Dave Semmens) **reescribió todo**: del código de
  la Mega Drive "I only used one table". Sonic de reassembler
  (Mega Drive → Amiga, mismo CPU) apunta a A1200 primero; la versión A500
  queda para después con "a smaller palette".
- **Super Mario Bros. en el C64** (ZeroPaige): código del NES con la E/S
  reescrita, el mismo enfoque que el nuestro; sin documentación técnica
  publicada de cómo resolvió el tiempo de CPU.
- **EAB**: inaccesible para las herramientas (anti-bots); los hilos se
  bajan a mano desde el navegador (vista de impresión,
  `printthread.php?t=N&pp=40&page=P`). Leído: "Copper horizontal waits"
  (t=108695, §3.1) y "Best way to mix blitting with copper and copper
  effects" (t=84048, 2016, 4 mensajes). En este, roondar plantea lanzar
  los blits desde el copper (WAIT con espera de blitter + `SKIP` para no
  atrasar un efecto que tiene que caer en una posición exacta). Lazycow
  le contesta que no se puede tener a la vez lo más rápido y lo más
  flexible, y que "the biggest potential for optimisations is located at
  the higher levels of the algorithm"; roondar abandona la idea. Para
  nosotros: blits lanzados por el copper **no** entran en S8 (la lista ya
  tiene sus ranuras contadas, P39) y el consejo coincide con el resto de
  este informe (O5, S7, S1c antes que ciclos). El fragmento sobre
  "trampolines" (cambiar de lista con una escritura atómica a `COP1LCL`)
  que mostró el buscador **no está en este hilo**: es de otro, sin
  identificar. "Arcade / Console --> Amiga conversion discussions"
  (t=87502): leído **entero** (30 páginas, 588 mensajes, jun 2017 - sep
  2018), resumen en §11. Es anterior a las transcodificaciones de JOTD
  (2020 en adelante), que no aparecen ahí. Leídos también t=98219,
  t=69491, t=105582, t=113136, t=81866 y t=105358 (§12; la vista de
  impresión da siempre 20 mensajes por página, aunque se pida `pp=40`).
  Pendiente: el hilo de EAB donde JOTD cuenta sus transcodificaciones, si
  existe.

---

## 11. EAB, "Arcade / Console --> Amiga conversion discussions" (2017-2018)

587 mensajes, casi todos sobre CPS1, Ghouls'n'Ghosts, Strider y OutRun, y
mucha discusión Amiga contra ST. Lo que nos sirve (filtrado por temas
técnicos: 103 mensajes):

- **El coste de los planos para la CPU, con números** (roondar): durante
  el DMA de planos la CPU va al 100 % con hasta 4 planos en lowres, al
  **75 % con 5 y al 50 % con 6**; fuera de las líneas visibles, al 100 %.
  "A 5 BPL 320x256 scrolling screen has the CPU running ... roughly 80%
  overall". Nuestro DPF es de 6 planos: en las 224 líneas visibles la CPU
  rinde la mitad. Es la regla ×1,3-1,4 de ROADMAP §9 vista desde el
  hardware, y refuerza §9.6: lo que sea trabajo de bus va en las 88
  líneas sin planos. ReadOnlyCat agrega que las instrucciones largas sin
  acceso al bus (`mulu`, `divu`, desplazamientos largos) siguen corriendo
  aunque el DMA tenga el bus: en la parte visible conviene el código que
  calcula, y fuera de ella el que copia.
- roondar, sobre lo que le piden a los ports: "people expect ... 50Hz
  updates, 32 colour graphics + sprite layer background + extra copper
  effects + great sound and running in 512KB". Los ports de 32 colores
  pierden mucho rendimiento en OCS por la contención; la "mejor relación"
  según varios (zero, DanScott) es lowres de 16 colores + sprites. Es el
  trade-off que D8/D1 ya eligió al revés (fidelidad primero), y explica
  por qué casi ningún juego comercial hizo lo que hacemos.
- **Cada blit cuesta ~100 ciclos de CPU** de preparación con
  interrupción (roondar), y consultar el estado del blitter es un acceso
  al bus de chip (frank_b). Coincide con P31 (~42 µs por blit medidos).
- **Listas del copper que lanzan los blits** ("Copper driven Blitter
  lists", ReadOnlyCat): "by far the most efficient way to sequence a large
  number of blits", pero "hard to mix ... with color gradients, sprite
  updates". Nuestro copper ya está lleno (P39): descartado, como en
  t=84048.
- **La CPU arma la lista del copper y copia solo la diferencia** (roondar,
  pensado para fast RAM): es la idea de S3. Con slow RAM (P29) no hay
  paralelismo de bus, así que lo que cuenta es escribir menos, no dónde.
- **Cambiar RAM por CPU** (zero): precalcular movimientos y usar tablas
  en todo lo posible. Ya es nuestra regla (ROADMAP §9.7, `T8X`/`T16X`).
- **Colisiones con una lista ordenada** (DanScott, varios juegos
  comerciales): "a sorted list will not change a great deal from one
  frame to the next". Para L2 (`spr_spr_interact` es O(n²)): mantener los
  sprites ordenados por x de un frame al siguiente (inserción continua,
  §5.2) y comparar solo vecinos dentro de la caja más ancha. Ojo: tiene
  que dar los mismos resultados y en el mismo orden que el ROM.
- **60 Hz en una A500 PAL** (ReadOnlyCat, especulativo, "I have not
  tested that"): forzar el VBL antes con `VPOSW` para tener un frame de
  ~262 líneas. Sería otra salida para D15 (la velocidad del 83 %), pero
  cada frame tendría ~16 % menos de ciclos, justo lo que nos falta, y
  con 224 líneas visibles el margen de borrado vertical se achica. No
  conviene ahora; se anota.
- Leander (GameHut, ex Traveller's Tales): DPF + sprites + copper para
  que los sprites sirvan también para el marcador, con detección de
  colisión por hardware. Para el HUD (D11) es otra referencia de barra con
  sprites; DanScott avisa que la colisión por hardware "only tells you
  there has been a collision", así que no sirve para la lógica 1:1.
- Shatterhand comenta una rutina de scroll de tilemap "great for games
  like Super Mario Bros where you only scroll forward" (rápida, poca
  memoria); sin detalles. YI1 scrollea en los dos sentidos.

---

## 12. EAB, hilos cortos sobre el copper y el 68000

### 12.1 "Combining copper scrolling with copper background" (t=69491) — el más útil

phx (2013) scrollea un mapa grande y quiere un color de fondo distinto
por línea: reescribir la lista entera cada frame le cuesta **~48 líneas
de raster**. Las respuestas:

- **Toni Wilen (el autor de WinUAE): una lista grande precalculada, con
  un par WAIT + MOVE por cada línea del nivel**, donde el WAIT espera
  solo el final de la línea (sin mirar la vertical). La lista normal
  espera la primera línea visible y **salta** (`COPJMP`) a la lista grande
  en la línea que corresponde a la cámara. Para el corte (puntero de
  planos), se reemplaza un MOVE de color por una escritura a `COPJMPx` y
  después se vuelve. "Now you only need to change COPJMP pointer and 2
  words ... when you need to change vertical position ... it is still
  faster and more optimal than rewriting whole copperlist with CPU."
- **DanScott (Chuck Rock 2, Wonderdog, juegos comerciales de A500): el
  blitter copia la lista del copper.** Una tabla con el número
  acumulado de instrucciones del copper hasta cada línea; para insertar
  algo en la línea X, blitea la parte de antes, inserta, blitea el resto:
  "It took hardly any time in total. This also allowed for any (variable)
  number of other copper instructions per line".
- earok (Scorpion Engine): con `COPJMP` a una lista secundaria bajó de 17
  a 5 operaciones del copper por línea.
- phx termina reconociendo que cambiar el color en cada línea "was
  stupid": cada 10 líneas ya se veía bien. Otra vez la palanca de S7.

**Para nosotros:**

1. **La cámara vertical (ROADMAP §10.2b, S8)** es exactamente el caso
   de Toni Wilen: los segmentos ya son por línea; si quedan indexados por
   línea **del nivel** y encadenados, mover la cámara en vertical es
   cambiar el punto de entrada (`COP2LC`) y el de salida (un salto
   parcheado en la última línea visible), dos o tres palabras, en vez de
   las "224 × 2 palabras, ~3 000 ciclos" que estimaba §10.2b. Requisito:
   los WAIT de cada segmento tienen que ser **relativos a la línea** (solo
   h, máscara vertical a 0), con la salvedad del bit V7 (§3.2): dos
   variantes del WAIT según la línea de pantalla sea < 128 o ≥ 128, o un
   salto que cambie de cadena en la línea 128. Hay que medir si el
   borrado (2 WAIT + 14 MOVE) entra con WAIT solo horizontal, con
   `copcal.s`.
2. **S8 tiene precedente comercial:** DanScott blitea la lista del copper
   en Chuck Rock 2. Para nosotros, la parte fija de cada segmento
   (borrado, cargas que no cambian) se podría copiar con el blitter desde
   segmentos precalculados mientras la CPU corre la lógica, y la CPU solo
   parchea las h. Sigue pendiente de S3-S5, como decía §9.2, pero ya no es
   una idea sin probar.

### 12.2 "Multiple copper waits beyond 255" (t=98219): confirma P59

- Después de `$FFDF,$FFFE` **no hace falta** un segundo `$FFDF` ("the
  second wait actually breaks things", porque nunca vuelve a ocurrir en el
  frame). Es lo que encontramos en P59.
- ross: con muchos planos (`DDFSTOP` = `$D8`) la ranura de `$E1` se la
  roba el DMA de planos y **`WAIT $FFE1` no termina nunca**: por eso
  todo el mundo usa `$xxDF` como última posición. Nuestro fallo de la línea
  255 (esperábamos en `$E2`) es esto mismo.
- Para que un cambio de color no se vea en el borde derecho de la línea
  anterior, la h del WAIT tiene que ser ≥ `$07` (`$05` todavía se ve en
  algunos monitores). Referencia que todos citan: el artículo de Photon
  en Coppershade sobre los tiempos del WAIT. Para revisar en `scroll.s`:
  qué h usa el primer WAIT de cada segmento.

### 12.3 "Copper SKIP/WAIT timing" (t=105582)

El copper tiene **113 ranuras por línea** en PAL (en NTSC las líneas
alternan de largo, en PAL no); "55 CMOVE + 1 CWAIT per line" si no hay
ranuras robadas. Los tiempos del HRM para WAIT y SKIP son correctos.
Photon escribió en Coppershade los tiempos de MOVE y WAIT.

### 12.4 "optimisations for 68000" (t=113136)

- jotd: `MULU` es más lento que una tabla; usa un macro que genera la
  tabla (`rept 256 / dc.w REPTN*n`). Es nuestra regla (ROADMAP §9.7).
- **roondar, el matiz**: la tabla gana en ciclos de CPU pero **hace más
  accesos a memoria** que el `MULU` (que corre sin tocar el bus). Cuando
  el bus está ocupado (blitter trabajando, o planos), "it ends up taking
  almost the same amount of actual elapsed frame time to just use the
  MULU instead of the table". En nuestras líneas visibles con 6 planos la
  CPU tiene la mitad del bus (§11): en lo que corre ahí, un `mulu` puede
  costar lo mismo que la tabla. Medir antes de cambiar uno por otro.
- `MOVEM` gana a partir de 3 registros (2 da igual); `movem.w` extiende
  el signo a 32 bits.
- Herramientas: **68kcounter** (`68kcounter.grahambates.com`, contador de
  ciclos en línea) y el comando `fi` del depurador de WinUAE, que da los
  ciclos de chip y de CPU entre dos puntos con la posición del haz.
- El consenso, otra vez: "99% of the time it is better to improve the high
  level program structure than do micro-optimizations".

### 12.5 "Sprite multiplexing on Amiga" (t=81866): la recarga por copper funciona

Es la pregunta abierta de §5.1 (G0: encadenar por DMA o recargar
`SPRxPT` por copper). Lo que confirma el hilo:

- Leffmann: "You change the sprite pointers during the display to chain
  together different sprites structures in memory ... wait until the last
  line of the sprite and hpos 20 or something, and change the pointer to a
  new pair of control words and sprite data ... this way you can at least
  avoid the overhead of copying sprite data around in memory."
- Toni Wilen: se puede escribir `SPRxPOS` **en cualquier momento** para
  rearmar un sprite que ya terminó en modo DMA, siempre que la nueva
  posición vertical sea igual o mayor que la actual. La línea en la que el
  DMA de sprites carga siempre las palabras de control es la **25 en PAL**
  (20 en NTSC): las escrituras a mano, después de esa línea. Superfrog y
  Project-X lo usan.
- DanScott lo probó y "everything works as was anticipated"; lo usa para
  sprites grandes animados multiplexados en vertical, "as I just don't want
  to be building huge sprite DMA lists".
- El orden por Y "nearly sorted" se reordena rápido sin un orden completo,
  y si no hay canal libre, **parpadeo a 50 Hz** alternando qué objeto se
  queda afuera: "better than totally not showing it" (DanScott, otra vez
  la regla de Silkworm, §2.1).
- Recorte vertical de un sprite alto: escribir una palabra de control
  dentro de los datos en la línea de corte y restaurarla el frame
  siguiente.
- Toni Wilen: si un canal de DMA (sprites incluidos) no necesita su ranura
  en una línea, aunque esté habilitado, la ranura la puede usar el resto,
  la CPU incluida. Los sprites que no se ven no cuestan bus.

**Para nosotros:** la elección de ROADMAP §10.6 (un `SPRxPT` nuevo por
copper, sin copiar datos) tiene respaldo en hardware real y en juegos
comerciales. El coste en el copper es 1-2 MOVE por recarga (`SPRxPTL`, y
`SPRxPTH` si cambia el banco de 64 KB); si los frames de las poses quedan
todos en un mismo banco, es **un** MOVE. G0 se reduce a medir si ese MOVE
entra en las líneas más cargadas de `copsim.py`; el encadenado por DMA de
ACE queda como plan B para esas líneas.

### 12.6 "Copper driven blitter waits in WinUAE" (t=105358): cambiar de lista sin riesgo

El hilo empieza como un fallo de blits lanzados por el copper y termina
con Toni Wilen explicando, con analizador lógico, un fallo del OCS/ECS
(con un solo WAIT de blitter y sin `BLTPRI`, el puntero D del blit
siguiente puede quedar mal; hacen falta dos WAIT). Nosotros no lanzamos
blits desde el copper, así que eso no nos toca. Lo que sí:

- **Arrancar el copper:** el copper "recuerda" que pasó el VBL aunque su
  DMA esté apagado, y al encenderlo ejecuta `COP1LC` **al instante**, en
  la línea que sea. Lo mismo el blitter: escribir `BLTSIZE` con el DMA
  apagado lo deja armado y arranca al encender el DMA. Regla: esperar la
  línea 0 antes de encender el DMA (si el primer frame sale corto, las
  listas A y B quedan invertidas: le pasó a Jobbo). **Revisado en
  `game.s` (2026-10-03):** enciende el DMA justo después de dos `WaitTOF`
  con `COPJMP1`, y el bucle por frame trabaja desde la línea `$110`, con
  la pantalla ya dibujada, y escribe `COP1LC` desde la CPU: un frame que
  se pasa solo atrasa el cambio de lista, no escribe sobre la lista que
  se está mostrando. No hace falta cambiar nada.
- **Cambiar de lista cuando la CPU no llega** (pink^abyss, Tiny Bobble):
  cada lista empieza poniendo `COP1LC` en una lista "neutra" que solo
  muestra la pantalla; la CPU es la que escribe `COP1LC` con la lista
  nueva, en su bucle de fin de frame. "If the cpu was too slow this frame
  then nothing bad happend, because the CPU does handle the switching."
  Es justo el mecanismo que pide **O5** (§2.1): si el scroll no terminó,
  se sigue mostrando la lista anterior sin que nada se rompa. `game.s` ya
  cambia la lista así (ver arriba); para O5 falta que la lógica no espere
  al scroll.
- Photon: una lista "cabecera" con un WAIT de posición, que la escribe
  el VBI y salta (`COP2`) a la lista preparada, o directamente que el VBI
  escriba los registros. Separa el cambio de escena del trabajo del
  copper.

---

## 13. Del 65816 a C y del C al 68000, fuera de la Amiga (2026-10-03)

### 13.1 snesrecomp: el 65816 de SMW ya traducido a C

`github.com/RetroPortingToolKit/snesrecomp` es un recompilador estático
genérico de SNES, de la misma comunidad que `smwrecomp` (el que grabó
`oracle_yi1`). Traduce el 65816 a C **por funciones**, con un analizador
que hace justo lo difícil de X1:

- descubre el código y sigue el flujo de control;
- **sigue el estado M/X** (8 o 16 bits) instrucción por instrucción
  (`recompiler/v2/widths.py`, `exit_mx_autoroute.py`);
- resuelve saltos indirectos y tablas de punteros (`pointer_recovery.py`)
  y, lo que no puede resolver, lo deja a un intérprete en vez de un
  agujero;
- verifica con co-simulación contra un emulador independiente (bsnes,
  Snes9x) hasta la **primera divergencia**, con hashes del estado
  completo (`SNES_COSIM.md`): el mismo método que `marioverify`;
- graba cobertura (`docs/COVERAGE_FEEDBACK.md`, `ram_coverage.py`): qué
  se ejecutó de verdad, para saber qué falta verificar (V2, P69).

**Super Mario World está soportado** ("believed playable end to end"). El
C que genera **no sirve tal cual en el 68000**: cada acceso es
`cpu_read16(cpu, banco, dir)` sobre un modelo genérico del bus (es
código para PC). Pero para X1 hay dos usos:

1. **Borrador:** generar en local, desde la ROM del usuario, el C de las
   rutinas de los sprites que faltan (bolas de fuego, monedas, reserva,
   capa, `pw_3up`...) y pasarlo a nuestros macros (`R8`, `R16`, `RX8`,
   `T8X`) a mano o con un script. Ya trae resueltos los anchos M/X y los
   saltos por tabla, que es donde se equivoca un traductor hecho de cero.
2. **Usar su analizador y escribir nuestro emisor:** las funciones, los
   anchos por instrucción y los destinos de los saltos salen de su
   análisis; el emisor escribe C con nuestros macros y nuestros nombres
   de `smwram.h`. Más trabajo, pero el resultado ya es "C del port".

Licencia PolyForm Noncommercial 1.0.0: sirve para un proyecto personal.
El C generado es derivado de la ROM: como `player/gen/smwrom00.c`, se
genera en local y **no entra en git** (R9). Esto cambia la tarjeta X1:
antes de escribir `tools/x65c.py` desde cero, probar `snesrecomp_cli.py
generate` con la configuración de `SuperMarioWorldRecomp` y medir cuánto
del borrador sirve en un sprite ya portado (Rex, Chuck), comparando con
el C nuestro.

### 13.2 Los hilos de JOTD y su conversor binario

- EAB: "Pacman - the Amiga conversion from the arcade game" (t=98727, 10
  páginas o más) y "Ms Pacman conversion WIP" (t=108339). Sin leer
  todavía.
- JOTD pasó de convertir el **fuente** desensamblado a convertir el
  **binario** de Z80 (Commando, Vulgus, 2026: "a simple yet properly coded
  & reversed game to test my new Z80 converter"), y escribió
  `6809to68k` para Gyruss (2025, **OCS con 1 MB**).
- Xevious de tcdev (Mark McDougall): núcleo de 68000 independiente de la
  plataforma + una capa "OSD" por máquina (Neo Geo primero, Amiga AGA
  después). Es la misma separación que tenemos (C del port + `game.s` /
  `scroll.s`).

### 13.3 El compilador: lo que dicen Atari ST y Mega Drive

Mismo CPU, y bastante más trabajo publicado sobre gcc que en la Amiga:

- **`-mshort` (int de 16 bits).** ROADMAP §9.7 regla 2: con vbcc `int` es
  de 32 bits y cada `u8`/`u16` se promociona con `ext`/`and.l`. gcc tiene
  `-mshort`, que hace `int` de 16 bits. Nosotros no usamos libc, así que
  la incompatibilidad de ABI con las bibliotecas no nos toca. **Ojo con
  la semántica:** las promociones cambian (`(u16)x << 8` ya no pasa por 32
  bits), así que todo el C tiene que pasar `regress.py`; la convención
  de §7 (nada de `int` a secas) ayuda.
- **gcc 15 experimental para el 68000** (PeyloW, para Atari ST, `-mshort
  -mfastcall`): modelo de costes con los ciclos reales del 68000, LRA,
  `dbra` en los bucles, `(An)+` en vez de `(An,Dn)` (4 contra 10
  ciclos), `muls.w` cuando el rango alcanza, saca los `andi.l #$FFFF`
  (16 ciclos cada uno) fuera de los bucles. Medido en `memcmp`: **43 % más
  rápido y 30 % más chico**. Es ELF: para nuestro binario crudo sirve
  igual (enlazar con `vlink` u `objcopy`).
- **Mega Drive (SGDK):** el mismo código pasó de **48 a casi 60 fps**
  cambiando gcc 3.4.6 por 6.3, "with virtually zero changes"; gcc 4.x-5.x
  tenía optimizaciones del 68000 rotas; LTO suma un poco más.
  `gcc_m68k_optimizer` (fabri1983) es un plugin de mirilla sobre la
  salida de gcc: ~1 % de CPU por frame en sus pruebas.
- **Amiga:** AmigaPorts mantiene la continuación del amiga-gcc de bebbo
  (gcc 16.2) con `-fbaserel` (datos relativos a un registro, nuestro
  `a4`, P36) y `-mregparm` (argumentos en registros). Slamy/m68k-elf-gcc
  es un gcc para Amiga **sin sistema operativo**, que arranca con su
  propio cargador desde el ADF, como nosotros.
- Compiler Explorer (godbolt) tiene gcc para m68k: sirve para ver en
  segundos qué genera una función con distintas opciones, antes de tocar
  el build.

**L5 cambia**: probar primero **gcc moderno con `-m68000 -mshort -O2
-fomit-frame-pointer`** (y `-fbaserel` o equivalente para `a4`), no solo
"gcc en vez de vbcc". Medir por función con `m68kprof` contra vbcc. Si
gana, es la mejora más grande y más barata de la lógica: toca el build,
no el C.

### 13.4 Los hilos de JOTD en EAB (Pac-Man t=98727, Ms Pacman t=108339)

- **2019, el primer intento de traducir Z80 → 68000 falló:** usó un
  conversor viejo (de Motorola) y lo abandonó en días: "a LOT of issues",
  y usaba registros de dirección con 16 bits con signo, así que el
  programa tenía que vivir en `$0000-$8000`. NorthWay le contesta lo que
  después JOTD construyó: hace falta un "assembler compiler" que siga el
  flujo entre puntos de entrada y **descarte el cálculo de flags que nadie
  lee**. SyX cuenta cómo se hizo en Atari 800: fuente Z80 → una
  herramienta en C → 6502, más rutinas a mano para las instrucciones
  complejas (`LDIR`).
- **Pac-Man 500 (2021) NO es una traducción:** lo reescribió en asm desde
  la documentación ("the Pacman dossier"). Resultado: "99% identical",
  pero "behaviour in turns is not exactly the same" (2026) y los patrones
  de los jugadores expertos no funcionan. Desde Pengo (2023) traduce el
  código original. Es el argumento a favor de nuestro método (portar el
  ROM y verificar contra el oráculo, no reimplementar desde la
  descripción).
- jotd sobre C en la Amiga: "I coded a game in C++ before for the amiga
  and it's really too cumbersome ... I suspect it's not optimized enough
  for A500"; pasó a 100 % asm, con una sola multiplicación (el aleatorio)
  y tablas para el resto.
- Rendimiento: fantasmas en sprites; Pac-Man en **un solo plano** con un
  orden de paleta pensado para no tener que hacer "cookie cut" (máscara)
  ni guardar fondo; sin doble buffer. "Doing less big blits is also less
  penalizing than more small blits" (P31), y **preparar en registros
  todo lo del blit siguiente antes de esperar al blitter**, para escribir
  los registros enseguida (buzzybee muestra el bucle de Proxima 3).
- El sonido con el temporizador de CIA de `ptplayer`: bucles de sonido
  sin chasquidos, y el juego entra en 512 KB.

### 13.5 Consejos de SpritesMind que ya cumplimos (y uno que no)

Menos multiplicaciones y divisiones, tablas, `(An)+`, comparar con cero
y con el signo, y "hacer menos" antes que micro-optimizar: ya están en
ROADMAP §9.7. El que no se puede: **repartir el trabajo de los objetos
entre frames** y no procesar los que están fuera de pantalla. Cambia la
semántica respecto del ROM (§9.8); solo vale donde el ROM ya lo hace.

## 14. Coppershade y código de juegos leído (2026-10-03)

Se leyeron entero el sitio de Photon (coppershade.org: 70 páginas, sus
herramientas, descargas y la *Cheat Sheet* en PDF) y el código de
amiga-game-kit, png2amiga, Knightmare, Blocky Skies y Planet Rocklobster
(clonados en el scratchpad, no en el repo). Lo que sirve, por tema.

### 14.1 Copper: la temporización exacta (Coppershade)

"Copper: Exact WAIT Timing" da el modelo con números, en OCS:

- **Cada instrucción del copper ocupa 8 ciclos = 8 px = 4 unidades de h.**
  Para cargar N registros antes de una posición, se resta 4 por MOVE.
- **Dentro de la ventana de fetch (`DDFSTRT`-`DDFSTOP`) un MOVE tarda más:**
  con 5 planos se alinea a 16 px, alternando MOVEs de 12 y de 8 ciclos;
  **con 6 planos cada MOVE tarda 16 ciclos.** Es la explicación de fondo
  de P42 (rejilla de 8 px del WAIT en DPF) y del límite de ~14 MOVEs en el
  borrado.
- Los colores tienen que estar cargados antes del borde izquierdo (`$38`
  en la pantalla estándar, donde el DMA lee hasta 6 planos en 16 ciclos):
  un MOVE de color que coincide con el borde va en el WAIT `$3D`. Para 15
  colores se resta 14 × 4: WAIT `$05`.
- **Las posiciones `$E5`-`$03` del borrado valen todas como `$E5`**, y
  `$E7`-`$03` "no se pueden usar". Por compatibilidad, Photon usa `$DF` y
  `$07` a cada lado del borrado y pasos de 4 desde ahí (`$DB`, `$0B`...).
  Un WAIT a `$3FFF` o `$3FDF` cambia el color en la línea **anterior**.

### 14.2 Sprites (Coppershade, "Sprite Programming")

Confirma lo que hace §5.1 y agrega los tiempos:

- Las palabras de control se precargan en el borrado vertical, antes de la
  línea 25 PAL. **Cuando VPOS = VSTART, los datos del sprite se leen en
  HPOS `$15`-`$34`.** Las palabras de control se pueden cambiar en
  cualquier momento hasta que se leen los primeros datos. Cambiarlas
  después de mostrar los datos de una línea y antes de HPOS `$15` deja
  **un hueco de 1 línea**.
- En una cadena hay **1 línea de hueco vertical** entre dos sprites del
  mismo canal (las palabras de control ocupan la lectura de esa línea).
  amiga-game-kit lo mide igual: el siguiente empieza en `VSTOP + 1` o
  después (regla de 17 líneas para sprites de 16).
- `DDFSTRT ≤ $34` empieza a quitar sprites, hasta dejar solo el 0 en
  `$1C`. Con nuestro `$30` se pierde el 7 (ya en R5).
- **Prender o apagar el DMA de sprites a destiempo** (`DMACON` `$0020`
  fuera de la última línea del frame) deja basura que baja por la pantalla
  ("rolling sprites"). Hay que hacerlo en el borrado vertical, o apuntar
  los 8 a un sprite vacío: `dc.l $20002100,0,0` (artículo "DMACON") o
  `dc.w $1905,$1a00,0,0,0,0` ("Sprite Programming").
- **Colisiones gratis por hardware:** `CLXCON`/`CLXDAT` detectan solapes
  sprite-sprite y sprite-playfield a nivel de píxel. Para nosotros no
  sirve como lógica del juego (el ROM decide por cajas, y hay que
  reproducirlo 1:1), pero sí como **comprobación de depuración** barata.

### 14.3 Blitter (Coppershade + la Cheat Sheet)

La página "Blitter primer (PAL OCS)" de la *Cheat Sheet* es la tabla más
útil del sitio:

- **Ciclo del blitter: mínimo 4 ticks, +2 si usa B, +2 si usa C y D a la
  vez.** ABCD = 8 ticks por palabra. Tiempo = n × H × W / 7,09 µs.
  Corolario: **usar `BLTAPT` + `BLTBDAT` (B como constante) es más rápido
  que `BLTBPT` + `BLTADAT`.** El modo línea siempre tarda 8 ticks por
  píxel.
- Tabla de secuencias por `USEx` (blit de 3 palabras): `F` (ABCD) usa todos
  los ciclos en 8 ticks; `D` (AB-D) y `B` (A-CD) también, en 6. "B y D son
  más eficientes que 7; 9 es más eficiente que 5 y 3". Un borrado (`1`,
  solo D) tarda lo mismo que una copia A→D (`9`).
- **Con 4 planos queda el 50 % de los ciclos de la línea para el blitter;
  con 6, solo el 25 %** (con `BLTPRI`). El bitplane roba hasta 80 ciclos
  por línea, los sprites 16, el audio 4 y el disco 3. Con más de 4 planos
  y `BLTPRI` encendido, la CPU se para hasta que termina el blit; con
  `BLTPRI` apagado le queda 1 de cada 4 ciclos libres (12,5 % con 6
  planos). Conclusión de Photon: **con 5 o 6 planos apagar `BLTPRI` casi
  no sirve**, y la CPU debería trabajar en registros mientras el blitter
  corre ("MULS/DIVS are great, really!"). Coincide con lo medido en la
  etapa 4: con `BLTPRI` encendido los bobs bajaron de 63 % a 47 % del
  frame con 5 planos (`docs/decisiones-medidas.md`).
- **Hacer los blits caros cuando Denise muestra pocos planos o ninguno:**
  los bobs después de la última línea visible, y el borrado (1 canal)
  durante la imagen. Para nosotros: el HUD y el borde inferior son la
  ventana barata.
- Los registros `$DFF040`-`$DFF074` **se conservan entre blits**, y los
  punteros quedan donde estaría la palabra siguiente si el blit tuviera
  una línea más. Se pueden cargar una sola vez antes de un bucle.
- Orden de carga: esperar, `BLTCON`, `BLTxDAT`, `BLTAxWM`, `BLTSIZE`; los
  punteros y módulos en cualquier momento antes de `BLTSIZE`. La primera
  palabra se carga y desplaza al escribir el puntero o el dato, así que el
  dato va antes que el registro que lo desplaza.
- **No hace falta esperar al blitter** si el código está en chip RAM,
  `BLTPRI` = 1 y el blit usa todos los ciclos (`BLTCON0` = `$x9xx` o
  `$xFxx`): la CPU no ejecuta nada hasta que termina. La espera correcta
  para cualquier Amiga lee `DMACONR` una vez antes del `btst #6`.
- `BZERO` (bit 13 de `DMACONR`) dice si todo lo que escribió el blit fue
  cero: con un AND de dos máscaras da colisión exacta por píxel. Solo
  sirve para depurar, por lo mismo que `CLXDAT`.

### 14.4 Otras páginas de Coppershade

- **"Collision Detection in Amiga Games":** una comprobación de cajas
  óptima en 68000 con mitades de ancho y alto, para salir antes y sin
  `Scc` en el bucle (`sub`/`bpl`/`neg`/`cmp`/`bhi`). Y el "skip issue":
  dos cajas se cruzan sin tocarse cuando la velocidad relativa supera la
  suma de los anchos; comprobar cada N frames multiplica la velocidad por
  N. Sirve de argumento a §13.5: SMW comprueba todos los frames y hay que
  respetarlo.
- **"Support 3 Buttons":** los botones 2 y 3 del joystick se leen en
  `POTGOR`. Escribir `$FF00` en `POTGO` después de cada lectura deja los
  pines listos para el frame siguiente sin esperar los 300 µs. Puerto 2:
  bits 14 y 12 en 0 si están apretados. Para D14 (el joystick como
  alternativa al teclado: SMW necesita B, A, Y y X) `game.s` ya lee el
  botón 2 así (`read_input`, Y = correr); el 3 no está asignado.
- **"Centered Display Setup":** escribir siempre `BPLCON1 = 0` si no se
  usa, porque si no queda el valor de la pantalla anterior.
- **"Maximum Overscan":** los televisores CRT muestran unos 342 × 268 y a
  veces desplazados 12 px a la derecha. No cambia D10 (256 px).
- **Herramientas:** la *Cheat Sheet* (registros, mapa de memoria, ranuras
  de DMA de la HRM, la tabla del blitter y los tiempos del 68000 en una
  hoja), AsmTwo (Asm-One con depurador) y The Nibbler, un compresor que
  descomprime más de 3 veces más rápido que un gzip en 68000 (candidato
  para C3, junto a LZ4 de §8). P6112 es un reproductor de módulos; no
  aplica a D5.
- Sin interés para el port: los artículos de Protracker, el de muestras,
  el diario, los de la historia de la demoscene y el de IA.

### 14.5 png2amiga: `build_mid` en otro proyecto, calibrado en hardware

El modo "DPF + strips" de png2amiga (`src/strips.hpp`) hace lo mismo que
nuestra `build_mid`: **cambia colores de PF2 a mitad de línea en DPF de 6
planos.**

- Cada línea abre con los 8 colores de PF2 en el borrado (~9 MOVEs, fijo,
  para que nada pase de una línea a otra). Después, un WAIT en h = `$38`
  abre la cadena y **20 MOVEs seguidos, sin relleno, caen cada 16 px**
  (x = 0, 8, 24, 40... 296). Un WAIT en h = `$E1` la cierra.
- Las posiciones se **calibraron en una OCS real** con `--strips-probe`.
  Su presupuesto publicado: **~14 MOVEs en el borrado + ~20 en la parte
  visible por línea con 6 planos.** Es nuestro número.
- **Guarda de 1 px a cada lado del cambio:** el planificador no usa en ese
  píxel el registro que se está cambiando, porque la transición no es
  exacta.
- Rellena con un MOVE a `COLOR31`, que con DPF 3+3 no se lee. Nosotros no
  podemos (los sprites usan 17-31, D8), y `build_mid` ya rellena con
  `MOVE $1FE` (NOOP), no con ceros.
- **Contrastado con P59 (2026-10-03):** en la línea 255 escriben `$FFE1`
  (`src/cheader.cpp`: `max(w0, $FFDF)` en la cadena de strips y "keep the
  late horizontal position on line 255 too" en la rebanada), para no
  adelantar el cambio a píxeles visibles. No documentan haber probado
  esa línea con 6 planos en hardware, y P59 está medido en WinUAE (con 6
  planos `$FFE1` no llega). **No cambia nada nuestro:** P59 sigue, y
  `build_copper` mantiene `$FFDF` + un MOVE nulo.
- La captura `docs/scap.png` es el overlay de DMA de vAmiga con la lista
  saturada: sirve de referencia visual de cómo se ve en el bus.

### 14.6 amiga-game-kit: sidescroller en DPF

Su `examples/sidescroller/README.md` es un juego DPF con paralaje en dos
bandas, héroe en 4 sprites y enemigos multiplexados, medido en A500:

- **Cambiar de banda de PF2:** WAIT en x = `$D8` (`DDFSTOP` `$D0` + una
  unidad de fetch), después de la última lectura de la línea. El módulo
  ya se sumó, así que el puntero nuevo vale para la línea siguiente, y el
  `BPL2MOD` nuevo también rige desde la siguiente.
- **"Unos 8 MOVEs seguros, 15 no"** en el borrado con 6 planos y
  `DDFSTRT` `$30`: la primera versión metía 15 y los últimos caían 7 px
  dentro de la línea. Lo arreglaron con **una línea vacía** entre bandas,
  donde se carga la paleta.
- **PF2 "vacío" con módulo negativo:** 42 bytes en cero y `BPL2MOD = -42`,
  así cada línea vuelve a leer los mismos ceros.
- `BPLCON1` lleva el retardo de los dos playfields: cada cambio de banda
  tiene que volver a escribir también el de PF1.
- **Multiplexado:** cadena por canal, el siguiente sprite a ≥ 17 líneas, y
  ante un conflicto **alternan**: un frame el de arriba y el otro el de
  abajo (parpadeo a 25 Hz en vez de que uno desaparezca). Las 16 filas de
  datos se copian solo cuando cambia el cuadro de animación; si no, solo
  las 2 palabras de control. Las cadenas están en doble buffer, igual que
  la lista del copper.
- **El tick de ptplayer puede pasar de 40 líneas.** El frame empezaba en
  la línea 300 y un tick ahí lo atrasaba un frame (uno cada ~2 s, aun
  quieto). Lo adelantaron 64 líneas (32 no alcanzaban). Aviso para D5: el
  tick de la música tiene que estar en el presupuesto del peor frame.
- "El 68000 es lento en todo": un bucle de 7 vueltas con una ordenación
  cuesta ~1 % del frame. Su primera versión de enemigos costó +12 %, y
  bajó precalculando una vez lo que no cambia.
- La pantalla va 1-2 frames detrás de la lógica (doble buffer). En las
  pruebas sincronizan por serie, no por frame fijo (lo mismo que P41/P75).
- Su emulador: vAmiga sin ventana con un parche de 35 líneas para
  `wait N frames` (el original solo espera segundos enteros). Funciona en
  macOS y Linux; en Windows haría falta revisar las rutas de `/tmp`.

### 14.7 Knightmare (djh0ffman): shooter vertical de A500 en asm

Port de MSX a 256 px de ancho y 5 planos, el juego entero en asm. **No
tiene licencia: se lee, no se copia.**

- **Planos entrelazados** (una línea = los 5 planos seguidos): un bob es un
  solo blit para todos los planos. Ya lo hacemos (`bench*.s`).
- **Scroll vertical con un buffer del doble de alto**: cada fila de tiles
  se dibuja dos veces (mitad de arriba y mitad de abajo), así la ventana
  siempre es contigua. Es el equivalente vertical de nuestro buffer
  circular.
- **Restaura el fondo detrás de los bobs desde la otra mitad del mismo
  buffer**, con un blit C→D (`$03AA`). No tiene un buffer de fondo limpio
  aparte; si la zona cruza el borde, parte el blit en dos. Para nosotros
  (scroll horizontal) la idea sería restaurar desde la copia de la columna
  que ya existe en el buffer circular.
- Cola de restauración **por buffer** (dos colas que rotan con la
  pantalla). Si el bob no está desplazado (x múltiplo de 16) no agrega la
  palabra extra. `BLTCON0`/`BLTCON1` salen de una tabla de 16 entradas por
  desplazamiento.
- **Detecta frames perdidos:** la VBL pone una bandera, el bucle la pone en
  2 al terminar si ya llegó otra VBL, y en ese caso no espera.
- **Banderas de "sucio" para la lista del copper:** la paleta y los
  punteros de sprites se reescriben solo si cambiaron, con un contador
  que empieza en 2 para cubrir los dos buffers.
- Ordena los bobs con un intercambio adyacente que retrocede al
  encontrar un desorden (casi inserción): barato porque la lista viene
  casi ordenada del frame anterior. Es la idea de la ordenación de Ocean
  (§5.2).

### 14.8 Blocky Skies y Planet Rocklobster

- **Blocky Skies** (alpine9000, BSD): un juego chico. DPF con scroll
  independiente, el copper cambia de modo a mitad de pantalla y la paleta
  6 veces, y los ítems son sprites. Lo nuevo es su **fork de FS-UAE con
  símbolos en el depurador aun después de arrancar desde el bootblock**
  (github.com/alpine9000/fs-uae), que es nuestro caso (D6). Trae el
  trackloader de Photon y una copia de "How to code" (`docs/Howtocode5.txt`).
- **Planet Rocklobster** (Oxyron, Unlicense): efectos de demo (vóxel,
  vectores, rotozoom). El *framework* tiene cargador por pistas,
  descompresor doynax y un `benchmark` que pinta `COLOR00` mientras mide
  (barra de tiempo por raster). Nada nuevo para el port.

### 14.9 Otros enlaces encontrados (sin leer a fondo)

- **Emuladores para V1 (§6.1):**
  - **vamiga-lua**, del autor de AmiGalaga: vAmiga con Lua por un socket.
    Lee memoria y registros, pone breakpoints de CPU, copper y posición del
    haz, saca capturas y guarda y restaura el estado. Determinista, ~720
    fps en warp. Compila en Linux y macOS (sirve en cloud, no en la PC
    Windows).
  - **Copperline**, cycle-exact nuevo (1.0 rc), **corre en Windows**. Su
    *Frame Analyzer* muestra quién usó el bus de chip en cada ciclo; tiene
    depuración hacia atrás y control por JSON-RPC sin ventana. Habría que
    validarlo contra WinUAE con `bench2.s` antes de creerle; podría
    reemplazar las calibraciones con `copcal` (P42, P46, P51).
- **SMWDisX**: desensamblado de SMW con mejores nombres que `smw-src`.
  Ensambla las 4 versiones y es de donde snesrecomp saca los nombres, el
  mapa de RAM y los límites de las funciones (tarjeta X0, §13.1).
- **grovdata/Amiga_Sources**: catálogo de juegos de Amiga con fuentes
  publicadas (casi todos de jotd666).
- No están publicados: los ports de mcgeezer (Rygar, Kung Fu Master).

### 14.10 Qué hacer con esto

Ya cumplido, no hace falta nada: `build_mid` no deja ceros (rellena con
`MOVE $1FE`), los planos entrelazados y la medida con y sin `BLTPRI`.

**Hecho el 2026-10-03:**

- **Banderas de "sucio" en `mario_draw`** (`game.s`, idea de Knightmare,
  §14.7): los punteros de sprite de cada lista se escriben una sola vez y
  la paleta de Mario solo cuando cambia. `game.total` en Musashi: peor
  frame 118 724 → 117 796 ciclos, media 39 978 → 39 053 (−0,65 % del
  frame, en todos los frames). Verificado: `regress.py` igual en todo lo
  demás; la cabecera de la lista escrita es la de antes en los 6314
  frames del replay (pasando por 2 paletas de Mario); captura de WinUAE
  del replay en el frame 1200 idéntica píxel a píxel a la del commit
  anterior.
- **Sprite vacío válido** (§14.2): `g_null` pasa de `0,0` a
  `$1905,$1A00,0,0,0,0` (12 bytes), como recomienda Photon.
- **P59 contra png2amiga** (§14.5): leído; no cambia nada.
- Ya estaba: el botón 2 del joystick por `POTGO`/`POTINP` (§14.4).

Candidatos que quedan, en orden de valor (no hay tarjetas abiertas):

1. ~~Contrastar P59 con el `$E1` de png2amiga~~: hecho, ver arriba.
   (También del §9, el mismo día: **L4** medida y descartada, §4.2; **V3**
   hecha, `tools/asmlint_port.py` en `lint_port.py`; **V2** hecha,
   `tools/coverage.py` y `docs/cobertura.md`.)
2. **Restaurar desde el buffer en vez de guardar el fondo** (§14.7), si la
   restauración de bobs pesa cuando llegue el bob en PF1 (D8).
3. **Rehacer el presupuesto del blitter con la tabla de ciclos** (§14.3):
   B como constante, blits caros durante el HUD.
4. **Sumar el tick de la música al peor frame** al cerrar D5 (§14.6).
5. **El botón 3 del joystick** (bit 12 de `POTINP`) como X (D14, §14.4):
   el 2 ya se lee; el 3 no está asignado.
6. **Herramienta:** el FS-UAE de alpine9000 (símbolos tras el bootblock) o
   el parche `wait N frames` de vAmiga, si V1 avanza.

---

## Fuentes

- JOTD: [amiga68ktools](https://github.com/jotd666/amiga68ktools)
  (`tools/6502to68k.py`, `z80268k.py`, `asmcoverage.py`, `profiler.s`),
  [galaga](https://github.com/jotd666/galaga),
  [mpatrol](https://github.com/jotd666/mpatrol),
  [donkey_kong](https://github.com/jotd666/donkey_kong),
  [Indie Retro News sobre Double Dragon](https://www.indieretronews.com/2026/04/double-dragon-near-arcade-experience.html)
- [AmiGalaga](https://github.com/mwulffn/AmiGalaga) (`CLAUDE.md`,
  `asmlint/`, `game/tools/amiga.py`) y su
  [fork de FS-UAE con Lua](https://github.com/mwulffn/fs-uae)
- [ACE](https://github.com/AmigaPorts/ACE),
  [PR #292, sprites multiplexados](https://github.com/AmigaPorts/ACE/pull/292)
- Codetapper: [Sprite Tricks](https://codetapper.com/amiga/sprite-tricks/),
  [Risky Woods](https://codetapper.com/amiga/sprite-tricks/risky-woods/),
  [Shadow of the Beast](https://codetapper.com/amiga/sprite-tricks/shadow-of-the-beast/),
  entrevistas con [Chris Sorrell](https://codetapper.com/amiga/interviews/chris-sorrell/),
  [Dave Semmens](https://codetapper.com/amiga/interviews/dave-semmens/),
  [Ronald Pieket Weeserik](https://codetapper.com/amiga/interviews/ronald-pieket-weeserik/),
  [Martin Pedersen](https://codetapper.com/amiga/interviews/martin-pedersen/)
- HRM: [A Copper Loop Example](http://amigadev.elowar.com/read/ADCD_2.1/Hardware_Manual_guide/node005B.html),
  [The WAIT Instruction](http://amigadev.elowar.com/read/ADCD_2.1/Hardware_Manual_guide/node004B.html)
- [png2amiga + Scorpion Engine (The Oasis BBS)](https://theoasisbbs.com/amiga-copper-graphics-bring-more-color-to-scorpion-engine-games/),
  [Copper Chunky (powerprograms.nl)](https://www.powerprograms.nl/amiga/copper-chunky.html)
- Lionheart: [Lilura1](https://lilura1.blogspot.com/2022/04/Lionheart-Amiga-1993-Thalion-Software.html),
  [EAB "Lion Heart & Colours"](https://eab.abime.net/showthread.php?t=17405)
- [Atari-Forum, "50fps games"](https://www.atari-forum.com/viewtopic.php?t=28962) (Stardust)
- Endianness: [rcheevos #302, memory swizzling](https://github.com/RetroAchievements/rcheevos/issues/302),
  [skmp, negative addressing](https://skmp.dev/blog/negative-addressing-bswap/)
- [LLMario](https://github.com/Wynplusplus/LLMario)
- Compiladores: [Benchmarking C compilers for Amiga](https://weblambdazero.blogspot.com/2015/06/benchmarking-c-compilers-for-commodore.html),
  [EAB, GCC 6.2 toolchain](https://eab.abime.net/showthread.php?t=85474&page=7),
  [vscode-amiga-debug](https://github.com/BartmanAbyss/vscode-amiga-debug)
- WinUAE: [4.9.0](https://www.winuae.net/2021/12/04/winuae-4-9-0/) y
  [4.10.0](https://www.winuae.net/2022/12/17/winuae-4-10-0/) (depurador visual de DMA)
- Multiplexores: [Cadaver, codebase64](https://codebase.c64.org/doku.php?id=base:sprite_multiplexing)
- Audio: [LSPlayer](https://github.com/arnaud-carre/LSPlayer)
- Compresión: [lz4-68k](https://github.com/arnaud-carre/lz4-68k),
  [L-Packer](https://github.com/arnaud-carre/L-Packer),
  [ZX0](https://github.com/einar-saukas/ZX0)
- Sonic de reassembler: [Generation Amiga](https://www.generationamiga.com/2026/05/01/from-mega-drive-to-amiga-reassemblers-upcoming-sonic-port-is-a-retro-coding-marvel/),
  [Indie Retro News](https://www.indieretronews.com/2025/11/hot-news-as-sonic-hedgehog-is-in-works.html)
- SMB en C64: [Hackaday](https://hackaday.com/2019/05/20/that-super-mario-bros-c64-port-was-too-good-for-this-world/)
- 65816 → C: [snesrecomp](https://github.com/RetroPortingToolKit/snesrecomp),
  [SuperMarioWorldRecomp](https://github.com/mstan/SuperMarioWorldRecomp)
- JOTD en EAB: [Pacman](https://eab.abime.net/showthread.php?t=98727),
  [Ms Pacman](https://eab.abime.net/showthread.php?t=108339);
  [Commando (Indie Retro News)](https://www.indieretronews.com/2026/08/commando-1980s-military-shooter-by.html),
  [Gyruss](https://www.indieretronews.com/2025/05/gyruss-exciting-news-as-jotd-is-now.html),
  [Xevious de tcdev](https://tcdev.itch.io/xevious)
- Compiladores: [gcc 15 experimental, M68K_OPTIMIZATIONS](https://github.com/PeyloW/gcc-15-experimental-build/blob/main/M68K_OPTIMIZATIONS.md),
  [opciones M680x0 de gcc](https://gcc.gnu.org/onlinedocs/gcc/M680x0-Options.html),
  [AmigaPorts gcc](https://github.com/AmigaPorts/gcc),
  [amiga-gcc](https://franke.ms/amiga/amiga-gcc.wiki),
  [m68k-elf-gcc (Slamy)](https://github.com/Slamy/m68k-elf-gcc),
  [gcc_m68k_optimizer](https://github.com/fabri1983/gcc_m68k_optimizer),
  [SpritesMind: GCC version vs performance](https://gendev.spritesmind.net/forum/viewtopic.php?t=2634),
  [SpritesMind: 68000 optimization tips](https://gendev.spritesmind.net/forum/viewtopic.php?t=2598)
- Coppershade (Photon): [Copper: Exact WAIT Timing](https://coppershade.org/articles/AMIGA/Agnus/Copper:_Exact_WAIT_Timing/),
  [Sprite Programming](https://coppershade.org/articles/AMIGA/Denise/Sprite_Programming/),
  [Programming the Blitter](https://coppershade.org/articles/AMIGA/Agnus/Programming_the_Blitter/),
  [DMACON](https://coppershade.org/articles/Code/Reference/DMACON/),
  [Collision Detection in Amiga Games](https://coppershade.org/articles/More!/Topics/Collision_Detection_in_Amiga_Games/),
  [Support 3 Buttons](https://coppershade.org/articles/More!/Topics/Support_3_Buttons_in_Amiga_Games!/),
  [Centered Display Setup](https://coppershade.org/articles/AMIGA/Denise/Centered_Display_Setup/),
  [Downloads](https://coppershade.org/articles/More!/Downloads/),
  [Photon's Cheat Sheet (PDF)](http://coppershade.org/helpers/DOCS/Photons-Cheat-Sheet.PDF)
  (el servidor responde 404 pero manda la página: WebFetch falla por eso, curl y un navegador no)
- [png2amiga](https://github.com/tinic/png2amiga) (`README.md` "Strip palette", `src/strips.hpp`)
- [amiga-game-kit](https://github.com/codebase/amiga-game-kit)
  (`examples/sidescroller/README.md`, `techniques/*/TECHNIQUE.md`, `docs/spike-results.md`, `docs/references.md`)
- [Knightmare](https://github.com/djh0ffman/KnightmareAmiga) (`logic/blitter.asm`, `logic/copper.asm`, `logic/map.asm`; sin licencia)
- [Blocky Skies](https://github.com/alpine9000/blockyskies) y su [FS-UAE con símbolos](https://github.com/alpine9000/fs-uae)
- [Planet Rocklobster](https://github.com/AxisOxy/Planet-Rocklobster)
- Emuladores: [vamiga-lua](https://github.com/mwulffn/vamiga-lua), [Copperline](https://copperline.dev/)
- Desensamblado de SMW con nombres: [SMWDisX](https://github.com/IsoFrieze/SMWDisX);
  catálogo de fuentes publicadas: [grovdata/Amiga_Sources](https://github.com/grovdata/Amiga_Sources/blob/master/software.md)
