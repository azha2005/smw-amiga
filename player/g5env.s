; B2bis: generado por tools/g5env_asm.py, sin datos de la ROM.
; --- _g5env_decode ---
; entrada: pila vbcc +4 = buffer de 4 sprites (84 palabras cada uno),
;          +8 = salida de 2484 B como maximo, alineada a palabra.
; salida: d0 = bytes escritos, $FFFF si cabeceras incompatibles.
;         height.w, columns.w; por fila: masks de indices 1..15.
;         columns=1: 15 masks.w (30 B/fila, todas escritas, cero = ausente).
;         columns=2: indices.w + 15 masks.l (62 B/fila).
;         pixel izquierdo = bit 15/31. En dos columnas solo cuenta el bit valido.
; registros destruidos: d0/d1/a0/a1; preserva d2-d7/a2-a6, incluido a4.
; ciclos: los mide tools/g5env_verify.py decode, Musashi sin DMA.
        ifd SPR_G5
        public _g5env_decode
_g5env_decode:
        move.l  4(sp),a0
        move.l  8(sp),a1
        movem.l d2-d7/a2-a6,-(sp)
        move.l  a1,a6
        move.l  (a0),d0
        bne.s   .first
        lea     336(a0),a0
        move.l  (a0),d0
        bne.s   .one
        clr.l   (a1)
        moveq   #4,d0
        bra.w   .return
.first:
        move.l  336(a0),d1
        beq.s   .one
        ; Ambas columnas de mario_sprite comparten VSTART/VSTOP.
        move.w  (a0),d0
        move.w  336(a0),d1
        eor.w   d1,d0
        andi.w  #$ff00,d0
        bne.w   .bad
        move.w  2(a0),d0
        move.w  338(a0),d1
        eor.w   d1,d0
        andi.w  #$ff06,d0
        bne.w   .bad
        bsr.w   .height
        cmpi.w  #40,d1
        bhi.w   .bad
        move.w  d1,(a1)+
        move.w  #2,(a1)+
        move.l  a0,a3
        addq.l  #4,a0
        lea     168(a0),a2
        move.l  a0,a5
        add.w   d1,d1
        add.w   d1,d1
        adda.w  d1,a5
        cmpa.l  a5,a0
        beq.w   .finish_wide
        bra.w   .left_row
.one:
        bsr.w   .height
        cmpi.w  #40,d1
        bhi.w   .bad
        move.w  d1,(a1)+
        move.w  #1,(a1)+
        addq.l  #4,a0
        lea     168(a0),a2
        move.l  a0,a5
        add.w   d1,d1
        add.w   d1,d1
        adda.w  d1,a5
        cmpa.l  a5,a0
        beq.w   .finish
        lea     30(a1),a1
.mono_row:
.mono_first:
        move.w  (a0)+,d0
        move.w  (a0)+,d1
        move.w  (a2)+,d2
        move.w  (a2)+,d3
        move.w  d2,d4
        and.w   d3,d4
        move.w  d4,d6
        and.w   d1,d6
        eor.w   d6,d4
        move.w  d4,d5
        and.w   d0,d5
        eor.w   d5,d4
        move.w  d6,d7
        and.w   d0,d7
        eor.w   d7,d6
        movem.w d4-d7,-(a1)
        move.w  d2,d4
        not.w   d4
        and.w   d3,d4
        move.w  d4,d6
        and.w   d1,d6
        eor.w   d6,d4
        move.w  d4,d5
        and.w   d0,d5
        eor.w   d5,d4
        move.w  d6,d7
        and.w   d0,d7
        eor.w   d7,d6
        movem.w d4-d7,-(a1)
        move.w  d3,d4
        not.w   d4
        and.w   d2,d4
        move.w  d4,d6
        and.w   d1,d6
        eor.w   d6,d4
        move.w  d4,d5
        and.w   d0,d5
        eor.w   d5,d4
        move.w  d6,d7
        and.w   d0,d7
        eor.w   d7,d6
        movem.w d4-d7,-(a1)
        move.w  d2,d4
        or.w    d3,d4
        not.w   d4
        move.w  d4,d6
        and.w   d1,d6
        eor.w   d6,d4
        move.w  d4,d5
        and.w   d0,d5
        eor.w   d5,d4
        move.w  d6,d7
        and.w   d0,d7
        eor.w   d7,d6
        movem.w d5-d7,-(a1)
