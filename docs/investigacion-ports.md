# Investigación: cómo resolvieron otros lo que nos frena (ampliada 2026-10-05)

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
> **Ampliación:** §15 actualiza las conclusiones contra el port vigente;
> §16 contrasta nuevas fuentes primarias; §17 convierte los hallazgos en
> experimentos con puertas; §18 registra fuentes, límites y pendientes.
> **§19 (2026-10-06):** diez juegos de referencia del A500 (Lionheart,
> Agony, Beast, Kid Chaos, Jim Power, Elfmania, Disposable Hero, Apidya,
> Turrican II, Ruff 'n' Tumble) más Robocod, vistos con el depurador
> Engine9000; experimentos E11-E14.
> Las cifras de terceros y los cálculos teóricos **no son medidas del port**.
>
> Límite de la búsqueda: **English Amiga Board (eab.abime.net) no se pudo
> leer** (protección anti-bots); de sus hilos solo hay lo que muestran los
> buscadores. Varias respuestas buenas seguramente están ahí.

---

## 1. Resumen

| problema nuestro | quién lo resolvió y cómo | qué nos sirve | acción |
|---|---|---|---|
| El peor frame pasa del 100 % (D1, O4) | **Robocod** (Chris Sorrell): la lógica corre a 50 Hz fija por interrupción de timer y el bucle principal dibuja "lo antes que puede" las peticiones de render acumuladas | Una cuarta opción para el informe D1: **lógica siempre a 50 Hz, imagen que pierde un frame solo cuando no llega**. Ni 25 Hz fijos ni recortar | §2.1, tarjeta **O5** |
| Cola de blits por interrupción (`docs/plan-tecnico.md` §9.6) | **AmiGalaga**: sin fast RAM no gana de forma consistente; con `BLTPRI` pierde en los casos publicados | Comparar también máximos; no implementar la cola sin medirla | §2.2, corrige §9.6 |
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
| El DMA cambia mucho el coste según la rutina | **Bartman/Abyss**: perfilador de funciones y ranuras DMA, reproducción del frame y de los blits | Explicar los picos reales y los plazos de G5, sin un multiplicador global de Musashi | §16.1, E01 |
| Preparación de muchos blits pequeños | **Power Programs, Dual Layer Graphics**: agrupa restauraciones y dibujos, conserva registros | Especializar los lotes de G7 y la columna nueva; medir tiempo total con O5 | §16.2, E03 |
| Bobs supuestamente 3 veces más rápidos | **Power Programs, Fast Bobs**: copia y autoborrado, pero exige PF delantero vacío y separación entre objetos | No aplicarlo al terreno de PF1; buscar copias exactas solo dentro de regiones opacas | §16.3, E04 |
| Recarga de sprites contra copiar cadenas | **ACE PR #292**: encadenado DMA, gap 1, sin reasignador automático | Evaluar una combinación por objeto, contando CPU, chip y ventanas reales | §16.5, E02 |
| Música barata con picos de interrupción | **LSP**: tick y reactivación DMA separados; modo generado a cambio de memoria | Medir las dos fases y su interferencia con O5; eventos en slow, muestras en chip | §16.6, E08 |
| Cambio de compilador y traducción de lógica | **GCC oficial + SMBNeo/VS**: ABI explícita y C nativo contrastado con traducción de referencia | Separar prueba del compilador de cambios semánticos y conservar el oráculo | §16.7–§16.8, E07 |
| Ranuras del copper en `build_mid` | **Lionheart, Elfmania, Kid Chaos**: el número de planos cambia por franjas (4/5/6/5; 5→4; DPF 3+2) | Donde PF2 usa ≤ 3 colores, DPF 3+2 da una ranura de copper cada 12 px en vez de 16 | §19.3, **E11** |
| Colores de PF1 sin cargas a mitad de línea | **Kid Chaos, Lionheart**: colores copperizados por Y del nivel, en 8 direcciones a 50 fps; la lista se rehace al mover la cámara en vertical | Pasar al borrado los índices de PF1 que en YI1 nunca comparten línea con otra variante | §19.3, **E12** |
| Banzai Bill (64×64) | **Lionheart**: la bestia montada ocupa los 8 sprites; **Robocod**: sprite o bob según la banda | Banzai en sprites solo cuando sus líneas están libres; el peor caso sigue siendo el bob | §19.3, **E14** |

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

### 2.2 La cola de blits por interrupción no gana de forma consistente en A500

`docs/plan-tecnico.md` §9.6 propone "columna nueva y bobs en una cola servida por la
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
CPU. Es la opción "detrás del haz" de `docs/plan-tecnico.md` §10.6 para el Banzai en PF1:
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

**No se identificó en los casos revisados** un sistema equivalente de
cargas de color en coordenadas del nivel que se mueven con el scroll
horizontal y con nuestra densidad, que es lo que hace `build_mid`. Esto
no demuestra que no exista otro motor que lo haga. La lección
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
(~50 ciclos contra 12 de un `move.w`, `docs/plan-tecnico.md` §9.7). Los emuladores que
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

