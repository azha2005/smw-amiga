# Informe G5L-R — el Rex por sprites 4-7, colchón y tirones (2026-10-08/09)

Rama `g2t-b2bis` (worktree `wt-g2t-b2bis-1008`). Commits: `9c84534`
(G5L-R, 4 mapas limpios y camino rápido), `c90e961` (colchón de tercera
lista, `-DHZ25`, sin banco G3 en el juego), `052dac2` (caché del plan,
clave de Mario, traza por VBL). Todas las cifras de fotos son de WinUAE
cycle-exact (`tools/shot.ps1 -Exact` + `tools/game_read.py --auto`) sobre
el replay de YI1 (6312 frames lógicos); los ciclos por rutina, de Musashi
(`tools/g5l.py game` y perfiles de la sesión), cota inferior (×1,3-1,5).

## 1. Qué es G5L-R

El pedido del usuario: "que se dibujen los enemigos y quepan en el
presupuesto". Los enemigos **se ven por primera vez en la Amiga**: el Rex
va por los sprites de hardware 4-7 (adosados, 15 colores) y Mario por los
0-3. Comparten COLOR17-31; donde chocan, el copper recarga los colores por
fila (cubetas, `g5l_place`, `g5l_emit`).

- **4 mapas limpios** (`tools/g5l.py` `CLEAN_PERMS`): cada variante del
  Rex se pre-renderiza con 4 asignaciones de sus colores a índices. Por
  foto gana el primer mapa sin choque con Mario (camino rápido
  `g5l_fast`: dos transiciones o un recorrido de dos conjuntos); si todos
  chocan, el de menos choques va por el camino completo (need, plan con
  bandas, sweep, patch).
- **Máscaras de Mario** de 64 bits por índice (`g5l_mfill`, caché de 4
  poses) y las 15 ventanas de una vez (`g5l_mwall`, carga `MWLD`).
- **Sin banco G3 en el juego**: G5L-R solo dibuja variantes limpias
  (`g5l_cdma`); el banco hace falta para armar la tabla, no en la Amiga.
  Chip 489,9 → 424,8 KB.

| paso | fotos perdidas (WinUAE) |
|---|---|
| primer G5L-R (bench4) | 441 |
| 4 mapas limpios | 349 |
| `g5l_mfill` por pares | 299 |
| camino rápido extendido, `MWLD`, choques contados | **263** (`9c84534`) |
| control sin enemigos (misma tanda) | 27 |

Musashi por foto con Rex en `9c84534`: media 29,7 k, p50 23 k, p90 51 k,
máx. 94 k ciclos.

## 2. 25 Hz y el colchón de tercera lista

A pedido del usuario se armó una muestra a 25 Hz (`-DHZ25`: la imagen
cambia en VBL alternos) para compararla con 50 Hz en WinUAE. El usuario:
"es bastante duro perder tanta fluidez". Se propuso y probó el colchón.

**`-DCUSHION`** (solo replay + O5): tercera lista del copper (49 500 B de
chip) y **latencia fija de 2 frames lógicos**: `dc_vb` muestra la foto
publicada cuando `DC_NLOG − R_FRAME ≥ 2`; el render toma la foto
siguiente aunque la publicada espere (4 buffers de sprites de Mario). Un
render que llega hasta un frame tarde ya no repite imagen. La lista
siguiente es la que no está publicada ni se ve (`DC_FLIST`). Estado de la
lista C en `scroll.s` (`V_COP3`, `V_LSC`, `V_LTC` por AllocMem, P74) y en
`g5l.s` (`GV_RECC`, `GV_RKC`, `GV_PNVC`, `GV_NULLC`). Llamadas lejanas de
`dc_loop` a `scroll.s` con `FBSR` (P102). Chip con colchón: 483,8 KB
(quedan ~40 KB).

| | fotos perdidas | racha | VBL sin imagen nueva |
|---|---|---|---|
| sin colchón (`9c84534`) | 263 | — | — |
| con colchón (`c90e961`) | 88 (1,39 %) | 2 (una vez) | 90 |
| + caché del plan y clave de Mario (`052dac2`) | **67 (1,06 %)** | **1** | 69 |
| control sin enemigos | 27 | 1 | — |

**Decisión del usuario (2026-10-09): se acepta el colchón** (+20 ms de
latencia), "aunque hay que revisarlo más de cerca; Rex se mueve raro".

