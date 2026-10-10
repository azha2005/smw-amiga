# G4-2 — varios Rex por foto en el 68000

2026-10-10. Sigue a G4-1 (`informe-g4-1-1010.md`). Misma rama y worktree,
sin merge ni push.

## Objetivo

El 68000 hace lo que hace `plan_frame_n`: ubica hasta 4 Rex de la foto
(`G5L_MAXREX`) en los pares 4-5 y 6-7, con reuso vertical por
**encadenado DMA** (gap 1, medido en G0). No hay MOVE nuevos en el copper.
Lo que no entra no se dibuja y se cuenta. La cola de bobs es G7.

## Partida

```sh
export PATH="$TEMP/pyshim:/c/msys64/ucrt64/bin:$PATH" VBCC=/c/Users/JC/vbcc PY=python
python tools/lint_port.py
python tools/regress.py --baseline tools/baseline_pc.json --level --g5l --bm1
python tools/g5l.py trace --multi --traces yi1 normal spin_kill hills2 shells stress_back stress_sprites pw_estrella
```

Esperado: `RESULTADO: OK` y `G4-1 TRACE: OK` con los números del informe
de G4-1.

## Pasos

1. **Medir antes de diseñar el asm.** En `run_multi_photo`, de los Rex que
   G4-1 suma, contar cuántos comparten filas con otro Rex ubicado (dos
   Rex de una columna, uno al lado del otro) y cuántos están separados en
   vertical. Si los que comparten filas son pocos, la primera versión
   puede mandarlos a bob. Así el 68000 solo generaliza la secuencia de
   transiciones (sweep) y no la ocupación de colores en las mismas filas.
   Registrar la decisión con el número.
2. **Referencia de la lista.** `channels_n`: por par, un flujo por mitad
   en un búfer de chip **por lista**, con POS/CTL y las filas de cada Rex
   en orden y el terminador al final. Los Rex sin bandas copian de
   `g5l_clean.dma`; los que tienen bandas, del parche. Generalizar
   `expected_list` y `run_game` (opción `--multi`) para comparar palabra
   por palabra. Tamaño del búfer: 3 listas × 4 flujos × (2 Rex × (32 + 1)
   + 1) × 4 B ≈ 3,2 KB de chip, contra los ≈ 24,8 KB libres. Anotarlo en
   `memmap`.
3. **68000** (`g5l.s`): `g5l_choose` deja la lista de candidatos ordenada
   (fila, ranura). Por cada candidato: el par libre, la variante y las
   bandas contra Mario (y contra los Rex de las mismas filas, si el paso 1
   no los mandó a bob), las transiciones de todos (`g5l_sweep`) y el plazo
   (`g5l_place`). Después, el encadenado de flujos en el búfer de la
   lista. La caché del plan (`g5l_pcget`) se queda en el caso de un Rex;
   con dos o más va el camino completo, y se mide.
4. **Puertas:**
   - `g5l.py game --multi` exacto en el replay YI1 y en el de `hills2`.
   - `dc_loop_verify.py`, regresión completa y `memmap` sin violaciones.
   - A/B WinUAE (BENCH normal/back/sprites, el mismo método que G5L-N).
     Hoy el estrés tiene más Rex, así que más CPU es esperable: medir y
     reportar como trade. No se activa por defecto si D1 empeora más que
     el ruido del control sin que el usuario lo vea.
   - Captura de `hills2` en una foto con 2 Rex ubicados (`g5l.py shot`
     generalizado).
5. Informe `docs/informe-g4-2-1010.md` (o la fecha del día) y cierre según
   ROADMAP §7.

## Trampas

P39/P42/P46/P51/P59 (copper), P100 (dos columnas), P108 (el banco es
inmutable: el encadenado va en el búfer por lista, nunca en
`g5l_clean.dma`), P123 (registros de `dc_loop`) y P124.
