# G7-0 y G7-1 — memoria y doble PF1

2026-10-10. Continuación de `PROXIMO.md` después de SW-S. **Los efectos
todavía no se dibujan.** Se resolvió la memoria y se implementó el doble
PF1 opcional (`-DG7_DOUBLE`), con arbitraje del colchón y cursores propios.

## Memoria (G7-0)

El vivo incluía 38.602 B de replay aunque solo consume el arranque.
`tools/replay_seed.py` conserva exactamente la cabecera necesaria, la carga
de sprites inicial, la primera operación y su estado: **730 B**. `PADTEST`
y `REPLAY` conservan la grabación completa.

`mkscroll.py` ubica CHG delante de LNS, después de todos los datos del
chipset. BM1 vivo migra CHG y la cola a slow: **31.208 B adicionales de
chip recuperados**. No cambia el contenido de ninguna sección. Se corrigen
también los offsets de fuentes CHG que contiene D_COIN (143 referencias
totales entre chip y slow). `game_build.sh` regenera blobs del orden anterior;
el 68000 rechaza un layout incompatible antes de copiar.

Medidas de `memmap.py`, con C SPR_OAM y todos los tipos G5L:

| vivo BM1 | chip | slow |
|---|---:|---:|
| antes | 482.232 B | 516.512 B |
| G7-0, sin segunda reserva | 451.024 B | 509.896 B |
| `G7_RESERVE`: segundo PF1 + 12 KiB de fuentes/máscaras | 522.448 B | 509.936 B |
| `G7_DOUBLE`, mismas reservas | 522.448 B | 510.328 B |

El prototipo deja **1.840 B de chip y 13.960 B de slow** después de reservar
el segundo PF1 y los 12 KiB de fuentes. Ese banco todavía es una reserva:
G7-2 debe medir sus fuentes y respetar el tope. Diagnóstico, tres listas
del copper y fidelidad se conservan. No hay audio reservado.

## Propiedad de PF1 (G7-1)

Con CUSHION hay cuatro fotos y tres listas: visible, pendiente y render.
`g7_ownership_probe.py` reproduce en el 68000 la entrada al dibujo con las
tres ocupadas. Asignar dos PF1 por paridad de lista escribiría una foto
todavía publicada.

El render toma primero DC_REND y prepara el copper y los sprites de
la lista libre. Después `g7_select` espera, con IRQ habilitada, a que
VERTB consuma DC_PEND, justo antes de escribir columnas/mapa en PF1. Elige el PF1 opuesto al de DC_FLIST. La foto tomada queda
protegida por el protocolo O5 durante la espera; no se toma una foto más
nueva al salir. La lógica sigue en COPER a 50 Hz. La latencia y las fotos
omitidas se comprueban en BENCH; no se deducen de esta descripción.

Cada anillo conserva V_P, V_CCOL, V_CBLK y su secuencia `_tile_read`.
`tile_apply` vuelve a dibujar en el otro anillo aunque D_MAP ya tenga el
resultado. Solo se escribe el PF1 libre. Al arrancar/reiniciar se clona
la ventana inicial; cada lista guarda qué PF1 usa. Se espera el último
blit antes de publicar. No se copia el playfield entero por frame (R5).

El modo está **opt-in**. El vivo por defecto conserva el render anterior
y ya se beneficia de G7-0. La prueba por defecto del prototipo produjo el
mismo SHA256 del vivo que antes de añadir G7_DOUBLE.

## Verificación

- `regress.py --baseline tools/baseline_pc.json --level --g5l --bm1`:
  RESULTADO: OK; incluye reservas reales en vivo/replay, migración con
  arena agotada y layout inválido, consumidor real `coin_prepare`, muerte,
  reinicio, propiedad de los dos PF1 y espera/liberación por VBL.
- `sws_gate.sh`: RAM y OAM OK en las cinco corridas. `oam68k_gate.sh`:
  OAM68K: OK.
- WinUAE cycle-exact KS 1.2: antes/después de memoria, y después con
  doble PF1, **0 píxeles distintos** en k 199, 1199, 3149, 4699, 6049,
  6299. Evidencias `work/g7-visual/` y `work/g7-double-visual/`.
- Comparación de un blob viejo regenerado automáticamente: idéntico
  byte a byte al generado desde el conversor actual.

## Color: alcance del preflight

`g7_color_audit.py` lee los efectos del 68000 real y usa el criterio
conservador de intervalos/GAP=48 de `d8demote.py`: 1.417 fotos con efectos,
26 formas, 20.696 filas analizadas; 1.075 requieren estudiar otro plan.
Primer testigo k=409, humo, entrada 11, x=110, y=185, fila +2: blanco
`$FFF` sin registro libre **bajo ese criterio conservador**.

