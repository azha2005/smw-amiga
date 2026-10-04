/*
 * msprite.h - lo que comparten msprite.c (el motor de sprites y el
 * despachador) y los sprites de un fichero propio, player/spr_*.c.
 *
 * Un sprite nuevo va en su propio player/spr_<nombre>.c: los tres builds
 * (gcc de la PC, la biblioteca de --cross de regress.py y vbcc del 68000)
 * lo recogen solos por glob. Para engancharlo, el despachador de msprite.c
 * llama a su rutina principal, declarada abajo.
 *
 * spr_unsup, boost_mario y chain_points (helpers de msprite.c) son extern:
 * los spr_*.c los llaman, no llevan copia propia.
 */
#ifndef MSPRITE_H
#define MSPRITE_H

#include "mario.h"
#include "gen/smwram.h"
#include "smwmac.h"

/* OJO: gen/smwtab.h y gen/smwtabx.h NO se incluyen aca. Sus tablas son
   static const y vbcc emite las que no se usan (~16 KB de datos por fichero,
   contra el limite de 32 KB de a4, P36): un spr_*.c las incluye solo si las
   necesita de verdad. msprite.c las incluye (las usa). */

/* build de la Amiga: rutinas de player/logic68k.s en vez del C; lo que el
   asm llama deja de ser static (MSS) */
#if defined(__VBCC__) && !defined(NOASM)
#define LOGIC68K 1
#define MSS
#else
#define MSS static
#endif
/* lo que otro fichero necesita ver: nunca static */
#define MSX

/* G8: las rutinas de graficos escriben la OAM de la SNES en ram[]
   (player/spr_gfx.c). Todo build sin NOOAM (el marioverify del PC) o con
   -DSPR_OAM; el de la Amiga y libport.so (NOOAM) no. */
#if !defined(NOOAM) && !defined(SPR_OAM)
#define SPR_OAM 1
#endif

/* Convenciones de mario.c: x = ranura (el registro X del 65816). */
#define SPR(t, x)       RX8(t, x)
#define SETSPR(t, x, v) (RX8(t, x) = (u8)(v))

/* helpers de msprite.c (extern: los define alli; en el 68000 los llama con bsr) */
void spr_unsup(void);
void boost_mario(void);
void chain_points(u8 x);

/* motor de sprites de msprite.c (SubUpdateSprPos, GetDrawInfoBnk3...) */
#ifdef LOGIC68K
void spr_update_pos_asm(u8 x);
#define spr_update_pos spr_update_pos_asm   /* player/logic68k.s */
int get_draw_info_asm(u8 x);
#define get_draw_info get_draw_info_asm     /* player/logic68k.s */
void rex_main_asm(u8 x);
#define rex_main rex_main_asm               /* player/logic68k.s */
#else
void spr_update_pos(u8 x);
int get_draw_info(u8 x);
void rex_main(u8 x);
#endif
void sub_offscreen3(u8 x);
int mario_spr_interact(u8 x);
void spr_spr_interact(u8 y);
void spr_obj_interact(u8 x);

/* spr_chuck.c */
void chuck_main(u8 x);
void chuck_init(u8 x);

/* spr_goal.c (P5: cinta de meta $7B y estado 6) */
int get_draw_info1(u8 x);       /* msprite.c: GetDrawInfoBnk1 (solo los flags) */
void goal_init(u8 x);
void goal_tape(u8 x);
void goal_lvlend(u8 x);

/* spr_rex.c */
void rex_contact(u8 x);

/* spr_shell.c (P4: caparazones, estados 9 / A / B de los Koopas $04-$07) */
void shell_run(u8 x, u8 st);
void shell_kick_or_carry(u8 x);         /* CODE_01AA42: Mario toca un sprite quieto */
void shell_stun(u8 x);                  /* CODE_01AA01: Mario lo pisa y queda aturdido */
/* de msprite.c, para spr_shell.c */
u8 spr_horiz_pos(u8 x);                 /* SubHorizPos (Y = 1 si Mario esta a la izquierda) */
int spr_draw_info1(u8 x);               /* GetDrawInfoBnk1 */
void spr_spin_kill(u8 x);               /* _01A924: salto con giro sobre un sprite pisable */

/* spr_powerup.c (P6: la seta $74 y lo que sale de los bloques) */
void powerup_main(u8 x);                /* _PowerUpRt: la seta $74, estado 8 */
void powerup_init(u8 x);                /* InitPowerUp */
u8 powerup_from_block(void);            /* _02887D: m5 = contenido; crea el sprite (ranura o $FF) */
u8 powerup_flying_content(u8 x);        /* DATA_01AE88[...]: el contenido del bloque volador */
/* de msprite.c, para spr_powerup.c */
void spr_init_tables(u8 x);             /* JSL InitSpriteTables */
int spr_contact_a80f(u8 x);             /* _01A80F: 1 = las cajas de Mario y del sprite se tocan */

/* spr_gfx.c (G8: rutinas de graficos que escriben la OAM, solo con SPR_OAM) */
#ifdef SPR_OAM
extern u8 spr_oam_first[12], spr_oam_n[12];     /* indice OAM y fichas de cada ranura */
u8 spr_oam_index(u8 x);                 /* CODE_0180D2: wm_SprOAMIndex */
void rex_gfx(u8 x);                     /* RexGfxRt */
u8 sub_spr_gfx2(u8 x, u8 m4v);          /* SubSprGfx2Entry0/1 */
void spr_gfx2_tile(u8 x, u8 t);         /* SubSprGfx2Entry1 + un tile fijo */
void spin_jump_gfx(u8 x);               /* HandleSprSpinJump: la nube */
void spr013_gfx(u8 x);                  /* _Spr0to13Gfx de una ficha */
#endif

#endif
