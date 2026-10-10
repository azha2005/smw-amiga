# G5L-R-L — el racimo 3305-3364: camino lento de G5L, picos de la lógica y el primer pico de `build_mid`

2026-10-10. Bajo la autorización del usuario del 2026-10-09 ("hacé lo que
puedas, ojalá llegar al máximo nivel de optimización"): optimizar, medido,
cada paso con su commit. Toca `player/g5l.s`, `player/scroll.s` y, si la
medida lo pide, el C de la lógica.

## Por qué existe

Después de S9 (`docs/informe-g5l-r-s9-1010.md`) quedan **12 omitidas** en
VBTRACE (36 fotos BENCH). Primera causa: `g5l_sweep` 4, lógica 4,
`build_mid` 2, `g5l_mfill` 1, `g5l_patch` 1. Seis están en 3305-3364, donde
el plan de G5L falla (camino lento: `g5l_sweep` + `g5l_plan`, ~63 k contra
~26 k ciclos) y a la vez la lógica sube +14-15 k sobre su mediana. 4218 es
la primera foto de un pico de `bm_left` (68 k): S9 no la ayuda porque no hay
de dónde copiar.

## Reglas

- Worktree `C:/Users/JC/Downloads/sma/wt-g2t-b2bis-1008`, rama `g2t-b2bis`;
  sin merge ni push. Builds en serie, **una sola WinUAE midiendo**
  (`winuae_lock.ps1`), R9. `scrollsim` nunca dos a la vez (P76).
- asm: P40, P73, P88, P94, P102, P122 (rutinas nuevas de `scroll.s` después
  de `bm_left`; `jmp` calculado con `; lint: targets`). Cabeceras
  `registros destruidos` al día (V3).
- Lógica en C: V1 (`marioverify` + `m68kverify`; ninguna métrica empeora),
  P37/P38/P47/P62 (vbcc).

## Partida verde

```sh
export PATH="$TEMP/pyshim:/c/msys64/ucrt64/bin:$PATH" VBCC=/c/Users/JC/vbcc PY=python
python tools/lint_port.py                       # RESULTADO: OK
python tools/regress.py --baseline tools/baseline_pc.json --level --g5l --bm1   # RESULTADO: OK
GDEFS=-DREPLAY OUT=work/l/replay sh tools/game_build.sh
md5sum work/l/replay/game.bin                   # 4eee47fa7f8bf71b51a30c59a3f3f9b0
python tools/g5l.py game --bin work/l/replay/game.bin --lst work/l/replay/game.lst | tail -1
# G5L GAME: OK     (media 9892,5, max 90452)
```

## Pasos

1. **Medir antes de tocar.**
   - `g5l.py game --pcprof` ya da el render G5L y `build_mid` por PC.
     Sumar la lógica (lo que `frames.json` llama `logic`) al mismo
     histograma. Puerta: el total paso a paso igual al normal en las 6313
     fotos.
   - Con `q_report.py`: las rutinas de la lógica en 3324-3364 contra su
     mediana. Saber **qué** sube +15 k (¿carga de sprites? ¿colisiones?
     ¿un enemigo nuevo?) antes de elegir.
2. **Camino lento de G5L** (`g5l_sweep`, `g5l_plan`, `g5l_mfill` en los
   145 fallos): perfil de R1 en los fallos (`work/r1/q_report.txt`,
   segunda tabla). Reescrituras concretas como en R1 (desenrollar,
   claves, búsquedas). Cada una con `G5L GAME: OK` y su ahorro medido; si
   ahorra menos de la mitad de lo estimado, revertirla.
3. **El primer pico de `bm_left`** (4218, 68 k): el bucle por carga
   (`.ld`/`.w`/`.mv`/`.k1`/`.k2`, ~90 ciclos) lleva el máx. de a y el mín.
   de b; Q estimó −25-60 % sacándolos (**sin probar** que se pueda). Con
   `scrollsim --ret` (5119 px, 1215/1215) y `scrollprof` ida/vuelta.
4. **Lógica**, si el paso 1 encuentra un bucle concreto: reescribirlo en C
   o pasarlo a asm con su verificación (V1, `cruce RAM`).
5. **Medida en WinUAE** con lo que quedó (BENCH, VBTRACE), como en
   `informe-g5l-r-s9-1010.md` (Comandos). Base: 36 fotos, 12 omitidas.
6. **Red:** lint, regress `--level --g5l --bm1`, los cinco MD5 nuevos,
   memmap sin violaciones.

## Paradas

- `G5L GAME`, `scrollsim` o el cruce PC = 68000 fallan → revertir ese paso.
- BENCH o VBTRACE empeoran con la suma → parar y avisar.
- Una métrica de regress empeora → o se arregla, o es un canje explicado
  en el commit (como S9: `--update --force`).

## Informe

`docs/informe-g5l-r-l-<fecha>.md`: qué subía en el racimo, cada
reescritura con su ahorro medido, BENCH/VBTRACE antes y después, y lo que
falta para ≤ 5 omitidas. Si no queda palanca concreta, D1 vuelve al
usuario con los números (colchón aceptado; 25 Hz solo con la optimización
agotada). Cerrar según ROADMAP §7.