## 3. Los tirones del Rex

El usuario: "tirones sueltos, es como si se saltara pasos pero no
ralentiza el resto de la composición".

**Diagnóstico con la sucesión de frames real.** `-DVBTRACE` anota en cada
VBL la foto que se ve y el `SPR4POS` de su lista; `tools/vbtrace.py` la
lee de la memoria de WinUAE al terminar el replay. Resultados (`c90e961`):

- La imagen de cada foto **coincide con Musashi**: en los frames con
  saltos raros de posición (p. ej. 1534: hstart 273 → 278) es un cambio de
  pose (Rex aplastado, `62`/`60`), y siempre hstart = x0 + 160. No hay
  error del render ni de las tres listas.
- Sobre 5230 VBL: 40 repiten la imagen y 39 saltean una foto. **Cada
  repetición va seguida, ~3 frames después, de un salto** (P115): con el
  colchón la latencia no puede quedar en 3 (los 4 buffers de foto están
  ocupados), así que se pierde una. A la vista: el Rex "se traba y salta";
  con la cámara quieta solo él se mueve, por eso el resto no parece
  afectado.
- Las rachas tarde son tramos de ~8 frames: con Mario quieto y el Rex
  caminando el coste tiene período 16 (8 frames por el camino rápido,
  ~30 k; 8 por el completo, 50-75 k, según la pose de las patas), dos Rex
  en pantalla, y la zona del daño de Mario (frames 3305-3364).

**Arreglos (`052dac2`):**

1. **Caché del plan** (`g5l_pcget`/`g5l_pcput`, 4 entradas, reemplazo
   rotativo). need/plan/sweep no dependen de la x: la clave es la pose de
   Mario (`GV_KBUF`), `GV_R0`, `GV_MSH`, la paleta y la forma del Rex;
   se guardan `GV_VAR`, `GV_NREM`, `GV_REM` y las transiciones de las
   cubetas (hasta 80). Medida previa: 54 % de aciertos con 2 entradas, 59 %
   con 4, 61 % con 8, sobre 283 fotos lentas del camino completo.
   plan/sweep: ~300 → 145 llamadas en el replay.
2. **Clave de la caché de Mario** sin los pares de punteros GFX32 que sus
   fichas no leen (P116): un puntero animado que Mario no muestra avanzaba
   una ficha por foto y hacía fallar la caché en cada una (13,4 k por
   foto). `g5l_mfill`: 307 → 111 llamadas.
3. `g5l_table` por `GETBASE` (con `-DCUSHION` queda a más de 32 KB).

`tools/g5l.py game`: **G5L GAME: OK** (las 6313 listas del asm iguales a
la referencia). lint y `regress.py --baseline tools/baseline_pc.json
--level` verdes; los 5 builds por defecto dan el mismo binario.

## 4. Lo que queda

- **67 fotos perdidas contra 27 del control**: unos 40 tirones atribuibles
  al Rex. Zonas (traza de `052dac2`, repeticiones): 1042-1124, 1610-1708,
  2072-2076, 2457, 2757, **3309-3360** (14), 4040, 4214-4218, 4554-4574,
  5442, 5851. Peor tramo medido en Musashi: daño de Mario con el Rex,
  camino completo 60-90 k por foto (sweep 13 k, plan 11 k, patch 8-13 k,
  place 6-8 k, emit 6-8 k, fast fallido 5 k). D1 sigue roja (el control
  tampoco la cumple).
- **El colchón solo existe en el replay** (`game.s` falla a propósito con
  `-DCUSHION` sin `-DREPLAY`): falta el juego en vivo (reinicio, modo
  diagnóstico, latencia de entrada).
- G5L-R y el colchón **no son el build por defecto** (opt-in `-DG5L
  -DCUSHION`); hacerlos defecto cambia los hashes y es parte de la
  integración.
- `-DHZ25` queda como muestra; no se usa.

## 5. Decisiones tomadas por el agente (registradas)

- 4 mapas limpios con las permutaciones de `CLEAN_PERMS` (medidas con
  `mapsearch.py` de la sesión: cobertura del camino rápido).
- Quitar el banco G3 del juego cuando G5L está activo (65 KB de chip).
- Caché del plan de 4 entradas (la curva de aciertos se aplana después).
