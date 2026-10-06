/*
 * spr_shell.c - los caparazones: los Koopas $04-$07 en los estados 9
 * (aturdido / quieto: HandleSprStunned), A (pateado: HandleSprKicked) y B
 * (llevado por Mario: HandleSprCarried), de sprite_1-main.s (CODE_019554..
 * CODE_01A0B1). El caparazon rojo $DB de spr.lv nace como el $05 en estado 9
 * (spawn de msprite.c). Tercer sprite en fichero propio (I1, ver msprite.h).
 *
 * Aca tambien: lo que hace Mario al tocar un sprite quieto (patearlo o
 * agarrarlo, CODE_01AA42) y al pisar uno que se mueve (aturdirlo,
 * CODE_01AA01); los llama default_interact de msprite.c. El contacto entre
 * sprites (el pateado mata al Rex...) esta en spr_spr_interact (msprite.c).
 *
 * Transcripcion instruccion por instruccion (P27). Diferencias con la ROM:
 *   - el dibujo (CODE_01A187 -> CODE_019806 / CODE_019A2A) se reduce a
 *     GetDrawInfoBnk1 (los flags de fuera de pantalla); los tiles, la
 *     paleta que parpadea, el humo (_01AB72) y los puntos (GivePoints) son
 *     de la 9.2 / de la etapa 10 (MEV_SPRITE);
 *   - los otros sprites que pasan por los estados 9 / A / B (bomba, llave,
 *     POW, Goomba, globo, Yoshi, bloque de lanzar...): spr_unsup();
 *   - sin portar (spr_unsup): el Koopa que sale del caparazon
 *     (GeneralResetSpr, SetNormalStatus), el caparazon con pinchos
 *     (CODE_0198A9), un golpe de bloque (_00F160 con el bloque entre $11 y
 *     $2D: rebote), el Koopa $02 agarrando un caparazon.
 * Las tablas .DB vienen de tools/smwtabx.py (WANT_SHELL, SMWTABX_SHELL):
 * solo este fichero las incluye (P78).
 */
#include "msprite.h"
#define SMWTABX_SHELL
#include "gen/smwtabx.h"

/* _00F160 con Y = 0 (un caparazon contra un bloque): bloques que se golpean
   ($11-$2D, mas los del tileset 7 $6E-$6F) = rebote, sin portar; el resto no
   hace nada. Igual que f160 de mcoll.c (Mario) */
static void shell_hit_block(u8 a)
{
    a = (u8)(a - 0x11);
    if (a < 0x1D) { spr_unsup(); return; }
    if (R8(0x1931) != 7) { spr_unsup(); return; }   /* wm_LvHeadTileset */
    a = (u8)(a - 0x59);
    if (a >= 2)
        return;
    spr_unsup();
}

/* CODE_01999E: choca de costado: da la vuelta, suena y golpea el bloque */
static void shell_wall_hit(u8 x)
{
    W8(wm_SoundCh1, 0x01);
    SETSPR(wm_SpriteSpeedX, x, (u8)-SPR(wm_SpriteSpeedX, x));   /* _0190A2 */
    SETSPR(wm_SpriteDir, x, SPR(wm_SpriteDir, x) ^ 1);
    if (SPR(wm_OffscreenHorz, x))
        return;
    if ((u8)((u8)(SPR(wm_SpriteXLo, x) - R8(wm_Bg1HOfs)) + 0x14) < 0x1C)
        return;
    W8(wm_LayerInProcess, (SPR(wm_SprObjStatus, x) >> 6) & 1);
    shell_hit_block(R8(wm_MirBlkCheck));
    SETSPR(wm_DisSprCapeContact, x, 0x05);
}

/* SetSomeYSpeed */
static void shell_yspeed(u8 x)
{
    SETSPR(wm_SpriteSpeedY, x,
           (NEG(SPR(wm_SprObjStatus, x)) || SPR(wm_SpriteSlopeTbl, x)) ? 0x18 : 0x00);
}

/* SetStunnedTimer / _SetAsStunned (la pata comun de CODE_01AA01 y _01AA0B) */
static void shell_set_stunned(u8 x)
{
    u8 a = 0x02, n = SPR(wm_SpriteNum, x);
    if (n == 0x0F || n == 0x11 || n == 0xA2 || n == 0x0D)
        a = 0xFF;
    SETSPR(wm_SpriteDecTbl1, x, a);
}

/* CODE_01AA01 (Mario pisa un sprite que se mueve) */
void shell_stun(u8 x)
{
    SETSPR(wm_SprChainKillTbl, x, 0);
    if (SPR(wm_SpriteStatus, x) == 0x08 || SPR(wm_SpriteState, x))
        shell_set_stunned(x);
    else
        SETSPR(wm_SpriteDecTbl1, x, 0);
    SETSPR(wm_SpriteStatus, x, 0x09);
}

