# G2 — Dibujo de sprites desde la OAM

Contrato revisado el 2026-10-06, auditado sin subagentes. Este documento fija las interfaces
de G3–G7; no declara implementado el dibujador. Insumos:
`estudio-g1-g0.md`, `automatizar-9.2.md`, G8 (`spr_gfx.c`), G3a
(`mksprgfx.py`) y O5 (`game.s`). Los resultados del banco G0 se documentan
en `medida-g0.md`; sus plazos prevalecen sobre el modelo de 320 px.

## 1. Fase de gráficos y foto del render

**La OAM se genera dentro de la lógica, en el punto original de cada rutina.**
`rex_gfx` cambia también `SpriteGfxTbl`, los indicadores fuera de pantalla y
los temporales de RAM. Ejecutarla después de la física daría otra pose (P35);
ejecutarla sobre RAM viva desde el render interferiría con la interrupción.
No se copia toda la RAM ni se repite la lógica para dibujar.

Se conserva `NOOAM` para Mario, su `mario_oam` y `mspr_draw` en asm. La opción
separada `SPR_OAM` habilita las rutinas G8 de enemigos, incluido
`CALLX _rex_gfx` en `rex_main_asm`. Los builds de C y asm deben habilitarla
juntos. G8b verifica también Banzai, Piraña, Chuck, meta y caparazones en
PC/68000 (`validacion-g8b.md`). Sigue opt-in: el máximo observado de lógica
con OAM ampliada es 62110 ciclos, 43,8 % PAL **sin DMA**, por encima del
objetivo del 40 %. Activarla por defecto requiere optimizar y medir el juego
integrado. La OAM exacta no implica que los enemigos sean ya visibles.

La foto de O5 se amplía, por cada uno de sus tres buffers, con:

| campo | formato / tamaño máximo | uso |
|---|---|---|
| cámara X/Y, frame, paleta de Mario | palabras; conservar los campos actuales | mismo tick que la OAM |
| OAM normalizada visible | 128 entradas × 5 B = 640 B | X baja, Y, tile, atributos, X alta/tamaño |
| pertenencia a ranura | 128 B, `$FF` para partículas/Mario | agrupación y orden exactos |
| primera entrada y cantidad por ranura | 12 × 2 B = 24 B | límites de cada objeto |

Estos datos viven en **slow RAM** y se copian antes de publicar `DC_NEW`.
La foto tomada por el render y la pendiente de VBL quedan inmutables (P97).
El render usa exclusivamente esa cámara, OAM, prioridad y paleta; nunca
consulta `ram[]` viva. La cámara Y se guarda aunque S8 todavía no mueva el
fondo: así la interfaz no presupone Y = 192.

La OAM se limpia/oculta según la fase original cada tick; las cantidades se
reinician antes del despacho. `spr_oam_first` usa un offset de bytes en
`$0300` (ranura OAM = `64 + first/4`) y `spr_oam_n` incluye fichas con Y =
`$F0`. Al empaquetar solo fichas visibles, reconstruir primeros índices y
cantidades; no copiar esas marcas como índices de la foto. Una ranura
desaparecida no conserva fichas del tick anterior. Mario mantiene sus
punteros GFX32, que no son fichas estáticas
del GFX 00 (P99). La pertenencia sale de quien escribe la OAM, no de la
heurística por proximidad de `g1study.py`.

## 2. Contrato del banco G3 acotado

La prueba reproducible de G2 está en `informe-g2.md` y
`tools/g2_bank_audit.py`. Cierra la decisión de representación. G3 implementa conversor y loader SG3F/2 para el lote acotado (`informe-g3-final.md`); el dibujador y la cobertura global siguen pendientes. El prototipo **SG2A**
no es aceptado por SG3F/1 y nunca debe cargarse como si fuera ese formato.

### Cobertura y límites

