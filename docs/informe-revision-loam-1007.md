# Revisión L-OAM (2026-10-07): coste de OAM que queda y tarjeta propuesta

Fecha: 2026-10-07. Revisión independiente según `docs/instrucciones-revision-1007.md`
§0 y §1 (pasos 1-5). Solo lectura de código: no cambia `player/`, `tools/`,
baselines ni puertas. Revisión hecha por el modelo Haiku 5.5 (`claude-haiku-5-5`);
la §0 de las instrucciones pide "GPT-6.1 Sol high", que no es el modelo de esta
revisión.

## 0. Procedencia y límites

- Worktree `worktree-agent-af1f47afe6798aaf3`, HEAD `6bef73f`. `master` está en
  `29ef39b` (tres commits G2T más). `player/` es idéntico entre ambos (0 líneas de
  diff); `tools/regress.py` cambia 1 línea. Las conclusiones de código valen para master.
- Commits L-OAM confirmados con `git log`: `e8ec165` (FinishOAMWrite en asm),
  `bbdf201` (RexGfxRt en asm), `cd5001c` (entrada C `rex_gfx` para `game_build`) y la
  fusión `cb8ba8f`, que está en master.
- Medidas WinUAE cycle-exact: tandas `l4` (agente, `work/l4_*/read.txt` en
  `wt-loam-1007`) y `coord4` (coordinador, `work/coord4_*/read.txt` en
  `wt-review-1007`). No se repitió WinUAE. Las dos tandas coinciden en cada build
  dentro de 0,2 pp (ver §2).
- Perfiles Musashi nuevos, solo lectura: copia de `tools/m68kprof.py` con 90 filas
  por frame y volcado por frame (`work/revision-loam-1007/`, ignorado por git). Los
  perfiles viejos del frame 3097 (top-20) son `work/loam_*_oam_prof.txt`.
- Unidades: 1 tick CIA-B = 10 ciclos nominales de CPU; frame = 14 210 ticks
  (`docs/medida-oam-o5.md`). Musashi: ciclos propios de función, sin DMA (P96).
- Índices de frame. El replay de YI1 empieza en el oráculo 5145 y el de estrés en
  1453 (`docs/medida-d1-estres.md`). La columna «oráculo» de las tablas `l4`/`coord4`
  usa 5145 también para `back` y `sprites`: para esos dos, el oráculo correcto es
  `1453 + frame` (`back` r=3360 es el 4813; `sprites` r=1648 es el 3101). Los
  máximos de Musashi caen un frame antes que los de WinUAE en YI1 (ver §7), así que
  la correspondencia exacta de frame es ±1.

## 1. Resumen

- **Lógica en YI1 con OAM: 41,2 % del frame** (`l4_yi1_oam/read.txt:9`; `coord4`
  igual). Sin OAM, 29,5 % en el mismo frame (r=4570, `l4_yi1_nooam/read.txt:9`).
  Para llegar a 40 % faltan 171 ticks (1,2 pp, unos 1 700 ciclos nominales).
- **El coste de OAM en YI1 se concentra en la ruta de la piraña, no en Rex.** En el
  pico (oráculo 9715) el delta de OAM es +11 540 ciclos Musashi. La ruta de la
  piraña en C (`piranha_gfx`, `sub_spr_gfx0`, `sub_spr_gfx2_at`, dos llamadas a
  `get_draw_info1`, `spr_oam_index` y `oam_mark` de esa ruta) suma 5 960 de bruto.
  De los 37 frames del replay por encima de 40 % (mapa B de §3.5), los 37 llevan
  piraña.
- **La limpieza de la OAM (`level_frame`, CLR16) es un coste fijo de 2 226 ciclos
  Musashi por frame**, igual en todos los frames (data-independiente). Está excluida
  por la tarjeta (`docs/instrucciones-loam.md` §3.3) y no se propone.
- **Estrés: con OAM las fotos omitidas suben** (`back` 145 → 295, racha 3 → 6;
  `sprites` 0 → 32; §2.3). El coste de OAM exclusivo de los frames más densos de
  Rex es de unos 14 900 ciclos Musashi (≈ 15 pp con el factor ×1,44 de §3.5; en
  WinUAE, en `back` r=3360, el delta del mismo frame es 18,9 pp, §2.1). Con las palancas
  de OAM que quedan, la puerta «estrés no peor que control» **no se puede cerrar**
  en el alcance de L-OAM (§4.2).
