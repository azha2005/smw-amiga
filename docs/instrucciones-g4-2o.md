# G4-2o — abaratar el camino de varios Rex

2026-10-10. Sigue a G4-2 (`informe-g4-2-1010.md`). Misma rama y worktree,
sin merge ni push.

## Por qué

G4-2 es exacto, pero una foto con 2 Rex cuesta ≈ 63 k ciclos de mediana
contra ≈ 25 k con uno. En el A/B, D1 empeora mucho más que el ruido (hills2
pasa de 210 a 398 fotos perdidas, sprites de 91 a 194), así que quedó
**apagado por defecto** (`G5L_MAXPL` = 1). Esta tarjeta tiene que dejar la
foto con 2 Rex lo bastante barata para activarlo. G4-3 (más Rex en los
pares de Mario) cuesta todavía más, así que va después.

**Objetivo:** con `-DG5L_MAXPL=2`, el A/B dentro del ruido del control
(±10 fotos en back) en back, sprites y hills2. Una cota intermedia que
sirve: la mediana de una foto con 2 Rex ≤ 1,3 × la de una foto con 1 Rex
(≈ 33 k).

## Partida

```sh
export PATH="$TEMP/pyshim:/c/msys64/ucrt64/bin:$PATH" VBCC=/c/Users/JC/vbcc PY=python
python tools/lint_port.py
python tools/regress.py --baseline tools/baseline_pc.json --level --g5l --bm1
ORACLE=work/oracle_hills2.bin REPLAY=work/hills2_replay.bin GDEFS="-DREPLAY -DG5L_MAXPL=2" OUT=work/g42o/hills2 sh tools/game_build.sh
python tools/g5l.py game --bin work/g42o/hills2/game.bin --lst work/g42o/hills2/game.lst
```

Igual para `stress_back` y `stress_sprites` (`ORACLE`/`REPLAY`, como en
`work/g42/ab_build.sh`). Esperado:
`G5L GAME: OK` con los números del informe de G4-2 §3. Las partes (`partes`
del JSON) dan la línea de base:

| parte (hills2, 605 fotos con 2 Rex) | media |
|---|---:|
| `g5l_sweepn` | 17.510 |
| `g5l_emitn` | 10.266 |
| `g5l_plan` (dos por foto) | ≈ 6.700 |
| `g5l_need` | 3.149 |
| `g5l_choose` | 2.201 |
| `g5l_rxsave`, `g5l_place_e`, `g5l_edges` | (con `--pcprof` y `pcsect.py`) |

## Ideas, en orden de lo que se espera ganar (medir cada una)

1. **Camino rápido sin bandas.** En la mayoría de las fotos ningún Rex
   choca con Mario (`con_bandas` es 217 de 1.893 en hills2). Entonces cada
   Rex tiene un grupo por índice, como en `g5l_fast`. Las transiciones de
   un índice son los tramos de Mario más un tramo por Rex, separados en
   vertical. Un `g5l_fastn` que las arme directamente se salta casi todo
   `g5l_sweepn` y `g5l_rxsave`. Tiene que dar las mismas cubetas que el
   camino completo: probarlo con `g5l.py game` y comparar las partes.
2. **Caché del plan de varios Rex.** La misma idea que `g5l_pcget`, con
   la clave (VLIST, R0) de cada Rex más la de Mario. Medir primero la
   tasa de acierto en Python (la cantidad de claves repetidas en las fotos
   con 2 Rex). Con un Rex casi todo lo resuelve `g5l_fast`, no la caché:
   no suponer que acierte.
3. **`g5l_emitn`.** La copia de las cadenas (hasta 4 flujos × 2 × 32
   filas) se cachea solo con las dos fuentes del banco (P125).
   Alternativas a medir:
   - copiar solo las columnas en pantalla (ya se hace) y las filas del
     recorte;
   - que el parche de bandas escriba directamente en la cadena en vez de
     en su búfer y después copiarlo.
4. **Lo fijo:** `g5l_choose` y los dos `g5l_plan` (la variante de cada
   Rex). Mirar con `--pcprof` + `pcsect.py`
   (`scratchpad/pcsect.py` de la sesión de G4-2: ciclos por etiqueta local)
   antes de tocar.

## Puertas

- `g5l.py game` exacto con `-DG5L_MAXPL=2` en yi1, hills2, stress_sprites
  y stress_back, y también con el defecto (1).
- Regresión completa, `dc_loop_verify.py` y memmap sin violaciones.
- A/B BENCH WinUAE como en G4-2: `work/g42/ab_build.sh` + `ab_run.ps1`,
  bajo el candado y en serie. Si entra en el ruido, el defecto pasa a 2.
  Si no, se reporta el trade nuevo y sigue apagado.
- Si se activa: las capturas `--only` de hills2 (frames 1825 y 2130, ver
  el informe de G4-2 §6) con 0 píxeles distintos.

## Trampas

P37 (vbcc incorpora en línea las funciones `static`), P53, P108, P123 y
P125.
