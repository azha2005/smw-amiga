; SW-Q: OAM del bloque volador y los power-ups. Referencia: spr_gfx.c.
; Incluido dentro de SPR_OAM, cerca del resto de rutinas de dibujo (P102).

; --- flying_gfx ---
; entrada: pila vbcc = u8 x, u8 fase; a4 = datos del C
; salida: OAM, marcas y scratch de FlyingBlock / CODE_019E95
; registros destruidos: d0-d1/a0-a1
; ciclos: sprite_oam_verify.py, Musashi sin DMA
        public _flying_gfx
_flying_gfx:
        movem.l d2-d5/a2-a3,-(sp)
        moveq   #0,d2
        move.b  24+7(sp),d2
        lea     _ram(a4),a3
        add.w   d2,a3
        move.b  24+11(sp),d0
        beq     .base
        cmp.b   #2,d0
        beq     .tail
        moveq   #0,d5
        move.b  wm_SprOAMIndex(a3),d5
        moveq   #0,d4
.wing:  moveq   #0,d3
        move.b  wm_SpriteMiscTbl6(a3),d3
        lsr.b   #3,d3
        and.w   #1,d3
        add.w   d4,d3
        tst.w   d4
        bne.s   .off
        move.b  d3,_ram+m2(a4)
.off:   tst.b   wm_OffscreenVert(a3)
        bne     .next
        move.b  wm_SpriteXHi(a3),d0
        lsl.w   #8,d0
        move.b  wm_SpriteXLo(a3),d0
        subq.w  #2,d0
        tst.w   d4
        beq.s   .wx
        addq.w  #4,d0
.wx:    move.w  d0,d1
        lsr.w   #8,d1
        move.b  d1,_ram+m4(a4)
        lea     tg2_KoopaWingDispXLo(pc),a0
        move.b  (a0,d3.w),d1
        ext.w   d1
        add.w   d1,d0
        move.b  d0,_ram+m0(a4)
        move.b  wm_SpriteYLo(a3),d1
        addq.b  #2,d1
        move.b  d1,_ram+m1(a4)
        move.w  _ram+wm_Bg1HOfs(a4),d1
        ror.w   #8,d1
        sub.w   d1,d0
        cmp.w   #256,d0
        bhs.s   .next
        move.w  d5,d1
        addq.b  #4,d1
        tst.w   d4
        beq.s   .oy
        addq.b  #4,d1
.oy:    lea     _ram+wm_OamSlot(a4),a2
        adda.w  d1,a2
        move.b  d0,(a2)
        move.b  _ram+m1(a4),d0
        sub.b   _ram+wm_Bg1VOfs(a4),d0
        lea     tg2_KoopaWingDispY(pc),a0
        add.b   (a0,d3.w),d0
        move.b  d0,1(a2)
        lea     tg2_KoopaWingTiles(pc),a0
        move.b  (a0,d3.w),2(a2)
        lea     tg2_KoopaWingGfxProp(pc),a0
        move.b  (a0,d3.w),d0
        or.b    _ram+wm_SpriteProp(a4),d0
        move.b  d0,3(a2)
        lsr.w   #2,d1
        lea     _ram+wm_OamSize(a4),a2
        lea     tg2_KoopaWingTileSize(pc),a0
        move.b  (a0,d3.w),(a2,d1.w)
.next:  addq.w  #2,d4
        cmp.w   #4,d4
        blo     .wing
        lea     _spr_oam_n(a4),a0
        tst.b   (a0,d2.w)
        beq.s   .ret
        move.b  #3,(a0,d2.w)
        lea     _spr_oam_first(a4),a0
        move.b  d5,(a0,d2.w)
        bra.s   .ret
.base:  move.w  d2,d1
        bsr     sg_index
        tst.b   wm_SpriteDecTbl6(a3)
        beq.s   .g2
        clr.b   wm_SprOAMIndex(a3)
        tst.b   _ram+wm_OnYoshi(a4)
        bne.s   .g2
        move.b  #4,wm_SprOAMIndex(a3)