- **Scroll**: no forma parte de `level_frame`. El coste de OAM no tiene ningún
  componente de scroll; el scroll solo afecta a través del tiempo que deja libre (§3.4).
- **Factor Amiga/Musashi**: P96 dice ×1,03 para `level_frame`. Con los mismos frames
  de WinUAE y Musashi sale ×1,07-1,13 sin OAM y ×1,16-1,21 con OAM, y el delta de
  OAM es ×1,44 (§3.5). No se convierte ningún ciclo de Musashi a tiempo real sin
  ese factor.
- **Tarjeta propuesta (una):** portar a asm la ruta de la piraña (§5). Ahorro
  necesario ≥ 1 500 ciclos Musashi en el pico; estimación de ahorro 3 000-3 600
  (**estimado**, no medido). Si no basta, la puerta de YI1 no se cumple y se para.

## 2. Lógica, interrupción, render y fotos (WinUAE cycle-exact)

Cada columna sale de un fichero distinto: no se suman máximos de frames distintos.
Todos los números son del peor frame de la columna indicada, salvo los de medias.

### 2.1 Lógica (`level_frame`, peor frame)

| escenario | sin OAM | con OAM | Δ en el mismo frame | fuente (sin OAM / con OAM) |
|---|---:|---:|---:|---|
| YI1 (r=4570, oráculo 9715) | 29,5 % (4192 t) | **41,2 %** (5855 t) | +11,7 pp | `l4_yi1_nooam/read.txt:9`, `l4_yi1_oam/read.txt:9` |
| back (r=3360, oráculo 4813) | 55,0 % | 73,9 % | +18,9 pp | `l4_back_nooam/read.txt:9`, `l4_back_oam/read.txt:9` |
| sprites (r=1648, oráculo 3101) | 53,7 % | 70,7 % | +17,0 pp | `l4_sprites_nooam/read.txt:9`, `l4_sprites_oam/read.txt:9` |

Repetibilidad (`coord4`, mismo commit, otra tanda): YI1 29,5 / 41,2 %
(`coord4_yi1_*/read.txt:9`); back 55,0 / 73,9 % (`coord4_back_*/read.txt:9`); sprites
53,5 / 70,8 % (`coord4_sprites_*/read.txt:9`).

### 2.2 Interrupción completa (lógica + foto), peor frame

| escenario | sin OAM | con OAM | fuente |
|---|---:|---:|---|
| YI1 | 38,7 % (5493 t) | 50,3 % (7146 t) | `l4_yi1_*/read.txt:26` |
| back | 66,6 % (9458 t) | 83,8 % (11904 t) | `l4_back_*/read.txt:26` |
| sprites | 63,8 % (9070 t) | 81,6 % (11601 t) | `l4_sprites_*/read.txt:26` |

Coordinador: 66,5 / 83,8 % en back (`coord4_back_*/read.txt:26`); 38,6 / 50,3 % en YI1.

### 2.3 Fotos omitidas (O5) y rachas

| escenario | sin OAM | con OAM | racha máx. | VBL sin imagen nueva | fuente |
|---|---:|---:|---|---|---|
| YI1 (6312 lógicos) | 14 (0,22 %) | 27 (0,43 %) | 1 → 1 | 15 → 28 | `l4_yi1_*/read.txt:22-23,25` |
| back (4126) | 145 (3,51 %) | **295 (7,15 %)** | 3 → 6 | 146 → 296 | `l4_back_*/read.txt:22-23` |
| sprites (1914) | 0 (0,00 %) | **32 (1,67 %)** | 0 → 2 | 1 → 33 | `l4_sprites_*/read.txt:22-23` |

Coordinador: idénticos (`coord4_*/read.txt:22`). Los agregados BENCH no dan ventana250
ni p99 (P107); aquí solo se comparan los contadores de `read.txt`.

### 2.4 Render (scroll) y tiempo total

| escenario | `build_mid` peor frame, sin / con OAM | total medio (entrada→blitter libre) | fuente |
|---|---:|---:|---|
| YI1 | 88,8 % (r=5852) / 88,4 % (r=5852) | 31,3 % → 38,1 % | `l4_yi1_*/read.txt:5,12` |
| back | 165,1 % (r=2583) / 173,4 % (r=2595) | 46,2 % → 54,3 % | `l4_back_*/read.txt:5,12` |
| sprites | 43,3 % (sin OAM, `l4_sprites_nooam/read.txt:12` tabla) / 49,0 % | 40,9 % → 48,6 % | `l4_sprites_*/read.txt:5,12` |

