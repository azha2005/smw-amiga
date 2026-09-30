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

/* spr_rex.c */
void rex_contact(u8 x);

#endif
