# G5L-R-R1 — reescrituras concretas del render G5L y su medida en WinUAE

2026-10-09. **Necesita la autorización del usuario antes de empezar:**
es un candidato, toca `player/g5l.s`.

## Por qué existe

Q (`docs/informe-g5l-r-q-1009.md`): el perfil por PC del render G5L es
plano (el bucle más caro, 5,1 %). Las reescrituras concretas y exactas por
construcción ahorran ~8 % del render en las ventanas de salto y ~9 % en
todas las fotos dibujadas (ESTIMADO). El modelo de cola dice 25 → 17-18
saltos con solo eso, y 14-16 sumando `build_mid`. Nunca se midió en
WinUAE cuánto vale un ciclo de Musashi en fotos omitidas. **Esta tarjeta es
esa medida**, con el recorte que es seguro.

## Reglas

- Worktree `C:/Users/JC/Downloads/sma/wt-g2t-b2bis-1008`, rama `g2t-b2bis`;
  sin merge/push. Builds en serie, **una sola WinUAE midiendo**
  (`winuae_lock.ps1`), R9.
- Solo `player/g5l.s` (y `tools/t2_keys.py` si cambia la clave). Nada de
  `scroll.s`/`bm_left` en esta tarjeta.
- Cada reescritura en su commit, con `G5L GAME: OK` antes de seguir.
- asm: P40 (`(An,Dn.w)` con signo), P73, P88, P94 (una etiqueta global
  corta las locales), P102; ABI y cabeceras `registros destruidos`
  al día (V3 de `lint_port.py`).

## Partida verde

```sh
export PATH="$TEMP/pyshim:/c/msys64/ucrt64/bin:$PATH" VBCC=/c/Users/JC/vbcc PY=python
python tools/lint_port.py                       # RESULTADO: OK
python tools/regress.py --baseline tools/baseline_pc.json --level --g5l --bm1
# RESULTADO: OK
GDEFS=-DREPLAY OUT=work/t2/replay sh tools/game_build.sh
md5sum work/t2/replay/game.bin                  # 4328e9c83a309e7527c62d0da7e3a6c4
python tools/g5l.py game --bin work/t2/replay/game.bin --lst work/t2/replay/game.lst | tail -1
# G5L GAME: OK     (media 10477,6, max 93752)
python tools/g5l.py game --bin work/t2/replay/game.bin --lst work/t2/replay/game.lst --pcprof work/t2/q_prof.json
python tools/q_report.py --prof work/t2/q_prof.json --frames work/t2/frames.json \
    --vblog work/t2/vt/vbtrace.out --lst work/t2/replay/game.lst | sed -n 2p
# == g5l_render en las ventanas de salto: 98 fotos, 5120968 ciclos (52254 por foto)
```

## Pasos

Después de **cada** reescritura: build REPLAY en `work/r1/replay`,
`g5l.py game ... | tail -1` → `G5L GAME: OK` (compara la lista y el
búfer byte a byte y envenena la ABI), y `--pcprof` + `q_report.py` para el
ahorro real del bucle. **Si una reescritura ahorra menos de la mitad de
lo estimado, revertirla** y anotarlo.

1. **`g5l_pckey`: la clave con lo que cambia primero.** Orden nuevo de
   `GV_PK`: `.l GV_VLIST`, `.w GV_R0`, `.w GV_MSH`, `.l GV_COL`, los 52 B
   de `GV_KBUF`. Solo la leen `g5l_pcget` (`.e`), `g5l_pcput` y
   `g5l_pckey` (grep `GV_PK`). Medido hoy: 6,7 `cmpm.l` por entrada,
   159 aciertos en 1980 llamadas. Estimado: −75 % de `g5l_pcget.c`
   (1,7 % del render en ventanas, 2,3 % en todas). Actualizar `F` de
   `tools/t2_keys.py` al orden nuevo.
2. **Copias y borrados con `movem`:** `g5l_patch.cl` (copia del flujo de
   DMA limpio, `d7 + 2` palabras largas: bloque de N registros libres +
   resto), `g5l_pckey.k`, `g5l_pcput.bc`, `g5l_pcget.bc`/`.r`,
   `g5l_mario.kz` (52 B a cero). El ahorro depende de cuántos registros
   queden libres: con 4, `movem` da ~15 %; con 8, ~35 %. Anotar los usados.
3. **`g5l_emit.mv` desenrollado sin cambiar el formato:** `move.l
   8*k(a1),(a0)+` (24 ciclos) en un bloque desenrollado con salto
   calculado, contra `move.l (a1),(a0)+` + `addq.l #8,a1` + `dbf`
   (38). Antes, medir el máximo de MOVE por segmento en el replay
   (el bloque tiene que cubrirlo). Estimado: −35 %.
4. **`g5l_place.f1`:** mapa de bits de los segmentos con lugar
   (`GV_ROOM` > 0), actualizado donde `GV_ROOM` cambia; buscar el más
   alto ≤ hi de 32 en 32 filas. Medido: 3,7 % de las dibujadas. Estimado
   −60 %. Si mantener el mapa cuesta más que lo que ahorra (`--pcprof`),
   revertir.
5. **`g5l_emit.jl` (condicionado):** recorre 3,8 pasos de media (17 548
   comparaciones en 4619 llamadas) porque lo que hay entre las cargas y
   el salto `$0084` varía. Solo si el offset del salto ya se conoce sin
   costo en algún lado (grep de quien escribe `$0084` en `scroll.s`):
   usarlo. Si hace falta escribirlo desde `build_mid`, **no** (fuera de
   alcance).
6. **Medida en WinUAE** con todo lo que quedó:
   ```sh
   GDEFS='-DREPLAY -DBENCH' OUT=work/r1/bench sh tools/game_build.sh
   GDEFS='-DREPLAY -DVBTRACE' OUT=work/r1/vt sh tools/game_build.sh
   ```
   ```powershell
   & C:\Users\JC\Downloads\sma\winuae_lock.ps1 .\tools\shot.ps1 -Exact -Adf work\r1\bench\game.adf -Out work\r1\bench\shot.png -Wait 190
   ```
   ```sh
   python tools/game_read.py --shot work/r1/bench/shot.png --auto | tail -9
   python tools/vbtrace.py work/r1/vt/game.adf work/r1/vt/trace.bin 175 > work/r1/vt/vbtrace.out
   ```
   Base de comparación: 66 fotos perdidas (racha 1) y 25 omitidas.
   Comparación visual del frame 1700 (0 píxeles distintos, como en V/T).
7. **Red:** lint, regress `--level --g5l --bm1`, los cinco MD5 nuevos
   anotados (cambian: es el candidato), memmap sin violaciones.

## Paradas

- `G5L GAME` falla tras una reescritura → revertirla; no seguir con ella.
- La suma del paso 6 empeora BENCH o VBTRACE → parar y avisar.
- Tocar `scroll.s` o la lógica → fuera de alcance.

## Informe

`docs/informe-g5l-r-r1-<fecha>.md`: por reescritura, el ahorro medido en
Musashi contra el estimado de Q; render en ventanas antes/después;
BENCH y VBTRACE antes/después (la primera medida de cuánto vale el ciclo
en fotos omitidas); el modelo de cola recalibrado con eso; y la
recomendación (S5, patch por blitter, o D1 al usuario). Cerrar según
ROADMAP §7.