`docs/plan-tecnico.md` §10.6 eligió la segunda (un `SPRxPT` nuevo por copper, sin copiar
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
frames. Coincide con lo que `docs/plan-tecnico.md` §9.5 ya intuía ("inserción: casi
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
  rinde la mitad. Es la regla ×1,3-1,4 de `docs/plan-tecnico.md` §9 vista desde el
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
  en todo lo posible. Ya es nuestra regla (`docs/plan-tecnico.md` §9.7, `T8X`/`T16X`).
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

1. **La cámara vertical (`docs/plan-tecnico.md` §10.2b, S8)** es exactamente el caso
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
  tabla (`rept 256 / dc.w REPTN*n`). Es nuestra regla (`docs/plan-tecnico.md` §9.7).
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

**Para nosotros:** la elección de `docs/plan-tecnico.md` §10.6 (un `SPRxPT` nuevo por
copper, sin copiar datos) tiene respaldo en hardware real y en juegos
comerciales. El coste en el copper es 1-2 MOVE por recarga (`SPRxPTL`, y
`SPRxPTH` si cambia el banco de 64 KB); si los frames de las poses quedan
todos en un mismo banco, es **un** MOVE. G0 se reduce a medir si ese MOVE
entra en las líneas más cargadas de `copsim.py`; el encadenado por DMA de
ACE queda como plan B para esas líneas.

**Actualización 2026-10-05:** el párrafo anterior solo presupuestaba el
puntero de un canal. Para poses compartidas faltan POS/CTL; G0 midió hasta
8 MOVE por pareja y ventanas más tempranas. Aplicar `medida-g0.md`, G2 y
§15.1/§16.5 de este documento; el coste de 1 MOVE no es el de una recarga
completa de objeto.

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

- **`-mshort` (int de 16 bits).** `docs/plan-tecnico.md` §9.7 regla 2: con vbcc `int` es
  de 32 bits y cada `u8`/`u16` se promociona con `ext`/`and.l`. gcc tiene
  `-mshort`, que hace `int` de 16 bits. Nosotros no usamos libc, así que
  hay menos dependencia de bibliotecas, pero sigue habiendo ABI con el
  asm y los arneses (corrección 2026-10-05: §16.7). **Ojo con
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

**Revisión 2026-10-05:** §16.7 sustituye ese orden: empezar con ABI y
tamaños compatibles, y probar `-mshort` aparte. La ganancia no está
demostrada y la integración no se limita necesariamente al build.

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
`docs/plan-tecnico.md` §9.7. El que no se puede: **repartir el trabajo de los objetos
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

## 15. Revisión contra el estado vigente (2026-10-05)

Esta ampliación se hizo leyendo `ROADMAP.md` (continuación de ola 3),
`baseline_pc.json`, `informe-d1.md`, `medida-g0.md`, `diseno-9.2.md` y
las rutinas de columna/copper de `player/scroll.s`. **No se ejecutaron
nuevos bancos de rendimiento ni se implementaron las propuestas.**

### 15.1 Qué cambió desde la primera investigación

| Afirmación o propuesta anterior | Lectura vigente | Consecuencia |
|---|---|---|
| O5 como cuarta opción para D1 (§2.1) | O5 está autorizado e integrado por defecto | Investigar cómo reducir imágenes omitidas y conservar ticks; no volver a proponer 25 Hz |
| Una recarga de sprite cuesta 1–2 MOVE (§12.5) | Eso cuenta solo PT de **un canal**; con poses compartidas hay que programar también POS/CTL. G0 mide hasta 8 MOVE por pareja, o 6 con banco físico común | Planificar G5 con ese coste, no con el del puntero aislado |
| El borrado alcanza para la recarga (§14.2) | A 256 px, G0 pierde píxeles con PT desde h=$D8 anterior; desde $80/$C0 anterior hay controles exactos | La ventana medida de `medida-g0.md` prevalece; falta combinarla con colores reales |
| Un único PF1 detrás del haz ahorra el segundo (§2.3) | G2 prevé segundo PF1 porque O5 debe poder repetir una foto intacta | Battle Squadron sigue siendo antecedente; no reemplaza la propiedad de buffers de G2 |
| L4, V2 y V3 pendientes (§1) | L4 se probó y descartó; V2/V3 ya están hechas | Buscar cobertura de escenarios y coste de OAM, sin repetir esas tarjetas |
| Listas enormes con cambios mínimos solucionan el scroll (§3) | Es una dirección útil, no una prueba de que SMW admita O(1) por frame | Dar presupuesto de memoria y semántica a cada precálculo; S5 sigue abierto |
| Cinco planos como presupuesto general | `build_copper` emite `$01006600`: **seis planos en DPF 3+3** | Todo banco integrado debe reproducir seis fetch, ancho 256 y P51; no usar el banco antiguo de cinco planos como garantía |

### 15.2 Baseline que debe acompañar los experimentos

Los siguientes son **resultados existentes**, no ganancia de esta investigación:

| Métrica | Valor | Entorno / alcance |
|---|---:|---|
| `game.total.max` / media | 119 998 / 39 130 ciclos | `baseline_pc.json`, 2026-10-05; Musashi, sin esperas DMA |
| `game.build_mid.max` | 80 868 ciclos | Misma baseline, replay; incluye corrección P51 |
| `scroll.vuelta.max`, s=4580 | 111 520 ciclos | Misma baseline, barrido de scroll; escenario distinto del replay |
| Lógica con OAM, máximo | 46 718 ciclos | `diseno-9.2.md`; OAM opt-in; antes 39 026 |
| O1 total máximo | 152 640 ciclos, 107,4 % | WinUAE exacto, `informe-d1.md` §5; **anterior a P51 y a la integración OAM** |
| G0, cadenas gap 1 | 0 errores de píxel | WinUAE exacto, carga sintética; no equivale a G5 integrado |

**Medido después de la investigación (2026-10-05):**
[OAM + O5 y barrido del scroll](medida-oam-o5.md). Lógica con OAM:
37,24 % del frame; interrupción completa: 46,40 %; `build_mid`: 89,16 %.
Ambas variantes completan 6312 frames lógicos con 0 incidencias COPER
detectadas y 14 fotos omitidas. El barrido separado alcanza 87,2 % en
s=4576. Son tiempos de WinUAE exacto con P51; no una ganancia de S5.

La medida anterior de O1 da factores muy diferentes: lógica ×1,03,
Mario ×1,44, columna ×3,2 y `build_mid` ×1,46. No permite predecir
el juego completo multiplicando todo por ×1,3. Tampoco se suman máximos
de rutinas registrados en frames distintos para llamarlos «peor frame».

## 16. Fuentes nuevas y conclusiones aplicables

En cada apartado, **evidencia** describe lo que publica la fuente;
**aplicación** es una propuesta nuestra que todavía necesita la puerta de §17.

### 16.1 Bartman/Abyss: ver quién ocupa el bus, además de contar ciclos

**Evidencia.** El [README del autor](https://github.com/BartmanAbyss/vscode-amiga-debug)
documenta perfiles de funciones y DMA, reproducción de un frame por ciclos,
blits y lista del copper. Su preset A500 usa KS 1.3 y ECS Agnus;
no es automáticamente nuestro perfil KS 1.2/OCS.

**Aplicación (E01).** Capturar el pico de vuelta, un frame con columna y
uno con recarga de cuatro parejas. Separar CPU ejecutando, espera de
blitter y ocupación de bitplanes/copper/sprites/audio. Esto explica si
conviene escribir menos palabras o mover el trabajo a otra fase del haz.

Para nuestro binario crudo, el flujo de símbolos/perfilado debe probarse:
el README no demuestra carga directa del ADF propio con símbolos vbcc.
Conservar WinUAE de referencia para aprobar medidas; usar este perfilador
como diagnóstico si la integración requiere otro formato de build.

No instalar ni migrar el proyecto como parte de esta investigación.
El experimento primero debe reproducir un banco conocido con el perfil
exacto del port y registrar versión/configuración del emulador.

### 16.2 Power Programs: agrupar blits ahorra preparación

**Evidencia.** [Dual Layer Graphics, optimizaciones](https://www.powerprograms.nl/amiga/dual-layer.html)
agrupa blits por clase, conserva registros y reduce recargas. En su
comparativa, tener ciclos DMA libres parecidos no asegura igual cantidad
de bobs: preparar más operaciones también cuesta CPU.

**Aplicación (E03).** En `blit_steps` se vuelven a cargar control,
máscaras y módulos para cada bloque de 16×16×3. Evaluar un lote de
bloques con configuración común y una configuración distinta para
la copia final. Reinstalar el estado al entrar al lote: ningún otro
usuario del blitter debe heredar módulos por accidente.

En G7, agrupar **todas las restauraciones antes de dibujar**, y luego
dibujar en el orden de prioridad OAM. No ordenar dibujos por material
si eso altera los solapes. El beneficio se debe medir en el frame
completo, incluyendo esperas y la interrupción de lógica de O5.

No aplicar aquí la idea de «espera implícita» por chip+BLTPRI:
nuestro código corre en slow y esa precondición no se cumple.

### 16.3 Mega Typhoon / Fast Bobs: el truco y por qué no se traslada entero

**Evidencia.** El experimento del autor [Dual Playfield Fast Bobs](https://www.powerprograms.nl/amiga/dpl-fastbobs.html)
parte de Mega Typhoon y utiliza PF delantero dedicado a objetos.
Copia con márgenes transparentes para borrar la pose previa, exige
separación entre bobs y adapta el margen al doble buffer. Publica
mejoras de 2,5–3 veces en su escena, con esas restricciones.

**Aplicación.** Nuestro PF1 contiene terreno; una copia rectangular
destruiría sus píxeles. No convertir Banzai ni todos los excedentes a
este método. Tampoco podemos rediseñar trayectorias para evitar solapes.

**Experimento E04 (inferencia nuestra).** El conversor puede detectar
rectángulos interiores totalmente opacos y dibujarlos por copia;
los bordes transparentes siguen con máscara. Conserva píxeles y
prioridad, pero añade operaciones: dividir un bob pequeño podría
costar más de lo que ahorra. Probar primero Banzai, con todas sus
poses, desplazamientos y recortes. Conservar la ruta genérica si
el coste integrado no baja. No hay aún un ahorro demostrado para SMW.

### 16.4 Máscara compartida, anchura desplazada y un presupuesto de Banzai

**Evidencia.** El HRM describe [canales DMA](https://www.amigadev.elowar.com/read/ADCD_2.1/Hardware_Manual_guide/node011B.html),
[shifts y máscaras](https://www.amigadev.elowar.com/read/ADCD_2.1/Hardware_Manual_guide/node011F.html)
y [copia de regiones](https://www.amigadev.elowar.com/read/ADCD_2.1/Hardware_Manual_guide/node0121.html).
El canal A tiene máscaras de primera/última palabra; los desplazamientos
y módulos forman parte del cálculo del área tocada. Tener 64 px de
imagen no garantiza que un bob desplazado escriba solo cuatro palabras.

**Cálculo nuestro, sin contención ni preparación:** con la tabla del
blitter de §14.3, un dibujo ABCD consume 8 ticks por palabra y una
restauración A→D, 4. Para un bob en PF1 de tres planos:

```
palabras = ceil((ancho + (x & 15)) / 16)
ticks_dibujo_y_restauracion = palabras * alto * 3 * (8 + 4)
```

| Caso completo, sin recorte | Palabras/fila | Ticks mínimos | Tiempo aproximado a 7,09 MHz |
|---|---:|---:|---:|
| Banzai 64×64, alineado | 4 | 9 216 | 1,30 ms |
| Banzai 64×64, desplazado 1–15 px | 5 | 11 520 | 1,62 ms |
| Rex, envolvente 20×32, alineado | 2 | 2 304 | 0,32 ms |
| Rex, misma envolvente, shift 13–15 | 3 | 3 456 | 0,49 ms |

Son cotas de transferencias; no son tiempos del ADF. No incluyen guardar
fondo, CPU, recargas de color, recortes ni competencia DMA. La fórmula
supone que fuente y máscaras permiten ese ancho; una ruta genérica con
palabra extra incondicional puede hacer más trabajo.

**Experimento E05.** Comparar máscara repetida por plano (un blit
entrelazado) contra máscara única y un blit por plano. No elegir solo por
tamaño del asset: tres lanzamientos pueden perder frente a uno. Recortar
márgenes transparentes manteniendo origen OAM, y medir desplazamientos
0–15; nunca completar con ceros que borren fuera del rectángulo válido.

### 16.5 ACE: un plan híbrido de cadenas y poses compartidas

**Evidencia.** [PR #292](https://github.com/AmigaPorts/ACE/pull/292)
usa encadenado DMA, necesita gap de una línea y no proporciona clipping
ni reasignación automática. Sus pruebas declaran vAmiga, AROS y **1 MB
chip**; no constituyen validación en nuestra configuración.
Los [descriptores de sprites adosados](https://github.com/AmigaPorts/ACE/blob/10ca68a321989738e9ac40f895bdd9f1d8e040fe/docs/programming/advancedmultiplexedsprites.md)
documentan 16 px/4 bpp = dos canales y 32 px/4 bpp = cuatro.

**Aplicación E02.** Mantener el diseño G2, pero permitir evaluar por
objeto una cadena DMA copiada cuando su recarga competiría con colores.
La cadena ahorra órdenes de recarga; cuesta copia y chip adicional.
Las poses compartidas hacen el intercambio contrario.

Elegir por el coste completo de la foto: copia, MOVEs, colores,
plazos y bobs evitados. Una cadena no libera los canales mientras se
dibujan sus píxeles. G0 ya mide gap 1 y el coste de copiar 1408 B;
no hace falta volver a demostrar el caso aislado. Falta probar
la combinación en las líneas saturadas por P51 y por el dibujo real.

No interpretar el éxito de un shooter de ACE como prueba de que
Rex de 20 px ocupe una columna: necesita dos, según G1/G2.

### 16.6 LSP: separar el tick del plazo de reactivar Paula

**Evidencia.** [LSP estándar/insane](https://github.com/arnaud-carre/LSPlayer)
intercambia código/memoria por coste de reproducción. Su media publicada
no es un máximo integrado. El [wrapper CIA, código leído](https://github.com/arnaud-carre/LSPlayer/blob/main/LightSpeedPlayer_cia.asm)
ejecuta el tick y arma después un timer B one-shot para escribir
DMACON. El comentario recomienda, para efectos ajustados, integrar el
tick en la interrupción existente y reactivar DMA después mediante copper.
Sus datos de eventos pueden vivir fuera de chip; el banco de muestras, no.

**Aplicación E08.** En D5, compilar offline los eventos SPC a comandos
de Paula, conservando el tick CIA independiente del render. Medir por
separado ISR principal y reactivación de canales. Usar timer o copper
solo tras comprobar plazos y recursos disponibles: O1 también usa CIA.

No copiar el retardo del wrapper como constante universal ni ocupar
silenciosamente sus dos timers. Auditar qué CIA y qué timer usa cada
rutina, incluido teclado, banco y juego. Un formato barato en media
puede concentrar KON, cambios de muestra y efectos en el mismo tick.

Probar tick normal, todas las voces reactivadas y un efecto robando el
cuarto canal durante el peor render. El límite ≤3 % incluye ISR,
reactivación y control de efectos; audio continuo al repetir foto O5.

### 16.7 GCC: primero ABI compatible, luego promociones de 16 bits

**Evidencia.** La [documentación oficial m68k](https://gcc.gnu.org/onlinedocs/gcc/M680x0-Options.html)
confirma que `-mshort` cambia `int` **y la alineación de argumentos en
stack**, incluso donde la API pide promoción a 32 bits. `-m68000`
selecciona el juego de instrucciones del 68000. Las opciones de forks
Amiga como baserel/regparm no se deducen de la documentación genérica.

**Corrección de §13.3:** no usar libc no elimina la incompatibilidad ABI:
tenemos asm, llamadas desde arneses, estructuras y retornos que verificar.
Un objeto ELF tampoco se integra sin comprobar relocaciones y arranque.

**Aplicación E07.** Primera comparación: vbcc contra GCC con tamaños y
llamadas compatibles, mismo C y mismos oráculos; luego estudiar `-mshort`
como variante aparte. Comprobar tamaños/alineaciones, parámetros de los
puentes, registros preservados y direcciones PIC/absolutas. Mantener el
modelo de datos explícito del port.

Pasar PC y binario 68000, no solo recompilar el verificador host.
Medir rutinas calientes y frame integrado con DMA. Un cambio que reduzca
código puede ganar por menos fetch aunque apenas cambie el contador
sin DMA; lo contrario también es posible.

### 16.8 SMBNeo/VS: C nativo rápido con traducción como oráculo

**Evidencia.** [SMBNeo](https://github.com/sabino/smbneo) porta SMB a
MC68000 con C y hardware Neo Geo. Su [edición VS](https://github.com/sabino/smbneo/blob/main/variants/vs/README.md)
documenta C directo para producción y conserva la traducción por
instrucciones como oráculo diferencial. Verifica estados PPU/APU y
orden de escrituras de audio, además del juego. Estas son declaraciones
del proyecto; no se ejecutó su suite en esta investigación.

**Aplicación (L1/X1/V2).** Sustituir una rutina caliente completa,
manteniendo una implementación de referencia y comparando efectos
observables. Antes de eliminar un temporal o una escritura OAM,
verificar si la siguiente rutina lo lee. Comparar también orden y
efectos de las escrituras, no solo posición final de Mario.

No extrapolar sus fps a una A500: comparten familia de CPU, pero el
reloj, memoria, vídeo y audio son distintos. No importar datos ni
relajar R9 según la política de ese repositorio. Lo transferible es
la separación entre referencia, implementación nativa y verificación.

### 16.9 Modulo Tricks y CPU Assisted Blitting: reutilizar o descartar con causa

**Evidencia.** [Modulo Tricks](https://www.powerprograms.nl/amiga/modulo-tricks.html)
reutiliza líneas de imagen mediante módulos y precalcula offsets ya
escalados. No prueba scroll de un nivel con paletas horizontales móviles.
[CPU Assisted Blitting](https://www.powerprograms.nl/amiga/cpu-blit-assist.html)
depende de acceso chip de 32 bits y se dirige a A1200 y similares.

**Aplicación.** En H1/H2, generar punteros/módulos del HUD offline y
reutilizar sus líneas constantes cuando la imagen exacta lo permita.
No reducir fetch de PF2 suponiendo que todas sus líneas son iguales:
comparar el bitmap antes. Una fila vacía puede apuntar a ceros; habilitar
su plano sigue costando DMA.

**Descartado para este port:** dibujar con CPU para ayudar al blitter.
Además de no compartir las ventajas del A1200, viola la convención
del proyecto. Tampoco eliminar esperas al blitter por analogía con
una demo sin probar ubicación del código, BLTPRI y todos los canales.

## 17. Experimentos priorizados y métricas de aceptación

Son propuestas vinculadas a las tarjetas existentes, **no tarjetas cerradas
ni un reemplazo del orden de ROADMAP**. Primero OAM+O5 integrado; G3–G9
siguen con sus dependencias. No se promete un porcentaje de mejora.

### 17.1 Matriz de trabajo

| ID | Experimento / tarjetas | Qué compara | Métrica que debe mejorar | Puerta de corrección / descarte |
|---|---|---|---|---|
| E01 | Perfil de DMA; O1/O3, G5 | Frame normal, columna, vuelta y recargas | Diagnóstico: tiempo por fase, esperas y ranuras disponibles | Reproduce banco conocido y perfil OCS/KS 1.2; no usar otro preset para aprobar |
| E02 | Multiplexado híbrido; G4–G6 | Poses compartidas vs cadenas por objeto | Menos bobs o menor preparación sin más fotos omitidas | Todos los píxeles OAM y prioridades exactos; copia y chip incluidos |
| E03 | Lotes del blitter; G7, columna | Configurar cada bloque vs conservar estado por lote | Máximo integrado, número de escrituras custom, espera total | Columnas/bobs exactos; estado reinstalado al cambiar usuario del blitter |
| E04 | Interior opaco; G3/G7 | Cookie-cut completo vs copia interior + bordes | Tiempo total para Banzai, incluidos lanzamientos adicionales | Todas las poses y shifts exactos; descartar si dividir aumenta coste |
| E05 | Recorte y máscara; G3/G7 | Máscara repetida/un blit vs única/tres blits | Chip final y peor dibujo/restauración | Origen, borde circular y recorte exactos; no premiar solo el asset menor |
| E06 | Restauración válida; G7/O5 | Fondo guardado, copia espejo o bloques reconstruidos | Coste total y memoria auxiliar | No leer una copia contaminada por otro bob; publicada intacta al abortar |
| E07 | GCC y ABI; L5 | Primero mismo ABI; `-mshort` después | Máximo lógica con OAM y coste integrado | RAM/mapa/ABI/PIC exactos, oráculos PC y 68000, regresión sin empeorar |
| E08 | Audio por eventos; A3–A7 | Tick, retrigger y efecto en distintas fases del haz | Máximo ≤3 %, jitter y ticks lógicos perdidos | Tempo independiente de fotos O5; muestras exactas según tolerancias D5 |
| E09 | Plan offline exacto; S5/S7 | Plan actual vs nuevas asignaciones de índices/ventanas | Máximo vuelta y palabras de lista escritas por foto | Píxeles iguales, ida/vuelta/cámara Y; no aproximar colores para pasar |
| E10 | Precálculo selectivo; S3/S5/C2 | Plantillas solo de zonas costosas vs construir todo | Pico de vuelta con bytes de memoria limitados | Datos CPU a slow; lista activa a chip; posiciones no grabadas también correctas |

**E06 requiere una cautela nueva para §14.7:** la segunda copia del
buffer circular no es un fondo limpio por definición. Si ambos espejos
reciben bobs, o una restauración lee píxeles dibujados por otro objeto,
contamina el fondo. Etiquetar regiones/columnas con versión de mapa y
buffer, o reconstruirlas desde bloques limpios. Primero restaurar todo
lo viejo, luego dibujar lo nuevo; contabilizar ambos pasos. Una foto O5
retenida no autoriza escribir en su PF1 ni en sus flujos DMA.

**E09 es una hipótesis nuestra**, inspirada en el precálculo de §3/§14:
la asignación de colores a índices puede admitir alternativas con igual
imagen y menos cambios. Optimizar registros que de verdad estén sin uso
en la ventana, incluidos sprites; no borrar un MOVE solo porque repita el
valor de una línea sin comprobar estado de entrada de ambas listas.
Evaluar el codo de P51, no una rejilla uniforme de seis planos.

**E10 no implica precalcular cada cámara.** Solo 49 500 B × 16 fases
serían 792 000 B de listas, antes de cubrir todo el nivel. Esa estrategia
no cabe en chip, y copiar desde slow sigue costando bus. Medir plantillas
parciales de los postes y los bytes reales que habría que copiar/parchear.
No codificar frames del replay: la selección depende de cámara/mapa.

### 17.2 Qué debe guardar cada medición

1. Commit y hash del binario/datos, flags (`SPR_OAM`, O5, BENCH), versión
   de WinUAE, ROM y configuración exacta. Baseline A y candidato B iguales
   en todo salvo la modificación. Assets y capturas quedan en `work/` (R9).
2. Escenario reproducible: cámara x/y y sentido, entradas, poses,
   solapes, cantidad de columnas, bobs, cambios de mapa y estado del audio.
   Incluir vuelta en s≈4580, Banzai, Mario grande, solapes y HUD activo.
3. Tiempo integrado por foto y por tick lógico; media, p99, máximo,
   fotos omitidas, mayor racha, edad de la foto mostrada y ticks perdidos.
   Separar fps de imagen de frecuencia de lógica. La latencia de foto
   importa aunque no cambie el estado simulado.
4. DMA por fase del haz, CPU preparando, espera al blitter, número y
   ancho de blits, MOVEs del copper y bytes escritos/copias. No sumar
   porcentajes DMA a tiempo transcurrido como si fueran trabajo independiente.
5. Pico de chip/slow **en vivo**, incluyendo alineación, bancos de 64 KiB,
   segundo PF1, tres fotos O5, listas, muestras, tablas e inicialización.
6. Regresión, reconstrucción exacta OAM y captura cycle-exact contra
   referencia. Para cambios del terreno, también comparación apilada contra
   `SuperMarioWorldMap02.png`. Si no hay evidencia integrada, queda pendiente.

Los escenarios sintéticos sirven para aislar causas, pero **aprobar una
optimización exige volver al juego integrado**. Con DMA, una ganancia
en Musashi puede convertirse en una espera igual o mayor.

### 17.3 Qué conviene intentar primero

- **Medición inicial hecha:** OAM+O5 pasa el objetivo de lógica en el
  replay probado, sin incidencias COPER detectadas y sin aumentar las
  fotos omitidas; ver [informe](medida-oam-o5.md). E01 sigue pendiente
  como perfil de ranuras DMA, y falta el renderer final.
- **Durante G3–G6:** E02/E05, con comparación exacta de píxeles y coste de
  chip; evitar construir una solución que dependa de ventanas inexistentes.
- **Después de C2/C4, en G7:** E03/E04/E06. La mejora de bobs todavía
  es potencial: los enemigos no se dibujan en el ADF vigente.
- **En audio:** E08 desde el primer driver, no después de integrar música.
- **Sesión acotada de S5:** E09/E10 sobre el pico de vuelta. Si no ganan,
  conservar O5 y registrar el resultado; no bajar fidelidad por iniciativa propia.
- **L5:** E07 si el perfil identifica lógica como limitante; no mezclar
  migración de compilador, ABI y reescritura de rutinas en una sola prueba.

## 18. Trazabilidad y límites de la ampliación

### 18.1 Registro de fuentes consultadas el 2026-10-05

| Fuente primaria | Qué se leyó | Evidencia / límite |
|---|---|---|
| [Bartman/Abyss README](https://github.com/BartmanAbyss/vscode-amiga-debug) y [releases](https://github.com/BartmanAbyss/vscode-amiga-debug/releases) | Perfilador CPU/DMA, debugger gráfico, presets | Capacidades publicadas; no se instaló ni se probó nuestro ADF |
| [Power Programs: Dual Layer Graphics](https://www.powerprograms.nl/amiga/dual-layer.html) | Comparativas, buffers, agrupación y preparación | Experimento del autor; geometría y distribución de planos diferentes |
| [Power Programs: Fast Bobs](https://www.powerprograms.nl/amiga/dpl-fastbobs.html) | Algoritmo, restricciones y rendimiento publicado | La mejora depende de PF vacío y separación; no aplica globalmente a YI1 |
| [Power Programs: Free Form Sprite Layer](https://www.powerprograms.nl/amiga/spr-layer.html) | Coste de sprites/copper y scroll del layer | No usar sus cuentas PAL como calibración nuestra: las páginas manejan distintos totales de líneas/ciclos |
| [Power Programs: Modulo Tricks](https://www.powerprograms.nl/amiga/modulo-tricks.html) | Fórmulas, repetición de líneas y precálculo | Demo específica, no sustituto de `build_mid` |
| [Power Programs: CPU Assisted Blitting](https://www.powerprograms.nl/amiga/cpu-blit-assist.html) | Hardware y condiciones del método | Ventaja de bus de 32 bits; descartado en A500 y por convención del port |
| [ACE PR #292](https://github.com/AmigaPorts/ACE/pull/292) | Descripción, límites y condiciones de pruebas | PR abierta al consultar; no afirmar integrada ni probada en 512 KB chip |
| [ACE documentación fijada en `10ca68a`](https://github.com/AmigaPorts/ACE/blob/10ca68a321989738e9ac40f895bdd9f1d8e040fe/docs/programming/advancedmultiplexedsprites.md) | Formato, columnas y canales | Referencia reproducible; no se ejecutó el gestor |
| [LSP README](https://github.com/arnaud-carre/LSPlayer) | Modos estándar/insane y benchmark | Coste publicado, no medida de nuestro tema ni de ISR completas |
| [LSP wrapper CIA](https://github.com/arnaud-carre/LSPlayer/blob/main/LightSpeedPlayer_cia.asm) | Código de tick, timers y reactivación DMA | Se leyó implementación; no se portó ni se copió |
| [GCC, opciones M680x0](https://gcc.gnu.org/onlinedocs/gcc/M680x0-Options.html) | `-m68000`, `-mshort` y convenciones | Documentación genérica; forks y puentes requieren comprobación local |
| [SMBNeo README](https://github.com/sabino/smbneo) | Arquitectura y problemas observados en hardware | Otro presupuesto de CPU/memoria/vídeo; no demuestra fps en Amiga |
| [SMBNeo VS README](https://github.com/sabino/smbneo/blob/main/variants/vs/README.md) | C directo, oráculo y pruebas diferenciales | Método trasladable; tests ajenos no ejecutados |
| HRM: [canales](https://www.amigadev.elowar.com/read/ADCD_2.1/Hardware_Manual_guide/node011B.html), [máscaras](https://www.amigadev.elowar.com/read/ADCD_2.1/Hardware_Manual_guide/node011F.html), [regiones](https://www.amigadev.elowar.com/read/ADCD_2.1/Hardware_Manual_guide/node0121.html) | Extractos indexados del manual de Commodore | Las aperturas directas fallaron; no se presenta como lectura completa del capítulo |

Los enlaces a `main/master` pueden cambiar. Antes de reutilizar código
o reproducir una cifra, fijar commit/versión y licencia. En esta ampliación
se incorporan explicaciones y propuestas, sin código ni assets de terceros.

### 18.2 Búsquedas que no justifican una implementación todavía

- **Solid Gold:** localizado el paquete del autor en
  [Aminet](https://aminet.net/package/game/jump/SolidGold.adf), pero lectura
  bloqueada (403); la entrevista devolvió 429. No se descargó ni auditó su
  motor. Pendiente: restauración, scroll vertical y distribución de memoria.
- **Agony:** encontrados anuncios de archivo de fuentes y descripciones;
  no se obtuvo el archivo original del autor ni se leyó el motor.
  No atribuirle un algoritmo de restauración por deducción de un vídeo.
- **Tiny Bobble/Tinyus:** no se obtuvo fuente original del juego en esta
  búsqueda. El código de un instalador WHDLoad no es el motor del juego.
  El antecedente de doble lista de §12.6 sigue teniendo alcance de testimonio.
- **Sonic AGA/Scorpion:** los resultados encontrados no demuestran el
  objetivo OCS/512 KB chip + A501 a 50 Hz. No incorporarlos como garantía.
- **Copperline:** permanece candidato de §14.9; no se verificó su exactitud
  contra nuestros bancos. No reemplaza WinUAE de referencia para cerrar puertas.
- **EAB:** no se volvió a leer íntegramente todo el foro. Las limitaciones
  de acceso del relevamiento anterior permanecen; no completar citas de memoria.

**Resultado de esta ampliación:** hay diez experimentos acotados y varias
correcciones de aplicabilidad. La investigación amplía las opciones medibles;
los objetivos ≤25 % scroll, ≤40 % lógica, ≤8 % preparación de sprites y
≤3 % audio siguen siendo puertas del port, no resultados obtenidos aquí.

---

## 19. Los diez escaparates del A500, vistos por dentro (2026-10-06)

> Lista pedida por el usuario: Lionheart, Agony, Shadow of the Beast,
> Ruff 'n' Tumble, Kid Chaos, Elfmania, Disposable Hero, Apidya,
> Turrican II y Jim Power. Se añadió Robocod porque §2.1 y §5.3 ya se
> apoyan en él.
>
> **De dónde sale cada dato.** Casi ningún autor documentó su motor. La
> fuente principal es la serie de vídeos **"How Amiga Games Work"**
> (canal `@psquaredish`, 72 episodios). Cada juego se inspecciona con el
> depurador **Engine9000** (alpine9000): se apagan planos y sprites uno a
> uno, se "bloquea" el copper a partir de una línea y se ven el
> visualizador de blits, los de paleta y copper, las ranuras DMA y los fps.
> Se leyeron las transcripciones automáticas de los episodios 1 y 36
> (Lionheart), 4 (Agony), 5 (Beast), 7 (Kid Chaos), 8 (Turrican II), 13
> (Jim Power), 18 (Apidya), 27 (Disposable Hero), 41 (Robocod) y 48
> (Elfmania), bajadas con `yt-dlp` y `youtube-transcript-api`. Son
> **observaciones de un emulador (libretro-uae)**, narradas por quien no
> programa ("I'm not a coder myself"). Valen como "qué registro cambia y
> dónde", no como cifras de ciclos. Donde había fuente escrita se
> contrastó: Codetapper para Agony, Beast y Jim Power, y Wikipedia y
> entrevistas para Ruff 'n' Tumble y Kid Chaos. **Ruff 'n' Tumble no
> tiene episodio** y su motor queda sin documentar.

### 19.1 Qué hace cada uno

| juego | modo de pantalla | sprites de hardware | copper | blitter / fps |
|---|---|---|---|---|
| **Lionheart** (1993) | DPF 3+3, pero **cambia el número de planos por bandas**: 5 arriba, 6 solo donde están las montañas, 5 y 4 abajo (visto en el mapa DMA). Otros niveles: 16 colores normales (4 planos) o EHB | héroe = 2 pares adosados (32 px, 15 colores); el agua es **un sprite de 3 colores repetido en horizontal**; HUD con sprites (0/1 pasan de corazones a "pausa"); la bestia montada usa **los 8 sprites**; la luna en 6/7 con COLOR29-31 recargados | en los niveles de 16 colores **copperiza los 15 colores, uno por línea en rotación** (1, 2, … 15, vuelve a 1): degradados suaves, 70-190 colores en pantalla, **con scroll en 8 direcciones**. Paralaje de fondo **por línea** cambiando `BPLxPT`. Cambia la prioridad (`BPLCON2`) en una franja para que un trozo del fondo pase delante | poco blitter (héroe en sprites): enemigos y columnas nuevas. DMA total ≈ ½ del frame |
| **Agony** (1992) | DPF, el fondo **partido en 1 plano (fondo fijo) + 2 planos (medio)**: tres capas | búho = 4 sprites (2 pares adosados, 32 px). Balas en 4/5. Lluvia y pociones **comparten** 6/7 porque el diseño nunca las pone a la vez | degradado en la capa de 1 plano. **Paleta del PF delantero cambiada por franjas horizontales**: los enemigos de arriba y los de abajo tienen paletas distintas, y **el diseño del nivel no los deja cruzar la línea** (en los niveles 3, 5 y 6 se les escapa y cambian de color) | ~26 blits por frame; 50 fps fijos en el emulador; DMA ≈ ¾ |
| **Shadow of the Beast** (1989) | DPF 3+3, 13 franjas de paralaje | héroe = 4 sprites, **6 al estirar brazo o pierna**. Los enemigos-sprite van todos en 6/7 (32 px, 3 colores). El juego **impide la patada mientras vuela el plasma**: no quedan canales | **cambia los 7 colores del PF delantero en la línea exacta del suelo** para el bob que pasa, y vuelve a la paleta del suelo en su pie. Bobs con paletas distintas **separados al menos una pantalla**. Prioridad de sprites cambiada por franja | columna de 16 px al ir en horizontal; **en vertical re-blitea la pantalla entera** y aun así va a 50 fps |
| **Kid Chaos** (1994) | DPF **3+2** (5 planos) | Kid (2 pares adosados) + marcador en el mismo canal más abajo | **colores copperizados también en el PF delantero**: un índice vale rojo, naranja y luego azul según la línea. El nivel está pintado para que dos variantes **nunca compartan línea**: no hay ladrillo de color en la línea del agua. **La lista se reescribe al mover la cámara en vertical**: el visualizador la ve cambiar al subir y bajar | columnas nuevas en 2 bordes a la vez (8 direcciones); solo se blitea lo animado. 50 fps |
| **Jim Power** (1992) | DPF arriba; **desde el suelo hacia abajo otra pantalla de 16 colores** abierta por copper (`BPLxPT`) | **fondo entero con 2 sprites (6/7) reposicionados cada 16 px** a lo ancho de la línea; disparos en 4/5 (máximo 2); héroe ≤ 32 px | lista **fija**: no es de 8 direcciones. Prioridad cambiada por franja; en el jefe final, `BPLCON1` y módulos por línea | **los jefes grandes son un playfield entero que se mueve**; solo se blitean sus partes móviles. 320×256 a 50 fps |
| **Elfmania** (1994) | 5 planos (32 colores) arriba; **`BPLCON0` baja a 4 planos** en la franja de abajo, con la misma paleta repetida para que no se note el corte | fondos (peces, postes, la luna) con **pares adosados multiplexados en horizontal y en vertical**; nunca más de 4 objetos-sprite por línea. Pantalla de 288 px **para que entren los 8 sprites** | agua: en un solo playfield el scroll por línea deformaría a los luchadores, así que **lo hace con blits de franjas finas**. Abajo, donde no hay personajes, usa `BPLCON1` y módulos por línea | luchadores troceados en blits por parte del cuerpo. Concesión: **las animaciones de fondo se paran cuando hay mucho trabajo**. 50 fps |
| **Disposable Hero** (1993) | 32 colores; en el último nivel la pantalla **cambia de modo a mitad**: 32 colores, 8 y una franja DPF para la lava | marcador y recuadro multiplexados en horizontal; disparos mejorados en 0/1 (multiplexados en vertical); estrellas en un solo canal | **reflejo del agua: módulo negativo + todos los colores teñidos a partir de una línea que se mueve** con el objeto (63-95 colores). Un "edificio" que en realidad son barras de COLOR00 | todo lo demás por blitter, 50 fps. El autor: carga máxima "at all times" sin caer de 50 fps; las armas están diseñadas para que nunca se pasen |
| **Apidya** (1992) | **cada nivel con otra configuración**: 32 colores con franjas de 16 arriba y abajo, DPF con deformación de `BPLxPT`, 16 colores a 256×192 | fondos (trigo, engranajes) con **los 8 sprites repetidos cada 128 px** por copper; el jugador es bob en unos niveles y sprite en otros | partición de paleta en la línea del agua: **los enemigos no la cruzan, pero los colores del jugador quedan fijos** en ambos lados. Partición de la lista para enganchar arriba con abajo (scroll vertical infinito) | el pez gigante es pantalla, no blit; solo se blitean aletas y jinete. 50 fps |
| **Turrican II** (1991) | **4 planos, 16 colores, sin DPF** | solo el jugador (y en la nave, 6 sprites + 2 de plasma). El HUD no es de sprites | casi nada | **todo por blitter**; el paralaje de la nave se hace blitteando **solo las franjas que se mueven, a 2 planos**, y solo donde se ve el fondo. El puente se blitea **solo en la parte pisada**; ~4 blits a la vez. 50 fps |
| **Robocod** (1991) | 16 colores **repetidos dos veces en la paleta de 32**: el 5.º plano es un fondo de 1 plano que no altera el resto | **cada objeto pasa de bob a sprite y vuelve** según las bandas (≤ 32 px de alto, sin cruzar el borde de la banda). Se vio a 8 sprites en una línea y, al saltar, dos enemigos volviendo a bob | 2 colores con degradado (6 y 22) | el plano de fondo solo se re-blitea **al cruzar 16 px**. Excepción documentada: baja a 12,5 fps con el cuerpo estirado |
| **Ruff 'n' Tumble** (1994) | 32 colores (las afirmaciones de foro de que es EHB **no están verificadas**) | — | — | **renunciaron al paralaje** "to make the game fast and playable"; fondos difuminados para dar profundidad. Sin análisis técnico publicado |

### 19.2 Lo que se repite, y qué significa para nosotros

1. **Nadie mueve cargas de color en horizontal con el scroll.** Lo
   confirma §3.1 con diez casos más. Hasta Lionheart y Kid Chaos, los
   que más color sacan en un nivel de 8 direcciones, cambian colores
   **por línea, según la Y del nivel**. Cuando la cámara se mueve en
   vertical se reescribe la lista; en horizontal no cambia nada. `build_mid`
   sigue siendo una técnica sin precedente comercial encontrado.
2. **El diseño del nivel paga las franjas de paleta**: Agony, Beast,
   Kid Chaos y Apidya separan los objetos de paletas distintas (una
   pantalla de distancia, o "no cruza la línea del agua"). Nosotros no
   podemos rediseñar YI1 (1:1). Por eso las bandas solo de Y siguen siendo
   el **plan B con pérdida** de §3.1, no un atajo.
3. **El sprite de Mario con colores fijos es lo que hace Apidya**: sus
   colores no cambian al cruzar la partición y los de los enemigos sí.
   Es nuestro D8/D9 (Mario en 17-31 fijos y los demás recargados por
   línea). El aviso de Lionheart (§3.1) es el mismo que ven Agony en los
   niveles 3, 5 y 6 y Beast con sus bobs: **un objeto que cruza la línea
   de recarga cambia de color**. `copsim.py` tiene que seguir comprobándolo.
4. **El número de planos no es fijo en toda la pantalla.** Lionheart
   (4/5/6/5), Elfmania (5→4), Kid Chaos (DPF 3+2), Disposable Hero
   (32→8→DPF) y Jim Power (DPF→16 colores) cambian `BPLCON0` o la
   distribución por franjas. Es la idea nueva más aprovechable (§19.3, E11).
5. **Un sprite repetido a lo ancho de la línea** (Lionheart, Jim Power,
   Apidya, Elfmania y Risky Woods en §3.1) da una capa entera con un
   par de canales. Exige que **ningún otro objeto use esos canales en
   esas líneas** (en Jim Power, como mucho 2 disparos y un héroe de 32 px).
6. **Los objetos grandes no se blitean enteros.** Jim Power y Apidya
   convierten al jefe en un playfield que se mueve; Turrican II y Kid
   Chaos blitean solo la parte que cambia. Elfmania deja quietas las
   animaciones de fondo cuando no llega. Todos degradan algo **elegido de
   antemano**; ninguno deja que el frame caiga al azar.
7. **Sprite o bob se decide por objeto y por frame**: Robocod (bandas),
   Beast (enemigos en 6/7 y bloqueo de la patada), Agony (lluvia y pociones
   nunca juntas). Coincide con §5.3 y `d8demote`. Lo nuevo es la **regla de
   exclusión explícita**: cuando los canales no alcanzan, el juego
   prohíbe la combinación en vez de perder un objeto.

### 19.3 Cómo lo podemos implementar

En orden de lo que más mueve el presupuesto. Todos son **experimentos con
puerta**, como en §17; ninguno se ha probado en el port.

**E11 — Menos planos donde PF2 no los usa (Lionheart, Elfmania, Kid
Chaos).** La primera fila no depende de la cámara: es la recarga de 16
colores por línea de `build_mid` (P39/P42) y vale para cualquier línea.
En DPF de 6 planos el copper tiene **una ranura cada 16 px**; con 5,
cada 12 (roondar, §3.1) y con 4, cada 8.

- **Medir primero, sin tocar el juego.** En `mkleveld.py` (o en una
  herramienta aparte), para cada línea de pantalla y cada cámara del
  recorrido del oráculo, buscar el **índice máximo de PF2** usado:
  - si es ≤ 3, basta con 2 planos de PF2 (DPF 3+2, como Kid Chaos);
  - si es 0, PF2 está vacío en esa línea.

  Con el mismo recuento sale cuánto `build_mid` gana con el
  copper a 12 px en esas líneas (P51 ya mostró cuánto cambia el modelo
  con más ranuras libres). Si en YI1 casi no hay líneas así (el cielo
  de capa 2 con colinas probablemente ocupa casi todo), **se descarta con
  el número** y se anota en §18.2.
- Si da, el plan del copper escribe `BPLCON0` (5 o 6 planos) al principio
  de cada franja, en el borrado horizontal, y `copsim.py` modela el cambio
  de ranuras por línea. Detalles: con 5 planos en DPF, PF2 solo lee los
  planos 2 y 4, así que en esas líneas sus píxeles tienen que caber en
  los índices 0-3 de PF2 (es lo que mide el recuento). Y `BPL6PT` no
  avanza mientras el plano está apagado: hay que recargarlo al volver a
  6 planos, como ya se hace con los punteros en la partición vertical.
- **Puerta:** píxeles iguales (capturas cycle-exact contra la referencia y
  `cmp_ref.py` sin cambios), ida/vuelta/cámara Y. Métrica: el pico de vuelta
  y las fotos omitidas con el protocolo de §17.2. Una franja depende de la
  Y de la cámara (como en Kid Chaos), así que la lista se rehace al moverse
  en vertical: entra en el mismo mecanismo que S8/§12.1.

**E12 — Colores de PF1 por línea con el nivel, sin pérdida (Kid Chaos,
Lionheart).** Es lo que E09 (§17.1) llamaba "asignación de índices".
Kid Chaos muestra que puede hacerse **en un nivel de 8 direcciones a 50
fps** si las variantes de un índice nunca comparten línea. Nosotros no
elegimos el arte. Lo que sí podemos hacer es buscar en el plan offline los
índices de PF1 cuyas variantes **por casualidad** nunca comparten línea en
YI1, y pasarlos de carga a mitad de línea (`build_mid`) a carga en el borrado
según la Y del nivel. Solo se aceptan los que dan píxeles iguales; los
demás siguen en `build_mid`. Puerta: la de E09. Si no hay suficientes
índices así, el número cierra la idea.

**E13 — Cambiar la prioridad por franja (Lionheart, Beast, Jim Power).**
Lionheart pone un trozo del fondo **delante** del PF1 cambiando
`BPLCON2` en una franja. Es la herramienta para tiles de **capa 2 con
prioridad sobre capa 1** o para sprites detrás del terreno en una zona,
si YI1 los tiene. **Sin caso confirmado en YI1**: anotarlo en `docs/plan-tecnico.md`
como recurso y no abrir tarjeta hasta que una comparación 1:1 lo pida.

**Banzai Bill (§16.4), dos opciones a medir junto con E04:**

- **Con sprites, como la bestia de Lionheart**: 64 px de ancho = 4 pares
  adosados = **los 8 sprites**, 15 colores. Solo sirve si en sus 64
  líneas no hay nadie más en sprites. Mario sí puede estar en esas
  líneas, así que por sí sola **no basta**. Como mixto al estilo Robocod
  ("sprite cuando cabe, bob cuando no"), el coste en el peor caso sigue
  siendo el del bob. Vale si reduce las fotos omitidas en el replay de
  estrés (`oracle_stress_sprites`), no por el caso medio.
- **Como playfield, como los jefes de Jim Power**: **no se traslada**. PF2
  ya lleva la capa 2 y PF1 el terreno. Descartado por D8.

**HUD (D11, H2-H4) — una alternativa para comparar, no para reemplazar.**
Lionheart, Kid Chaos, Disposable Hero y Robocod hacen el marcador con
sprites, multiplexados en horizontal por copper. Para nosotros eso
**gasta los canales en y = 0..35** (`docs/medida-hud.md`), donde Mario y
los enemigos sí pueden estar. Haría falta comprobar en los oráculos
si alguna OAM entra en esa banda. El overlay de D11 no tiene esa
restricción. Queda solo como medida comparativa si el overlay sale caro
en H2.

**Degradar algo elegido de antemano (Elfmania, Robocod), para O5.**
Elfmania deja quietas las animaciones de fondo cuando no llega; Robocod
re-blitea el plano de fondo solo al cruzar 16 px. En el port, el
equivalente sería **retrasar la animación de tiles** (moneda de Yoshi
P22/P23, bloques `?`) un frame en las fotos que vienen justas, con la
lógica a 50 Hz intacta (O5). **Choca con el criterio 1:1**: es una
diferencia visible, aunque mínima. Solo se plantea al usuario con los
números de D1-medida, junto al plan B de 25 Hz de ROADMAP §3, nunca por
iniciativa propia.

**Lo que no se traslada, y por qué:**

- **Copperizar los 15 colores por línea en rotación (Lionheart):** da
  degradados donde el arte original no los tiene. Contradice el 1:1.
- **Fondo de 1 plano con paleta duplicada (Robocod, Agony):** la capa 2
  de SMW tiene más de 2 colores por línea. Ya la resuelve PF2 en
  hardware (D8).
- **Sin paralaje (Ruff 'n' Tumble), 4 planos sin DPF (Turrican II):**
  más rápidos, pero sin la capa 2 que D8 decidió mantener.
- **Reflejo con módulo negativo (Disposable Hero), agua con blits por
  franja (Elfmania):** YI1 no tiene agua. Quedan para niveles futuros
  (`docs/mas-alla-yi1.md`).

### 19.4 Engine9000 como herramienta (diagnóstico, no medida)

[alpine9000/engine9000-public](https://github.com/alpine9000/engine9000-public)
es emulador (fork de libretro-uae) y depurador. Tiene justo lo que se usa en
los vídeos: apagar planos y sprites, bloquear el copper desde una línea,
visualizadores de blitter, copper, paleta y DMA, fps, depuración en fuente
(ELF o stabs) y un **"smoke tester"** que graba un escenario, lo repite y
compara vídeo y audio. Tiene periféricos de depuración en `$FC0000`-`$FC0300`:
salida por consola, checkpoints de perfilado y contadores que se ven en la
barra de estado. En `$B7E928` se lee el **contador de ciclos ÷ 4**.

Para el port:

- **Útil para ver** si una franja de E11/E12 cambia lo que se cree, o qué
  sprite ocupa qué canal en un frame de G5a. Es lo mismo que haríamos
  a mano con capturas, pero interactivo.
- **No sirve para cerrar puertas:** AGENTS §11 exige `a500.uae` en WinUAE.
  Los vídeos marcan que el juego va "más lento en el depurador", y los
  fps que muestra no son una medida nuestra.
- Las escrituras a `$FC0000` caen en la zona de la ROM. Si se usan, irían
  tras un flag de compilación (como `-DBENCH`) y nunca en el ADF que se
  mide. El soporte de Windows es vía MSYS2 y el autor dice que está "poco
  probado".
- Lo mismo vale para §16.1 (Bartman): las dos herramientas solo sirven
  de diagnóstico.

### 19.5 Experimentos nuevos (se suman a §17.1)

| ID | Experimento / tarjetas | Qué compara | Métrica que debe mejorar | Puerta de corrección / descarte |
|---|---|---|---|---|
| E11 | Planos por franja; S5/S7, `build_mid` | DPF 3+3 en toda la pantalla vs 3+2 o 3+0 donde PF2 lo permite | Primero: líneas aptas por cámara (herramienta offline). Después: pico de vuelta y fotos omitidas | Píxeles iguales, ida/vuelta/cámara Y; descartar con el recuento si las líneas aptas no alcanzan |
| E12 | Índices de PF1 por Y; S7/E09 | Carga a mitad de línea vs carga en el borrado para los índices sin conflicto en la misma línea | Palabras de lista por foto y pico de vuelta | Solo índices que den píxeles iguales en todas las cámaras posibles, no solo las grabadas |
| E13 | Prioridad por franja; D8 | — | — | Sin caso en YI1; se abre solo si una comparación 1:1 lo pide |
| E14 | Banzai en 8 sprites; G7/§16.4 | Bob (E04) vs sprite cuando las líneas están libres | Fotos omitidas en `oracle_stress_sprites` | OAM y prioridades exactas; el peor caso no puede empeorar |

### 19.6 Fuentes de esta sección

| fuente | qué se usó | límite |
|---|---|---|
| "How Amiga Games Work" (`youtube.com/@psquaredish`): [Lionheart](https://www.youtube.com/watch?v=sk2tDtYSEqY), [Lionheart, niveles posteriores](https://www.youtube.com/watch?v=KoccBs7ItLo), [Agony](https://www.youtube.com/watch?v=_PHwir4xb3Q), [Shadow of the Beast](https://www.youtube.com/watch?v=_2NIkR0kRa0), [Kid Chaos](https://www.youtube.com/watch?v=D6JSY0pFhf0), [Turrican II](https://www.youtube.com/watch?v=4XueETgTXio), [Jim Power](https://www.youtube.com/watch?v=sxLp8yqgvR8), [Apidya](https://www.youtube.com/watch?v=eZZlTuQAwvQ), [Disposable Hero](https://www.youtube.com/watch?v=qdrgFQSJs9Q), [Robocod](https://www.youtube.com/watch?v=B81xfOHT6dA), [Elfmania](https://www.youtube.com/watch?v=zQuiCQzvX64) | Transcripciones automáticas, leídas completas | No se vieron las imágenes; un dato que solo está en pantalla no entra. Observación en emulador, narrador no programador |
| Codetapper: [Agony](https://codetapper.com/amiga/sprite-tricks/agony/), [Shadow of the Beast](https://codetapper.com/amiga/sprite-tricks/shadow-of-the-beast/), [Jim Power](https://codetapper.com/amiga/sprite-tricks/jim-power/) | Reparto de planos y sprites, lista del copper | Coincide con los vídeos (Agony: fondo a 25 fps, agua de 12 frames cada 4) |
| [Engine9000](https://github.com/alpine9000/engine9000-public) | README: funciones y periféricos de depuración | No se instaló ni se probó con nuestro ADF |
| [Wikipedia, Ruff 'n' Tumble](https://en.wikipedia.org/wiki/Ruff_%27n%27_Tumble) (cita The One y Amiga Power, 1994) | La decisión de no hacer paralaje | Sin detalle del motor |
| [Andrew Morris (amigapd)](https://www.amigapd.com/interview-andrew-morris.html), [Super Adventures, Kid Chaos](http://superadventuresingaming.blogspot.com/2023/02/kid-chaos-amiga-part-1-guest-post.html) | "3 colour backgrounds … closer to 100 colours", utilidades propias | Sin detalle de programación |
| [Hardcore Gaming 101, Disposable Hero](https://www.hardcoregaming101.net/disposable-hero/) | Objetivo de 50 fps con carga máxima; armas pensadas para no pasarse | Entrevista indirecta |

**Buscado y no encontrado:** una entrevista técnica de Jason Perkins
(Ruff 'n' Tumble), Shaun Southern (Kid Chaos) o Erwin Kloibhofer
(Lionheart). La página de Thalion Source (`home.wtal.de`) no resuelve.
El hilo de EAB "Lionheart Parallax question" (t=59490) devuelve la
protección anti-bots, igual que en §10.

---

## Fuentes del relevamiento original (§1–§14)

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