/* _01AA0B (un pateado que se frena) */
static void shell_stun_0b(u8 x)
{
    if (SPR(wm_SpriteState, x))
        shell_set_stunned(x);
    else
        SETSPR(wm_SpriteDecTbl1, x, 0);
    SETSPR(wm_SpriteStatus, x, 0x09);
}

/* CODE_01AA42: Mario toca un sprite quieto (estado 9, DecTbl2 = 0): el salto
   con giro lo deshace, con Y lo agarra, si no lo patea */
void shell_kick_or_carry(u8 x)
{
    u8 n = SPR(wm_SpriteNum, x);
    if ((R8(wm_IsSpinJump) | R8(wm_OnYoshi)) && !NEG(R8(wm_MarioSpeedY))
        && (SPR(wm_Tweaker1656, x) & 0x10)) {
        spr_spin_kill(x);                       /* JMP _01A924 */
        return;
    }
    if ((R8(wm_JoyPadA) & 0x40) && !(R8(wm_IsCarrying) | R8(wm_OnYoshi))) {   /* CODE_01AA58 */
        SETSPR(wm_SpriteStatus, x, 0x0B);
        W8(wm_IsCarrying, R8(wm_IsCarrying) + 1);
        W8(wm_PickUpImgTimer, 0x08);
        return;
    }
    if (n < 0x04 || n > 0x07) {                 /* CODE_01AA74: llave, POW, bomba... */
        spr_unsup();
        return;
    }
    chain_points(x);                            /* CODE_01AA94 -> CODE_01AB46 */
    W8(wm_SoundCh1, 0x03);                      /* _01AA97: PlayKickSfx */
    SETSPR(wm_SpriteState, x, SPR(wm_SpriteDecTbl1, x));
    SETSPR(wm_SpriteStatus, x, 0x0A);
    SETSPR(wm_SpriteDecTbl2, x, 0x10);
    SETSPR(wm_SpriteSpeedX, x, ts_ShellSpeedX[spr_horiz_pos(x)]);
}

/* CODE_019624 (num != $0D) + CODE_01965C: el temporizador del aturdido.
   Devuelve 1 si el sprite hace algo que no esta portado (sale el Koopa) */
static int shell_timer(u8 x)
{
    u8 d1 = SPR(wm_SpriteDecTbl1, x), d3 = SPR(wm_SpriteDecTbl3, x);
    SETSPR(wm_SpriteState, x, d1 | d3);
    if (d3 == 1 && !SPR(wm_SpriteEatenTbl, SPR(wm_SpriteMiscTbl7, x))) {
        spr_unsup();                            /* se mete el Koopa: LoadSpriteTables... */
        return 1;
    }
    if (!d1)                                    /* CODE_01969C */
        return 0;
    if (d1 == 3 || d1 == 1) {
        spr_unsup();                            /* SetNormalStatus / GeneralResetSpr */
        return 1;
    }
    if (!(R8(wm_FrameA) & 0x01))                /* IncrmntStunTimer */
        SETSPR(wm_SpriteDecTbl1, x, d1 + 1);
    return 0;
}

/* CODE_0197D5: en el suelo, la velocidad X a la mitad y rebota (DATA_0197AF) */
static void shell_ground(u8 x)
{
    u8 v = SPR(wm_SpriteSpeedX, x), s, y;
    if (NEG(v))
        v = (u8)-(u8)(((u8)-v) >> 1);
    else
        v >>= 1;
    SETSPR(wm_SpriteSpeedX, x, v);
    s = SPR(wm_SpriteSpeedY, x);
    shell_yspeed(x);
    y = (u8)(s >> 2);
    if (y >= 38) {                              /* mas alla de DATA_0197AF: bytes de codigo */
        spr_unsup();
        return;
    }
    if (!NEG(SPR(wm_SprObjStatus, x)))
        SETSPR(wm_SpriteSpeedY, x, ts_0197AF[y]);
}

