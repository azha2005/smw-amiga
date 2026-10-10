# G5L-N — clave normalizada y máscaras compartidas en la tabla del Rex

2026-10-10. Sigue a G4-A (`informe-g4a-1010.md` §3, §6). Misma rama y
worktree, sin merge ni push.

## Por qué

1. **Fidelidad:** G5L busca la forma exacta, con dx/dy relativos a la
   ranura. El Rex aplastado o medio aplastado aparece con otros dy
   (−3 … +1) y no está en el banco: `rex_sin_forma`, y ese Rex no se
   dibuja. Pasa en 340 de 2.110 frames con Rex en `hills2`, 96 en
   `stress_sprites`, 62 en `shells` y en `stress_back`, y 37 en
   `pw_estrella`. 30 de las 33 formas que faltan son traslaciones de una
   que ya está.
2. **Memoria:** las máscaras de `g5l_patch` son el 69 % del registro y se
   repiten en los 4 mapas. Con la clave normalizada y las máscaras una vez
   por forma, la tabla pasa de 128.724 B a ≈ 45.918 B (estimado de G4-A,
   con las máscaras de Mario).

## Partida

```sh
export PATH="$TEMP/pyshim:/c/msys64/ucrt64/bin:$PATH" VBCC=/c/Users/JC/vbcc PY=python
python tools/lint_port.py
python tools/regress.py --baseline tools/baseline_pc.json --level --g5l --bm1
python tools/g5l.py trace > work/g5ln/trace0.log     # contadores de control
GDEFS='-DREPLAY' OUT=work/g5ln/control sh tools/game_build.sh
```

Trazas del Rex para las grabaciones nuevas, con el host de G4-A (filtrar
`$AB` como `informe-g2.md`): `work/oam_<nombre>.trace` para `hills2`,
`shells`, `stress_back`, `stress_sprites` y `pw_estrella`. Son derivadas
de la ROM y van en `work/`, nunca en git.

## Pasos

1. **Referencia (Python), `tools/g5l.py`:**
   - La clave se normaliza al mínimo dx y dy (s8) de las fichas, sin
     reordenarlas. G4-A ordenó las fichas; hay que medir que en el orden
     de la OAM salgan las mismas 22 formas del banco. Si no, explicar.
   - El directorio guarda una forma por clave normalizada. El origen de
     la variante es relativo al mínimo: `x0 = sx + mindx + ox`, igual en Y.
   - Formato `G5L2`: por forma, un bloque de máscaras por color, una vez.
     El byte de relleno de cada grupo (`>BBHI`: d, **0**, c, m) pasa a ser
     el número de máscara. `Table.variant` y `g5l_patch` (en la
     referencia) leen desde ahí.
   - Puerta: `g5l.py trace` con los mismos contadores que el control en
     `yi1`/`normal`/`spin_kill`, salvo `rex_sin_forma`, que puede bajar. Con
     las trazas nuevas, `rex_sin_forma` ≤ 3 formas distintas, con cero
     errores y cero `sin_plan`.
2. **68000, `player/g5l.s`:** en `g5l_choose`, una pasada de mínimos
   antes de armar la clave. Sumar el mínimo a `x0`/`r0`. En `g5l_patch`,
   la máscara por índice. ABI y registros según el comentario de cada
   rutina. Puerta: `g5l.py game` en los tres replays (`G5L GAME: OK`).
3. **Red:** lint y regresión completa. `memmap.py` en replay y en el vivo:
   anotar cuánta slow se libera. `dc_loop_verify.py` en los tres replays.
4. **A/B WinUAE** (lock, `shot.ps1 -Exact`, comandos de S10 §5): BENCH
   en normal, back y sprites contra el control de la misma tanda. La
   normalización suma unos 100 ciclos por Rex y foto. Si BENCH empeora más
   que el ruido del control, se mide y se explica antes de integrar.
5. **Evidencia visual:** un replay de `hills2` (como los de estrés:
   `ORACLE=work/oracle_hills2.bin REPLAY=work/hills2_replay.bin`), con
   captura en un frame donde antes faltaba el Rex aplastado y ahora se ve.
   Compararla con la referencia de snesorc.
6. Informe `docs/informe-g5l-n-1010.md` y cierre según ROADMAP §7.

## No toca

El banco G3, `scroll.s`, el C. Las 3 formas que no son traslaciones
quedan listadas en el informe; agregarlas al banco es otra tarjeta.