.mono_advance:
        lea     60(a1),a1
        cmpa.l  a5,a0
        bne.w   .mono_row
        lea     -30(a1),a1
        bra.w   .finish
.left_row:
        moveq   #0,d4
        move.w  (a0)+,d0
        move.w  (a0)+,d1
        move.w  (a2)+,d2
        move.w  (a2)+,d3
        move.w  d2,d5
        or.w    d3,d5
        not.w   d5
        move.w  d1,d6
        or.w    d0,d6
        and.w   d6,d5
        beq.s   .left_group0_end
        move.w  d5,d6
        and.w   d1,d6
        eor.w   d6,d5
        beq.s   .left_p1_0
        move.w  d5,d7
        and.w   d0,d7
        tst.w   d7
        beq.s   .left_p0_1
        move.w  d7,2(a1)
        clr.w   4(a1)
        ori.w   #$0002,d4
.left_p0_1:
.left_p1_0:
        tst.w   d6
        beq.s   .left_p1_2
        move.w  d6,d7
        and.w   d0,d7
        eor.w   d7,d6
        beq.s   .left_p0_2
        move.w  d6,6(a1)
        clr.w   8(a1)
        ori.w   #$0004,d4
.left_p0_2:
        tst.w   d7
        beq.s   .left_p0_3
        move.w  d7,10(a1)
        clr.w   12(a1)
        ori.w   #$0008,d4
.left_p0_3:
.left_p1_2:
.left_group0_end:
        move.w  d3,d5
        not.w   d5
        and.w   d2,d5
        beq.s   .left_group4_end
        move.w  d5,d6
        and.w   d1,d6
        eor.w   d6,d5
        beq.s   .left_p1_4
        move.w  d5,d7
        and.w   d0,d7
        eor.w   d7,d5
        beq.s   .left_p0_4
        move.w  d5,14(a1)
        clr.w   16(a1)
        ori.w   #$0010,d4
.left_p0_4:
        tst.w   d7
        beq.s   .left_p0_5
        move.w  d7,18(a1)
        clr.w   20(a1)
        ori.w   #$0020,d4
.left_p0_5:
.left_p1_4:
        tst.w   d6
        beq.s   .left_p1_6
        move.w  d6,d7
        and.w   d0,d7
        eor.w   d7,d6
        beq.s   .left_p0_6
        move.w  d6,22(a1)
        clr.w   24(a1)
        ori.w   #$0040,d4
.left_p0_6:
        tst.w   d7
        beq.s   .left_p0_7
        move.w  d7,26(a1)
        clr.w   28(a1)
        ori.w   #$0080,d4
.left_p0_7:
.left_p1_6:
.left_group4_end:
        move.w  d2,d5
        not.w   d5
        and.w   d3,d5
        beq.s   .left_group8_end
        move.w  d5,d6
        and.w   d1,d6
        eor.w   d6,d5
        beq.s   .left_p1_8
        move.w  d5,d7
        and.w   d0,d7
        eor.w   d7,d5
        beq.s   .left_p0_8
        move.w  d5,30(a1)
        clr.w   32(a1)
        ori.w   #$0100,d4
.left_p0_8:
        tst.w   d7
        beq.s   .left_p0_9
        move.w  d7,34(a1)
        clr.w   36(a1)
        ori.w   #$0200,d4
.left_p0_9:
.left_p1_8:
        tst.w   d6
        beq.s   .left_p1_10
        move.w  d6,d7
        and.w   d0,d7
        eor.w   d7,d6
        beq.s   .left_p0_10
        move.w  d6,38(a1)
        clr.w   40(a1)
        ori.w   #$0400,d4
.left_p0_10:
        tst.w   d7
        beq.s   .left_p0_11
        move.w  d7,42(a1)
        clr.w   44(a1)
        ori.w   #$0800,d4
