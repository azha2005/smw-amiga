> Archivado el 2026-10-06: sustituido por el contrato G2 auditado.

# G2 — Dibujo de sprites desde la OAM

Diseño del 2026-10-05, después de la ola 3. Este documento fija las interfaces
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
juntos. Primero se verifica como opción de compilación: activarla por defecto
requiere medir el juego integrado con DMA y comprobar que no pierde ticks
lógicos. La medida integrada de Musashi con OAM, limpieza y puentes PIC pasa
de 39 026 a 46 718 ciclos máximos (+19,7 %), y de 28 588 a 32 692 de media
(+14,4 %). Son incrementos **relativos al coste de `level_frame`**, no puntos
del frame PAL; sustituyen la estimación anterior de G8 (+13,7 %).

G8 cubre Rex, las rutinas compartidas ya portadas y la nube del giro. No cubre
todavía todas las rutinas de Banzai, Piraña, Chuck, meta ni partículas. Activar
la OAM no hace visibles los enemigos: faltan asignación, DMA y copper.

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

## 2. Formato que debe emitir G3

Índices, tablas y descriptores: big endian, sin punteros absolutos en el
fichero. Los offsets se validan al cargar. Tablas y diccionarios van a slow;
únicamente los flujos DMA y las fuentes del blitter van a chip, alineados a
8 B. Salidas derivadas en `work/`, nunca en git.

Un descriptor de pose contiene ancho y alto reales, origen relativo a la
ranura, número de columnas, paleta SNES, prioridad OAM, offsets de los dos
flujos de cada columna y offset de máscara/fuente planar para bob. Su clave
es la lista ordenada de fichas `(dx,dy,tile9,tamaño,flipX,flipY,paleta)`;
no incluye posición absoluta ni frame del replay. Recortar solo márgenes
transparentes, conservando el origen. Rex normal mide 20 px: **dos columnas**.

Cada columna adosada almacena dos flujos de canal:

```
POS provisional, CTL provisional
DATA, DATB                  ; 4 bytes por fila, por canal
...
0, 0                        ; terminador
```

Los dos canales de una columna de altura H cuestan `16 + 8*H` B, antes de
alineación. El segundo activa ATTACH. Una pose compartida no contiene la
posición de un objeto: G5 debe programar POS y CTL tras la lectura de control
y antes del fetch de sus píxeles, conforme al banco G0. No basta actualizar
PT. Dos objetos con igual pose y posiciones distintas deben funcionar.

Objetivo: **un banco de 64 KiB** para poses DMA. El límite incluye variantes,
flips, controles, terminadores y alineación; no sale de los ~11 KB de fichas
del formato intermedio. El puntero alto solo puede omitirse si ambos canales
permanecen en el mismo banco físico de 64 KiB. Hasta C2, presupuestar dos MOVE
por puntero y comprobar las direcciones reales; un `AllocMem(65536)` normal
no garantiza el banco. No reservar silenciosamente otros 64 KiB para alinear.

El conversor debe rechazar un banco que se desborde, una ficha desconocida o
una pose que pierda píxeles. Para el juego en vivo, enumerar las poses legales
de las tablas del ROM además de las observadas: un replay no cubre todo (P69).

### Colores: el remapeo es parte del formato

Todos los pares adosados comparten COLOR17–31. Copiar índices SNES de distintas
paletas sin remapearlos genera colores incorrectos aunque quepan 15 colores.
El estudio de `copsim.py` usa filas de unas poses de referencia: es una
estimación, no una prueba de todas las poses ni de todos los estados de Mario.

G3 conserva el índice SNES y la máscara como fuente de verdad y emite por fila
la correspondencia `(paleta,índice) → color OCS` y el conjunto de colores
opacos. El empaquetado DMA usa una correspondencia explícita a índices 1–15;
0 siempre transparente. Se reutiliza un índice entre colores distintos solo
si sus intervalos de uso no se solapan y hay plazo para la recarga del copper.
El mapeo debe respetar los índices del buffer de Mario existente, o producir
una variante de Mario verificada; cambiar COLOR17–31 no remapea sus píxeles.

Primera puerta de G3/G6: auditar con los píxeles reales todos los remapeos,
incluidas variantes de paleta de Mario. Precalcular las variantes necesarias
de pose y su mapa de colores; contar sus bytes dentro del banco. Si esa
enumeración excede el banco o no resuelve una coincidencia de colores, G2 se
reabre con los casos concretos. No declarar resuelto por contar solamente la
unión de colores, ni esconder el problema con el color más cercano.