Lote: `yi1`, `normal` y `spin_kill`, solo las rutinas compartidas AB/BD/02/B9,
con pertenencia SOT1 cotejada con la OAM del oráculo, reservas reales por fila
y ocho paletas de Mario. Se agregan las seis poses legales normales de Rex,
ambas direcciones. Las 2593 peticiones observadas abarcan 43 formas; faltan
cinco formas legales, que se agregan sin reservas. Resultado: **48 formas,
289 descriptores, cero peticiones rechazadas**. No agregar mapas nuevos para
formas legales que ya tienen un descriptor compatible sin reservas.

Fuera de esta puerta: Banzai, Piraña, Chuck, meta, power-ups y partículas
adicionales; prioridad/estados no recorridos; reservas de todas las poses de
Mario; convivencia de varios enemigos; bobs PF1 de G7. La nube del giro y las
partículas que comparten VRAM/paleta de Mario sí están en las trazas/reservas.
Cobertura acotada aprobada no significa cobertura final de todo YI1.

| componente | bytes medidos | límite de contrato |
|---|---:|---:|
| flujos DMA, controles, terminadores, alineación y variantes | **64528** | **65536** |
| descriptores y tablas de color/fichas | 71554 | parte del límite de tablas |
| directorio por forma/listas de variantes | 1162 | parte del límite de tablas |
| todas las tablas e índices residentes | **72716** | **98304** |
| espacio de trabajo G4/G6 | sin implementar | **32768** slow |
| ampliación de las tres fotos O5 | 2376 | **2376** slow |

### DMA directo e inmutable

La clave de forma sigue siendo la lista **ordenada** de fichas
`(dx,dy,tile9,tamaño,flipX,flipY,paleta)` y prioridad. No incorpora frame,
posición absoluta ni nombre de replay. Recortar solo márgenes transparentes
conservando el origen; Rex normal necesita dos columnas.

Cada columna conserva dos flujos attached completos: POS/CTL provisionales,
DATA/DATB (4 B por fila por canal) y terminador cero. Para H filas son
`16 + 8*H` B por columna antes de alineación. Los offsets se alinean a 8 B;
solo el canal alto lleva ATTACH. No se borra padding transparente ni se
acortan alturas para ahorrar bytes.

El empaquetador offline primero comparte flujos iguales, después subcadenas
completas a offsets alineados y por último el sufijo/prefijo exacto más largo.
Orden reproducible: longitud decreciente y bytes lexicográficos. El banco
sin solapes mide 66336 B; con solapes **64528 B**. Todos los bytes de cada
flujo siguen presentes y se decodifican de nuevo desde sus offsets finales.

**El banco es inmutable.** G5 escribe PT completo y POS/CTL en registros
mediante copper, según G0; no parchea controles compartidos en chip. No hay
copias, descompresión ni recodificación por frame en esta representación.
El tamaño ≤64 KiB no garantiza que AllocMem lo ubique dentro de un único
banco físico: presupuestar PT alto **y** bajo, sin otra reserva de alineación.
Reuso y plazos con el copper real siguen siendo puertas G5/G6.

### Tablas y selección de variantes

Big endian, offsets relativos y comprobados. Metadata y directorio se cargan
en **una reserva slow**, concatenados a frontera par (72720 B redondeados);
el directorio conserva su propia base relativa. Mover también las tablas
CPU de C2/C4 como un bloque para usar el redondeo presupuestado.
Para la revisión siguiente de
SG3F conservar el descriptor de 32 B y las tablas directas actuales: fichas
10 B, parejas de offsets u32, puntero u32 por fila, mapa por fila con cuenta
u16 y entradas `(paleta,índiceSNES,índiceDMA,pad,colorOCS)` de 6 B. Internar
cada tabla idéntica. El descriptor conserva origen s16, W/H, columnas,
prioridad y cantidad de fichas. En este lote DMA **source y mask = $FFFFFFFF**
indican bob ausente; nunca se usan como punteros. G3 debe versionar y validar
esa ausencia de forma explícita. SG3F/1 conserva su lector anterior.