.left_p0_11:
.left_p1_10:
.left_group8_end:
        move.w  d2,d5
        and.w   d3,d5
        beq.s   .left_group12_end
        move.w  d5,d6
        and.w   d1,d6
        eor.w   d6,d5
        beq.s   .left_p1_12
        move.w  d5,d7
        and.w   d0,d7
        eor.w   d7,d5
        beq.s   .left_p0_12
        move.w  d5,46(a1)
        clr.w   48(a1)
        ori.w   #$1000,d4
.left_p0_12:
        tst.w   d7
        beq.s   .left_p0_13
        move.w  d7,50(a1)
        clr.w   52(a1)
        ori.w   #$2000,d4
.left_p0_13:
.left_p1_12:
        tst.w   d6
        beq.s   .left_p1_14
        move.w  d6,d7
        and.w   d0,d7
        eor.w   d7,d6
        beq.s   .left_p0_14
        move.w  d6,54(a1)
        clr.w   56(a1)
        ori.w   #$4000,d4
.left_p0_14:
        tst.w   d7
        beq.s   .left_p0_15
        move.w  d7,58(a1)
        clr.w   60(a1)
        ori.w   #$8000,d4
.left_p0_15:
.left_p1_14:
.left_group12_end:
.left_row_end:
        move.w  d4,(a1)
        lea     62(a1),a1
        cmpa.l  a5,a0
        bne.w   .left_row
        ; Segunda columna: solo rellena mitades bajas y suma indices.
        lea     340(a3),a0
        lea     168(a0),a2
        move.l  a0,a5
        move.w  (a6),d1
        add.w   d1,d1
        add.w   d1,d1
        adda.w  d1,a5
        lea     4(a6),a1
.right_row:
        moveq   #0,d4
        move.w  (a1),d4
        move.w  (a0)+,d0
        move.w  (a0)+,d1
        move.w  (a2)+,d2
        move.w  (a2)+,d3
        move.w  d2,d5
        or.w    d3,d5
        not.w   d5
        move.w  d1,d6
        or.w    d0,d6
        and.w   d6,d5
        beq.w   .right_group0_end
        move.w  d5,d6
        and.w   d1,d6
        eor.w   d6,d5
        beq.s   .right_p1_0
        move.w  d5,d7
        and.w   d0,d7
        tst.w   d7
        beq.s   .right_p0_1
        btst    #1,d4
        bne.s   .right_have1
        clr.w   2(a1)
.right_have1:
        move.w  d7,4(a1)
        ori.w   #$0002,d4
.right_p0_1:
.right_p1_0:
        tst.w   d6
        beq.s   .right_p1_2
        move.w  d6,d7
        and.w   d0,d7
        eor.w   d7,d6
        beq.s   .right_p0_2
        btst    #2,d4
        bne.s   .right_have2
        clr.w   6(a1)
.right_have2:
        move.w  d6,8(a1)
        ori.w   #$0004,d4
.right_p0_2:
        tst.w   d7
        beq.s   .right_p0_3
        btst    #3,d4
        bne.s   .right_have3
        clr.w   10(a1)
.right_have3:
        move.w  d7,12(a1)
        ori.w   #$0008,d4
.right_p0_3:
.right_p1_2:
.right_group0_end:
        move.w  d3,d5
        not.w   d5
        and.w   d2,d5
        beq.w   .right_group4_end
        move.w  d5,d6
        and.w   d1,d6
        eor.w   d6,d5
        beq.s   .right_p1_4
        move.w  d5,d7
        and.w   d0,d7
        eor.w   d7,d5
        beq.s   .right_p0_4
        btst    #4,d4
        bne.s   .right_have4
        clr.w   14(a1)
.right_have4:
        move.w  d5,16(a1)
        ori.w   #$0010,d4
.right_p0_4:
        tst.w   d7
        beq.s   .right_p0_5
        btst    #5,d4
        bne.s   .right_have5
        clr.w   18(a1)
.right_have5:
        move.w  d7,20(a1)
        ori.w   #$0020,d4
.right_p0_5:
.right_p1_4:
        tst.w   d6
        beq.s   .right_p1_6
        move.w  d6,d7
        and.w   d0,d7
        eor.w   d7,d6
        beq.s   .right_p0_6
        btst    #6,d4
        bne.s   .right_have6
        clr.w   22(a1)