En el mismo frame de YI1 (r=5852, pico de `build_mid`) el total hasta blitter libre
pasa de 17 018 a 18 311 t (`l4_yi1_*/read.txt:14`): la lógica con OAM ocupa parte de
ese frame aunque el pico de scroll no cambia. El render por sí solo ya pasa el 100 %
del frame en el estrés `back` con y sin OAM (165 % y 173 %).

## 3. Coste de OAM que queda (Musashi, sin DMA; frames del oráculo)

### 3.1 Pico de YI1: oráculo 9715 (`work/revision-loam-1007/diff_yi1_9715.txt`)

Perfil por función con `--every 1` sobre `oracle_yi1.bin`, build sin OAM
(`loam_base_nooam`) y build final (`loam_rexentry_oam`). Ciclos propios:

| función | sin OAM | con OAM | Δ | nota |
|---|---:|---:|---:|---|
| `finish_oam_write_asm` | 0 | 2 772 | +2 772 | dos llamadas: Rex y `sub_spr_gfx0` |
| `level_frame` (limpieza) | 502 | 2 728 | +2 226 | constante, excluida |
| `sub_spr_gfx0` (C) | 0 | 1 906 | +1 906 | una llamada: piraña |
| `rex_gfx_asm` | 0 | 1 088 | +1 088 | una llamada |
| `piranha_gfx` (C) | 0 | 1 044 | +1 044 | una llamada |
| `sub_spr_gfx2_at` (C) | 0 | 986 | +986 | una llamada: piraña |
| `get_draw_info1` (C) | 754 | 1 508 | +754 | dos llamadas, 754 c. cada una |
| `spr_oam_index` (C) | 0 | 384 | +384 | dos llamadas (Rex y piraña) |
| `oam_mark` (C) | 0 | 224 | +224 | dos llamadas, ambas de piraña |
| `oam_offscreen_vert` (C) | 0 | 100 | +100 | piraña |
| puentes C/PIC | — | — | +314 | `f44d` 120, `sprite_run` 96, `rex_gfx` 66, `mario` 32 |
| `jumping_piranha` | 860 | 646 | −214 | el dibujo pasa a `piranha_gfx` |
| `rex_main_asm` | 694 | 650 | −44 | |
| **total de `level_frame`** | **37 050** | **48 590** | **+11 540** | |

Mismo delta en 9714 (+11 540; `work/revision-loam-1007/yi1an_replay.py`): el
delta de OAM es plano en el pico.

Ruta de la piraña, bruto en 9715: 1 044 + 986 + 1 906 + 1 508 + 192 + 224 + 100
= **5 960 ciclos** (los 192 de `spr_oam_index` son la mitad de la llamada que
usa la piraña). El reparto de `finish_oam_write_asm` entre Rex y piraña no está
separado en el perfil.

### 3.2 Estrés `back`: oráculo 3097 (frame del perfil de L-OAM, top-3 con `--every 4`)

| función | sin OAM | con OAM | Δ |
|---|---:|---:|---:|
| `finish_oam_write_asm` | 0 | 5 836 | +5 836 |
| `rex_gfx_asm` | 0 | 5 440 | +5 440 |
| `level_frame` (limpieza) | 502 | 2 728 | +2 226 |
| `spr_oam_index` | 0 | 960 | +960 |
| `rex_gfx` (puente C, `cd5001c`) | 0 | 330 | +330 |
| puentes PIC | 0 | 320 | +320 |
| `rex_main_asm` | 3 470 | 3 250 | −220 |
| **total** | **58 008** | **72 900** | **+14 892** |

Fuente: `work/revision-loam-1007/diff_frames_3097_3101.txt`. Frame 3101 da lo mismo
(+14 878). El `loam_*_oam_prof.txt` del informe L-OAM (top-20) coincide en cada
cifra que lista.

El frame 3097 tiene cinco llamadas a `rex_gfx_asm` y ninguna a la ruta de la
piraña (`work/revision-loam-1007/back_composicion.txt`).

### 3.3 Media del estrés (1032 frames, cada 4)

Sin OAM 34 996 → con OAM 43 601 (+8 605 ciclos/frame): `finish` +2 246, limpieza
+2 226, `rex_gfx_asm` +1 124, `sub_spr_gfx0` +502, `sub_spr_gfx2_at` +468,
`spr_oam_index` +404, `banzai_gfx` +387, `piranha_gfx` +275, `chuck_gfx` +181,
`goal_gfx` +144, `get_draw_info1` +199, `oam_mark` +91 (`diff_media_replay_stress.txt`).
Es decir: lo de Rex es algo más de un tercio; el resto son las demás rutinas de
gráficos C (G8), entre ellas la piraña.

