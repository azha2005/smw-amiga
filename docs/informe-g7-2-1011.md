# G7-2 — OAM de la foto, fuentes y límite local de color

2026-10-11. Continuación de `7389276`, sin subagentes. **G7-2 parcial**:
captura y fuentes verificadas; tres sondas exactas en WinUAE; la paleta
general no pasa. No hay cola de bobs ni efectos activados en el vivo.

## OAM y memoria

`G7_DOUBLE` captura 256 B de `$0200` y 64 B de `$0420` en cada foto.
Con CUSHION son 1.280 B adicionales de slow. `R_SWS_VALID` permanece a
cero tras `loadstate`: SYNC no contiene OAM inicializada. Se habilita
después de `level_frame`. El render consumirá `DC_REND`, no la RAM futura.

`sws_cmp.py` cruza además el contenido de la foto con la RAM de la
lógica. Las cinco trazas dan `SWS RAM/OAM/PHOTO: OK`, 0 diferencias:
6.279 / 2.075 / 2.954 / 1.006 / 3.017 fotos comparables. Evidencia:
`work/g7s2-sws.log`. `g7_photo_verify.py` comprueba todas las capturas,
la cobertura gráfica y diez capturas nuevas con FRONT/PEND/REND ocupadas;
esas tres fotos permanecen idénticas. `work/g7s2-photos.log`:

| traza | frames | fichas visibles | formas | máximo de captura, ciclos CPU |
|---|---:|---:|---:|---:|
| yi1 | 6.313 | 3.500 | 24 | 12.450 |
| pw_bloques | 2.076 | 1.459 | 14 | 11.846 |
| chuck_kill | 2.955 | 1.921 | 15 | 12.050 |
| spin_kill | 1.007 | 980 | 14 | 11.844 |
| stress_piranha | 3.018 | 2.086 | 16 | 13.202 |

Los ciclos son de **toda** `dc_capture` en el estado sintético final,
sin DMA; no son el incremento de la copia ni una medida D1.

`memmap.py`, con segundo PF1 y los 12 KiB ya reservados:

| BM1 | chip | libre chip | slow | libre slow |
|---|---:|---:|---:|---:|
| vivo | 522.448 | 1.840 | 511.656 | 12.632 |
| replay | 510.920 | 13.368 | 512.136 | 12.152 |

0 violaciones. Logs `work/g7s2-live-memory.log` y
`work/g7s2-replay-memory-final.log`. No se ha incorporado el banco
generado al binario; el espacio chip para él ya está contabilizado.
El vivo por defecto sigue idéntico, SHA256
`33f2250a1b4231069ab975bfdc4f7d2336cd814a0e4e95d13bd862659c5b638b`.

## Fuentes exactas

`python tools/g7_sources.py` genera `work/g7/sources.bin`, formato G7S1:
directorio de 512 offsets, 128 colores OCS y fichas canónicas 8×8 con
cuatro planos de índices más máscara, 80 B por ficha. Las fichas de
16×16 se componen como la VRAM SNES; el flip se aplica a toda la ficha.

79 fichas, 79 únicas, **7.616 B**: quedan 4.672 B de la reserva para
trabajo. 25.088 píxeles contrastados contra `ref_pixel`, con flips,
tamaños, clipping y máscaras. En las cinco trazas también se comprueban
todas las formas observadas. El replay expuso `$6C-$6E` y `$FF` de
`StarSparkleTiles`; se incluyeron, además de los rangos originales,
cuadrantes del humo y las fichas de 3-UP de la página alta.

## Referencia de color y sondas reales

`g7_color_plan.py` prepara el copper real y el diario del mapa con el
68000 de Musashi para cada foto; reconstruye los índices del terreno y
las recargas de PF1. Conserva el instante de los eventos de hardware y
busca préstamo de registros o un plan nuevo. Los índices del terreno
permanecen fijos en esta búsqueda. La OAM se sitúa en **fila de copper
= y + 1**, como `mspr/g5l`. Se excluyen los píxeles tapados por Mario y
los objetos G5L efectivamente ubicados delante de PF1.

Se corrigieron tres rechazos del prototipo: no mover recargas que
rozaban un píxel visible en el margen exploratorio; ampliar la búsqueda
de asignaciones multicolor (las primeras 64 no bastaban); y permitir
índices distintos en grupos de efectos separados. La búsqueda sigue
acotada y su fallo **no demuestra imposibilidad**.

La puerta principal usa el contrato **medido** de G2T-A
(`informe-g2t-a-1007.md` §§4–6), sin encadenar desde el borrado, con
WAIT libre conservador ≥48 px, P110 y fin ≤351−8·nb. Un experimento
adicional `--phase-max 7` desplaza las recargas entre 0 y 7 píxeles;
es más restrictivo y no es el contrato calibrado. Sus rechazos antiguos
no se presentan como falta física de colores. D8 no se cambia.