/* HandleSprStunned (num $04-$07): CODE_01956A */
static void shell_stunned(u8 x)
{
    if (!R8(wm_SpritesLocked)) {
        if (shell_timer(x))
            return;
        spr_update_pos(x);
        if (SPR(wm_SprObjStatus, x) & 0x04)
            shell_ground(x);
        if (SPR(wm_SprObjStatus, x) & 0x08) {   /* _019598: el techo */
            SETSPR(wm_SpriteSpeedY, x, 0x10);
            if (!(SPR(wm_SprObjStatus, x) & 0x03)) {    /* sin pared: golpea el bloque de arriba */
                W16(wm_BlockYPos, (u16)((SPR(wm_SpriteXLo, x) | SPR(wm_SpriteXHi, x) << 8) + 8));
                W16(wm_BlockXPos, (u16)((SPR(wm_SpriteYLo, x) & 0xF0) | SPR(wm_SpriteYHi, x) << 8));
                W8(wm_LayerInProcess, (SPR(wm_SprObjStatus, x) >> 5) & 1);
                shell_hit_block(R8(wm_SprOnBreakableBlk));
                SETSPR(wm_DisSprCapeContact, x, 0x08);
            }
        }
        if (SPR(wm_SprObjStatus, x) & 0x03) {   /* de costado (num < $0D: no golpea) */
            u8 v = SPR(wm_SpriteSpeedX, x);     /* ROR dos veces: v >> 2 aritmetico */
            SETSPR(wm_SpriteSpeedX, x, (NEG(v) ? 0xC0 : 0x00) | (v >> 2));
        }
        spr_spr_interact(x);                    /* _SubSprSprMarioSpr */
        mario_spr_interact(x);
    }
#ifdef SPR_OAM
    shell_gfx(x, 0);
#else
    spr_draw_info1(x);                          /* _0195F5: CODE_01A187 (dibujo) */
#endif
    sub_offscreen3(x);
}

/* HandleSprKicked (num $04-$07): CODE_01991B */
static void shell_kicked(u8 x)
{
    u8 sl, v, a;
    if (SPR(wm_SprStompImmuneTbl, x) || (SPR(wm_Tweaker167A, x) & 0x10)) {
        spr_unsup();                            /* CODE_0198A9 (con pinchos) / _01AA0B + dibujo */
        return;
    }
    if (!SPR(wm_SpriteMiscTbl4, x) && (u8)(SPR(wm_SpriteSpeedX, x) + 0x20) < 0x40)
        shell_stun_0b(x);                       /* se frena: queda aturdido (sigue el frame) */
    SETSPR(wm_SpriteMiscTbl4, x, 0);
    if (!(R8(wm_SpritesLocked) | SPR(wm_SpriteDecTbl6, x))) {
        v = SPR(wm_SpriteSpeedX, x);            /* UpdateDirection */
        if (v)
            SETSPR(wm_SpriteDir, x, NEG(v) ? 1 : 0);
        sl = SPR(wm_SpriteSlopeTbl, x);
        spr_update_pos(x);
        a = 0;                                  /* 1: _019975 (el bloque de abajo) */
        if (sl && !SPR(wm_SprInWaterTbl, x) && sl != SPR(wm_SpriteSlopeTbl, x)
            && !NEG((u8)(sl ^ SPR(wm_SpriteSpeedX, x)))) {
            SETSPR(wm_SpriteSpeedY, x, 0xF8);   /* pegado a la pendiente */
            a = 1;
        } else if (SPR(wm_SprObjStatus, x) & 0x04) {    /* CODE_019969 */
            shell_yspeed(x);
            SETSPR(wm_SpriteSpeedY, x, 0x10);
            a = 1;
        }
        if (a) {                                /* _019975: B4 / B5 (cintas) */
            v = R8(wm_SprOnTileXLo);
            if (v == 0xB5 || v == 0xB4)
                SETSPR(wm_SpriteSpeedY, x, 0xB8);
        }
        if (SPR(wm_SprObjStatus, x) & 0x03)
            shell_wall_hit(x);
        spr_spr_interact(x);                    /* _01998C: _SubSprSprMarioSpr */
        mario_spr_interact(x);
    }
    sub_offscreen3(x);                          /* _01998F */
#ifdef SPR_OAM
    shell_gfx(x, 1);
#else
    spr_draw_info1(x);                          /* CODE_019A2A (dibujo) */
#endif
    SETSPR(wm_SpriteDecTbl3, x, 0);
}

/* CODE_01A0B1: el llevado sigue a Mario (la mano segun la pose) */
static void shell_follow(u8 x)
{
    u8 y = 0, a, t;
    u16 mx, my;
    if (!R8(wm_MarioDirection))
        y++;
    a = R8(wm_FaceCamImgTimer);
    if (a) {
        y += 2;
        if (a >= 5)
            y++;
    }
    if (R8(wm_YoshiInPipe) == 2 || (R8(wm_PlayerTurningPose) | R8(wm_IsClimbing)))
        y = 5;
    if (R8(wm_IsOnSolidSpr) == 3) {
        mx = R16(wm_MarioXPos);
        my = R16(wm_MarioYPos);
    } else {                                    /* LDY #$3D: wm_PlayerXPosLv / wm_PlayerYPosLv */
        mx = R16(wm_PlayerXPosLv);
        my = R16(wm_PlayerYPosLv);
    }
    mx = (u16)(mx + (u16)(s16)(s8)ts_019F5B[y]);
    SETSPR(wm_SpriteXLo, x, (u8)mx);
    SETSPR(wm_SpriteXHi, x, mx >> 8);
    a = 0x0D;
    if (R8(wm_IsDucking) || !R8(wm_MarioPowerUp))
        a = 0x0F;
    if (R8(wm_PickUpImgTimer))
        a = 0x0F;
    my = (u16)(my + a);
    SETSPR(wm_SpriteYLo, x, (u8)my);
    SETSPR(wm_SpriteYHi, x, my >> 8);
    t = 1;
    W8(wm_IsCarrying2, t);
    W8(wm_IsCarrying, t);
}