**Puerta reabierta el 2026-10-05:** la auditoría de G3 reconstruye las
2593 variantes con reservas de Mario sin diferencias de color, pero la estrategia
ensayada necesita 145600 B de blobs chip; el banco estricto de 65536 B
solo admite 1724. Su diccionario también ocupa 693884 B slow. Estas cifras
no son un mínimo demostrado: hay que reducir variantes y representación
antes de fijar G4/G6. Los casos, el formato SG3F y los comandos están en
`informe-g3.md` y `formato-sprgfx.md`; `--final` rechaza la cobertura incompleta.

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

Mapa actual reproducido con `memmap.py work/rg_game/game.lst` el 2026-10-05:
chip 390 704 B; slow 207 296 B; tablas solo de CPU en chip 135 468 B.
Estos números corresponden al replay, sin diagnóstico en vivo.

| reserva de chip | bytes |
|---|---:|
| juego actual | 390 704 |
| banco máximo de poses DMA + fuentes de bob | 65 536 |
| segundo PF1 | 59 136 |
| audio (D5) | 65 536 |
| subtotal, antes de HUD/copper extra | **580 912** |
| subtotal después de mover tablas CPU a slow (C2/C4) | **445 444** |
| margen restante, para HUD, listas, flujos encadenados y subzona | **78 844** |

El banco de 64 KiB es un **tope propuesto**, no el tamaño demostrado por G3a.
Sus ~11 040 B describen 276 fichas fuente de 8×8 con máscara; con flips y
composición por objeto el tamaño cambia. Los 3 snapshots añaden ~2,4 KB a
slow, no chip. G5 debe contar el crecimiento real de ambas listas; no consumir
el margen como si las recargas fueran gratuitas en memoria.

**C2/C4 preceden a G7+audio:** las reservas juntas no entran en 512 KB.
G3/G4/G6 pueden desarrollarse antes; cada integración pasa `memmap` sobre el
ADF concreto, también en vivo. Queda además comprobar el pico de carga del
loader: el binario transitorio en chip no es memoria libre durante el arranque.

Presupuestos separados: lógica con OAM ≤40 % del frame PAL; asignación,
preparación DMA y copper de enemigos ≤8 %; audio ≤3 %; HUD ≤2 %. Bobs se miden
aparte. Los ciclos Musashi son cota inferior: P96 propone ×1,05 para lógica y
×1,5 para preparación/scroll, sin sustituir una medida cycle-exact. Publicar
media, máximo y frame del máximo, junto con fotos omitidas/ticks perdidos de
O5. Ninguna cifra del diseño declara que el conjunto ya entra a 50 Hz.

El banco G0 mide copiar 1408 B chip→chip en **7,47–7,52 %** con DMA de seis
planos activo y **4,81–4,95 %** en VBlank (32 repeticiones, timer CIA-B,
coste del arnés restado). La alternativa de encadenar no debe presupuestarse
con el 4,5 % sin DMA del estudio inicial; puede consumir casi todo el 8 %.

## 6. Puertas y siguiente orden

1. ~~Banco G0 a 256 px~~ **hecho el 2026-10-05** (`docs/medida-g0.md`):
   PT/POS/CTL, canales 0–7, poses compartidas y carga sintética de color.
   Lo que no cubre (copper real, audio, blitter concurrente) pasa a G5/G7.
2. ~~OAM en Amiga~~ **hecho el 2026-10-05** como opción `-DNOOAM -DSPR_OAM`
   (`docs/oam-amiga.md`): Rex 2671/2671, RAM/ABI exactos, replay sin
   diferencias. Activarla por defecto sigue pendiente de medir OAM/O5 con DMA.
3. G3: empaquetado, remapeo exacto de color y tamaño del banco comprobados.
4. G4 + G6: asignador C/asm, cola de bobs explícita, píxeles reconstruidos
   exactos y plazos de cada recarga. No confundirlos con enemigos visibles.
5. G5 + G9: listas del copper y capturas de enemigos contra la OAM; medir DMA
   integrado. Ampliar las tres copias de scroll cuando corresponda (P97).
6. C2/C4 y G7: PF1 doble, Banzai y desbordes, memoria y colores sin aproximar.

Z1, H1, A1/A2 quedan independientes cuando estén satisfechas sus dependencias.
S5 sigue acotado a una sesión y con prioridad menor por O5.