Deduplicar el descriptor por forma y **mapas del enemigo**. Las entradas 255
con reservas de Mario no son datos del enemigo: no se almacenan por variante.
El directorio residente, medido en el prototipo, tiene cabecera 8 B y por
forma 12 B: offset de fichas u32, prioridad u8, cantidad de fichas u8, número
de variantes u16 y offset de lista u32; la lista contiene índices u16 de
descriptor. Usa como fuente las fichas de la tabla, sin duplicarlas.

G4 busca por la OAM de la misma foto y prueba la compatibilidad de cada mapa
con sus reservas de Mario y con los otros enemigos asignados. Hay hasta
**31 candidatos por forma** en este lote; debe presupuestar ese peor caso.
G3 debe ofrecer `--final --scope g2-bounded`: acepta únicamente el lote
declarado tras su verificación; el modo global sigue exigiendo cobertura
completa de YI1.

No seleccionar por frame grabado ni usar el índice de petición como una
tabla del juego. El JSON de aliases es evidencia offline, fuera de RAM.
Sin candidato compatible: salida explícita para G6/G7; nunca descarte,
color aproximado ni lectura de RAM viva. La selección y los MOVE de color
siguen pendientes de implementación y medida dentro del 8 % de G4/G5.

Se conserva la fuente SNES y la máscara como verdad offline. **No duplicar
cada variante DMA en una fuente bob y máscara residente:** G7 debe generar
su propio banco PF1 con siete índices y el terreno. Quitar esas fuentes
incompatibles con PF1 de este lote no completa G7 ni elimina su cola.

### Copper con una imagen por forma: alternativa evaluada

Sin reservas, las 48 formas ocuparían 4824 B DMA tras solapes (5104 B sin
solapes; 10840 B en el formato antiguo con bobs). Pero una recarga por fila
no cambia los índices fijos del bitmap de Mario. El matching bipartito exacto,
con píxeles reales y las ocho paletas, falla en **12 de 43 formas observadas**,
incluso permitiendo un mapa de índices distinto en cada fila de la imagen.

Caso `trace_ab_f5811_m0_291`, fila local 6: los colores OCS `$44D`, `$66D`
y `$88F` solo pueden ocupar 7 y 15 si la misma imagen ha de respetar todas
sus reservas reales. Tres colores necesitan tres índices y solo quedan dos.
No basta contar la unión de colores ni recargar COLOR17–31 por fila.

Se descarta **esa** alternativa para este contrato. Recargas a mitad de
línea podrían separar usos en X; no están refutadas por la prueba por fila,
pero requieren posiciones de ambos objetos, plazos de `build_mid` (P51) y
medida G5a/G6. No se presupuestan como solución ya medida. No se altera D8.

### Ampliación del alcance

La muestra de cinco trazas G8b agrega 106 formas observadas. Sin reservas de
Mario para esas formas nuevas, el mismo esquema ocupa 81904 B DMA y 85798 B
de metadata, antes del directorio; **excede** 64 KiB. Es una medición de esta
representación, no un mínimo demostrado ni cobertura legal completa.
Banzai seguirá en bob: excluyéndolo aún se necesitan **77152 B DMA**,
con 148 formas y 83526 B metadata, sin reservas nuevas de Mario.
El escaso margen de 1008 B no autoriza ampliar el lote automáticamente.
G3 debe informar alcance, crecimiento y límites; banco bob/PF1 y nuevos
estados requieren presupuesto propio y una nueva auditoría de G2/G7.

## 3. Asignación y reuso de canales (G4/G6)

Se parte de cuatro parejas `(0,1)`, `(2,3)`, `(4,5)`, `(6,7)` a 256 px.
Mario ocupa una o dos según su caja real durante todo su intervalo vertical;
SPR2/3 se libera cuando no la necesita. Fuera de ese intervalo las parejas
se pueden reutilizar. El orden respeta la prioridad OAM en las superposiciones.

