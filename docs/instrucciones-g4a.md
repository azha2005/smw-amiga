# G4-A — todos los enemigos en sprites: inventario y presupuesto

2026-10-10. Primera tarjeta de la ola 4 (a), antes de G4+G6. Misma rama
y worktree, sin merge ni push. **Solo medida, en Python; el binario no
cambia.**

## Por qué

G5L dibuja solo al Rex. Su tabla (`work/g5l/g5l.bin`, slow) ocupa
128.724 B: 48 formas × 4 mapas de color (≈ 550 B por variante, 106 KB)
más 22 KB de máscaras de Mario, que se comparten. Las variantes DMA
(`g5l_clean.dma`, chip) ocupan 16.656 B. En el vivo quedan 61.288 B de
slow y 24.856 B de chip (`memmap.py work/rg_bm1/game.lst`). Antes de
generalizar el plan (G4) hay que saber, con números:

1. qué enemigos aparecen, con cuántas formas, de qué tamaño y con cuántos
   colores;
2. cuántas columnas de sprite pide cada línea fuera de Mario, contra los
   4 canales que hoy usa el Rex (4-7), y qué iría a la cola de bobs;
3. cuánta memoria costaría la tabla G5L para todos, y si entra.

## Partida

```sh
export PATH="$TEMP/pyshim:/c/msys64/ucrt64/bin:$PATH" VBCC=/c/Users/JC/vbcc PY=python
python tools/lint_port.py
python tools/regress.py --baseline tools/baseline_pc.json --level --g5l --bm1
```

Entradas (todas en `work/`, derivadas de la ROM, nunca en git, R9):

- `oam_{yi1,normal,spin_kill}.trace` (SOT1): cada despacho de sprite con
  su número, ranura y fichas OAM (`g5ref.read_trace`). Sirven para el
  inventario por tipo.
- `oracle_*_oam.bin`: la OAM entera por frame de cada grabación, incluido
  el estrés (`stress_back`, `stress_sprites`, `stress_piranha`,
  `stress_vert`), Banzai, Chuck, meta, power-ups y caparazones
  (`G.load_oam_bin`). Sirven para la demanda por línea.

## Pasos

1. `tools/g4a.py inv`: por número de sprite, en las tres trazas: frames
   visibles, máximo simultáneo, formas distintas (la clave de
   `g5l.build_table`: fichas + prioridad), ancho y alto del rectángulo,
   columnas de 16 px y paletas OAM usadas. **Puerta de cruce:** el Rex
   (`$AB`) tiene que dar las formas del banco G3 que usa G5L (48, o
   explicar la diferencia ficha por ficha).
2. `tools/g4a.py lines`: en cada `oracle_*_oam.bin`, separar las fichas
   de Mario (las mismas que `g5l.mario_entries`) del resto. Por línea
   visible (224), columnas de 16 px que piden los objetos que no son
   Mario. Un objeto es un grupo de fichas de un mismo despacho cuando hay
   traza. Sin traza, usar fichas adyacentes con la misma paleta, y decir
   que la agrupación es aproximada. Por grabación: frames con más de 4
   columnas en alguna línea, máximo, y líneas con más de 4 (y con más de
   6, si Mario dejara 2-3 libres en esas líneas).
3. Asignación simple, como cota: columnas a los canales 4-7 por orden de
   la OAM, objeto entero o nada (P100: el Rex mide 20 px, dos columnas).
   Lo que no entra se cuenta como bob, por tipo. No es el plan de G4.
   Sirve para saber cuánta cola de bobs hace falta.
4. Memoria, **estimado y rotulado así**: por tipo, formas × mapas ×
   tamaño de `variant_record` (con el ancho, el alto y los colores
   medidos), y flujos DMA por columna y mitad (`clean_streams`), con la
   deduplicación medida en el Rex como factor. Comparar con el margen de
   slow y chip del vivo, y con lo que piden C2/C4 (ROADMAP 10.7).
5. Informe `docs/informe-g4a-1010.md`: tablas por tipo y por grabación,
   la cota de bobs y la memoria. Al final, qué formato de tabla puede
   servir para G4: el G5L tal cual, menos mapas, formas compartidas o una
   máscara calculada en vivo. Cada opción con su número. Esto es diseño,
   no decisión del usuario. Si una opción toca la fidelidad (por ejemplo,
   parpadeo o enemigos que faltan), se registra como dato y no se elige.

## No toca

`player/*`, el banco G3, `g5l.py` (solo se importa). Sin builds de
WinUAE: es todo en la PC.
