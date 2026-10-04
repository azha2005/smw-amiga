# Cobertura del C del port bajo el verificador (V2)

> Generado por `tools/coverage.py` (no editar a mano salvo la sección "Notas (a mano)" del final, que se conserva). Qué es y por qué: `docs/investigacion-ports.md` §4.4 y P69.

**Corridas:** 137 de 137 terminaron bien (27 grabaciones: banzai, chuck, diagpipe, goal, goal_low, goal_miss, goalhit, hills, hills2, normal, pipe, pw_1up, pw_bloques, pw_c7, pw_estrella, pw_flor, pw_medio, pw_morir_caida, pw_morir_enemigo, pw_seta, pw_yoshicoin, shells, stress_back, stress_piranha, stress_sprites, stress_vert, yi1). Una línea cuenta como ejecutada si corrió bajo `marioverify` con cualquiera de ellas.

## Resumen por fichero

| fichero | funciones ejecutadas | líneas ejecutadas | ramas tomadas |
|---|---|---|---|
| `player/manim.c` | 13/13 | 277/342 (81 %) | 163/244 (67 %) |
| `player/mario.c` | 6/6 | 176/201 (88 %) | 108/142 (76 %) |
| `player/mcam.c` | 3/3 | 116/125 (93 %) | 58/76 (76 %) |
| `player/mcoll.c` | 38/44 | 619/889 (70 %) | 298/572 (52 %) |
| `player/mgfx.c` | 2/2 | 128/141 (91 %) | 42/64 (66 %) |
| `player/msprite.c` | 61/64 | 910/1092 (83 %) | 518/788 (66 %) |
| `player/spr_chuck.c` | 17/18 | 213/261 (82 %) | 92/134 (69 %) |
| `player/spr_goal.c` | 5/5 | 114/120 (95 %) | 43/48 (90 %) |
| `player/spr_powerup.c` | 6/7 | 113/162 (70 %) | 59/117 (50 %) |
| `player/spr_rex.c` | 2/2 | 66/66 (100 %) | 37/38 (97 %) |
| `player/spr_shell.c` | 14/16 | 164/238 (69 %) | 71/154 (46 %) |
| **total** | 167/180 | 2896/3637 (80 %) | |

## Funciones que no corren nunca

Ninguna grabación las comprueba: pueden estar mal sin que `regress.py` lo vea.

| fichero | función | líneas | rutina de SMW |
|---|---|---|---|
| `player/mcoll.c` | `unsup` (l. 46) | 1 | - |
| `player/mcoll.c` | `f443` (l. 259) | 1 | CODE_00F443 |
| `player/mcoll.c` | `kill_mario` (l. 278) | 5 | CODE_00F629 |
| `player/mcoll.c` | `no_buttons` (l. 283) | 4 | CODE_00F629 |
| `player/mcoll.c` | `f629` (l. 287) | 1 | CODE_00F629 |
| `player/mcoll.c` | `efcd` (l. 693) | 7 | CODE_00EFBC |
| `player/msprite.c` | `spr_unsup` (l. 40) | 1 | CODE_01AB46 |
| `player/msprite.c` | `spr_spr_contact` (l. 294) | 24 | - |
| `player/msprite.c` | `spr_spin_kill` (l. 749) | 13 | _01A924 |
| `player/spr_chuck.c` | `chuck_die` (l. 119) | 7 | _02C7B1 |
| `player/spr_powerup.c` | `powerup_init` (l. 59) | 5 | - |
| `player/spr_shell.c` | `shell_set_stunned` (l. 68) | 7 | - |
| `player/spr_shell.c` | `shell_stun_0b` (l. 88) | 8 | _01AA0B |

## Funciones que corren a medias

Las que tienen líneas sin ejecutar, de más a menos. Los tramos son líneas del fuente (solo las que tienen código).