G4 recibe objetos de la foto y produce asignaciones por intervalo
`[y0,y1)`, con pareja, posición, pose y mapa de colores, más una cola explícita
de bobs y una cola de casos no resueltos. Primero reserva Mario; después
ordena por Y y prioridad de forma estable. Banzai `$9F` va siempre a bob.
Las poses anchas piden todas sus columnas; no se asigna media figura.

El reuso por PT busca al menos una línea libre **solo cuando G0 valide el
plazo para esa pareja y esa carga**. El banco a 256 px comprueba los ocho
canales: PT completo desde h=$80/$C0 de la línea anterior, seguido de
POS/CTL desde h=$38 de VSTOP, da 512 píxeles exactos incluso con 8 MOVE de
color en borrado y 6 a mitad de línea. PT desde h=$D8 anterior ya falla;
no usarlo como ventana segura. Es una calibración sintética, no la lista
completa de las capas del juego. Presupuestar por columna hasta 8 MOVE
(PT alto/bajo + POS/CTL en ambos canales), más WAIT y colores. Compartir el
banco baja a 6 MOVE; no elimina POS/CTL. Si no hay plazo, encadenar un flujo
con controles propios en un buffer de chip de la foto, o mandar el objeto a
bob. El encadenado debe validar su intervalo mínimo por separado.

Ningún objeto se descarta ni parpadea por defecto. Los 55 frames con Rex fuera
de `oracle_yi1` y los 207 de `stress_back` del estudio van a la cola de bob.
El supuesto canal suelto de tres colores para la cola de Rex queda fuera del
primer diseño: no está demostrada su fidelidad de color.

`g1study.py`/`copsim.py` son referencias para demanda y planificación;
G6 añade una simulación de canales que reconstruya **cada píxel** desde el
flujo DMA, controles y recargas. Compara contra la OAM renderizada con G3a;
comprueba tanto coordenadas como color, oclusión, clipping y objetos a bob.
La equivalencia del asignador C/68000 se verifica en Musashi. Cero objetos
sin destino y cero diferencias de píxeles son puertas separadas.

## 4. Bobs y publicación de O5

Para G7 se elige **doble buffer PF1**, +59 136 B de chip. Dibujar detrás del
haz sobre el único PF1 puede alterar una imagen que O5 repite cuando el render
llega tarde; sin una garantía medida del blitter no conserva la foto publicada.
El doble PF1 pertenece a las listas front/back, no a los tres buffers de foto.

En el PF1 libre: restaurar las regiones del último uso de ese buffer desde
BLK/mapa, aplicar columnas/cambios de mapa y dibujar los bobs de la nueva foto.
Mantener por buffer la lista de regiones sucias y su posición de cámara.
Escribir las dos copias del anillo y manejar el cruce de su borde. El render
es el único dueño del blitter; publicar después del último blit, nunca antes.

PF1 tiene solo siete índices opacos y comparte colores con el terreno. G7 debe
resolver sus intervalos de color y fuentes remapeadas junto con el plan del
copper. El estudio `d8demote.py` deja casos sin color exacto: son trabajo
pendiente, no fidelidad aprobada. Cualquier aproximación requiere mostrar el
caso y consultar al usuario; no queda autorizada por este diseño.

## 5. Memoria y coste

Medida del 2026-10-06 con `memmap.py`, listados de G8b opt-in:

| modo | chip actual | slow actual | chip + banco G2 |
|---|---:|---:|---:|
| replay | 390704 | 214880 | **455232** |
| vivo | 402232 | 251120 | **466760** |

La auditoría aplica el modelo de `memmap` al banco propuesto (MEMF_CHIP,
alineación 8) y a esas bases: cero violaciones. **Es una proyección, no un
ADF que ya cargue el banco.** G3 verifica las reservas concretas y el loader
en ambos modos. También debe medir el pico transitorio de carga; evitar
que una segunda copia de assets quede residente en el binario slow/chip.

