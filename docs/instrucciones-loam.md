# L-OAM — abaratar la OAM ampliada: instrucciones paso a paso

Escrito el 2026-10-07 para quien ejecute la tarjeta (persona o agente).
Seguilo **en orden**. Cada paso dice qué correr, qué tiene que salir y
cuándo parar. Si algo no sale como dice acá, **no lo arregles por tu
cuenta: pará y avisá** con la salida exacta.

## 0. Por qué existe esta tarjeta

Con `SPR_OAM` (la OAM de los enemigos, G8b) la lógica del peor frame sube
del 55 % al 83-87 % del frame en los replays de estrés, y el render no
llega: 17,28 % de fotos perdidas en `stress_back` contra 3,51 % sin ella
(`docs/medida-d1-winuae.md`, último apartado). Sin bajar esto, dibujar
enemigos (G5) hunde el juego.

Lo que agrega la OAM ampliada en el peor frame de `stress_back` (oráculo
3097, muchos Rex; Musashi sin DMA, build PROF sin inline), **después del
paso 1**:

| función | sin OAM | con OAM | diferencia |
|---|---:|---:|---:|
| `finish_oam_write` | 0 | 8 704 | +8 704 |
| `rex_gfx` | 0 | 7 150 | +7 150 |
| `level_frame` (limpieza de la OAM, ya desenrollada) | 0 | 2 728 | +2 728 |

**Objetivo de la tarjeta:** que con `SPR_OAM` el A/B de estrés (§4) no
pierda más fotos que sin ella, y `level_frame` máx. ≤ 40 % en el replay de
YI1 con `SPR_OAM`.

**El paso 1 ya está hecho** (commit `4b713c4`): `finish_oam_write` sin
temporales en RAM. Usalo como modelo: `git show 4b713c4`.

## 1. Reglas que no se negocian

1. **La RAM tiene que quedar idéntica.** Cada byte de `ram[]` después de
   la función tiene que valer lo mismo que antes del cambio, incluidos los
   temporales `$00-$0F` (`m0`..`m15`). Lo comprueban `regress.py` (PC) y
   `tools/oam68k_gate.sh` (68000). Si una de las dos da distinto, el cambio
   está mal, aunque "parezca" equivalente.
2. **Nunca cambiar `tools/baseline*.json`**, nunca aflojar ni saltear una
   comprobación, nunca tocar la puerta para que pase.
3. **Un cambio por commit**, con la medida antes → después en el mensaje.
4. **No declarar nada que no corriste.** Si el informe dice "pasa X", en el
   informe va la salida de X. Si no pudiste correr algo, el informe dice
   "no corrido" y por qué.
5. **Nada sin commitear** al terminar. Lo que no pasa su puerta va en un
   commit `WIP:` que diga qué falta.
6. Antes de tocar C del 68000, leé en `docs/pitfalls.md`: **P36, P37, P38,
   P47, P62, P78** (vbcc). Resumen: vbcc incorpora en línea las `static`
   (P37), puede sumar dos veces la base de un puntero (P38/P62) y emite
   direcciones absolutas al tomar la dirección de un array `static` (P47).
   `logicbench_build.sh` para el build si vbcc emitió algo absoluto.

## 2. Preparar el entorno (una vez por terminal)

En **Git Bash** (no PowerShell), desde el repo:

```sh
cd /c/Users/JC/Downloads/sma/port-amiga
export PATH="$TEMP/pyshim:/c/msys64/ucrt64/bin:$PATH" VBCC=/c/Users/JC/vbcc PY=python
which python      # tiene que decir /c/Users/JC/AppData/Local/Microsoft/WindowsApps/python
python -c "import machine68k, unicorn; print('ok')"     # tiene que decir ok
```

Si `which python` da otra ruta o falta `machine68k`: **pará**. Con otro
Python la regresión dice "FALLO 68000" y con gcc fuera de orden dice
"FALLO build PC" **sin ningún mensaje** (no es un error de tu código).

Comprobar que se parte de verde:

```sh
git status --short                 # vacío
python tools/lint_port.py          # última línea: RESULTADO: OK
python tools/regress.py --baseline tools/baseline_pc.json --level   # RESULTADO: OK
sh tools/oam68k_gate.sh            # última línea: OAM68K: OK
```

