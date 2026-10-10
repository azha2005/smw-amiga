# G4-3 — Rex en los pares de Mario (0-1/2-3) fuera de sus filas

2026-10-10. Sigue a G4-2 (`informe-g4-2-1010.md`). Misma rama y worktree,
sin merge ni push. **Va después de G4-2o**: G4-2 quedó apagado por
defecto (`G5L_MAXPL` = 1) porque empeora D1, y G4-3 cuesta todavía más.
Todo lo de abajo se construye con `-DG5L_MAXPL=2`.

## Objetivo

Hoy los Rex van solo en los pares 4-5 y 6-7 (G4-2: hasta 2 por foto, con
reuso vertical por encadenado DMA). Los pares 0-1 y 2-3 son de Mario, pero
en las filas donde Mario no está (±1 línea) quedan libres. La cota sin
colores de G4-1 §3 dice cuánto se gana:

| traza | hoy (G4-2) | cota con 0-3 |
|---|---:|---:|
| `yi1` | 2.043 | 2.111 |
| `normal` | 632 | 691 |
| `hills2` | 2.498 | 2.865 |
| `stress_back` | 2.576 | 2.882 |

Lo que no entra sigue yendo a la cola de bobs (G7).

## Partida

```sh
export PATH="$TEMP/pyshim:/c/msys64/ucrt64/bin:$PATH" VBCC=/c/Users/JC/vbcc PY=python
python tools/lint_port.py
python tools/regress.py --baseline tools/baseline_pc.json --level --g5l --bm1
python tools/g5l.py trace --multi --traces yi1 normal spin_kill hills2 shells stress_back stress_sprites pw_estrella
python tools/g5l.py game --bin work/g42/hills2/game.bin --lst work/g42/hills2/game.lst   # binario de G4-2 con MAXPL 2: informe §3
```

Esperado: `RESULTADO: OK`, `G4-1 TRACE: OK` y `G5L GAME: OK` con los
números de los informes de G4-1 y G4-2.

## Pasos

1. **La referencia primero (Python, como G4-1).** En `plan_frame_n`
   (opción `mario_pairs`), los pares 0-1/2-3 como canales que solo valen
   en las filas libres de Mario (±1). Medir con colores, porque la cota de
   G4-1 §3 no los tiene. Hay que contar:
   - **Rex que comparten filas con otro Rex ubicado.** Es muy probable en
     `yi1`, donde los Rex que faltan caminan sobre el mismo suelo. G4-2 los
     evitó: el 68000 calcula bandas solo contra Mario. Si son la mayoría
     de lo que se gana, el paso 3 tiene que llevar al 68000 la ocupación
     por fila de `band_need_n`/`band_assign_n`.
   - **Prioridad.** Los sprites 0-3 se ven delante de los 4-7. Contar las
     fotos en las que un Rex de 0-3 y uno de 4-7 se cruzan en el mismo
     píxel y el orden de la OAM de la SNES dice lo contrario
     (`check_trace_n`: "tapados"). Si pasa, se cambian los pares o el Rex
     va a bob.

   Puerta: `trace --multi --mario-pairs` con 0 errores y 0 tapados. Con la
   opción apagada, los números de hoy sin cambios. Registrar la decisión
   con el número.
2. **El flujo.** El flujo de Mario lo arma la CPU en cada foto
   (`mario_sprite`, `MSPR_WORDS` = 84: 40 filas por sprite, `SPRBUF` por
   foto en `game.s`). Para que un Rex vaya en el mismo canal, encadenarlo
   detrás o delante del de Mario. Hay dos opciones:
   - agrandar el búfer de Mario por foto (POS/CTL + filas del Rex + fin);
   - una cadena por lista como la de G4-2 que copie las filas de Mario.

   Elegir midiendo bytes de chip (memmap; el margen era de 35.680 B en el
   replay) y ciclos de copia. Generalizar `channels_n` y `expected_list`
   para que `g5l.py game` compare también los punteros y flujos de 0-3.
3. **68000** (`g5l.s`): los canales 0-3 en `g5l_geo`/`.multi`, los colores
   según el paso 1 y el encadenado del paso 2. El camino de un Rex
   (`g5l_pcget`) no cambia.
4. **Puertas:**
   - `g5l.py game` exacto en yi1, hills2, stress_sprites y stress_back;
   - `dc_loop_verify.py`, regresión completa y memmap sin violaciones;
   - A/B BENCH en WinUAE (normal/back/sprites/hills2, como en G4-2), con
     el costo reportado como trade;
   - captura de una foto con un Rex en un par de Mario (`g5l.py shot
     --only`), con 0 píxeles distintos contra el control.
5. Informe `docs/informe-g4-3-<fecha>.md` y cierre según ROADMAP §7.

## Trampas

- P108 (el banco es inmutable) y P125 (la caché de una cadena solo vale si
  las dos fuentes son del banco). Con Mario como fuente no hay banco: su
  flujo cambia en cada foto.
- P39/P42/P46/P51/P59 (copper), P100 (dos columnas), P115/P116 (colchón y
  caché de Mario) y P123 (registros de `dc_loop`).
