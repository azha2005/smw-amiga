# G5L-R-T2 — medir por qué se saltan las fotos, antes de otro candidato

2026-10-09. T se detuvo en su puerta con dos candidatos (66 y 65 fotos
BENCH contra 9 del control con colchón; `informe-g5l-r-tirones-1009.md`).
VBTRACE sin BENCH da **25 fotos omitidas**, agrupadas (daño de Mario
3305–3364, 1041–1127, 1670–1711, 2073–2078, 4214–4221, 4556–4567). D1
sigue roja. Esta tarjeta es **solo de medida**: atribuir cada salto a lo
que corrió en los frames anteriores. Un candidato nuevo necesita la
autorización del usuario después de leer el informe (parada de T).

## Reglas

- Worktree `C:/Users/JC/Downloads/sma/wt-g2t-b2bis-1008`, rama `g2t-b2bis`
  (o la que integre esto); sin merge/push. Builds en serie, **una sola
  WinUAE midiendo** (`winuae_lock.ps1`), R9.
- El defecto ya es G5L+CUSHION+SPR_OAM (`53e6453`): `GDEFS='-DREPLAY ...'`
  basta. `PROFILE=legacy` es el control sin G5L.
- No se cambia código del juego. Instrumentación solo con flag opt-in y sin
  cambiar los cinco MD5 del defecto (`informe-cierre-v-bm1-1009.md` §2).
- Musashi no es la Amiga: no extrapolar sus ciclos a DMA ni sumar máximos
  de frames distintos.

## Partida verde

```sh
export PATH="$TEMP/pyshim:/c/msys64/ucrt64/bin:$PATH" VBCC=/c/Users/JC/vbcc PY=python
python tools/lint_port.py                       # RESULTADO: OK
python tools/regress.py --baseline tools/baseline_pc.json --level --g5l --bm1
# RESULTADO: OK
GDEFS=-DREPLAY OUT=work/t2/replay sh tools/game_build.sh
md5sum work/t2/replay/game.bin                  # 4328e9c83a309e7527c62d0da7e3a6c4
python tools/g5l.py game --bin work/t2/replay/game.bin --lst work/t2/replay/game.lst | tail -2
# ... "ciclos_max": 93752, "ciclos_max_frame": 6755, "ciclos_media": 10477.6 ...
# G5L GAME: OK
```

## Pasos

1. **Reproducir las dos cifras de la parada** con el defecto nuevo.
   ```sh
   GDEFS='-DREPLAY -DBENCH' OUT=work/t2/bench sh tools/game_build.sh
   ```
   ```powershell
   & C:\Users\JC\Downloads\sma\winuae_lock.ps1 .\tools\shot.ps1 -Exact -Adf work\t2\bench\game.adf -Out work\t2\bench\shot.png -Wait 190
   ```
   ```sh
   python tools/game_read.py --shot work/t2/bench/shot.png --auto | tail -9
   # fotos perdidas : 66 (1.05 %), racha 1   (informe T, build "shared")
   GDEFS='-DREPLAY -DVBTRACE' OUT=work/t2/vt sh tools/game_build.sh
   python tools/vbtrace.py work/t2/vt/game.adf work/t2/vt/trace.bin 175
   # 25 fotos omitidas, mismos frames que el informe T
   ```
   Si alguna no coincide (±1 foto), **parar**: algo cambió entre la
   entrega T y el defecto; comparar MD5 antes de seguir.
2. **Fase de medida (no existe todavía la herramienta)**: volcado por
   frame del replay en Musashi con el coste de cada parte G5L
   (`g5l.py game` ya las acumula en `partes`; falta guardarlas por frame)
   y el de `build_mid`/`level_frame` (de `gamecheck.py`). Salida: CSV
   `frame, render, fast, sweep, plan, patch, place, emit, mfill,
   build_mid, level_frame, total`. Puerta: la suma por frame tiene que
   coincidir con `ciclos_media`/`ciclos_max` del paso 0.
3. Cruzar el CSV con los 25 frames de VBTRACE y los tres frames lógicos
   anteriores a cada salto (la pareja repetir/saltear está a ~3 frames,
   P115). Tabla por salto: qué parte pasa su media en más de 2×, si es
   `fast` fallido → `sweep`, si `build_mid` está en su pico (S5) o si es
   `g5l_mfill` (caché de Mario, P116).
4. Si un patrón explica **≥ 20 de los 25** saltos, escribir la propuesta
   de candidato con su coste estimado (marcado como estimado) y la puerta
   que lo mediría. **No implementarla.** Si no hay patrón, decirlo y
   proponer qué instrumentar en la Amiga (BENCH por parte), sin adivinar.

## Paradas

- Paso 1 no reproduce 66/25 → parar y avisar.
- La instrumentación cambia algún MD5 del defecto sin flag → deshacer.
- Cualquier cambio de comportamiento del juego → fuera de alcance.

## Informe

`docs/informe-g5l-r-t2-<fecha>.md`: cifras del paso 1 con su fuente, el CSV
(en `work/`, ignorado) resumido, la tabla de los 25 saltos, el patrón (o su
ausencia) y la propuesta con coste estimado. Cerrar según ROADMAP §7.