Si cualquiera no da OK **antes de tocar nada**: pará y avisá.

## 3. La vuelta de trabajo (repetirla por cada función)

### 3.1 Medir dónde se va el tiempo

```sh
PROF=1 CDEFS='-DNOOAM -DSPR_OAM' sh tools/logicbench_build.sh > work/prof_build.log 2>&1
cp work/prof/logicbench.bin work/prof/lb_oam.bin
cp work/prof/logicbench.lst work/prof/lb_oam.lst
python tools/m68kprof.py --bin work/prof/lb_oam.bin --lst work/prof/lb_oam.lst \
    --oracle work/oracle_stress_back.bin --sprites --every 4 --worst 3 --at 3097 \
    > work/prof_oam.txt
```

Para comparar contra el mismo frame sin OAM ampliada, lo mismo con
`CDEFS='-DNOOAM'` en `lb_nooam.*`. **Solo te interesan las funciones que
existen o crecen con `SPR_OAM`** (las de `player/spr_gfx.c`, la limpieza de
la OAM en `level_frame`). `spr_tile_asm`, `f44d_asm`, etc. cuestan igual
sin OAM ampliada: no son de esta tarjeta.

Anotá: ciclos del frame 3097 y de la función elegida, antes.

### 3.2 Leer el original antes de cambiar

Cada función de `spr_gfx.c` dice arriba qué rutina del ROM transcribe.
Buscala en `../smw-src-master/project/mw_e10/` (`grep -n NombreRt *.s`) y
leela entera. Hacé una lista de:

- qué temporales (`m0`..`m15`) **escribe** y cuál es su **último** valor;
- qué temporales **lee** que no escribió antes (esos vienen de afuera:
  hay que leerlos de `ram[]`, no inventarlos);
- qué otras direcciones de `ram[]` escribe (OAM, tablas de sprites).

### 3.3 Transformar (el patrón del paso 1)

1. Al principio de la función, cargar en variables locales (`u8`, `u16`,
   `s16`) lo que el bucle lee de `ram[]` y **no cambia dentro del bucle**.
2. Dentro del bucle, usar las locales en lugar de `R8(mN)`/`W8(mN, ...)`.
3. Donde el 65816 arma un número de 16 bits con dos bytes y un acarreo
   (`LDX #0 / BPL / DEX / ADC / TXA / ADC`), es una suma de 16 bits con un
   desplazamiento **con signo**: `(u16)(base + (u16)(s16)(s8)(u8)desp)`.
4. Al final, **una sola vez**, escribir con `W8` cada temporal que el
   original deja escrito, con su valor final (para los del bucle: el de la
   última vuelta).
5. No cambiar el orden de escritura de la OAM ni de tablas que el mismo
   bucle vuelve a leer. Si el bucle lee algo que él mismo escribió (alias),
   **no** lo pases a local: dejalo como estaba.
6. Comentario arriba, en español, diciendo qué se hizo y por qué la RAM
   queda igual (copiar el estilo del paso 1).

Objetivos en este orden (de §0):

1. `rex_gfx` (`player/spr_gfx.c`): escribe `m0`-`m3` y los relee en el
   bucle de 2 fichas; mismo patrón que el paso 1.
2. `finish_oam_write` otra vez, ahora mirando el código que genera vbcc
   (`work/cc/spr_gfx.s` después de `logicbench_build.sh`): si el bucle
   sigue haciendo extensiones `ext.w`/`and.w #$ff` de más, probar tipos
   `u16` para los índices. Si con C no baja, una versión en asm en
   `player/logic68k.s` **siguiendo cómo se hizo con `rex_main_asm`** (el asm
   reemplaza al C solo en el build de la Amiga; el C queda como referencia
   en el PC y la puerta compara los dos).

**No es objetivo:** la limpieza de la OAM en `level_frame`
(`player/manim.c`, `CLR16`). Ya está desenrollada, son 128 bytes en
direcciones impares intercaladas con la X (no se pueden juntar en
palabras) y la SNES limpia las 128: limpiar menos cambia la RAM.

### 3.4 Verificar (todo, siempre, en este orden)

```sh
python tools/lint_port.py                                          # RESULTADO: OK
python tools/regress.py --baseline tools/baseline_pc.json --level  # RESULTADO: OK
sh tools/oam68k_gate.sh                                            # OAM68K: OK
```