.right_have6:
        move.w  d6,24(a1)
        ori.w   #$0040,d4
.right_p0_6:
        tst.w   d7
        beq.s   .right_p0_7
        btst    #7,d4
        bne.s   .right_have7
        clr.w   26(a1)
.right_have7:
        move.w  d7,28(a1)
        ori.w   #$0080,d4
.right_p0_7:
.right_p1_6:
.right_group4_end:
        move.w  d2,d5
        not.w   d5
        and.w   d3,d5
        beq.w   .right_group8_end
        move.w  d5,d6
        and.w   d1,d6
        eor.w   d6,d5
        beq.s   .right_p1_8
        move.w  d5,d7
        and.w   d0,d7
        eor.w   d7,d5
        beq.s   .right_p0_8
        btst    #8,d4
        bne.s   .right_have8
        clr.w   30(a1)
.right_have8:
        move.w  d5,32(a1)
        ori.w   #$0100,d4
.right_p0_8:
        tst.w   d7
        beq.s   .right_p0_9
        btst    #9,d4
        bne.s   .right_have9
        clr.w   34(a1)
.right_have9:
        move.w  d7,36(a1)
        ori.w   #$0200,d4
.right_p0_9:
.right_p1_8:
        tst.w   d6
        beq.s   .right_p1_10
        move.w  d6,d7
        and.w   d0,d7
        eor.w   d7,d6
        beq.s   .right_p0_10
        btst    #10,d4
        bne.s   .right_have10
        clr.w   38(a1)
.right_have10:
        move.w  d6,40(a1)
        ori.w   #$0400,d4
.right_p0_10:
        tst.w   d7
        beq.s   .right_p0_11
        btst    #11,d4
        bne.s   .right_have11
        clr.w   42(a1)
.right_have11:
        move.w  d7,44(a1)
        ori.w   #$0800,d4
.right_p0_11:
.right_p1_10:
.right_group8_end:
        move.w  d2,d5
        and.w   d3,d5
        beq.w   .right_group12_end
        move.w  d5,d6
        and.w   d1,d6
        eor.w   d6,d5
        beq.s   .right_p1_12
        move.w  d5,d7
        and.w   d0,d7
        eor.w   d7,d5
        beq.s   .right_p0_12
        btst    #12,d4
        bne.s   .right_have12
        clr.w   46(a1)
.right_have12:
        move.w  d5,48(a1)
        ori.w   #$1000,d4
.right_p0_12:
        tst.w   d7
        beq.s   .right_p0_13
        btst    #13,d4
        bne.s   .right_have13
        clr.w   50(a1)
.right_have13:
        move.w  d7,52(a1)
        ori.w   #$2000,d4
.right_p0_13:
.right_p1_12:
        tst.w   d6
        beq.s   .right_p1_14
        move.w  d6,d7
        and.w   d0,d7
        eor.w   d7,d6
        beq.s   .right_p0_14
        btst    #14,d4
        bne.s   .right_have14
        clr.w   54(a1)
.right_have14:
        move.w  d6,56(a1)
        ori.w   #$4000,d4
.right_p0_14:
        tst.w   d7
        beq.s   .right_p0_15
        btst    #15,d4
        bne.s   .right_have15
        clr.w   58(a1)
.right_have15:
        move.w  d7,60(a1)
        ori.w   #$8000,d4
.right_p0_15:
.right_p1_14:
.right_group12_end:
.right_row_end:
        move.w  d4,(a1)
        lea     62(a1),a1
        cmpa.l  a5,a0
        bne.w   .right_row
.finish_wide:
.finish:
        move.l  a1,d0
        sub.l   a6,d0
.return:
        movem.l (sp)+,d2-d7/a2-a6
        rts
.bad:
        move.w  #$ffff,d0
        bra.s   .return
.height:
        moveq   #0,d0
        move.b  (a0),d0
        btst    #2,3(a0)
        beq.s   .vs
        addi.w  #256,d0
.vs:
        moveq   #0,d1
        move.b  2(a0),d1
        btst    #1,3(a0)
        beq.s   .ve
        addi.w  #256,d1
.ve:
        sub.w   d0,d1
        rts
        endif