Esto **no demuestra imposibilidad de color**: incluye intervalos futuros
en el margen de 48 px y no construye recargas nuevas ni mide su ranura.
No autoriza aproximar y no se usa como puerta negativa de G7. Evidencia:
`work/g7-colors/report.json`, `first-effect.png`.

## Iteraciones de G7-1

La barrida completa SW1 de 126 fotos a HOLDEVERY=50 encontró **8 píxeles
físicos (dos lógicos) distintos en k4599**, en el borde derecho de una
tubería gris: el control y la SNES tienen negro, el prototipo `$777`.
Las seis capturas aisladas anteriores no detectaban este caso.
Evidencia: `work/g7-sweep-multi/result.json`; 126 pares, ninguno ausente.

BENCH cycle-exact KS1.2, control y candidato en la misma tanda:

| variante | fotos omitidas / 6312 | racha máxima | peor columns (ticks CIA) |
|---|---:|---:|---:|
| control, reserva sin doble PF1 | 217 (3,44 %) | 2 | 2.882 |
| doble PF1 inicial | 772 (12,23 %) | 11 | 28.492 |
| doble PF1, avance incremental de columnas | 741 (11,74 %) | 3 | 5.906 |

Evidencias iniciales: `work/g7-bench-initial/` y `work/g7-bench-multi/`
(`read.txt`); el primer control tuvo 218 fotos omitidas y los siguientes 217.
El avance incremental evita `draw_window` al atravesar varias columnas
en un uso del anillo; se prueba en ambas direcciones y al cruzar SLOTS.
La espera de propiedad está antes del tramo total medido por BENCH:
su media no representa todo el coste; manda el contador de fotos omitidas.
No se acepta el aumento de pérdidas ni se activa el prototipo por defecto.
G7-2 se preparó con un audit informativo; no se inició el dibujo de bobs.

Prueba aislada STOPF=4599: el prototipo actual da 0 píxeles distintos
frente al control SW1; suprimiendo las dos llamadas a `bm_share`, da 8.
Esto no reproduce el historial de la barrida completa y **no cierra**
la puerta: quitar S9 no es un arreglo demostrado. Evidencia:
`work/g7-share-probe/`, `work/g7-share-probe.log`.

## Tercera iteración: preparar antes de esperar

La espera al principio desperdiciaba el colchón aunque la lista del
copper de render ya estaba libre. Se adelantan build_mid/coin_list y
g5l_render; g7_select, columnas y diario se ejecutan después, y se
reparan los punteros de esa lista antes de dc_hdr/publicar. El PF1
publicado no se escribe. DC_REND no se cambia durante la preparación.

La copia temporal dio **261/6312 fotos omitidas (4,13 %), racha 2**
frente a 217/6312 del control. SW1 completo: **126 pares, 0 píxeles
distintos, ninguno ausente**, incluido k4599. Evidencias:
`work/g7-bench-defer/`, `work/g7-sweep-defer/result.json`.
El cambio de historial evita la diferencia observada; no se presenta
como una corrección general de la caché S9.

El código integrado incorpora sellos BENCH 18/19 para incluir la espera
y las columnas diferidas en columns/total y descontarlas de resto.
`g7_double_verify.py` sobre un binario BENCH prueba la aritmética con
sellos sintéticos (570/790/700/2610/480 ticks, partes 3/4/5/6/8).
Las medidas iniciales de 772 fotos se preservan en
`work/g7-bench-initial/`; `work/g7-bench/` se usa para la repetición final.

## Repetición del código integrado

BENCH final, con sellos de espera/columnas corregidos: **269/6312 fotos
omitidas (4,26 %), racha máxima 2**, frente a **217/6312 (3,44 %), racha 2**
del control. Son 52 fotos adicionales, no una mejora de D1. No hay
frames sin COPER ni resincronizaciones en ninguno. El doble PF1 sigue
opt-in; por defecto solo se activa la recuperación de memoria.

Media total del candidato: 13.477 ticks (94,8 %); máximo 32.747.
Columns ahora incluye espera, diario y segunda escritura de punteros:
máximo 11.245 ticks, no comparable con las etapas que excluían la espera.
Build_mid máximo 15.301; resto 19.356. Evidencia: `work/g7-bench/*/read.txt`.
La lógica conserva 50 Hz; la compuerta D1 de fotos omitidas sigue roja.
Lint y regresión completa pasan sobre el código integrado.

Barrida final sobre el código integrado: **126 pares, 0 píxeles
distintos, ninguna captura ausente**. `work/g7-sweep-final/result.json`.
El vivo distribuible `work/live/game.adf` conserva el render simple;
su binario coincide con el recompilado por la regresión (SHA256
`33f2250a1b4231069ab975bfdc4f7d2336cd814a0e4e95d13bd862659c5b638b`).
G7-0 y las pruebas de G7-1 quedan integradas; G7 completo queda WIP
porque las fuentes, los colores y los bobs de efectos aún faltan.
