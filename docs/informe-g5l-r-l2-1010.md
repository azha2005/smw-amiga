# G5L-R-L2 — la lógica a asm (lote 1), 2026-10-10

Directiva del usuario (2026-10-10): "todo necesita ser asm y bare metal, lo
más optimizado posible. escribir C no alcanza". El C queda como referencia
del PC; cada función pasada se verifica PC = 68000 (V1).

## 1. Commits (rama `g2t-b2bis`, sin merge ni push)

| commit | qué |
|---|---|
| `ffdc7dd` | `level_frame`, `sprites_all`, `mario_player`, `cddd`, `mario_collide` |
| `64fe31d` | `mario.c` (D5F2, D062, D7E4) y `mario_CEB1` |
| `6be4088` | `get_draw_info1` y los gráficos de `spr_gfx.c` (Banzai, Piranha, meta, spin…) |
| `eb4a42c` | `sub_offscreen3`, `mario_spr_interact`, `process_interact` |
| `0183faa` | `sprite_load_level`, `blocks_update` (camino rápido), `f8ab`, `sprite_tweakers`, `banzai_bill` |
| `222fb64` | `finish_oam_write_asm` en registros (~140 ciclos por ficha, antes ~250) |

Herramienta nueva: `tools/fuzzcall.py` (llama a una función del binario y
del C del PC con imágenes de RAM reales: `m68kverify --dumpall`, y compara).
Puentes PIC en `player/pic68k.s` y `sed` en `tools/logicbench_build.sh`
(P102). Todas con `lint_port.py` y `regress.py --level --g5l --bm1` verdes.

## 2. Replay normal de YI1

Musashi (`tools/g5l.py game`, lógica por foto, sin DMA):

| build | media | máx. | saltos del modelo (`t2_model`) |
|---|---:|---:|---|
| S9 (`b67ee4b`) | 40 886 | 59 792 | 15 15 18 12 16 |
| L2 lote inicial | 35 457 | 53 958 | 7-10 |
| tras `0183faa` | 33 298 | 49 614 | 5 5 7 5 4 |
| `222fb64` | 32 301 | 47 892 | 4 4 6 4 4 |

WinUAE cycle-exact (`a500` vía `shot.ps1 -Exact`, KS 1.2):

| | S9 | `64fe31d` | `0183faa` | `222fb64` |
|---|---:|---:|---:|---:|
| VBTRACE, fotos omitidas | 12 | 4 | 1 | **0** (solo el VBL 0 del arranque) |
| BENCH, fotos perdidas | 36 | 16 | 13 | **10** (0,16 %), racha 1 |

ADF de `222fb64`: VBTRACE `d989cde6ec7520e840890374c94ef110`, BENCH
`ca8c9952477230d2e05ed5621a2cbb2f`. VBTRACE y BENCH cuentan cosas
distintas (P107): el sondeo de BENCH cuesta.

**El objetivo D1 del replay normal (0 omitidas) se cumple en VBTRACE.**

## 3. Estrés (compuerta mínima: ≤ 0,1 %, racha 1, ≤ 1 cada 250)

BENCH, WinUAE cycle-exact, `game_read.py --auto`. "Antes" = `e7234ab`
(el S9 con la tarjeta L2 escrita, sin código L2), mismo replay.

| escenario | antes | `222fb64` | `level_frame` máx. | total medio |
|---|---|---|---:|---:|
| `stress_back` (4126) | **Guru 3** (§4), no mide | 341 = 8,26 %, racha 4 | 60,9 % | 96,9 % |
| `stress_sprites` (1914) | 192 = 10,03 %, racha 6 | 92 = 4,81 %, racha 3 | 57,8 % | 94,8 % |

ADF: `33c288b8ce5b28d162f6e0c034888e0b` (back),
`a689837efe6c928df35c0c093ba7b7c5` (sprites). **Roja.** Lo que domina ya
no es la lógica: en `stress_back` el peor `build_mid` es 171 % del frame y
"resto de scroll_frame" 122 % (vuelta con muchas columnas); en sprites,
`resto de scroll_frame` 95 %. La próxima palanca es el render/scroll en
estrés, no más C → asm.

## 4. Guru 3 en `stress_back` con `e7234ab` (abierto)

Reproducible (2 de 2 corridas). Con `-DADRTRAP` (P123):

```
grupo 0: lectura en $31FA00A7 (24 bits: $FA00A7, impar)
PC binstart + $32772 = g5l.s:1248  move.w 16(a3,d7.w),d0   (g5l_render)
a3 = $31FA0031 = GV_TAB(a6)   a6 = g5l_v
```

`GV_TAB` está pisado. Va justo detrás de `GV_W` (224 × 8 B, escrito por
`g5l_wcache` con índice = segmento). Candidato: un segmento ≥ 224 (o con
basura en la parte alta de `d0.w`). El render G5L es el mismo en
`222fb64`, que no cae en este replay: **el fallo puede estar latente**.
`m68kverify --odd` sobre la lógica de `e7234ab` en `stress_back`: 0 accesos
impares (la lógica no es).

Siguiente paso: en `tools/g5l.py game` (Musashi) con el binario de
`e7234ab` + `stress_back`, comprobar `GV_TAB` después de cada llamada y,
en la foto donde cambia, `step_call` instrucción a instrucción hasta el
PC que lo escribe; o un `chk` de `d0 < LINES` en `g5l_wcache` con
`-DADRTRAP`.

## 5. Lo que queda en C

Caminos fríos: `default_interact`, el spawn de `load_column`,
`blocks_update_c`, Chuck/caparazón/power-ups, `mgfx.c`, `mspr.c`, los
caminos raros de `mcoll`, `camera_F6DB_c` (vertical). En el perfil del
replay normal, el C es ~5 % del tiempo de la lógica por foto; lo caliente
ya es asm: `mspr_draw` 3103, `finish_oam_write_asm` 2830, `_mario_E2BD`
2320, `_level_frame` 2184, `g5l_capture` 1946, `_spr_tile_asm` 1755,
`mc_pxy` 1705, `_camera_F6DB` 1693 ciclos por foto (`work/l2/prof3.json`).
