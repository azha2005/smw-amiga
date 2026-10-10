# Investigación: técnicas de la demoscene de Amiga aplicables al port

2026-10-10. Relevamiento solicitado por el usuario. **Informe de investigación,
sin implementación ni nuevas medidas de rendimiento.**

> **Actualización post-L2 (2026-10-10, más abajo §11):** este relevamiento
> se hizo contra S9. Después de L2 el orden de prioridades cambia: el
> speedcode de poses de Mario baja, y el speedcode aplicado a `build_mid`
> pasa a ser la candidata, condicionado al perfil de estrés.

## 1. Conclusión y alcance

Sí hay técnicas que el port emplea parcialmente y otras que no aparecen en
las rutas de juego examinadas. La candidata más interesante es **generar
código 68000 especializado para operaciones de dibujo conocidas** (speedcode).
Otra posibilidad es que el **copper lance cadenas de blits** en ventanas
reservadas. Ninguna fuente permite afirmar que estas técnicas cerrarían D1.

Se revisaron fuentes y explicaciones de autores de demos, además de los
documentos y código del proyecto. No se descargaron archivos al workspace,
no se ejecutaron demos ni se modificó código durante el relevamiento.
Este informe conserva los resultados de esa consulta; no es un estudio
exhaustivo de todos los archivos de la demoscene.

La comparación usa dos árboles:

- `C:/Users/JC/Downloads/sma/port-amiga`: documentación y código del checkout
  principal, donde se guarda este informe.
- `C:/Users/JC/Downloads/sma/wt-g2t-b2bis-1008`: worktree abierto en el IDE,
  cuyo `PROXIMO.md` e informes ya incluyen R1 y S9 del 2026-10-10.

Este documento no cambia decisiones ni abre tarjetas. El trabajo autorizado
para la implementación sigue definido en `PROXIMO.md` del árbol correspondiente.

## 2. Estado del port contra el que se comparó

El worktree contiene avances posteriores a los informes del checkout principal.
Según `docs/informe-g5l-r-s9-1010.md` del worktree:

| medida WinUAE PAL cycle-exact | T2 | R1 | S9 |
|---|---:|---:|---:|
| BENCH, fotos perdidas | 66 | 53 | 36 |
| VBTRACE, fotos omitidas | 25 | 17 | 12 |

BENCH y VBTRACE tienen instrumentación diferente: sus cifras no deben
compararse entre sí. D1 sigue roja; el informe usa un objetivo de ≤ 5 omitidas.

**S9 ya comparte el trabajo entre listas:** copia las cargas de una línea de
la lista anterior cuando siguen siendo válidas, con una copia desenrollada;
reconstruye el salto propio y deja fuera los sufijos de G5L.
**S5 se probó y se descartó:** las variantes ensayadas aumentaron la media
o no redujeron suficientemente el pico. No se propone repetirlas como si
fueran una técnica pendiente de descubrir.

Según `docs/informe-g5l-r-l1-1010.md` del worktree, el costo de la lógica
está distribuido: la función más cara representa 6,5 % y muchas rutinas
ya son asm manual. El modelo de cola estima que reducir toda la lógica
20 % permitiría llegar a 2-5 saltos. **Es una estimación del modelo, no un
ahorro demostrado ni una medida de las técnicas de este informe.**

El mismo informe registra 24 856 B libres de chip en el vivo y 57 692 B
por lista adicional. La memoria también limita cualquier precálculo.

## 3. Speedcode: compilar datos conocidos en instrucciones

### Evidencia de terceros

