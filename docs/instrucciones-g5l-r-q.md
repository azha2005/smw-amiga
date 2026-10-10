# G5L-R-Q — qué recortes de ciclos son posibles (medida)

2026-10-09. **Necesita la autorización del usuario antes de empezar.**
Solo medida: **no se toca código del juego.**

## Por qué existe

T2 y Pa (`informe-g5l-r-t2-1009.md`, `informe-g5l-r-pa-1009.md`): los 25
saltos de VBTRACE (66 fotos BENCH) son atraso acumulado. La caché del plan
no sirve: sin `R0` el plan corrido es igual al 100 %, pero acierta 0 con
N = 4; sin `MSH` acierta, pero el plan es otro en el 92 %. Según el modelo
(ESTIMADO), para bajar a ≤ 5 saltos hace falta una de estas tres:

- **S5** (`build_mid` −50 % del exceso) + sweep/plan/exceso de patch −50 %
  en los fallos: 2-6;
- **S5** + `g5l_render` −20 % en todas las fotos: 1-2;
- `g5l_render` −30 % en todas: 4-5.

Antes de elegir hace falta saber qué recortes **se pueden** hacer. Esta
tarjeta los estima rutina por rutina, con el perfil real.

## Reglas

- Worktree `C:/Users/JC/Downloads/sma/wt-g2t-b2bis-1008`, rama `g2t-b2bis`;
  sin merge/push. R9. No hace falta WinUAE.
- Solo herramientas. Los cinco MD5 del defecto no cambian
  (`informe-g5l-r-t2-1009.md` §6).
- Musashi no es la Amiga (V2): ciclos sin DMA; sirven para repartir.

## Partida verde

```sh
export PATH="$TEMP/pyshim:/c/msys64/ucrt64/bin:$PATH" VBCC=/c/Users/JC/vbcc PY=python
python tools/lint_port.py                       # RESULTADO: OK
GDEFS=-DREPLAY OUT=work/t2/replay sh tools/game_build.sh
md5sum work/t2/replay/game.bin                  # 4328e9c83a309e7527c62d0da7e3a6c4
python tools/g5l.py game --bin work/t2/replay/game.bin --lst work/t2/replay/game.lst | tail -1
# G5L GAME: OK
cp work/g5l/game_frames.json work/t2/frames.json
python tools/pa_levers.py --frames work/t2/frames.json --csv work/t2/frames.csv | head -1
# g5l_render: fallo 66056 (145 fotos), dibujada sin fallo 27562 (1898 fotos)
```

## Pasos

1. **Histograma por PC (fase sin herramienta todavía).** Igual que
   `gamecheck.GameCheck.call` / `fr.call`, pero paso a paso: `m.execute(1)`
   corre una sola instrucción y devuelve sus ciclos (probado con
   machine68k el 2026-10-09: `move.l (a0)+,(a1)+` 20, `nop` 4, `dbf` 10
   al saltar y 14 al salir);
   acumular `{pc: (veces, ciclos)}` en `g5l_render` para las fotos de las
   25 ventanas de salto (`t2_attrib.py`: de la repetición − 2 hasta el
   salto) y para los 145 fallos. **Puerta:** la suma del histograma de
   cada foto es igual a su `c` de `game_frames.json` (±34 por la trampa de
   línea A de cada llamada).
2. **Mapear al listado.** PC → línea de `work/t2/replay/game.lst` →
   rutina y bucle (`.etiqueta` local). Tabla: las 20 líneas o bucles más
   caros, con veces, ciclos y % del total de las ventanas.
3. **`build_mid`, lo mismo**, en las fotos de más de 40 000 ciclos
   (60 de la vuelta, s ≈ 1780-1900 y 2016-2152; 11 de la ida;
   `pa_levers.py`), con `scrollprof.py --at S` como cruce para una s.
4. **Por cada bucle caliente, una reescritura concreta y su recorte
   ESTIMADO** (ciclos del 68000 por instrucción, de la tabla de
   Motorola o medidos con `execute(1)` como en el paso 1). Sin escribirla en `player/`.
5. **Sumar contra las tres metas** de arriba y re-correr el modelo con
   los recortes por rutina (variante de `pa_levers.py` que reste por
   rutina, no un porcentaje).

## Paradas

- Paso 1 no cuadra con `game_frames.json` → parar: el histograma está mal.
- Cualquier cambio en `player/` → fuera de alcance.
- No implementar: un candidato necesita otra autorización con el número.

## Informe

`docs/informe-g5l-r-q-<fecha>.md`: las tablas de los pasos 2 y 3, las
reescrituras con su recorte estimado, el modelo con esos recortes y la
recomendación (qué meta alcanza, en cuántas sesiones). Si ninguna alcanza,
decirlo con números: es la entrada para que el usuario revise D1. Cerrar
según ROADMAP §7.