C2/C4 mueven 135468 B de tablas CPU a slow; presupuestar 135472 B con
redondeo de AllocMem. En vivo quedan **137696 B**. El tope es:
`98304 tablas + 32768 trabajo + 2376 fotos = 133448 B`; margen final mínimo
**4248 B** con el binario actual. El crecimiento de código/loader exige
recalcular, nunca consumir un margen ficticio del replay. La implementación
medida usa 72720 B de tablas redondeadas + 2376 fotos; con C2/C4 dejaría
**461688 B slow**, o **494456 B** reservando todo el espacio de trabajo.

| reserva de chip, modo vivo opt-in | bytes |
|---|---:|
| juego actual | 402232 |
| banco máximo DMA | 65536 |
| segundo PF1 | 59136 |
| audio D5 (tope; A1 mide 50560) | 65536 |
| subtotal antes de C2/C4 | **592440** |
| después de mover tablas CPU | **456976** |
| margen para banco bob G7, HUD, copper, cadenas y subzona | **67312** |

La reserva futura acredita conservadoramente **135464 B liberados de chip**
(alineación 8) y carga 135472 B a slow; el loader definitivo debe comprobar
sus redondeos reales.

Las fuentes bob ya no están dentro de los 64 KiB DMA. G7 debe contar ese
coste en el margen restante y demostrar color PF1 exacto. Segundo PF1 y
audio juntos siguen necesitando C2/C4. No hay presupuesto para un banco
G8b de 81904 B bajo este contrato.

Presupuestos separados: lógica con OAM ≤40 % PAL (G8b hoy excede el objetivo);
asignación, preparación DMA y copper de enemigos ≤8 %; audio ≤3 %; HUD ≤2 %.
Bobs se miden aparte. Musashi es cota inferior; no sustituye cycle-exact.
Publicar media/máximo/frame del máximo, fotos omitidas y ticks perdidos O5.
No se han medido aquí tiempos del renderer nuevo ni sus recargas de color.

G0 mide copiar 1408 B chip→chip en 7,47–7,52 % con seis planos DMA y
4,81–4,95 % en VBlank. Esta representación no agrega esa copia por frame.
Cadenas dinámicas, selección y cargas reales quedan sujetos a G4/G5/G6.

## 6. Puertas y siguiente orden

1. ~~Banco G0 a 256 px~~ **hecho el 2026-10-05** (`docs/medida-g0.md`):
   PT/POS/CTL, canales 0–7, poses compartidas y carga sintética de color.
   Lo que no cubre (copper real, audio, blitter concurrente) pasa a G5/G7.
2. ~~OAM en Amiga~~ **hecho el 2026-10-05** como opción `-DNOOAM -DSPR_OAM`
   (`docs/oam-amiga.md`): Rex 2671/2671, RAM/ABI exactos, replay sin
   diferencias. Activarla por defecto sigue pendiente de medir OAM/O5 con DMA.
3. **G2 revisada y auditada el 2026-10-06** (`informe-g2.md`): contrato
   acotado 64528 B chip / 72716 B tablas, sin recodificación por frame.
   **G3 acotada hecha:** conversor y loader SG3F/2, aceptación explícita y memmap concreto replay/vivo (`informe-g3-final.md`). `--final` global sigue rechazando cobertura incompleta; el scope acotado no cubre todo YI1.
4. G4 + G6: asignador C/asm, cola de bobs explícita, píxeles reconstruidos
   exactos y plazos de cada recarga. No confundirlos con enemigos visibles.
5. G5 + G9: listas del copper y capturas de enemigos contra la OAM; medir DMA
   integrado. Ampliar las tres copias de scroll cuando corresponda (P97).
6. C2/C4 y G7: PF1 doble, Banzai y desbordes, memoria y colores sin aproximar.

Z1, H1, A1/A2 quedan independientes cuando estén satisfechas sus dependencias.
S5 sigue acotado a una sesión y con prioridad menor por O5.