| fichero | función | sin ejecutar / con código | tramos sin ejecutar |
|---|---|---|---|
| `player/mcoll.c` | `eb77` | 55 / 234 | 865, 884, 886, 889-893, 898, 900, 904-907, 909-919, 962, 979-981, 993-995, 1000, 1009, 1014, 1023-1024, 1045-1046, 1052, 1058, 1069-1070, 1073-1075, 1083, 1104-1105, 1117-1121, 1135 |
| `player/mcoll.c` | `f545` | 23 / 29 | 96-101, 103-107, 109-114, 120-122, 124, 126-127 |
| `player/spr_chuck.c` | `chuck_run` | 23 / 59 | 310-312, 327, 331-340, 343-346, 357-359, 366, 375 |
| `player/mcoll.c` | `bounce_spawn` | 22 / 46 | 372-373, 375-391, 393, 395, 406 |
| `player/msprite.c` | `shellless_koopa` | 22 / 71 | 1313-1314, 1316-1320, 1328-1329, 1339-1340, 1344-1347, 1350-1354, 1368, 1370 |
| `player/mcoll.c` | `blocks_update` | 21 / 46 | 419, 427, 429-431, 433-437, 439-441, 443-445, 455, 457, 464-465, 470 |
| `player/mcoll.c` | `f005` | 20 / 24 | 714-727, 729-734 |
| `player/manim.c` | `mario_CEB1` | 19 / 138 | 81, 105-107, 114-115, 125, 128, 135, 137, 151, 157-159, 161, 183-186 |
| `player/spr_powerup.c` | `powerup_main` | 19 / 59 | 124-125, 129-131, 133-135, 152, 157-160, 165-166, 174, 177-178, 183 |
| `player/mcoll.c` | `e92b` | 18 / 63 | 1173-1174, 1180-1181, 1192, 1197-1198, 1213-1217, 1224-1225, 1233, 1242, 1245-1246 |
| `player/manim.c` | `cddd` | 17 / 49 | 204, 217-232 |
| `player/msprite.c` | `spr_obj_vert` | 17 / 70 | 457-463, 483, 485, 494-501 |
| `player/manim.c` | `anim_death` | 16 / 29 | 323-329, 331-334, 336, 338-341 |
| `player/spr_shell.c` | `shell_release` | 16 / 35 | 291-296, 300-308, 315 |
| `player/spr_powerup.c` | `pw_touch` | 15 / 35 | 81-82, 85, 87, 89, 93-94, 100-101, 110-115 |
| `player/msprite.c` | `sprspr_react` | 14 / 31 | 1172, 1178-1180, 1183-1185, 1187, 1192-1194, 1196-1198 |
| `player/mcoll.c` | `eee1` | 13 / 68 | 774-775, 789, 798-803, 805-807, 810 |
| `player/mgfx.c` | `mario_E2BD` | 13 / 114 | 97-98, 113-115, 126-129, 165, 200, 237-238 |
| `player/msprite.c` | `default_interact` | 13 / 56 | 807-808, 812-813, 817-818, 833, 839-841, 846-847, 850 |
| `player/mcoll.c` | `f127` | 11 / 17 | 534, 537-539, 541-543, 545-548 |
| `player/msprite.c` | `sprspr_hop` | 11 / 16 | 1126, 1129-1138 |
| `player/msprite.c` | `invis_blk` | 10 / 39 | 919, 922, 938-944, 947 |
| `player/spr_chuck.c` | `chuck_st0` | 10 / 24 | 180-182, 186-187, 193-194, 200-202 |
| `player/spr_shell.c` | `shell_stunned` | 10 / 22 | 171, 176-182, 186-187 |
| `player/mario.c` | `mario_D7E4` | 9 / 27 | 270-271, 278-280, 288-289, 293-294 |
| `player/mcoll.c` | `f28c` | 9 / 12 | 604-608, 610-613 |
| `player/spr_powerup.c` | `powerup_from_block` | 9 / 39 | 207-208, 215-218, 224, 227, 243 |
| `player/manim.c` | `mario_player` | 8 / 50 | 379, 388-390, 392-393, 397, 409 |
| `player/mcoll.c` | `mario_hurt` | 8 / 26 | 301, 303, 306-307, 315-317, 321 |
| `player/msprite.c` | `spawn` | 8 / 34 | 57-58, 69-71, 73-74, 86 |
| `player/spr_shell.c` | `shell_timer` | 8 / 14 | 132-133, 137-139, 141-143 |
| `player/mario.c` | `mario_D5F2` | 7 / 123 | 119, 161-162, 167-169, 212 |
| `player/mario.c` | `mario_D062` | 7 / 12 | 251-257 |
| `player/mcoll.c` | `f309` | 7 / 23 | 623, 625-626, 641-644 |
| `player/mcoll.c` | `mario_collide` | 7 / 21 | 1303, 1307, 1313, 1316-1319 |
| `player/spr_shell.c` | `shell_kicked` | 7 / 33 | 201-202, 205, 215-217, 226 |
| `player/mcoll.c` | `f461_xy` | 6 / 20 | 142-143, 153-154, 157-158 |
| `player/msprite.c` | `sprite_run_post` | 6 / 52 | 1608-1609, 1642, 1656-1657, 1667 |
| `player/spr_chuck.c` | `chuck_contact` | 6 / 30 | 135-137, 153-155 |
| `player/spr_shell.c` | `shell_follow` | 6 / 31 | 247-249, 252, 254-255 |
| `player/mcoll.c` | `f3c4` | 5 / 8 | 579-582, 585 |
| `player/mcoll.c` | `f2c9` | 5 / 17 | 662, 664-667 |
| `player/msprite.c` | `info_box` | 5 / 14 | 999-1003 |
| `player/msprite.c` | `handle_killed` | 5 / 17 | 1533-1534, 1537-1539 |
| `player/spr_shell.c` | `shell_kick_or_carry` | 5 / 20 | 103-105, 114-115 |
| `player/mcam.c` | `camera_F6DB` | 4 / 58 | 152-153, 176, 191 |
| `player/mcoll.c` | `f17f` | 4 / 31 | 487-488, 503, 509 |
| `player/mcoll.c` | `mario_DC2D` | 4 / 11 | 1272-1275 |
| `player/msprite.c` | `load_column` | 4 / 27 | 150, 158-159, 162 |
| `player/msprite.c` | `sprspr_stun_hit` | 4 / 12 | 1150, 1156-1157, 1159 |
| `player/manim.c` | `anim_flower` | 3 / 9 | 295-297 |
| `player/mcam.c` | `f7f4` | 3 / 50 | 101, 103, 111 |
| `player/mcoll.c` | `f267` | 3 / 6 | 592-594 |
| `player/mcoll.c` | `ee85` | 3 / 8 | 844-846 |
| `player/msprite.c` | `sprite_level_start` | 3 / 30 | 184, 192-193 |
| `player/msprite.c` | `spr_obj_push` | 3 / 13 | 540-541, 549 |
| `player/msprite.c` | `sprspr_koopa02` | 3 / 6 | 1044, 1046-1047 |
| `player/msprite.c` | `sprspr_kill_y` | 3 / 10 | 1076-1077, 1080 |
| `player/msprite.c` | `sprspr_kill_x_chk` | 3 / 7 | 1091-1092, 1095 |
| `player/spr_goal.c` | `goal_tape` | 3 / 45 | 151, 168, 172 |
| `player/spr_shell.c` | `shell_carried` | 3 / 14 | 331, 334, 337 |
| `player/manim.c` | `level_frame` | 2 / 19 | 458, 461 |
| `player/mcam.c` | `f8ab` | 2 / 17 | 40, 51 |
| `player/mcoll.c` | `generate_tile` | 2 / 18 | 71, 85 |
| `player/mcoll.c` | `f44d` | 2 / 29 | 244-245 |
| `player/mcoll.c` | `f3e9` | 2 / 11 | 568-569 |
| `player/mcoll.c` | `eadb` | 2 / 6 | 1146-1147 |
| `player/msprite.c` | `spr_obj_interact` | 2 / 27 | 590, 592 |
| `player/msprite.c` | `warp_blocks` | 2 / 5 | 1487-1488 |
| `player/msprite.c` | `spr_contact_a80f` | 2 / 6 | 1518, 1520 |
| `player/spr_chuck.c` | `chuck_hurt` | 2 / 6 | 112, 114 |
| `player/spr_goal.c` | `trigger_goal_tape` | 2 / 24 | 95-96 |
| `player/spr_powerup.c` | `pw_axis` | 2 / 15 | 41-42 |
| `player/spr_shell.c` | `shell_ground` | 2 / 14 | 159-160 |
| `player/spr_shell.c` | `shell_run` | 2 / 10 | 353-354 |
| `player/mario.c` | `fe4a` | 1 / 21 | 60 |
| `player/mario.c` | `mario_D92E` | 1 / 9 | 321 |
| `player/mcoll.c` | `f160` | 1 / 8 | 526 |
| `player/mcoll.c` | `efbc` | 1 / 5 | 704 |
| `player/mcoll.c` | `f595` | 1 / 8 | 1287 |
| `player/msprite.c` | `flip_sprite_dir` | 1 / 6 | 265 |
| `player/msprite.c` | `flip_if_touching_obj` | 1 / 4 | 275 |
| `player/msprite.c` | `off_scr_erase` | 1 / 7 | 324 |
| `player/msprite.c` | `spr_tile` | 1 / 26 | 423 |
| `player/msprite.c` | `spr_update_pos` | 1 / 13 | 611 |
| `player/msprite.c` | `sub_offscreen3` | 1 / 22 | 686 |
| `player/msprite.c` | `spr_mario_contact` | 1 / 23 | 718 |
| `player/msprite.c` | `process_interact` | 1 / 13 | 891 |
| `player/msprite.c` | `flying_block` | 1 / 31 | 988 |
| `player/msprite.c` | `sliding_koopa` | 1 / 36 | 1272 |
| `player/msprite.c` | `jumping_piranha` | 1 / 50 | 1476 |
| `player/msprite.c` | `sprite_main` | 1 / 15 | 1596 |
| `player/spr_chuck.c` | `chuck_st1` | 1 / 25 | 234 |
| `player/spr_goal.c` | `goal_lvlend` | 1 / 24 | 206 |
| `player/spr_shell.c` | `shell_hit_block` | 1 / 8 | 42 |
| `player/spr_shell.c` | `shell_wall_hit` | 1 / 11 | 54 |
| `player/spr_shell.c` | `shell_stun` | 1 / 7 | 81 |

