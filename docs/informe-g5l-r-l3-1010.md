# G5L-R-L3 — perfil de la lógica y cierre

2026-10-10. Rama `g2t-b2bis`. **Nada integrado**; el binario no cambia.
Tarjeta: `instrucciones-g5l-r-l3.md`.

## 1. Partida

Lint y regresión completa: OK. Control `GDEFS='-DREPLAY'` (G5L por
defecto) archivado en `work/l3/control_arch`; `g5l.py game --pcprof
--pclogic` sobre las seis ventanas de la tarjeta: `G5L GAME: OK`.

El perfil por etiqueta necesitó arreglos en el lector (nuevo
`tools/lprof.py`): las líneas de macro y de `rept` (`1M`, `1R`) no llevan
`:` y las etiquetas de vbcc tampoco. Sin eso, el bucle `rept` de `mspr_draw` y el C de los sprites
aparecían sin dueño o atribuidos a la etiqueta anterior.

## 2. Perfil (Musashi, ciclos propios, sin DMA)

| función | YI1 (321 fotos, media 39.960/foto) | back 2440-2600 (161 fotos, mediana 52.880, máx. 64.840) |
|---|---:|---:|
| `mspr_draw` (con su `rept`) | 7,8 % | 9,9 % |
| `_finish_oam_write_asm` | 7,1 % | 8,4 % |
| `_mario_E2BD` | 5,8 % | 4,5 % |
| `_level_frame` | 5,5 % | 4,3 % |
| `g5l_capture` | 4,9 % | 3,6 % |
| `_spr_tile_asm` | 4,4 % | 3,9 % |
| `mc_pxy` | 4,3 % | 3,5 % |
| `_camera_F6DB` | 4,2 % | 3,5 % |
| `_chuck_gfx` (C, vbcc) | — | 4,3 % |
| `_sprite_run_post` (C, vbcc) | — | 3,7 % |

Fuentes: `work/l3/control_pc.json`, `work/l3/back_logic.json`. El perfil es
**plano**: nada pasa del 10 %.

## 3. Candidatos

| candidato | resultado | decisión |
|---|---|---|
| `-DMCACHE`: caché de 64 bloques ya convertidos (4 KB) en el camino corto de `mspr_draw` | `gamecheck --spr` exacto; replay YI1 (perfil legacy, 6.312 fotos): media 4.188 → 3.854 (−8 %), **máx. 7.750 → 9.892 (+28 %)** | retirado: no llega al 25 % y empeora el pico |
| `_camera_F6DB`: RD16/WR16 por palabras en direcciones pares | **estimado** ≈ 15 % de la función (≈ 250 de 1.700 ciclos) | no se implementa |
| `_mario_E2BD`, `mc_pxy` | asm lineal, una vez por frame (≈ 2.300) o ≈ 312 por llamada; sin un 25 % visible | no se implementa |
| `gfx32` preintercalado para `mspr_draw` | ≈ −55 % de la función, pero +47,6 KB de slow (el vivo tiene 61 KB libres, que además hacen falta para las tablas de CPU que hoy están en chip) | no se implementa |
| `_finish_oam_write_asm` | ya retirado en L2 por BENCH peor | no se reintenta |

Los C de back (`_chuck_gfx`, `_sprite_run_post`, ≈ 8 % juntos) son
candidatos para la directiva de pasar todo a asm. Serían una tarjeta
de traducción con el cruce PC = 68000, no un recorte de L3.

## 4. Conclusión

Con este perfil, ningún recorte de la lógica mueve D1 de forma medible:
el mejor caso realista (≈ 15-25 % de una función del 4-8 %) es ≈ 1 % de
la lógica. Junto con S10/S11 y M1: lo que separa el estrés de D1 es la
reconstrucción de la vuelta multiplicada por el DMA de los 6 planos. Las
palancas que quedan son de diseño (decisión del usuario).
