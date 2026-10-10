# G5L-R-S9 — los picos de `build_mid`: S5 descartado, S9 integrado (2026-10-10)

Rama `g2t-b2bis`, commit `b67ee4b`. Autorización del usuario
(2026-10-09): "hacé lo que puedas, ojalá llegar al máximo nivel de
optimización". Toca `player/scroll.s` (`build_mid`, `bm_left`).

**Resultado.** WinUAE cycle-exact: **BENCH 53 → 36 fotos perdidas** (0,57 %,
racha 1) y **VBTRACE 17 → 12 omitidas**. Desde el informe T (66/25) se
llevan dos tercios menos de fotos perdidas y la mitad de omitidas. D1 sigue
roja (objetivo ≤ 5 omitidas).

## 1. Dónde estaba el costo

Después de R1, 8 de los 17 saltos tenían como primera causa `build_mid`, y
casi todos eran de `bm_left` (la cámara a la izquierda). Por foto, en
Musashi (`g5l.py game`, ciclos sin DMA):

```
5834 5835 5836 | 5837..5840 | 5841 5842 5843 | ... | 5850 5851 5852
 78k  83k  86k |   11-27k   |  77k  72k  77k |     |  72k  81k  82k
```

Los picos vienen **de a tres seguidos**: con el colchón hay tres listas del
copper y cada una reescribe las mismas líneas una foto después de la otra
(P121).

## 2. S5 (repartir con un presupuesto): descartado

`bm_left` con un margen `S5H` (px) y un presupuesto `S5N` (líneas por
pasada): una línea que vale en s pero vencería en `S5H` px más se reescribe
ya, solo si su pista es de esta época. Medido con `scrollprof.py` (vuelta,
dos listas, SPEED 4):

| variante | media | p90 | p99 | máx. |
|---|---:|---:|---:|---:|
| base | 23 308 | 56 526 | 100 332 | 115 590 |
| una pasada, H16 N20 | 30 671 | 68 550 | 106 248 | 127 546 |
| una pasada, H4 N8 | 24 722 | 58 554 | 102 612 | 116 832 |
| dos pasadas (debidas primero), H8 N20 | 28 026 | 56 526 | 100 388 | 115 646 |
| dos pasadas, H16 N40 | 36 710 | 79 308 | 101 386 | 113 310 |

Con una pasada el presupuesto se gasta arriba antes de llegar a las debidas
y el pico **sube**. Con dos pasadas el pico no cambia y la media sube. En
el juego (tres listas, H8 N20, una pasada) el modelo dio 22-26 saltos contra
19-22: peor. **Los picos no son adelantables**: son eventos de la línea
(cargas que entran o salen), no la base agotada.

## 3. S9 (compartir líneas entre listas): integrado

Lo escrito en una línea vale por su contenido, no por la lista: las h salen
de `htab - s0`, `[vl, vu)` está en `linetab` y lo único propio de cada lista
son las direcciones del salto al segmento siguiente (P50/P71). Entonces:

- `.jump` guarda los bytes de las cargas en `28(a4)` (el `$008a0000` del
  salto pasa a inmediato).
- En `.prw` (`build_mid` y `bm_left`), si la línea de la última lista escrita
  (`prevlt`) vale en s, `bm_share` copia sus cargas con un bloque
  desenrollado (`jmp .ce(pc,d1.w)`, 20 ciclos por palabra larga) y su
  estado (lo, hi, vl, vu, pista, época), y escribe el salto propio.
- Lo que agrega G5L (los sufijos COLOR17-31) va después de las cargas: no
  se copia. `g5l_clean` sigue viendo lo mismo que tras una escritura normal.
- La comprobación va en línea en `.prw`: 46 ciclos por línea cuando no se
  copia.

Por foto en el juego (Musashi, R1 → S9, miles de ciclos):

```
5441 5442 5443 | 5834 5835 5836 | 5850 5851 5852 | 4215 4216 4217 4218
75/82 75/29 78/28 | 78/79 83/37 86/35 | 72/77 81/39 82/38 | 75/70 88/60 53/42 60/36
```

La primera foto del pico calcula (no hay de dónde copiar); las otras dos
copian.