Replay de YI1 (6181 frames): media sin OAM 28 589 → con OAM 35 604 (+7 015), y 2 595
frames con piraña (`conteos_pirana_rex.txt`).

### 3.4 Qué parte es del scroll y qué es otra cosa

- **Scroll: 0 pp de la lógica.** `scroll_frame` (`columna`, `build_mid`, resto) corre
  en el render (`dc_loop`, `player/game.s`, cabecera de O5), no en `level_frame`. No
  aparece ninguna función de scroll en el delta de los perfiles (§3.1-3.3).
- `camera_F6DB` (lógica de cámara, no scroll de pantalla) es igual en los dos builds.
- Lo que no es OAM ni scroll: entrada (`game_step` sin `level_frame`) 0,7-1,0 pp
  (`l4_*/read.txt:8`), y `mspr_draw` (captura en COPER, ~8 %), que no cambia con OAM.
- El scroll sí influye en la OAM por el tiempo que deja libre el render (§4), no por
  código.

### 3.5 Factor Amiga/Musashi

| par (mismo oráculo) | Musashi | WinUAE (ciclos nominales) | factor |
|---|---:|---:|---:|
| YI1 sin OAM, 9715 (mapa A) / 9714 (mapa B) | 37 050 / 39 026 | 41 920 | 1,13 / 1,07 |
| YI1 con OAM, 9715 / 9714 | 48 590 / 50 566 | 58 550 | 1,21 / 1,16 |
| **Δ OAM, YI1** (plano en 9714-9715) | 11 540 | 16 630 | **1,44** |

Mapa A: r=4570 ↔ oráculo 9715 (el documentado). Mapa B: r=4570 ↔ 9714 (es el que
hace coincidir el máximo de Musashi con el de WinUAE en los dos builds). Ver §7.

- **P96 (×1,03 para `level_frame`) no se confirma para este código**: ×1,07-1,13 sin
  OAM. ROADMAP §2 (×1,3-1,4) queda más cerca.
- **Δ OAM: ×1,44 en YI1** (par fiable: mismo `oracle_yi1.bin` en `stress_ab_build.sh`
  y en Musashi).
- El par `back` no es estable: los frames vecinos de Musashi (4809-4812) tienen Δ de
  15 402 y el 4813 de 12 876, y el factor cae entre ×1,7 y ×2,1 según el mapa.
- El par `sprites` no es el mismo estado: el registro del oráculo 3101 difiere en
  27 de 576 bytes entre `oracle_stress_back.bin` y `oracle_stress_sprites.bin`
  (medido). No se usa como factor.

## 4. Por qué el estrés sale peor que su control

### 4.1 Mecanismo (con las cifras de §2)

En O5 la lógica corre en la interrupción COPER (línea 272) y el render después, en
el bucle principal (`player/game.s`, cabecera de O5). Cada ciclo que la lógica gasta
en esa interrupción sale del tiempo del render del mismo frame. Con OAM el peor
frame de interrupción sube de 66,6 a 83,8 % en `back` y de 63,8 a 81,6 % en
`sprites`, y las fotos que no llegan a tiempo se duplican en `back` (145 → 295) y
aparecen en `sprites` (0 → 32).

Esto es una explicación coherente con los números, no una medida aislada: no hay un
experimento que varíe solo la lógica de OAM y mida las fotos.

El control de `back` ya pierde 3,51 %, y su pico de `build_mid` (165 %, que supera el
frame entero sin OAM; `l4_back_nooam/read.txt:12`) coincide con esa pérdida. Ese pico está en s≈4606 y no coincide
con el pico de la lógica de OAM (Rex denso, r=3360, s=2804). Las dos cosas suman.

### 4.2 La puerta de estrés no es alcanzable con L-OAM

Para «estrés con OAM no peor que control» habría que quitar casi todo el coste de
OAM de los frames densos de Rex (14 892 ciclos Musashi a 3097, ≈ 15 pp con ×1,44).
Lo que queda:

- `finish_oam_write_asm` (5 836) y `rex_gfx_asm` (5 440): ya en asm; no hay palanca
  barata.
- Limpieza (2 226): excluida por la tarjeta.
- `spr_oam_index` (960): C de 5 llamadas por frame; es lo único pequeño y
  no excluido.