## Notas (a mano)

Clasificación del 2026-10-03 (primera corrida: 80 % de las líneas). Qué
tiene YI1: `AGENTS.md` D3 y D12. Lo que dice "a confirmar" no se miró en
el mapa del nivel.

**Importan para YI1 y ninguna grabación lo recorre** (candidatas a un
guion de snesorc nuevo, como las R de `SUBAGENTES.md`):

1. **Salto con giro sobre un enemigo** (`spr_spin_kill`, `_01A924`): el
   Rex y el Koopa se deshacen en humo. Nunca corre: ninguna grabación pisa
   un enemigo con giro. Guion: giro sobre un Rex y sobre el Koopa `$BD`.
2. **Matar al Chuck** (`chuck_die`, `_02C7B1`): el tercer pisotón o con la
   estrella. `oracle_chuck` lo pisa pero no lo mata; además `chuck_run`
   tiene 23 de 59 líneas sin correr (muriendo, `CODE_02C217`, y estados
   del salto). Guion: tres pisotones al Chuck.
3. **Mirar arriba parado** (`mario_CEB1` l. 151, `OWCreditsPose = 3`): la
   pose de apretar arriba quieto. Trivial de grabar.
4. **Caparazón que se frena y Koopa que se mete en un caparazón**
   (`shell_stun_0b`, `spr_spr_contact` en `shellless_koopa`): con el
   caparazón rojo `$DB` y el Koopa `$BD` del nivel puede pasar. El segundo
   termina en `spr_unsup` (no portado): primero portarlo, después grabarlo.