| medida | R1 | S9 |
|---|---:|---:|
| `build_mid` en el juego: media / p99 / máx. | 5 166 / 43 428 / 88 668 | 4 221 / 29 526 / 80 994 |
| total por foto: p99 / máx. | 120 838 / 155 330 | 118 004 / 152 310 |
| modelo de cola (cinco ajustes) | 20 19 22 19 19 | 15 15 18 12 16 |
| `scrollprof` ida: media / máx. (dos listas) | 16 493 / 82 898 | 14 875 / 73 718 |
| `scrollprof` vuelta: media / máx. | 19 530 / 111 520 | 17 283 / 105 786 |
| **WinUAE BENCH** | 53 | **36** |
| **WinUAE VBTRACE** | 17 | **12** |

## 4. Los 12 saltos que quedan

Omitidas: 1045 1127 1713 2078 2758 3308 3313 3329 3345 3350 3364 4218.
Primera causa (`t2_attrib.py`): `g5l_sweep` 4, lógica 4, `build_mid` 2,
`g5l_mfill` 1, `g5l_patch` 1. Desaparecieron 4042, 4563, 5445 y 5854 (picos
de `bm_left`); 4217/4219 quedó en 4218 (la primera foto de un pico de 68k);
2758, 3345 y 3350 son corrimientos de ventanas que ya existían.

El racimo 3305-3364 (6 saltos) es la zona donde el plan de G5L falla
(camino lento `g5l_sweep`/`g5l_plan`) junto con picos de la lógica (+14-15k
sobre la mediana). Es lo siguiente.

## 5. Red de seguridad

- `scrollsim.py --from 4 --to 4864 --ret`: 5119 px y vuelta igual a la ida
  en 1215/1215, **idéntico a la base** (la imagen no cambia).
- `G5L GAME: OK`; `lint_port.py` OK (P122: `bm_share` va después de
  `bm_left`; `; lint: targets .ce`).
- `regress.py --baseline tools/baseline_pc.json --level --g5l --bm1`: OK con
  la base actualizada a propósito (`--update --force`). Mejoran
  `scroll.ida/vuelta` máx. y media y `game.*.media`. **Empeoran**
  `game.build_mid.max` 80 868 → 81 244 (+0,5 %) y `game.total.max`
  119 998 → 122 096 (+1,7 %) en la configuración sin G5L de dos listas:
  la foto que calcula todo paga la comprobación. Es el canje: en el juego
  con G5L el máximo baja. La base suma además las métricas `orc.*` que
  todavía no estaban (valores exactos de hoy).
- MD5 (`game.bin`):

| build | MD5 |
|---|---|
| replay | `4eee47fa7f8bf71b51a30c59a3f3f9b0` |
| vivo | `510e1ee3b633a51f0cafb18d0179a34f` |
| bench | `8a7a98c39bb9bf316b29e43b943069b1` |
| dec | = replay |
| decbench | = bench |

## Comandos

```sh
python tools/scrollprof.py -D RETURN=4864 --stopx 0 --csv work/s5/p9b.csv
python tools/scrollsim.py --from 4 --to 4864 --ret          # 10 min, nunca dos a la vez (P76)
GDEFS=-DREPLAY OUT=work/s9/replay sh tools/game_build.sh
python tools/g5l.py game --bin work/s9/replay/game.bin --lst work/s9/replay/game.lst | tail -1
cp work/g5l/game_frames.json work/s9/frames.json
python tools/t2_attrib.py --frames work/s9/frames.json --vblog work/s9/vt/vbtrace.out --csv work/s9/frames.csv
GDEFS='-DREPLAY -DBENCH' OUT=work/s9/bench sh tools/game_build.sh
GDEFS='-DREPLAY -DVBTRACE' OUT=work/s9/vt sh tools/game_build.sh
python tools/game_read.py --shot work/s9/bench/shot.png --auto | tail -9
python tools/vbtrace.py work/s9/vt/game.adf work/s9/vt/trace.bin 175 > work/s9/vt/vbtrace.out
```
```powershell
& C:\Users\JC\Downloads\sma\winuae_lock.ps1 .\tools\shot.ps1 -Exact -Adf work\s9\bench\game.adf -Out work\s9\bench\shot.png -Wait 190
```
