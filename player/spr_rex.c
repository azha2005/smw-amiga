/*
 * spr_rex.c - el Rex (sprite $AB, RexMainRt de sprite_3-1.s). Primer sprite
 * en fichero propio (I1): la plantilla de los demas player/spr_*.c. Ver
 * msprite.h. En el 68000 rex_main es rex_main_asm (player/logic68k.s) y aca
 * queda solo rex_contact (la llama el asm).
 */
#include "msprite.h"
#ifndef LOGIC68K
/* solo el rex_main de C (host) lee tx_RexSpeed; en el 68000 las tablas static
   const se emitirian enteras en este fichero (P36), asi que no se incluyen */
#include "gen/smwtabx.h"
#endif

/* RexMainRt */
/* el Rex toco a Mario (mario_spr_interact): pisoton, giro o golpe */
#ifndef LOGIC68K                    /* con LOGIC68K: rex_main_asm de player/logic68k.s */
void rex_main(u8 x)
{
    u8 a, y;
    /* RexGfxRt: la pose y los flags de pantalla */
    if (SPR(wm_SpriteDecTbl3, x)) SETSPR(wm_SpriteGfxTbl, x, 5);
    if (SPR(wm_DisSprCapeContact, x)) SETSPR(wm_SpriteGfxTbl, x, 2);
    get_draw_info(x);
    if (SPR(wm_SpriteStatus, x) != 0x08 || R8(wm_SpritesLocked))
        return;
    a = SPR(wm_SpriteDecTbl3, x);
    if (a) {
        SETSPR(wm_SpriteEatenTbl, x, a);
        if (a == 1)
            SETSPR(wm_SpriteStatus, x, 0);
        return;
    }
    sub_offscreen3(x);
    SETSPR(wm_SpriteMiscTbl6, x, SPR(wm_SpriteMiscTbl6, x) + 1);
    a = (u8)(SPR(wm_SpriteMiscTbl6, x) >> 2);
    a = SPR(wm_SpriteState, x) ? (u8)((a & 1) + 3) : (u8)((a >> 1) & 1);
    SETSPR(wm_SpriteGfxTbl, x, a);
    if (SPR(wm_SprObjStatus, x) & 0x04) {
        SETSPR(wm_SpriteSpeedY, x, 0x10);
        y = SPR(wm_SpriteDir, x);
        if (SPR(wm_SpriteState, x))
            y += 2;
        SETSPR(wm_SpriteSpeedX, x, tx_RexSpeed[y]);
    }
    if (!SPR(wm_DisSprCapeContact, x))
        spr_update_pos(x);
    if (SPR(wm_SprObjStatus, x) & 0x03)
        SETSPR(wm_SpriteDir, x, SPR(wm_SpriteDir, x) ^ 1);
    spr_spr_interact(x);
    if (!mario_spr_interact(x))
        return;
    rex_contact(x);
}
#endif

void rex_contact(u8 x)
{
    if (R8(wm_StarPowerTimer)) {                            /* RexStarKill */
        u16 d = (u16)(R16(wm_MarioXPos) - (SPR(wm_SpriteXLo, x) | SPR(wm_SpriteXHi, x) << 8));
        u8 p = (u8)(R8(wm_StarKillPoints) + 1);
        SETSPR(wm_SpriteStatus, x, 0x02);
        SETSPR(wm_SpriteSpeedY, x, 0xD0);
        W8(m15, (u8)d);                     /* SubHorzPosBnk3 */
        SETSPR(wm_SpriteSpeedX, x, (d & 0x8000) ? 0x10 : 0xF0);    /* RexKilledSpeed */
        W8(wm_StarKillPoints, p > 8 ? 8 : p);
        mario_events |= MEV_SPRITE;         /* GivePoints */
        return;
    }
    if (SPR(wm_SpriteDecTbl2, x))
        return;
    SETSPR(wm_SpriteDecTbl2, x, 0x08);
    if (NEG((u8)(R8(wm_MarioSpeedY) - 0x10))) {             /* RexWins */
        u16 d;
        if (R8(wm_PlayerHurtTimer) | R8(wm_OnYoshi))
            return;
        d = (u16)(R16(wm_MarioXPos) - (SPR(wm_SpriteXLo, x) | SPR(wm_SpriteXHi, x) << 8));
        W8(m15, (u8)d);                     /* SubHorzPosBnk3: mira a Mario */
        SETSPR(wm_SpriteDir, x, (d & 0x8000) ? 1 : 0);
        mario_hurt();                       /* HurtMario */
        return;
    }
    chain_points(x);                       /* RexPoints (DATA_038000 = DATA_01A61E) */
    boost_mario();                          /* BoostMarioSpeed, DisplayContactGfx */
    if (R8(wm_IsSpinJump) | R8(wm_OnYoshi)) {   /* RexSpinKill */
        SETSPR(wm_SpriteStatus, x, 0x04);
        SETSPR(wm_SpriteDecTbl1, x, 0x1F);
        W8(wm_SoundCh1, 0x08);
        return;
    }
    SETSPR(wm_SpriteState, x, SPR(wm_SpriteState, x) + 1);
    if (SPR(wm_SpriteState, x) == 2) {
        SETSPR(wm_SpriteDecTbl3, x, 0x20);
        return;
    }
    SETSPR(wm_DisSprCapeContact, x, 0x0C);  /* SmushRex */
    SETSPR(wm_Tweaker1662, x, 0);
}