/* _StartKickPose */
static void shell_kick_pose(u8 x)
{
    SETSPR(wm_SpriteDecTbl2, x, 0x10);
    W8(wm_KickImgTimer, 0x0C);
}

/* ReleaseSprCarried: Mario suelta el boton (Y) */
static void shell_release(u8 x)
{
    u8 j = R8(wm_JoyPadA), y, v;
    SETSPR(wm_SprChainKillTbl, x, 0);
    SETSPR(wm_SpriteSpeedY, x, 0);              /* (el $0F, Goomba, sale con $EC: no llega aca) */
    SETSPR(wm_SpriteStatus, x, 0x09);
    if (j & 0x08) {                             /* TossUpSprCarried */
        W8(wm_SoundCh1, 0x03);                  /* CODE_01AB6F: PlayKickSfx (+ humo) */
        SETSPR(wm_SpriteSpeedY, x, 0x90);
        v = R8(wm_MarioSpeedX);
        SETSPR(wm_SpriteSpeedX, x, (NEG(v) ? 0x80 : 0x00) | (v >> 1));
        shell_kick_pose(x);
        return;
    }
    if (SPR(wm_SpriteNum, x) < 0x15 ? (j & 0x04) : !(j & 0x03)) {   /* _01A047: lo deja en el suelo */
        u16 p;
        y = R8(wm_MarioDirection);
        p = (u16)(R16(wm_PlayerXPosLv) + (u16)(s16)(s8)ts_019F67[y]);
        SETSPR(wm_SpriteXLo, x, (u8)p);
        SETSPR(wm_SpriteXHi, x, p >> 8);
        y = spr_horiz_pos(x);
        SETSPR(wm_SpriteSpeedX, x, ts_019F99[y] + R8(wm_MarioSpeedX));
        SETSPR(wm_SpriteSpeedY, x, 0);
        shell_kick_pose(x);
        return;
    }
    W8(wm_SoundCh1, 0x03);                      /* KickSprCarried: CODE_01AB6F */
    SETSPR(wm_SpriteState, x, SPR(wm_SpriteDecTbl1, x));
    SETSPR(wm_SpriteStatus, x, 0x0A);
    y = R8(wm_MarioDirection);
    if (R8(wm_OnYoshi))
        y += 2;
    v = ts_ShellSpeedX[y];
    SETSPR(wm_SpriteSpeedX, x, v);
    if (!NEG((u8)(v ^ R8(wm_MarioSpeedX)))) {   /* mismo sentido: suma la mitad de la de Mario */
        u8 m = R8(wm_MarioSpeedX);
        m = (NEG(m) ? 0x80 : 0x00) | (m >> 1);
        SETSPR(wm_SpriteSpeedX, x, m + v);
    }
    shell_kick_pose(x);
}

/* HandleSprCarried (num $04-$07): CODE_019F9B (sin el globo) + CODE_01A187 */
static void shell_carried(u8 x)
{
    spr_obj_interact(x);                        /* CODE_019140 */
    if (R8(wm_MarioAnimation) >= 1 && !R8(wm_YoshiInPipe)) {
        SETSPR(wm_SpriteStatus, x, 0x09);       /* Mario en una animacion: lo suelta */
    } else if (SPR(wm_SpriteStatus, x) != 0x08) {       /* CODE_019FF4 */
        if (R8(wm_SpritesLocked)) {
            shell_follow(x);
        } else {
            if (shell_timer(x))
                return;
            spr_spr_interact(x);
            if (R8(wm_YoshiInPipe) || (R8(wm_JoyPadA) & 0x40))
                shell_follow(x);
            else
                shell_release(x);
        }
    }
#ifdef SPR_OAM
    shell_gfx(x, 0);
#else
    spr_draw_info1(x);                          /* CODE_01A187 (dibujo) */
#endif
}

/* el despachador de los estados 9 / A / B (HandleSprite: ExecutePtr) */
void shell_run(u8 x, u8 st)
{
    u8 n = SPR(wm_SpriteNum, x);
    if (n < 0x04 || n > 0x07) {                 /* Goomba, bomba, llave, POW, globo... */
        spr_unsup();
        return;
    }
    if (st == 0x09)
        shell_stunned(x);
    else if (st == 0x0A)
        shell_kicked(x);
    else
        shell_carried(x);
}