`g7_color_probe.py` genera un **arnés temporal de una sola foto**, con
paleta e índices precalculados. Escribe PF1 por CPU sobre el anillo libre;
no implementa bobs, no selecciona tablas por frame en el producto y su
coste no sirve para BENCH. Comparación de pantalla completa contra el
control más los píxeles exactos esperados, WinUAE **cycle-exact** KS1.2:

| foto | píxeles de efecto visibles | distintos, captura ×2 |
|---|---:|---:|
| k409 | 7 | **0** |
| k5026 | 11 | **0** |
| k6015 | 191 | **0** |

Evidencias miradas: `work/g7-probe/<k>/probe/check.png` y `check.json`.
La captura inicial k409, con 35 s de espera, aún mostraba la carga;
se repitió control y candidato con 90 s. Las otras esperas fueron
140/160 s. No comparar una pantalla de carga como si fuera el juego.

La barrida anterior sin oclusión de enemigos, con 30.000 estados por
asignación, terminó con 9.644 filas: 9.582 planes y 62 sin resolver;
`work/g7-plan-final/report.json`. No es la medición final del modelo
con oclusión completa. La repetición con oclusión completa y presupuesto compartido de 30.000
estados por fila se interrumpió al cierre solicitado por el usuario:
`work/g7-plan-complete.log`. No hay informe final de esa barrida; no
contabilizarla como prueba completa ni usar el informe bounded abandonado.

## Cota independiente: k6047, fila 161

`g7_color_bound.py` no usa el resultado del buscador para decidir
factibilidad: toma los **píxeles requeridos** del testigo y enumera todas
las paletas iniciales y las cargas posibles en una ventana local.

En **x=151..181** aparecen nueve colores distintos:
`000,448,66B,851,88C,CCC,DA3,EFF,FD7`. Solo hay siete registros opacos
de PF1. En este tramo, antes del codo, el contrato calibrado permite
MOVE en x=7 mod 8 y una cadena avanza 16 px: candidatos
151,159,167,175; caben como máximo dos cargas. Se ignoran los costes
de WAIT, sprites y otras recargas, para favorecer al plan candidato.

Nueve colores con siete registros y dos cargas obligan a cargar cada
color una sola vez: se enumeran todas las parejas de colores ausentes
al inicio, sus órdenes, las parejas de ranuras separadas ≥16 px y las
expulsiones. **1.302 candidatos examinados, ninguno factible.** La
prueba permite reasignar cualquier índice del terreno: no depende de
la restricción de índices fijos del planificador. Tampoco hay oclusión
de hardware que elimine los píxeles de esta ventana en la foto.

```sh
python tools/g7_color_plan.py --bin work/rg_g7_double_replay/game.bin --lst work/rg_g7_double_replay/game.lst --from-k 6047 --to-k 6047 --out work/g7-case6047
# FALLA: las filas 161 y 163 siguen sin plan; conservar el report.json
python tools/g7_color_bound.py --report work/g7-case6047/report.json
# G7 COLOR BOUND: SIN PLAN EN ESTE CONTRATO; feasible=false
```

Certificado e imagen: `work/g7-bound/certificate.json`, `window.png`.
Esto prueba un límite del **contrato de temporización actual**, no que
todo método posible de la Amiga sea inviable. Cambiar la rejilla requiere
una calibración nueva; aumentar la búsqueda no resuelve esta cota.

## Estado de la puerta y alternativas

G7-2 queda parcial. La instrucción vigente dice: «Si un plan concreto
demuestra un color sin lugar exacto, mostrar al usuario el caso y las
alternativas». No se programa G7-3 sobre una paleta global que falla.

Alternativas exactas a evaluar: una temporización nueva conservando D8,
o apoyo puntual de sprites hardware para los píxeles que no caben en PF1
(excepción a la decisión de dibujar todos los efectos por bobs). La
segunda exige demostrar disponibilidad, rearmado y colores: no basta
con que Mario tenga píxeles transparentes. En k6047 Mario opaco ocupa
filas 133..160; G5L ubica objetos 16×16 en (125,129) y 19×32 en (253,161).
Es **geometría**, no una prueba de canales DMA libres en fila 161.
No se ha aproximado ningún color, omitido efectos ni alterado D8.

D1 sigue roja. Los 217→269 omitidos son la medición histórica de G7-1,
antes de añadir la copia de OAM; **no se midió BENCH nuevo**. El prototipo
sigue opt-in y el ADF vivo distribuible no cambia.

Lint y regresión completa `--level --g5l --bm1`, SWS RAM/OAM/PHOTO en las
cinco trazas y OAM68K: verdes. La regresión incluye generación de fuentes,
capturas protegidas, la sonda de color offline k409 y seis tests sintéticos
(incluidos controles positivo/negativo de la cota). Los derivados permanecen
en `work/`. Orden vigente: `PROXIMO.md`.

## Decisión recibida y cierre

2026-10-11, usuario: «Apoyo puntual de sprites hardware para conservar
los colores exactos». Queda autorizada la investigación de esa excepción
puntual a efectos por bobs. Disponibilidad DMA, rearmado y paleta compartida
todavía no están demostrados. El usuario pidió anotar su decisión y cerrar;
no se continúa la investigación en esta sesión.