En [Inside the Machine, explicación del autor](https://blog.grahambates.com/posts/inside-the-machine/#speed-code),
Graham Bates describe cómo sustituir un bucle que interpreta una tabla de
offsets por instrucciones con esos offsets incorporados. La rutina
[`GenerateTable` en `common/table-2x2.asm`](https://github.com/grahambates/inside-the-machine-public/blob/main/common/table-2x2.asm)
genera código a partir de tablas de deltas; se leyó su implementación.

El principio es preparar instrucciones concretas en lugar de leer un índice,
calcular una dirección y decidir la operación en cada iteración. La demo
lo aplica a efectos de tablas de textura; eso no constituye una medida
directamente trasladable a un motor de sprites.

### Diferencia con el port

El port ya tiene asm y bucles desenrollados: composición de tiles en
`mspr68k.s`, operaciones de G5L y copia de líneas S9. También existen fuentes
generadas por herramientas. **Generar una traducción de lógica o desenrollar
un bucle no equivale necesariamente a especializar el dibujo por pose.**

En las rutas examinadas no se identificó un banco de rutinas de composición
por pose que elimine la interpretación de todas sus fichas y máscaras.
Esta observación se limita al código revisado; no afirma que el proyecto
carezca de toda forma de especialización.

### Aplicación propuesta — hipótesis

Investigar un conjunto pequeño de rutinas de composición para poses de Mario,
con offsets, máscaras y combinaciones conocidos, manteniendo variables los
punteros GFX que realmente cambian. Un lugar relevante es el fallo de caché
durante el daño de Mario, donde el informe L1 registra más costo de `mspr_draw`.

La rutina especializada debe consumir las mismas entradas gráficas que la
actual: no puede fijar contenido que cambie, confundir pose con estado
lógico ni reutilizar una clave que ignore punteros GFX necesarios (P116).

No conviene generar una rutina para cada combinación de cámara y enemigos:
el espacio de estados crece y el costo de preparar código puede comerse el
ahorro. Generación offline o al cargar, sobre conjuntos acotados, parece
más razonable que regenerar código cada frame.

**Prioridad de investigación: alta entre las propuestas de este informe.**
No reemplaza la conclusión de L1: optimizar una sola rutina pequeña puede
ser insuficiente para cerrar D1.

## 4. Cadenas de blits ejecutadas por copper

### Evidencia de terceros

El framework [NoCpuDemo](https://github.com/askeksa/NoCpuDemo) genera listas
capaces de lanzar operaciones del blitter. En
[`no_cpu/lib/blitter.dart`](https://github.com/askeksa/NoCpuDemo/blob/main/no_cpu/lib/blitter.dart)
se leyó la secuencia: esperar al blitter, escribir los registros y arrancar
con `BLTSIZE`. La espera está implementada en
[`no_cpu/lib/copper.dart`](https://github.com/askeksa/NoCpuDemo/blob/main/no_cpu/lib/copper.dart).

El framework está orientado principalmente a AGA. El mecanismo básico
copper → blitter también existe en OCS; el
[Hardware Reference Manual, COPCON](https://www.amigadev.elowar.com/read/ADCD_2.1/Hardware_Manual_guide/node00AC.html)
documenta el permiso de acceso. No se presupone compatibilidad OCS de todas
las operaciones o efectos del framework citado.

### Diferencia y aplicación propuesta

En la ruta de scroll examinada, la CPU escribe los registros de blitter.
Una cadena dirigida por copper podría evitar esperas activas o una
interrupción por cada operación. Su posible destino son los lotes futuros
de restauración/dibujo de bobs, especialmente G7/Banzai.

**El copper del port ya tiene obligaciones de color y sprites.** Una espera
al blitter dentro de la lista visible puede bloquear recargas con plazo.
Los chips comparten el bus: delegar el lanzamiento no añade ancho de banda.
Además, la lista y todas las fuentes DMA deben estar en chip; tablas en
slow no pueden convertirse directamente en fuentes del blitter (R2).

La investigación debería limitarse primero a ventanas reservadas donde
la cadena no retrase la presentación. No se propone convertir toda la
lista de `build_mid` en una cadena de blits.

**Prioridad: media para el futuro motor de bobs; menor para los tirones actuales.**

## 5. Código automodificable y entrada/salida de secuencias

### Evidencia de terceros

[Planet Rocklobster, explicación de Axis/Oxyron](https://github.com/AxisOxy/Planet-Rocklobster)
describe un morph cuyos incrementos modifican operandos de instrucciones
`bset`, así como otros usos de código especializado.

En [D-Funk, comentario del autor gigabates](https://www.pouet.net/prod.php?which=94543),
el autor explica que el desplazamiento horizontal entra en una secuencia
generada de escrituras y reemplaza temporalmente una instrucción por `RTS`
para terminar en el punto elegido. Se consultó la explicación; no se
inspeccionó aquí el código fuente de ese efecto.

### Aplicación y límites

Podría permitir seleccionar y recortar una secuencia de dibujo preparada
sin comprobar límites por ficha. Es una hipótesis para composiciones
acotadas, no una sustitución general del clipping.

S9 ya salta dentro de una copia desenrollada: parte del principio está
presente. Solo habría ganancia adicional si desaparecen lecturas,
comprobaciones u operaciones que todavía se realizan.

El código modificado no debe ejecutarse a medio parchear desde otra fase
o interrupción. La generación y restauración también cuentan en el costo.
Código escrito por CPU puede vivir en slow; si lo modifica el blitter,
el destino debe estar en chip. No se asume que moverlo a slow acelere la
CPU (P29).

**Prioridad: complemento del speedcode, sujeto a una operación concreta.**

## 6. Carga y descompresión simultáneas

[LDOS, de Leonard/Oxygene](https://github.com/arnaud-carre/ldos), documenta
la descompresión mientras se carga del disquete, en lugar de separar ambas
fases. Puede aprovechar parte del tiempo de espera de disco.

BM1 ya introduce MFM propio y arenas fijas, pero eso no prueba que exista
este solapamiento. La técnica podría mejorar arranque o cargas posteriores
de bancos. No reduce el costo por frame de una escena ya residente.
La afirmación del autor sobre ocultar la descompresión no es una medida
del cargador del port.

**Prioridad: futura carga de bancos; no es una palanca para D1 actual.**

## 7. Técnicas ya presentes, previstas o descartadas

| técnica | situación observada en el proyecto |
|---|---|
| Scroll por punteros y `BPLCON1` | Ya usado; no requiere redibujar el playfield para cada píxel |
| Dual playfield, paletas por bandas y recargas horizontales | Ya forman parte de la arquitectura |
| Sprites adosados y multiplexado | Ya usados; las ventanas de color siguen siendo una restricción |
| Lógica fija y render desacoplado | O5 ya implementa esta separación |
| Evitar repetir cálculo entre listas | S9 ya comparte líneas válidas en el worktree |
| Cola de blits por interrupción | Ya investigada; sin fast RAM no hay ganancia general demostrada |
| Flujo de eventos de audio precalculado | Ya investigado mediante LSP y relacionado con D5; implementación pendiente |
| Repartir actualizaciones para aplanar picos | S5 ensayado y descartado en su variante reciente |
| Bucles de copper para filas repetidas | Ya evaluados en `investigacion-ports.md`; poca repetición en los datos examinados |

[LSP](https://github.com/arnaud-carre/LSPlayer) sigue siendo una referencia
útil para audio, pero no un descubrimiento nuevo de este relevamiento.
Su conversor recibe MOD; el proyecto requiere secuencias N-SPC convertidas
offline según D5.

## 8. Trucos de demos que no se trasladan directamente

Planet Rocklobster e Inside the Machine explotan HAM7: planos de control
constantes sin su fetch DMA normal. Rocklobster también describe apagar
la imagen en líneas alternas para liberar bus. Otras partes usan píxeles
grandes o 25 fps.

Estas combinaciones cambian modo, resolución efectiva o frecuencia. No son
una ruta directa para conservar YI1 píxel a píxel y el objetivo de 50 Hz.
No se propone adoptar HAM, EHB, líneas alternas vacías ni reducir resolución.

Una demo puede precalcular una trayectoria completa. El juego permite
movimiento e interacciones imprevistos: precalcular el replay demostraría
ese replay, no resolvería el juego en vivo. Se pueden especializar partes
estables sin fijar la partida.

## 9. Cómo determinar si una candidata sirve

Estos son criterios de evaluación, no una tarjeta de implementación abierta:

1. Elegir una operación concreta y registrar su costo y frecuencia actuales,
   incluyendo los fallos de caché. Comparar contra el asm vigente del worktree.
2. Contabilizar código generado, tablas, preparación y memoria chip/slow.
   El costo de producir o parchear código forma parte del balance.
3. Exigir las mismas salidas RAM/OAM y los mismos píxeles en poses,
   orientación, recortes y estados que consume esa operación. Mantener las
   puertas PC = 68000 y las convenciones ABI.
4. Medir primero el componente y luego el juego en WinUAE cycle-exact.
   Musashi solo aporta ciclos sin esperas DMA; no demuestra fluidez real.
5. Comparar fotos omitidas con la misma instrumentación y configuración.
   Una mejora media que empeore las rachas o no reduzca los saltos no cierra D1.

La recomendación es estudiar primero **speedcode acotado para composición
de poses**. Copper → blitter queda como referencia para bobs; carga y
descompresión simultáneas, para el loader. No se dispone de una estimación
fiable de ahorro para ninguna de estas propuestas.

## 10. Fuentes y trazabilidad

| fuente | qué se consultó | límite |
|---|---|---|
| [Inside the Machine, artículo del autor](https://blog.grahambates.com/posts/inside-the-machine/) | Speedcode, tablas, HAM7, tareas del framework | Explicación del autor; no benchmark del port |
| [Inside the Machine, table-2x2.asm](https://github.com/grahambates/inside-the-machine-public/blob/main/common/table-2x2.asm) | Implementación de `GenerateTable` y ejecución del código generado | Lectura de fuente, sin compilar ni ejecutar |
| [NoCpuDemo, blitter.dart](https://github.com/askeksa/NoCpuDemo/blob/main/no_cpu/lib/blitter.dart) y [copper.dart](https://github.com/askeksa/NoCpuDemo/blob/main/no_cpu/lib/copper.dart) | Esperas y emisión de registros de blitter | Framework principalmente AGA; no port OCS validado |
| [Hardware Reference Manual, COPCON](https://www.amigadev.elowar.com/read/ADCD_2.1/Hardware_Manual_guide/node00AC.html) | Acceso del copper al blitter | Capacidad de hardware, no prueba de ganancia |
| [Planet Rocklobster](https://github.com/AxisOxy/Planet-Rocklobster) | Explicaciones del autor sobre morph, speedcode y reducción de DMA | No se ejecutaron los efectos |
| [D-Funk](https://www.pouet.net/prod.php?which=94543) | Comentario técnico del autor del 2023-06-30 | No se leyó el fuente del efecto |
| [LDOS](https://github.com/arnaud-carre/ldos) | Carga y descompresión simultáneas | No se midió con nuestros datos |
| [LSP](https://github.com/arnaud-carre/LSPlayer) | Arquitectura y modos del reproductor | Antecedente ya incluido en la investigación del proyecto |

Referencias locales consultadas: `docs/investigacion-ports.md`,
`docs/plan-tecnico.md`, `player/scroll.s`, `player/game.s`, y en el worktree
`PROXIMO.md`, `docs/informe-g5l-r-s9-1010.md`,
`docs/informe-g5l-r-l1-1010.md`, `player/g5l.s` y `player/mspr68k.s`.

No se archivó ni reescribió `PROXIMO.md`: este relevamiento no ejecutó las
tarjetas allí previstas ni cambió el estado de implementación. La entrega
documental es este informe y su entrada en `docs/README.md`.

## 11. Actualización post-L2 (2026-10-10): qué vale y cómo aplicarlo

Estado de referencia: `docs/informe-g5l-r-l2-1010.md` (commit `222fb64`).
Replay normal de YI1: VBTRACE **0 omitidas**, BENCH 10 (0,16 %). Estrés
en rojo: `stress_back` 341/4126 (8,26 %), `stress_sprites` 92/1914
(4,81 %). En estrés domina el render/scroll: `build_mid` hasta 171 % del
frame en la vuelta, "resto de `scroll_frame`" 122 % (informe L2 §3).

### Reordenamiento

| técnica | antes (§9) | ahora | por qué |
|---|---|---|---|
| Speedcode para poses de Mario (§3) | alta | **baja** | `mspr_draw` = 3 103 ciclos por foto (`work/l2/prof3.json`), ~2 % del frame: aunque se reduzca a la mitad, no mueve el estrés |
| Speedcode en `build_mid`/`bm_left` | — | **candidata** | ahí está el pico; ver condición abajo |
| Entrada/salida parcheando `RTS` (§5) | complemento | **complemento del anterior** | la ventana `[s, s+LASTX]` elige un tramo contiguo de cargas por línea: se entra en el primero y se corta en el último sin comprobar rango por carga |
| Copper → blitter (§4) | media (bobs) | **condicionada** | solo si el "resto de `scroll_frame`" resulta ser espera del blitter (terminar una columna a medias al dar la vuelta, `blit_steps` con 99 pasos en `columns`) |
| Carga + descompresión (§6), trucos de §8 | — | sin cambio | no tocan el costo por frame / rompen 1:1 o D1 |

**Límite del 68000 para el speedcode:** `move.l #imm,(a0)+` y
`move.l (a1)+,(a0)+` cuestan lo mismo (20 ciclos); `move.w` igual (12).
Meter datos en instrucciones no ahorra por sí solo: solo ahorra las ramas,
comparaciones y lecturas de índices que desaparecen. En `build_mid` la h
del WAIT depende de `s` (`htab[x - s]`), así que esa lectura queda.

### Cómo aplicarlo (paso 2 de `PROXIMO.md`)

1. **Perfil antes de elegir.** `g5l.py game --pcprof` (P121) de
   `build_mid`, `bm_left` y `scroll_frame` sobre `stress_back`, separando
   (a) decisiones (rango, clase, validez de línea, `MIDMAX`), (b) copia de
   palabras a la lista, (c) esperas del blitter (`bwait`, `blit_steps`) y
   `draw_window` (CPU, ~24 000 ciclos por columna según `scroll.s`).
2. **Según lo que domine:**
   - (a) → rutinas por línea generadas offline por `tools/mkscroll.py`
     (código en slow: solo CPU, R2 no aplica; P29: no acelera ni frena)
     más el corte con `RTS` parcheado. Nada puede ejecutar ese código a
     medio parchear; el parcheo y la restauración entran en la cuenta.
   - (b) → ninguna técnica de demos: escribir menos palabras (más reuso al
     estilo S9, menos líneas reescritas).
   - (c) → copper → blitter en ventanas que no retrasen recargas con
     plazo, o cambiar cómo se termina la columna al dar la vuelta.
3. **Puerta de corrección:** en Musashi, la lista del copper resultante
   idéntica byte a byte a la actual en cada foto de YI1, `stress_back` y
   `stress_sprites`; `lint_port.py` y `regress.py` verdes.
4. **Puerta de rendimiento:** BENCH WinUAE cycle-exact en los dos
   replays de estrés y VBTRACE del normal (sigue en 0). Registrar la
   memoria del código generado.

Nada de esto tiene estimación de ahorro: **ESTIMADO no disponible hasta
el perfil del paso 1.** Va después de P123 (el Guru latente está en el
render que se tocaría).