5. **Bloques giratorios** (`blocks_update` l. 429-445, `TurnBlockSpr`: el
   giro y el tiempo de giro) y **varios bloques rebotando a la vez**
   (`bounce_spawn` l. 372-391, sin ranura libre): a confirmar que YI1
   tenga bloques giratorios; si los tiene, golpear uno desde abajo y
   pisarlo girando.

**No importan para YI1** (el nivel no lo tiene; quedan sin verificar a
propósito):

- Cintas transportadoras (`efcd`/`efbc`), correr por la pared (`f005`),
  bloques de nota, puertas (`f443`, parte de `eb77`), agua y capa 2
  interactiva (`e92b`), y la capa (vuelo, `mario_CEB1` l. 114-115).
- `KillMario` (`f629`/`kill_mario`): lava, tiles que matan, aplastado y
  empujado fuera de la pantalla. La caída al vacío va por otro camino
  (`kill_start`, sí cubierto con `pw_morir_caida`).
- Lo de Yoshi en `powerup_main` (la baya, salir de Yoshi) y `powerup_init`
  (un `$74` puesto por el nivel: YI1 no tiene).
- Interruptores P (`f545`): a confirmar que YI1 no tenga.
- `unsup`/`spr_unsup`: los avisos de "no portado", que tienen que no correr.

**Cómo seguir:** cada guion nuevo de snesorc entra solo en la próxima
corrida (`tools/coverage.py` toma todos los `work/oracle_*.txt`). Una
función de la primera lista que pase a ejecutarse se borra de acá.