Aunque `finish` y `rex` bajaran a la mitad, la limpieza se fuera y `spr_oam_index`
fuera a cero, quedarían ≈ 6 000 ciclos Musashi (≈ 6 pp con ×1,44) de coste OAM por
encima del control. El límite de la puerta lo fija la temporización del render
(`build_mid` 165 %), no solo la OAM. La puerta de estrés necesita decisión del
coordinador: o se redefine, o se combina con el reparto de picos de scroll (S5,
`ROADMAP.md` §2).

## 5. Tarjeta propuesta (una): ruta de la piraña en asm

**Nombre:** L-OAM 2 (paso 5): la ruta de la piraña en asm.

**Objetivo medible:** llevar `level_frame` máximo de YI1 con `SPR_OAM` a **≤ 40 %**
en WinUAE cycle-exact, con control en la misma tanda, sin empeorar el estrés.

**Por qué esta y no otra:**
- En YI1, el pico y los 37 frames por encima de 40 % (mapa B; 172 de 178 con el
  mapa A) tienen piraña. La ruta de la piraña en C es 5 960 ciclos Musashi brutos
  en el pico, más de la mitad del delta de OAM (§3.1).
- Las otras palancas del pico son la limpieza (excluida) y `finish`/`rex` (asm).

**Alcance (ficheros exactos):**
- `player/logic68k.s`: nuevas rutinas asm `_piranha_gfx_asm` (sustituye a
  `piranha_gfx`), con `sub_spr_gfx2_at(x, 0)` y `sub_spr_gfx0(x, 1)` integradas (la
  piraña es su único llamador de `sub_spr_gfx0`; `sub_spr_gfx2_at` lo usan también
  otros, así que su versión C se queda), y `_get_draw_info1_asm` como helper
  compartido con sus llamadores C.
- `player/spr_gfx.c`: `piranha_gfx`, `sub_spr_gfx2_at` y `sub_spr_gfx0` pasan a
  puente bajo `#ifdef LOGIC68K` (como `rex_gfx`, P109). La versión C queda para
  PC/NOASM.
- `player/msprite.c`: `get_draw_info1` pasa a puente bajo `LOGIC68K` (la C queda como
  referencia del PC).
- No se toca: `game_build.sh` (su comprobación de `_rex_gfx` sigue), baselines,
  puertas, ni la limpieza de `level_frame`.

**Presupuesto de ciclos (Musashi, perfil `--every 1`, oráculo 9714-9715):**
- Coste de la ruta de la piraña antes: 5 960 bruto. Después: objetivo ≤ 2 500
  (ahorro ≥ 3 400 **estimado**; mínimo aceptable ahorro ≥ 1 500).
- `level_frame` del pico: 48 590 → ≤ 45 000 (medido en Musashi, no en WinUAE).
- Presupuesto del frame en WinUAE tras la tarjeta: estimado ≈ 38 % (no medido).

**RAM que debe quedar idéntica (todo byte):**
- `ram[]` entera tras `piranha_gfx`, `sub_spr_gfx2_at`, `sub_spr_gfx0` y
  `get_draw_info1` (cruce PC = 68000: `m68kverify --cross`, `oam68k_gate.sh` paso 4).
- Temporales `m0`-`m15` (`$00-$0F`): `sub_spr_gfx0` deja `m4 = $FF` y `m15 = 0`.
- Entradas OAM `$0300-$03FF` (`wm_OamSlot`) y tamaños `$0460-$049F` (`wm_OamSize`).
- Sprite de la piraña: `wm_SpriteProp`, `wm_SpriteGfxTbl`, `wm_SpritePal`,
  `wm_SpriteYLo/Hi` (se modifican y se restauran), `wm_SprOAMIndex` (**queda en
  `first + 4`**, como la ROM), `wm_OffscreenHorz/Vert`, `wm_SpriteOffTbl`.
- `spr_oam_first[]`, `spr_oam_n[]` (arrays C del verificador, escritos por
  `oam_mark`): no son `ram[]`; comprobar con `sprite_oam_verify` (la traza).

**Oráculos que la ejercitan:**
- `oam68k_gate.sh`: `yi1:AB`, `chuck:95`, `goal:7B`, `shells:05`, `banzai:9F`,
  `stress_piranha:4F` (la piraña, con `--require 4F`).
- `m68kverify --mode loop --sprites --cross`: replay de YI1 (2 595 frames con piraña)
  y `oracle_stress_piranha.bin`.