.g2:    moveq   #0,d0
        bsr     sg_g2at
        moveq   #0,d0
        move.b  wm_SprOAMIndex(a3),d0
        lea     _ram+wm_OamSlot+1(a4),a0
        subq.b  #1,(a0,d0.w)
        bra.s   .ret
.tail:  moveq   #0,d0
        move.b  wm_SpriteDecTbl3(a3),d0
        lsr.w   #1,d0
        lea     tg2_DATA_01AE7F(pc),a0
        move.b  (a0,d0.w),d1
        move.b  d1,_ram+m0(a4)
        moveq   #0,d0
        move.b  wm_SprOAMIndex(a3),d0
        lea     _ram+wm_OamSlot(a4),a0
        sub.b   d1,1(a0,d0.w)
        move.b  #$2a,2(a0,d0.w)
        tst.b   wm_SpriteState(a3)
        beq.s   .ret
        move.b  #$2e,2(a0,d0.w)
.ret:   movem.l (sp)+,d2-d5/a2-a3
        rts

; --- powerup_gfx ---
; entrada: pila vbcc = u8 x; a4 = datos del C
; salida: OAM y temporales de CODE_01C61A / PowerUpGfxRt
; registros destruidos: d0-d1/a0-a1
; ciclos: sprite_oam_verify.py, Musashi sin DMA
        public _powerup_gfx
_powerup_gfx:
        movem.l d2-d3/a2-a3,-(sp)
        moveq   #0,d2
        move.b  16+7(sp),d2
        lea     _ram(a4),a3
        add.w   d2,a3
        move.w  d2,d1
        bsr     sg_index
        move.l  a3,a1
        bsr     sg_di1
        beq     .ret
        move.b  wm_SpriteXLo(a3),d0
        sub.b   _ram+wm_Bg1HOfs(a4),d0
        move.b  d0,_ram+m0(a4)
        move.b  wm_SpriteYLo(a3),d0
        sub.b   _ram+wm_Bg1VOfs(a4),d0
        move.b  d0,_ram+m1(a4)
        clr.b   _ram+m10(a4)
        tst.b   _ram+wm_ReznorSmokeFlag(a4)
        bne.s   .num
        cmp.b   #$c1,_ram+wm_LevelMode(a4)
        beq.s   .num
        btst    #6,_ram+wm_LevelMode(a4)
        beq.s   .num
        move.b  #$d8,wm_SprOAMIndex(a3)
.num:   cmp.b   #$76,wm_SpriteNum(a3)
        bne.s   .oam
        moveq   #0,d0
        move.b  _ram+wm_FrameA(a4),d0
        lsr.b   #1,d0
        and.w   #3,d0
        lea     tg2_StarPalValues(pc),a0
        move.b  (a0,d0.w),_ram+m10(a4)
.oam:   moveq   #0,d3
        move.b  wm_SprOAMIndex(a3),d3
        lea     _ram+wm_OamSlot(a4),a2
        adda.w  d3,a2
        move.b  _ram+m0(a4),(a2)
        move.b  _ram+m1(a4),d0
        subq.b  #1,d0
        move.b  d0,1(a2)
        moveq   #0,d0
        btst    #0,wm_SpriteDir(a3)
        bne.s   .prop
        moveq   #$40,d0
.prop:  or.b    _ram+wm_SpriteProp(a4),d0
        or.b    wm_SpritePal(a3),d0
        move.b  _ram+m10(a4),d1
        eor.b   d1,d0
        move.b  d0,3(a2)
        moveq   #0,d0
        move.b  wm_SpriteNum(a3),d0
        sub.b   #$74,d0
        lea     tg2_PowerUpTiles(pc),a0
        move.b  (a0,d0.w),2(a2)
        pea     2.w
        pea     0.w
        move.l  d2,-(sp)
        bsr     _finish_oam_write_asm
        lea     12(sp),sp
.ret:   movem.l (sp)+,d2-d3/a2-a3
        rts
