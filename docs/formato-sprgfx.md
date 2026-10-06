# SG3F/1 — formato de poses G3

Implementado por `tools/sprgfx_final.py`, mediante `mksprgfx.py --format-test`
para la ida y vuelta y `--final` para la auditoría de cierre.
Es un formato de herramientas verificable; todavía no está integrado en el
loader ni en el renderer. Los archivos derivados quedan exclusivamente en
`work/`: `.idx` para CPU/slow, `.dma` para chip, `.json` para auditoría.
La implementación no garantiza alineación del banco físico a 64 KiB.
G5 debe presupuestar PT alto y bajo; el loader debe verificar direcciones.

Todos los números de los dos archivos binarios son big endian. Ninguno
contiene punteros absolutos. Los offsets de tablas son relativos a `.idx`;
los offsets de flujos/fuentes son relativos a `.dma`. El decodificador
valida tamaños, offsets, alineación, controles y terminadores antes de usar
las fuentes. `.dma` tiene un límite estricto de 65536 bytes, incluyendo
padding y variantes. Un rechazo no consume espacio del siguiente objeto.

## Cabecera y descriptor

Cabecera de 24 bytes, `>4sHHIIII`:

| offset | campo |
|---|---|
| 0 | magic `SG3F` |
| 4 | versión u16 = 1 |
| 6 | tamaño de descriptor u16 = 32 |
| 8 | cantidad de descriptores u32 |
| 12 | offset de descriptores u32 = 24 |
| 16 | bytes de `.dma` u32 |
| 20 | bytes de `.idx` u32 |

Descriptor de 32 bytes, `>hhHHBBHIIIII`:

| offset | campo |
|---|---|
| 0, 2 | origen X/Y s16 relativo a la ranura |
| 4, 6 | ancho/alto recortados u16 |
| 8 | columnas attached u8 = ceil(ancho/16) |
| 9 | prioridad OAM u8, 0..3 |
| 10 | cantidad de fichas originales u16 |
| 12 | offset de fichas ordenadas u32 |
| 16 | offset de pares de offsets DMA u32 |
| 20 | offset de tabla de offsets de mapa por fila u32 |
| 24, 28 | offsets de fuente bob y máscara u32 |

Cada ficha original ocupa 10 bytes, `>hhHBBBB`: dx, dy, tile9, tamaño,
flags (flipX bit0, flipY bit1), paleta SNES 0..7 y cero reservado.
Se conserva la lista ordenada: la primera ficha opaca de la OAM gana.
La clave incluye esta lista y la prioridad. Una pose de prioridad mixta se
rechaza, hasta ampliar el contrato con prioridad por ficha. Dos descriptores
con iguales fichas pueden tener mapas distintos por las reservas de Mario.
La posición absoluta y el frame no forman parte de la clave.

Se recortan únicamente márgenes transparentes, conservando el origen.
Una pose completamente transparente tiene ancho/alto/columnas = 0, sin
fuentes DMA ni mapas. Conserva sus fichas para reconstruir la clave.
Un Rex normal recortado de 20 px ocupa dos columnas, sin perder el margen
relativo a la ranura. Los flujos compartidos no contienen la posición del
objeto: el consumidor debe programar POS/CTL para cada instancia.

## DMA, bob y mapas

La tabla de columnas contiene dos u32 por columna. Cada offset señala un
flujo alineado a 8 bytes: POS provisional = 0, CTL = 0 para canal par y
`$0080` para impar; H pares DATA/DATB de palabras; terminador 0,0.
Cada pareja cuesta `16 + 8*H` bytes antes de padding. Los flujos y fuentes
idénticos se deduplican por sus bytes.

La fuente bob tiene cuatro planos consecutivos con stride de palabra
`ceil(ancho/16)*2` bytes por fila. La máscara ocupa otro plano de igual
tamaño; 1 = opaco. El padding a la derecha es transparente. **Esta fuente
usa el remapeo de sprites attached, todavía no los siete índices PF1**;
G7 debe producir/verificar su variante exacta junto al terreno. No es
evidencia de que Banzai ya pueda dibujarse sobre PF1.

La tabla de filas contiene H offsets u32 a mapas internados en `.idx`.
Cada mapa es cantidad u16 seguida de registros `>BBBBH`:
paleta SNES, índice SNES opaco, índice DMA 1..15, cero reservado, color OCS
`$0RGB`. La paleta 255 señala una reserva de Mario: índice SNES = índice
DMA que debe conservarse. Todos los colores son `snes_to_amiga12`; ningún
color se aproxima a otro. El cero DMA siempre significa transparencia.
Las fichas originales más estos mapas conservan la fuente SNES de verdad.

El conversor intenta reutilizar mapas de variantes compatibles; después
busca una asignación estable por pose con backtracking acotado. Colores
distintos pueden compartir índice solo si nunca coinciden en una fila.
Si esa búsqueda no encuentra mapa estable, el fallback asigna por fila de
forma exacta o rechaza si no hay quince índices suficientes. La cota de
búsqueda limita la optimización, no relaja la fidelidad. **Los plazos de
recarga entre filas y la convivencia de varios enemigos son puerta G6**.

## Manifiesto y cobertura

`sprgfx_manifest.py` extrae poses desde SOT1 usando `first/n` reales de
cada despacho, y exige que la secuencia visible completa esté en la OAM
del oráculo del mismo frame. Usa el origen de la ranura post despacho y
desplazamientos firmados de ocho bits. Nunca usa agrupación por proximidad.
También enumera las seis poses Rex de sus tablas ROM, ambas direcciones y
prioridad normal. Las rutinas G8 no portadas no tienen pertenencia exacta
en estas trazas: su cobertura permanece pendiente.

`--mario-rows` reconstruye la VRAM dinámica desde los punteros RAM `$0D85`
y `$0D99` y GFX32, como `gamecheck.spr_ok`. Reserva los índices opacos
por fila de las entradas grabadas con paleta 0 y nombres de esa VRAM
dinámica; no les atribuye un dueño por heurística. Incluye partículas que
compartan tales nombres/colores. Aplica las ocho paletas de `mkmario.py`
conservando el índice existente de Mario. La prioridad/oclusiones se
resuelven entre entradas dinámicas; reservarlas aunque otro enemigo las
tape es conservador. No enumera todos los estados legales de Mario fuera
de esas grabaciones ni demuestra una reserva mínima.

El JSON de salida indica cobertura y `final_complete=false`, los nombres
de descriptores emitidos en orden, los rechazos separados por BANK/COLOR/
FORMAT y el tamaño requerido por todos los blobs con color exacto. Esa
medida puede exceder 64 KiB: se decodifican sus blobs, pero **nunca** se
emite como banco DMA cargable. `--format-test` devuelve 0 solo si todas
las poses del lote pasan la ida y vuelta dentro del banco; devuelve 1 con
cualquier rechazo. `--final` devuelve 1 mientras la cobertura final siga
incompleta, incluso con un lote que pasó su ida y vuelta. Sin manifiesto se
auditan fichas individuales observadas; eso no representa poses compuestas
ni sustituye la VRAM dinámica de Mario.