- `gamecheck --spr` con el replay de YI1 (binario sin `-DBENCH`, P97-4).
- `abcheck.py BASE --sprites` con `CDEFS='-DNOOAM -DSPR_OAM'` (lazo cerrado, 6547
  frames; semántica IGUAL).

**Puertas (en el último commit):**
1. `python tools/lint_port.py` → `RESULTADO: OK`.
2. `python tools/regress.py --baseline tools/baseline_pc.json --level` → `RESULTADO: OK`.
3. `sh tools/oam68k_gate.sh` → `OAM68K: OK`.
4. `sh tools/stress_ab_build.sh l5` → `STRESS_AB_BUILD: OK`; `stress_ab_shots.ps1 -Prefix l5`
   (`STRESS_AB_SHOTS: OK (6 capturas)`); `stress_ab_read.sh l5` → `STRESS_AB_READ: OK`.
5. En `l5`: **YI1 con OAM, `level_frame` máximo ≤ 40 %** (control `l5_yi1_nooam` en
   la misma tanda). Back y sprites con OAM: fotos omitidas **no peores** que `l4`
   (295 y 32).

**Condiciones de parada:**
- Tres intentos distintos sin cumplir la puerta de Musashi → parar (reglas de ola, regla 6).
- Ahorro medido en Musashi < 1 500 en 9714-9715 → parar y no seguir con otras
  funciones (la tarjeta no es suficiente).
- Cualquier byte de RAM distinto sin explicar → revertir el paso.
- `l5` YI1 > 40 % → parar; no añadir tarjetas sin decisión del coordinador.
- Estrés `l5` peor que `l4` → revertir.

**Trampas a vigilar** (AGENTS §8): P40 (índice `(An,Dn.w)` con signo, en el bucle de
tiles), P79 (`cmp/bhs` sin signo con registro reusado), P102 (`PICCALL` para C
lejano: `oam_offscreen_vert`, `get_draw_info1`, `spr_oam_index`), P109 (símbolos C
que el asm sustituye, como `rex_gfx`), P36 (sin datos nuevos cerca de `a4`).

**Riesgo:** `get_draw_info1` tiene otros llamadores (goal, powerup, shells). Si el
cruce de algún oráculo falla por esa parte, se deja una copia local de
`get_draw_info1` solo para la piraña (sin tocar los demás).

**No hace:** no toca la limpieza, `finish`, Rex ni scroll. No resuelve la puerta de
estrés (§4.2).

## 6. Lo que no se pudo confirmar

- Ahorro de la tarjeta: **no medido**. El 60 % de la ruta de la piraña es una
  estimación; el mínimo de 1 500 ciclos Musashi sí sale de las cifras medidas.
- Factor ×1,44 (Δ OAM): medido en dos mapas de frame de un solo par (YI1). Un par
  fiable no basta para fijar el factor de la piraña.
- Correspondencia exacta de frame WinUAE ↔ Musashi (±1): no resuelta.
- Coste de `finish` que corresponde a la piraña (dos llamadas por frame): no separado.
- Efecto marginal de la lógica de OAM sobre las fotos omitidas: no aislado.
- Estado de `back`/`sprites` en Musashi: se usó `oracle_stress_back.bin` para los dos
  pares, y el de `sprites` no coincide (§3.5).
- No se corrió WinUAE, FS-UAE ni hardware real en esta revisión.

## 7. Notas para el coordinador (no son cambios de código)

- Desfase de un frame: en YI1 el máximo de Musashi (9714) no coincide con el de
  WinUAE (r=4570 ↔ 9715) en ninguno de los dos builds; el delta de OAM sí es plano.
  Hace falta una comprobación del índice de frame en el exportador (medida-d1, P107).
- Columna «oráculo» de `l4`/`coord4` incorrecta para `back` y `sprites` (usa 5145).
  Ya está documentado en `docs/medida-d1-estres.md`; las tablas de L-OAM no lo corrigen.
- Los dos oráculos de estrés (`back` y `sprites`) tienen estados distintos en el mismo
  índice de frame (§3.5).
- Musashi de `back` en el frame 4809-4812 tiene Δ de 15 402; el worst de WinUAE está
  en 3360 (≈ 4813). Para estrés, medir por frame la traza de WinUAE sería mejor que
  el máximo.
- Archivos de evidencia (ignorados por git): `work/revision-loam-1007/*.txt` y los
  scripts `diff.py`, `diffavg.py`, `yi1an_replay.py`, `comp.py`, `m68kprof_dump.py`
  (copia de `tools/m68kprof.py` con más filas y volcado; no toca el original).
