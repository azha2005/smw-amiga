# G5L-R-L, paso 1 — qué sube en el racimo 3305-3364 (2026-10-10)

Rama `g2t-b2bis`. Solo medida (`instrucciones-g5l-r-l.md`, paso 1); el juego
no cambió. Herramientas: `g5l.py game --pcprof OUT --pclogic RANGOS` (la
lógica, `dc_cop`, instrucción por instrucción en esas fotos) y
`tools/l_funcs.py` (por función).

**Resultado.** La lógica también es **plana**: la función más cara es el
6,5 % y las diez primeras son casi todas asm ya escrito a mano. En el
racimo sube porque hay **más sprites vivos** (la piraña saltarina y los
Rex), un poco en cada rutina del motor de sprites. Según el modelo, bajar a
≤ 5 omitidas pide **−20 % de toda la lógica** (≈ 8,6 k ciclos por frame) o
**una cuarta lista** del copper (otros +20 ms de latencia): eso último lo
decide el usuario.

## 1. Puerta

321 fotos paso a paso (1020-1130, 1690-1715, 2050-2080, 2730-2760,
3280-3370, 4195-4225): el total paso a paso es **igual** a lógica + captura
de la corrida normal en las 321. `G5L GAME (pcprof): OK`.

## 2. La lógica por función (Musashi, 49 448 ciclos por foto con la captura)

| función | por foto | % | en los 63 picos |
|---|---:|---:|---:|
| `_finish_oam_write_asm` (asm) | 3 198 | 6,5 | 3 015 |
| `mspr_draw` (asm) | 3 103 | 6,3 | **6 014** |
| `_f44d_asm` (asm) | 3 025 | 6,1 | 2 833 |
| `_level_frame` (C) | 2 728 | 5,5 | 2 728 |
| `_mario_E2BD` (asm) | 2 320 | 4,7 | 2 328 |
| `g5l_capture` (asm) | 1 946 | 3,9 | 1 981 |
| `_spr_tile_asm` (asm) | 1 755 | 3,6 | 2 184 |
| `_camera_F6DB` (asm) | 1 693 | 3,4 | 1 706 |
| `_banzai_gfx` (C) | 1 452 | 2,9 | 400 |
| `_sprites_all` (C) | 1 363 | 2,8 | 1 385 |
| cuatro de `mcoll.c` (C) | 3 885 | 7,9 | 3 954 |

Por fichero: `logic68k.s` 40 %, `mcoll.c` 14 %, `msprite.c` 13,5 %,
`manim.c` 13 %, `mspr68k.s` 7 %. El C suma ~21 k por foto.

En los picos (lógica > mediana + 8000) lo que más sube es el motor de
sprites en C (+6,3 k entre todas sus funciones), `mspr_draw` (+2,8 k: la
caché de Mario falla más), `_finish_oam_write_asm` (+1,7 k) y
`_jumping_piranha` (+0,5 k).

## 3. Lo que da cada palanca (modelo de cola sobre las fotos de S9; base 15 15 18 12 16)

| palanca | saltos del modelo |
|---|---|
| lógica −10 % | 10-11 |
| **lógica −20 %** | **2-5** |
| lógica −30 % | 0-1 |
| todo −4 000 por foto | 11 |
| todo −8 000 por foto | 4-6 |
| **cuarta lista** (holgura + 1 frame) | **1-8** |

El modelo da 2-5 saltos de más que WinUAE (R1: 19-22 contra 17; S9: 12-18
contra 12).

## 4. Opciones

1. **Lógica a asm, por partes** (L2, L3...): `_level_frame`, `mcoll.c`,
   `_banzai_gfx`, `_sprites_all` y el resto del C de sprites, cada uno con
   el cruce PC = 68000 (V1). Estimado (ESTIMADO): −30-50 % de cada función
   pasada, unos −6-9 k por foto en total si se pasa casi todo el C; varias
   sesiones.
2. **Cuarta lista** (decisión del usuario): 20 ms más de latencia sobre el
   colchón ya aceptado (D1, 2026-10-09). Chip: una lista más (`CL_SIZE` =
   `$E15C` = 57 692 B en el vivo, `work/s9/vivo/game.lst`), con 24 856 B
   libres hoy: **no entra** sin liberar chip antes (C2/C4).
3. Seguir con G5L (camino lento) y `bm_left` (primer pico): según el
   modelo vale 1-3 saltos.

## Comandos

```sh
python tools/g5l.py game --bin work/s9/replay/game.bin --lst work/s9/replay/game.lst \
    --pcprof work/l/prof.json --pclogic 1020-1130,1690-1715,2050-2080,2730-2760,3280-3370,4195-4225
python tools/l_funcs.py work/l/prof.json work/s9/replay/game.lst work/s9/frames.json 32
```