- `regress.py` puede decir **MEJOR** en alguna métrica: está bien, decilo
  en el commit. **PEOR** o **FALLO**: el cambio está mal; deshacelo.
- `oam68k_gate.sh` imprime los ciclos de `sprite_run`
  (`grep "ciclos por sprite_run" work/oamgate/*_68000.log`): anotalos.
- Repetí 3.1 y anotá el frame 3097 después.

Si falla y no ves por qué en dos intentos: `git checkout -- <fichero>` y
pasá a la siguiente función, anotando el fallo en el informe.

### 3.5 Commit

```sh
git add player/spr_gfx.c          # solo lo que cambiaste
git commit -m "Etapa 8.2: L-OAM paso N, <función> <qué>" \
           -m "<ciclos antes -> después: frame 3097, sprite_run máx.>" \
           -m "lint, regress --level y oam68k_gate en verde."
```

## 4. La medida que vale: WinUAE cycle-exact

Musashi no tiene esperas de DMA: sirve para saber **dónde** se va el
tiempo, no **cuánto** cuesta en la A500. Al terminar cada 2-3 pasos, y
siempre al final:

```sh
sh tools/stress_ab_build.sh lN          # N = número de paso; STRESS_AB_BUILD: OK
```
```powershell
# en PowerShell, desde el repo (las capturas tardan ~6 minutos)
.\tools\stress_ab_shots.ps1 -Prefix lN  # STRESS_AB_SHOTS: OK (6 capturas)
```
```sh
sh tools/stress_ab_read.sh lN           # tabla + STRESS_AB_READ: OK
```

Arma y captura `back`, `sprites` y `yi1`, cada uno sin y con `SPR_OAM`.
No cierres ningún WinUAE que no hayas abierto vos. Si una captura sale
sin sincronía, repetí **solo** esa; si vuelve a fallar, pará.

Referencias (antes de L-OAM, `docs/medida-d1-winuae.md`):

| build | fotos perdidas | racha | `level_frame` máx. |
|---|---:|---:|---:|
| back sin OAM | 145 (3,51 %) | 3 | 55,1 % |
| back con OAM | 713 (17,28 %) | 48 | 83,1 % |
| sprites sin OAM | 0 | 0 | 53,5 % |
| sprites con OAM | 99 (5,17 %) | 10 | 86,6 % |
| yi1 con OAM (G5a, 1132 frames) | 0 | 0 | 49,4 % |

Después del paso 1 (`4b713c4`, prefijo `l1`, 2026-10-07):

| build | fotos perdidas | racha | `level_frame` máx. |
|---|---:|---:|---:|
| back sin OAM | 145 (3,51 %) | 3 | 55,0 % |
| back con OAM | 616 (14,93 %) | 38 | 79,3 % |
| sprites sin OAM | 0 | 0 | 53,5 % |
| sprites con OAM | 56 (2,93 %) | 4 | 76,5 % |
| yi1 sin OAM (replay entero) | 14 (0,22 %) | 1 | 29,5 % |
| yi1 con OAM (replay entero) | 28 (0,44 %) | 1 | 43,1 % |

Los números "sin OAM" coinciden con las medidas anteriores (control de que
el método no cambió). Faltan ~3,1 puntos de `level_frame` en YI1 y casi
todo el estrés.

## 5. Puerta de cierre de la tarjeta

- `level_frame` máx. con `SPR_OAM` en `l?_yi1_oam` **≤ 40 %**.
- Fotos perdidas de `back`/`sprites` con OAM **no peores** que sin ella.
- lint, regress `--level` y `oam68k_gate.sh` en verde en el último commit.
- Si después de `rex_gfx` y `finish_oam_write` en asm no se llega: **parar** y entregar la tabla con lo medido. No seguir probando a
  ciegas ni tocar lógica que no sea de la OAM.

## 6. El informe (lo que hay que entregar)

1. Commits (hash + título).
2. Tabla del frame 3097 por función, antes → después de cada paso.
3. La tabla de `stress_ab_read.sh` del último prefijo, entera.
4. Salida final (las últimas líneas) de lint, regress y `oam68k_gate.sh`.
5. Lo que **no** se pudo hacer o medir, dicho así.
6. Trampas nuevas como "Pnn sin número", con causa y síntoma.
