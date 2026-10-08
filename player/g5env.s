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
        ifnd G5ENV_N
G5ENV_N equ 8
        endif
G5ENV_ENTRY equ 1246
G5ENV_BYTES equ 2484+G5ENV_N*G5ENV_ENTRY
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
        btst    #2,d1                       ; alto multiplicado por 4: paridad
        bne.w   .mono_second
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
        move.w  d6,d7
        and.w   d0,d7
        eor.w   d7,d6
        movem.w d5-d7,-(a1)
        lea     60(a1),a1
.mono_second:
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

; --- _g5env_lookup ---
; entrada: pila vbcc +4 = cache G5ENV_BYTES, +8 = clave 40 B o cero,
;          +12 = sprites de la foto. Cache inicialmente a cero.
; salida: d0 = entrada, cero si invalida; d1 = 1 hit, 0 miss, 2 miss con alias.
; registros destruidos: d0/d1/a0/a1; preserva d2-d7/a2-a6.
; ciclos: tools/g5env_verify.py cache (incluye el decoder en los fallos).
; La tabla directa solo selecciona candidato: se comparan los 40 B siempre.
; Clave alineada: n/entradas 18 B, primer/ultimo byte de punteros,
; interior de punteros 20 B (permutacion sin perdida).
        public _g5env_lookup
_g5env_lookup:
        move.l  a2,-(sp)
        move.l  8(sp),a2
        move.l  12(sp),a0
        move.l  a0,d0
        beq.w   .uncached
        moveq   #0,d0
        move.b  5(a0),d0
        lsr.b   #6,d0
        move.b  21(a0),d1
        lsr.b   #5,d1
        eor.b   d1,d0
        move.b  18(a0),d1
        lsr.b   #6,d1
        eor.b   d1,d0
        add.w   d0,d0
        andi.w  #2*(G5ENV_N-1),d0
        lea     .offsets(pc),a1
        moveq   #0,d1
        move.w  (a1,d0.w),d1                ; P40: indice 0..62
        lea     2484(a2),a2
        adda.l  d1,a2                      ; offset unsigned, N=32 supera 32767
        tst.w   (a2)
        beq.w   .miss
        lea     16(a0),a0
        lea     18(a2),a1
        cmpm.l  (a0)+,(a1)+
        bne.s   .reject
        cmpm.l  (a0)+,(a1)+
        bne.s   .miss
        cmpm.l  (a0)+,(a1)+
        bne.s   .miss
        cmpm.l  (a0)+,(a1)+
        bne.s   .reject
        cmpm.l  (a0)+,(a1)+
        bne.s   .miss
        cmpm.l  (a0)+,(a1)+
        bne.s   .miss
        move.l  a1,d0
        move.l  12(sp),a0
        lea     2(a2),a1
        cmpm.l  (a0)+,(a1)+
        bne.s   .miss
        cmpm.l  (a0)+,(a1)+
        bne.s   .miss
        cmpm.l  (a0)+,(a1)+
        bne.s   .miss
        cmpm.l  (a0)+,(a1)+
        bne.s   .miss
        moveq   #1,d1
        move.l  (sp)+,a2
        rts
.reject:
        bra.w   .cold
.miss:
        tst.w   (a2)
        beq.w   .cold
        move.l  12(sp),a0
        ; Prueba conservadora para las fichas 0..2: solo leen punteros
        ; 0/1/5/6. Comparar 34 B cubre esos cuatro y algunos no usados.
        ; Otros tiles siempre decodifican: nunca se deduce una imagen
        ; de un hash ni se ignora un puntero usado.
        cmpi.w  #2,(a0)
        bhi.w   .cold
        cmpi.b  #2,4(a0)
        bhi.w   .cold
        cmpi.b  #2,8(a0)
        bhi.w   .cold
        lea     2(a2),a1
        cmpm.l  (a0)+,(a1)+
        bne.w   .cold
        cmpm.l  (a0)+,(a1)+
        bne.w   .cold
        cmpm.l  (a0)+,(a1)+
        bne.w   .cold
        cmpm.l  (a0)+,(a1)+
        bne.w   .cold
        cmpm.w  (a0)+,(a1)+
        bne.w   .cold
        move.l  12(sp),a0
        lea     2(a2),a1
        move.b  22(a0),d0
        cmp.b   22(a1),d0
        bne.w   .cold
        move.b  32(a0),d0
        cmp.b   32(a1),d0
        bne.w   .cold
        move.b  20(a0),d0
        cmp.b   20(a1),d0
        bne.w   .cold
        move.b  30(a0),d0
        cmp.b   30(a1),d0
        bne.w   .cold
        move.b  18(a0),d0
        cmp.b   18(a1),d0
        bne.w   .cold
        move.b  21(a0),d0
        cmp.b   21(a1),d0
        bne.w   .cold
        move.b  29(a0),d0
        cmp.b   29(a1),d0
        bne.w   .cold
        move.b  31(a0),d0
        cmp.b   31(a1),d0
        bne.w   .cold
        move.l  12(sp),a0
        lea     2(a2),a1
        move.l  (a0)+,(a1)+
        move.l  (a0)+,(a1)+
        move.l  (a0)+,(a1)+
        move.l  (a0)+,(a1)+
        move.l  (a0)+,(a1)+
        move.l  (a0)+,(a1)+
        move.l  (a0)+,(a1)+
        move.l  (a0)+,(a1)+
        move.l  (a0)+,(a1)+
        move.l  (a0)+,(a1)+
        move.l  a1,d0
        moveq   #2,d1                      ; fallo de clave, igualdad DATA demostrada
        move.l  (sp)+,a2
        rts
.cold:
        move.l  12(sp),a0
        lea     2(a2),a1
        move.l  (a0)+,(a1)+
        move.l  (a0)+,(a1)+
        move.l  (a0)+,(a1)+
        move.l  (a0)+,(a1)+
        move.l  (a0)+,(a1)+
        move.l  (a0)+,(a1)+
        move.l  (a0)+,(a1)+
        move.l  (a0)+,(a1)+
        move.l  (a0)+,(a1)+
        move.l  (a0)+,(a1)+
        move.w  #1,(a2)
        move.l  a1,-(sp)
        move.l  20(sp),-(sp)               ; buffer de la foto
        bsr.w   _g5env_decode
        addq.l  #8,sp
        cmpi.w  #$ffff,d0
        beq.s   .bad
        lea     42(a2),a0
        move.l  a0,d0
        moveq   #0,d1
        move.l  (sp)+,a2
        rts
.bad:
        clr.w   (a2)
        moveq   #0,d0
        moveq   #0,d1
        move.l  (sp)+,a2
        rts
.uncached:
        move.l  a2,-(sp)
        move.l  20(sp),-(sp)
        bsr.w   _g5env_decode
        addq.l  #8,sp
        cmpi.w  #$ffff,d0
        beq.s   .bad
        move.l  a2,d0
        moveq   #0,d1
        move.l  (sp)+,a2
        rts
.offsets:
        rept G5ENV_N
        dc.w REPTN*G5ENV_ENTRY
        endr

        ifd G5ENV_PROJECT
; --- _g5env_project ---
; entrada: pila vbcc +4 bloque B2, +8 sprites de la foto, +12 mascaras;
;          a4 = binstart (tabla g5env_bounds del C, <32 KB, P36).
; salida: vista Mario B2 o pack propio portable (tag $B2); Rex sin tocar.
; registros destruidos: d0/d1/a0/a1; preserva d2-d7/a2-a6.
; ciclos: tools/g5env_verify.py project; recorte ANTES de hallar extremos.
; La columna doble (camino raro del C) usa g5env_bind como control exacto.
        public _g5env_project
_g5env_project:
        move.l  4(sp),a1
        clr.w   10(a1)                     ; formato materializado por defecto
        move.l  8(sp),a0
        movem.l d2-d7/a2-a6,-(sp)
        move.l  56(sp),a2
        lea     12(a1),a6
        moveq   #0,d0
        move.l  d0,(a6)+
        move.l  d0,(a6)+
        move.l  d0,(a6)+
        move.l  d0,(a6)+
        move.l  d0,(a6)+
        move.l  d0,(a6)+
        move.l  d0,(a6)+
        move.l  d0,(a6)+
        move.l  d0,(a6)+
        move.l  d0,(a6)+
        move.l  d0,(a6)+
        move.l  d0,(a6)+
        move.l  d0,(a6)+
        move.l  d0,(a6)+
        move.l  d0,(a6)+
        move.l  d0,(a6)+
        move.l  d0,(a6)+
        move.l  d0,(a6)+
        move.l  d0,(a6)+
        move.l  d0,(a6)+
        move.w  (a2),d2
        bne.s   .visible
        clr.w   8(a1)
        bra.w   .return
.visible:
        cmpi.w  #4,2(a2)
        beq.s   .mono
        cmpi.w  #1,2(a2)
        beq.s   .mono
        movem.l (sp)+,d2-d7/a2-a6
        move.l  a4,a0
        add.l   #_g5env_bind-binstart,a0
        jmp     (a0)
.mono:
        move.l  (a0),d0
        bne.s   .pos
        lea     336(a0),a0
.pos:
        moveq   #0,d7
        move.b  (a0),d7
        btst    #2,3(a0)
        beq.s   .vs
        addi.w  #256,d7
.vs:
        subi.w  #44,d7
        move.w  d7,8(a1)
        moveq   #0,d5
        move.b  1(a0),d5
        add.w   d5,d5
        btst    #0,3(a0)
        beq.s   .hs
        addq.w  #1,d5
.hs:
        subi.w  #160,d5
        cmpi.w  #-16,d5
        ble.w   .return
        cmpi.w  #256,d5
        bge.w   .return
        moveq   #-1,d3                     ; no convertir si hay recorte
        tst.w   d5
        bmi.s   .recrop
        cmpi.w  #240,d5
        bgt.s   .recrop
        cmpi.w  #4,2(a2)
        beq.w   .warm
        tst.w   d7
        bmi.s   .raw
        move.w  d7,d0
        add.w   d2,d0
        cmpi.w  #224,d0
        bhi.s   .raw
        moveq   #0,d3
        bra.s   .raw
.recrop:
        cmpi.w  #4,2(a2)
        bne.s   .raw
        ; La caja cruzo el borde: los limites pierden los huecos.
        ; Decodificar DATA de la foto en el scratch slow, antes del recorte.
        move.l  a4,a2
        add.l   #g5env_cache-binstart,a2
        move.l  a2,-(sp)
        move.l  56(sp),-(sp)
        bsr.w   _g5env_decode
        addq.l  #8,sp
        move.l  48(sp),a1                   ; decoder destruye a1: recuperar salida
.raw:
        move.w  #$ffff,d6
        tst.w   d5
        bpl.s   .right
        move.w  d5,d0
        neg.w   d0
        lsr.w   d0,d6
.right:
        cmpi.w  #240,d5
        ble.s   .clip
        move.w  d5,d0
        subi.w  #240,d0
        lsl.w   d0,d6
.clip:
        ; x*257 traduce las dos coordenadas a la vez. El recorte garantiza
        ; que primer/ultimo+x estan en 0..255, tambien para x negativo.
        move.w  d5,d0
        lsl.w   #8,d5
        add.w   d0,d5
        lea     _g5env_bounds(a4),a3
        lea     12(a1),a6
        lea     92(a1),a1
        lea     4(a2),a0
        lea     -1204(sp),sp
        move.l  sp,a5
        subq.w  #1,d2
        tst.w   d3
        beq.w   .fast_row
.row:
        cmpi.w  #224,d7
        bhs.w   .skip_row                  ; negativo tambien queda fuera
        moveq   #0,d4
        tst.w   d3
        bne.s   .no_pack_row
        move.l  a5,d0
        sub.l   sp,d0
        cmpi.w  #1136,d0                   ; payload <=1200, incluso fila de 64 B
        bls.s   .pack_row
        moveq   #-1,d3                     ; denso excepcional: conservar mascaras
        bra.s   .no_pack_row
.pack_row:
        move.l  a5,a4
        addq.l  #4,a5
.no_pack_row:
.slow_continue:
        move.w  (a0)+,d0
        and.w   d6,d0
        beq.s   .done1
        tst.b   d0
        bne.s   .low1
        lsr.w   #8,d0
        add.w   d0,d0
        move.w  (a3,d0.w),d1
        bra.s   .store1
.low1:
        cmpi.w  #255,d0
        bhi.s   .both1
        add.w   d0,d0
        move.w  (a3,d0.w),d1
        addi.w  #$0808,d1
        bra.s   .store1
.both1:
        move.w  d0,d1
        lsr.w   #8,d1
        add.w   d1,d1
        move.w  (a3,d1.w),d1
        andi.w  #255,d0
        add.w   d0,d0
        move.w  (a3,d0.w),d0
        move.b  d0,d1
        addq.w  #8,d1
.store1:
        tst.w   d3
        bne.s   .translated1
        move.w  #0,(a5)+
        move.w  d1,(a5)+                    ; relativo; solo indices presentes
.translated1:
        add.w   d5,d1
        move.w  d1,0(a1)
        ori.w   #$0002,d4
.done1:
        move.w  (a0)+,d0
        and.w   d6,d0
        beq.s   .done2
        tst.b   d0
        bne.s   .low2
        lsr.w   #8,d0
        add.w   d0,d0
        move.w  (a3,d0.w),d1
        bra.s   .store2
.low2:
        cmpi.w  #255,d0
        bhi.s   .both2
        add.w   d0,d0
        move.w  (a3,d0.w),d1
        addi.w  #$0808,d1
        bra.s   .store2
.both2:
        move.w  d0,d1
        lsr.w   #8,d1
        add.w   d1,d1
        move.w  (a3,d1.w),d1
        andi.w  #255,d0
        add.w   d0,d0
        move.w  (a3,d0.w),d0
        move.b  d0,d1
        addq.w  #8,d1
.store2:
        tst.w   d3
        bne.s   .translated2
        move.w  #2,(a5)+
        move.w  d1,(a5)+                    ; relativo; solo indices presentes
.translated2:
        add.w   d5,d1
        move.w  d1,2(a1)
        ori.w   #$0004,d4
.done2:
        move.w  (a0)+,d0
        and.w   d6,d0
        beq.s   .done3
        tst.b   d0
        bne.s   .low3
        lsr.w   #8,d0
        add.w   d0,d0
        move.w  (a3,d0.w),d1
        bra.s   .store3
.low3:
        cmpi.w  #255,d0
        bhi.s   .both3
        add.w   d0,d0
        move.w  (a3,d0.w),d1
        addi.w  #$0808,d1
        bra.s   .store3
.both3:
        move.w  d0,d1
        lsr.w   #8,d1
        add.w   d1,d1
        move.w  (a3,d1.w),d1
        andi.w  #255,d0
        add.w   d0,d0
        move.w  (a3,d0.w),d0
        move.b  d0,d1
        addq.w  #8,d1
.store3:
        tst.w   d3
        bne.s   .translated3
        move.w  #4,(a5)+
        move.w  d1,(a5)+                    ; relativo; solo indices presentes
.translated3:
        add.w   d5,d1
        move.w  d1,4(a1)
        ori.w   #$0008,d4
.done3:
        move.w  (a0)+,d0
        and.w   d6,d0
        beq.s   .done4
        tst.b   d0
        bne.s   .low4
        lsr.w   #8,d0
        add.w   d0,d0
        move.w  (a3,d0.w),d1
        bra.s   .store4
.low4:
        cmpi.w  #255,d0
        bhi.s   .both4
        add.w   d0,d0
        move.w  (a3,d0.w),d1
        addi.w  #$0808,d1
        bra.s   .store4
.both4:
        move.w  d0,d1
        lsr.w   #8,d1
        add.w   d1,d1
        move.w  (a3,d1.w),d1
        andi.w  #255,d0
        add.w   d0,d0
        move.w  (a3,d0.w),d0
        move.b  d0,d1
        addq.w  #8,d1
.store4:
        tst.w   d3
        bne.s   .translated4
        move.w  #6,(a5)+
        move.w  d1,(a5)+                    ; relativo; solo indices presentes
.translated4:
        add.w   d5,d1
        move.w  d1,6(a1)
        ori.w   #$0010,d4
.done4:
        move.w  (a0)+,d0
        and.w   d6,d0
        beq.s   .done5
        tst.b   d0
        bne.s   .low5
        lsr.w   #8,d0
        add.w   d0,d0
        move.w  (a3,d0.w),d1
        bra.s   .store5
.low5:
        cmpi.w  #255,d0
        bhi.s   .both5
        add.w   d0,d0
        move.w  (a3,d0.w),d1
        addi.w  #$0808,d1
        bra.s   .store5
.both5:
        move.w  d0,d1
        lsr.w   #8,d1
        add.w   d1,d1
        move.w  (a3,d1.w),d1
        andi.w  #255,d0
        add.w   d0,d0
        move.w  (a3,d0.w),d0
        move.b  d0,d1
        addq.w  #8,d1
.store5:
        tst.w   d3
        bne.s   .translated5
        move.w  #8,(a5)+
        move.w  d1,(a5)+                    ; relativo; solo indices presentes
.translated5:
        add.w   d5,d1
        move.w  d1,8(a1)
        ori.w   #$0020,d4
.done5:
        move.w  (a0)+,d0
        and.w   d6,d0
        beq.s   .done6
        tst.b   d0
        bne.s   .low6
        lsr.w   #8,d0
        add.w   d0,d0
        move.w  (a3,d0.w),d1
        bra.s   .store6
.low6:
        cmpi.w  #255,d0
        bhi.s   .both6
        add.w   d0,d0
        move.w  (a3,d0.w),d1
        addi.w  #$0808,d1
        bra.s   .store6
.both6:
        move.w  d0,d1
        lsr.w   #8,d1
        add.w   d1,d1
        move.w  (a3,d1.w),d1
        andi.w  #255,d0
        add.w   d0,d0
        move.w  (a3,d0.w),d0
        move.b  d0,d1
        addq.w  #8,d1
.store6:
        tst.w   d3
        bne.s   .translated6
        move.w  #10,(a5)+
        move.w  d1,(a5)+                    ; relativo; solo indices presentes
.translated6:
        add.w   d5,d1
        move.w  d1,10(a1)
        ori.w   #$0040,d4
.done6:
        move.w  (a0)+,d0
        and.w   d6,d0
        beq.s   .done7
        tst.b   d0
        bne.s   .low7
        lsr.w   #8,d0
        add.w   d0,d0
        move.w  (a3,d0.w),d1
        bra.s   .store7
.low7:
        cmpi.w  #255,d0
        bhi.s   .both7
        add.w   d0,d0
        move.w  (a3,d0.w),d1
        addi.w  #$0808,d1
        bra.s   .store7
.both7:
        move.w  d0,d1
        lsr.w   #8,d1
        add.w   d1,d1
        move.w  (a3,d1.w),d1
        andi.w  #255,d0
        add.w   d0,d0
        move.w  (a3,d0.w),d0
        move.b  d0,d1
        addq.w  #8,d1
.store7:
        tst.w   d3
        bne.s   .translated7
        move.w  #12,(a5)+
        move.w  d1,(a5)+                    ; relativo; solo indices presentes
.translated7:
        add.w   d5,d1
        move.w  d1,12(a1)
        ori.w   #$0080,d4
.done7:
        move.w  (a0)+,d0
        and.w   d6,d0
        beq.s   .done8
        tst.b   d0
        bne.s   .low8
        lsr.w   #8,d0
        add.w   d0,d0
        move.w  (a3,d0.w),d1
        bra.s   .store8
.low8:
        cmpi.w  #255,d0
        bhi.s   .both8
        add.w   d0,d0
        move.w  (a3,d0.w),d1
        addi.w  #$0808,d1
        bra.s   .store8
.both8:
        move.w  d0,d1
        lsr.w   #8,d1
        add.w   d1,d1
        move.w  (a3,d1.w),d1
        andi.w  #255,d0
        add.w   d0,d0
        move.w  (a3,d0.w),d0
        move.b  d0,d1
        addq.w  #8,d1
.store8:
        tst.w   d3
        bne.s   .translated8
        move.w  #14,(a5)+
        move.w  d1,(a5)+                    ; relativo; solo indices presentes
.translated8:
        add.w   d5,d1
        move.w  d1,14(a1)
        ori.w   #$0100,d4
.done8:
        move.w  (a0)+,d0
        and.w   d6,d0
        beq.s   .done9
        tst.b   d0
        bne.s   .low9
        lsr.w   #8,d0
        add.w   d0,d0
        move.w  (a3,d0.w),d1
        bra.s   .store9
.low9:
        cmpi.w  #255,d0
        bhi.s   .both9
        add.w   d0,d0
        move.w  (a3,d0.w),d1
        addi.w  #$0808,d1
        bra.s   .store9
.both9:
        move.w  d0,d1
        lsr.w   #8,d1
        add.w   d1,d1
        move.w  (a3,d1.w),d1
        andi.w  #255,d0
        add.w   d0,d0
        move.w  (a3,d0.w),d0
        move.b  d0,d1
        addq.w  #8,d1
.store9:
        tst.w   d3
        bne.s   .translated9
        move.w  #16,(a5)+
        move.w  d1,(a5)+                    ; relativo; solo indices presentes
.translated9:
        add.w   d5,d1
        move.w  d1,16(a1)
        ori.w   #$0200,d4
.done9:
        move.w  (a0)+,d0
        and.w   d6,d0
        beq.s   .done10
        tst.b   d0
        bne.s   .low10
        lsr.w   #8,d0
        add.w   d0,d0
        move.w  (a3,d0.w),d1
        bra.s   .store10
.low10:
        cmpi.w  #255,d0
        bhi.s   .both10
        add.w   d0,d0
        move.w  (a3,d0.w),d1
        addi.w  #$0808,d1
        bra.s   .store10
.both10:
        move.w  d0,d1
        lsr.w   #8,d1
        add.w   d1,d1
        move.w  (a3,d1.w),d1
        andi.w  #255,d0
        add.w   d0,d0
        move.w  (a3,d0.w),d0
        move.b  d0,d1
        addq.w  #8,d1
.store10:
        tst.w   d3
        bne.s   .translated10
        move.w  #18,(a5)+
        move.w  d1,(a5)+                    ; relativo; solo indices presentes
.translated10:
        add.w   d5,d1
        move.w  d1,18(a1)
        ori.w   #$0400,d4
.done10:
        move.w  (a0)+,d0
        and.w   d6,d0
        beq.s   .done11
        tst.b   d0
        bne.s   .low11
        lsr.w   #8,d0
        add.w   d0,d0
        move.w  (a3,d0.w),d1
        bra.s   .store11
.low11:
        cmpi.w  #255,d0
        bhi.s   .both11
        add.w   d0,d0
        move.w  (a3,d0.w),d1
        addi.w  #$0808,d1
        bra.s   .store11
.both11:
        move.w  d0,d1
        lsr.w   #8,d1
        add.w   d1,d1
        move.w  (a3,d1.w),d1
        andi.w  #255,d0
        add.w   d0,d0
        move.w  (a3,d0.w),d0
        move.b  d0,d1
        addq.w  #8,d1
.store11:
        tst.w   d3
        bne.s   .translated11
        move.w  #20,(a5)+
        move.w  d1,(a5)+                    ; relativo; solo indices presentes
.translated11:
        add.w   d5,d1
        move.w  d1,20(a1)
        ori.w   #$0800,d4
.done11:
        move.w  (a0)+,d0
        and.w   d6,d0
        beq.s   .done12
        tst.b   d0
        bne.s   .low12
        lsr.w   #8,d0
        add.w   d0,d0
        move.w  (a3,d0.w),d1
        bra.s   .store12
.low12:
        cmpi.w  #255,d0
        bhi.s   .both12
        add.w   d0,d0
        move.w  (a3,d0.w),d1
        addi.w  #$0808,d1
        bra.s   .store12
.both12:
        move.w  d0,d1
        lsr.w   #8,d1
        add.w   d1,d1
        move.w  (a3,d1.w),d1
        andi.w  #255,d0
        add.w   d0,d0
        move.w  (a3,d0.w),d0
        move.b  d0,d1
        addq.w  #8,d1
.store12:
        tst.w   d3
        bne.s   .translated12
        move.w  #22,(a5)+
        move.w  d1,(a5)+                    ; relativo; solo indices presentes
.translated12:
        add.w   d5,d1
        move.w  d1,22(a1)
        ori.w   #$1000,d4
.done12:
        move.w  (a0)+,d0
        and.w   d6,d0
        beq.s   .done13
        tst.b   d0
        bne.s   .low13
        lsr.w   #8,d0
        add.w   d0,d0
        move.w  (a3,d0.w),d1
        bra.s   .store13
.low13:
        cmpi.w  #255,d0
        bhi.s   .both13
        add.w   d0,d0
        move.w  (a3,d0.w),d1
        addi.w  #$0808,d1
        bra.s   .store13
.both13:
        move.w  d0,d1
        lsr.w   #8,d1
        add.w   d1,d1
        move.w  (a3,d1.w),d1
        andi.w  #255,d0
        add.w   d0,d0
        move.w  (a3,d0.w),d0
        move.b  d0,d1
        addq.w  #8,d1
.store13:
        tst.w   d3
        bne.s   .translated13
        move.w  #24,(a5)+
        move.w  d1,(a5)+                    ; relativo; solo indices presentes
.translated13:
        add.w   d5,d1
        move.w  d1,24(a1)
        ori.w   #$2000,d4
.done13:
        move.w  (a0)+,d0
        and.w   d6,d0
        beq.s   .done14
        tst.b   d0
        bne.s   .low14
        lsr.w   #8,d0
        add.w   d0,d0
        move.w  (a3,d0.w),d1
        bra.s   .store14
.low14:
        cmpi.w  #255,d0
        bhi.s   .both14
        add.w   d0,d0
        move.w  (a3,d0.w),d1
        addi.w  #$0808,d1
        bra.s   .store14
.both14:
        move.w  d0,d1
        lsr.w   #8,d1
        add.w   d1,d1
        move.w  (a3,d1.w),d1
        andi.w  #255,d0
        add.w   d0,d0
        move.w  (a3,d0.w),d0
        move.b  d0,d1
        addq.w  #8,d1
.store14:
        tst.w   d3
        bne.s   .translated14
        move.w  #26,(a5)+
        move.w  d1,(a5)+                    ; relativo; solo indices presentes
.translated14:
        add.w   d5,d1
        move.w  d1,26(a1)
        ori.w   #$4000,d4
.done14:
        move.w  (a0)+,d0
        and.w   d6,d0
        beq.s   .done15
        tst.b   d0
        bne.s   .low15
        lsr.w   #8,d0
        add.w   d0,d0
        move.w  (a3,d0.w),d1
        bra.s   .store15
.low15:
        cmpi.w  #255,d0
        bhi.s   .both15
        add.w   d0,d0
        move.w  (a3,d0.w),d1
        addi.w  #$0808,d1
        bra.s   .store15
.both15:
        move.w  d0,d1
        lsr.w   #8,d1
        add.w   d1,d1
        move.w  (a3,d1.w),d1
        andi.w  #255,d0
        add.w   d0,d0
        move.w  (a3,d0.w),d0
        move.b  d0,d1
        addq.w  #8,d1
.store15:
        tst.w   d3
        bne.s   .translated15
        move.w  #28,(a5)+
        move.w  d1,(a5)+                    ; relativo; solo indices presentes
.translated15:
        add.w   d5,d1
        move.w  d1,28(a1)
        ori.w   #$8000,d4
.done15:
.pack_epilogue:
        tst.w   d3
        bne.s   .keep_raw
        move.w  d4,(a4)
        move.l  a5,d0
        sub.l   a4,d0
        lsr.w   #2,d0
        subq.w  #2,d0                      ; contador DBF: pares - 1
        move.w  d0,2(a4)
.keep_raw:
        move.w  d4,(a6)+
        lea     30(a1),a1
        addq.w  #1,d7
        tst.w   d3
        bne.s   .slow_advance
        dbf     d2,.fast_row
        bra.s   .rows_done
.slow_advance:
        dbf     d2,.row
.rows_done:
        tst.w   d3
        bne.w   .mono_return
        move.w  #4,2(a2)
        move.l  sp,a0
        lea     4(a2),a1
        move.l  a5,d0
        sub.l   a0,d0
        move.w  d0,d2
        lsr.w   #5,d2
        subq.w  #1,d2
        bmi.s   .pack_tail
.copy_pack:
        movem.l (a0)+,d0-d1/d3-d7
        movem.l d0-d1/d3-d7,(a1)
        lea     28(a1),a1
        move.l  (a0)+,(a1)+
        dbf     d2,.copy_pack
.pack_tail:
        move.l  a5,d0
        sub.l   a0,d0
        lsr.w   #1,d0
        subq.w  #1,d0
        bmi.s   .pack_done
.copy_tail:
        move.w  (a0)+,(a1)+
        dbf     d0,.copy_tail
.pack_done:
        bra.w   .mono_return
.skip_row:
        lea     30(a0),a0
        lea     30(a1),a1
        addq.l  #2,a6
        addq.w  #1,d7
        dbf     d2,.row
.mono_return:
        lea     1204(sp),sp
        bra.w   .return
.warm:
        ; Copiar el payload disperso y su indice por fila. La frontera
        ; traduce solo el indice solicitado, sin materializar 15 cajas.
        move.w  #$b200,d0
        or.w    d5,d0
        move.w  d0,10(a1)
        lea     4(a2),a0
        lea     12(a1),a6
        lea     92(a1),a1
        moveq   #0,d1
        moveq   #-1,d4
        rept    20
        move.l  d4,(a6)+
        endr
        lea     -80(a6),a6
        subq.w  #1,d2
.warm_row:
        move.w  2(a0),d3
        cmpi.w  #224,d7
        bhs.s   .warm_skip
        move.w  d1,(a6)
.warm_skip:
        addq.w  #2,d3
        lsl.w   #2,d3
        adda.w  d3,a0
        add.w   d3,d1
.warm_next:
        addq.l  #2,a6
        addq.w  #1,d7
        dbf     d2,.warm_row
        move.l  a0,a6                      ; fin del payload, sobrevive al MOVEM
        lea     4(a2),a0
        move.w  d1,d2
        lsr.w   #5,d2
        subq.w  #1,d2
        bmi.s   .warm_tail
.warm_copy:
        movem.l (a0)+,d0-d1/d3-d7
        movem.l d0-d1/d3-d7,(a1)
        lea     28(a1),a1
        move.l  (a0)+,(a1)+
        dbf     d2,.warm_copy
.warm_tail:
        move.l  a6,d0
        sub.l   a0,d0
        lsr.w   #1,d0
        subq.w  #1,d0
        bmi.w   .return
.warm_words:
        move.w  (a0)+,(a1)+
        dbf     d0,.warm_words
        bra.w   .return
.fast_row:
        cmpi.w  #224,d7
        bhs.w   .skip_row                  ; negativo tambien queda fuera
        moveq   #0,d4
        tst.w   d3
        bne.s   .fast_no_pack_row
        move.l  a5,d0
        sub.l   sp,d0
        cmpi.w  #1136,d0                   ; payload <=1200, incluso fila de 64 B
        bls.s   .fast_pack_row
        moveq   #-1,d3                     ; denso excepcional: conservar mascaras
        bra.w   .slow_continue
.fast_pack_row:
        move.l  a5,a4
        addq.l  #4,a5
.fast_no_pack_row:
        move.w  (a0)+,d0
        beq.s   .fast_done1
        tst.b   d0
        bne.s   .fast_low1
        lsr.w   #8,d0
        add.w   d0,d0
        move.w  (a3,d0.w),d1
        bra.s   .fast_store1
.fast_low1:
        cmpi.w  #255,d0
        bhi.s   .fast_both1
        add.w   d0,d0
        move.w  (a3,d0.w),d1
        addi.w  #$0808,d1
        bra.s   .fast_store1
.fast_both1:
        move.w  d0,d1
        lsr.w   #8,d1
        add.w   d1,d1
        move.w  (a3,d1.w),d1
        andi.w  #255,d0
        add.w   d0,d0
        move.w  (a3,d0.w),d0
        move.b  d0,d1
        addq.w  #8,d1
.fast_store1:
        move.w  #0,(a5)+
        move.w  d1,(a5)+                    ; relativo; solo indices presentes
.fast_translated1:
        add.w   d5,d1
        move.w  d1,0(a1)
        ori.w   #$0002,d4
.fast_done1:
        move.w  (a0)+,d0
        beq.s   .fast_done2
        tst.b   d0
        bne.s   .fast_low2
        lsr.w   #8,d0
        add.w   d0,d0
        move.w  (a3,d0.w),d1
        bra.s   .fast_store2
.fast_low2:
        cmpi.w  #255,d0
        bhi.s   .fast_both2
        add.w   d0,d0
        move.w  (a3,d0.w),d1
        addi.w  #$0808,d1
        bra.s   .fast_store2
.fast_both2:
        move.w  d0,d1
        lsr.w   #8,d1
        add.w   d1,d1
        move.w  (a3,d1.w),d1
        andi.w  #255,d0
        add.w   d0,d0
        move.w  (a3,d0.w),d0
        move.b  d0,d1
        addq.w  #8,d1
.fast_store2:
        move.w  #2,(a5)+
        move.w  d1,(a5)+                    ; relativo; solo indices presentes
.fast_translated2:
        add.w   d5,d1
        move.w  d1,2(a1)
        ori.w   #$0004,d4
.fast_done2:
        move.w  (a0)+,d0
        beq.s   .fast_done3
        tst.b   d0
        bne.s   .fast_low3
        lsr.w   #8,d0
        add.w   d0,d0
        move.w  (a3,d0.w),d1
        bra.s   .fast_store3
.fast_low3:
        cmpi.w  #255,d0
        bhi.s   .fast_both3
        add.w   d0,d0
        move.w  (a3,d0.w),d1
        addi.w  #$0808,d1
        bra.s   .fast_store3
.fast_both3:
        move.w  d0,d1
        lsr.w   #8,d1
        add.w   d1,d1
        move.w  (a3,d1.w),d1
        andi.w  #255,d0
        add.w   d0,d0
        move.w  (a3,d0.w),d0
        move.b  d0,d1
        addq.w  #8,d1
.fast_store3:
        move.w  #4,(a5)+
        move.w  d1,(a5)+                    ; relativo; solo indices presentes
.fast_translated3:
        add.w   d5,d1
        move.w  d1,4(a1)
        ori.w   #$0008,d4
.fast_done3:
        move.w  (a0)+,d0
        beq.s   .fast_done4
        tst.b   d0
        bne.s   .fast_low4
        lsr.w   #8,d0
        add.w   d0,d0
        move.w  (a3,d0.w),d1
        bra.s   .fast_store4
.fast_low4:
        cmpi.w  #255,d0
        bhi.s   .fast_both4
        add.w   d0,d0
        move.w  (a3,d0.w),d1
        addi.w  #$0808,d1
        bra.s   .fast_store4
.fast_both4:
        move.w  d0,d1
        lsr.w   #8,d1
        add.w   d1,d1
        move.w  (a3,d1.w),d1
        andi.w  #255,d0
        add.w   d0,d0
        move.w  (a3,d0.w),d0
        move.b  d0,d1
        addq.w  #8,d1
.fast_store4:
        move.w  #6,(a5)+
        move.w  d1,(a5)+                    ; relativo; solo indices presentes
.fast_translated4:
        add.w   d5,d1
        move.w  d1,6(a1)
        ori.w   #$0010,d4
.fast_done4:
        move.w  (a0)+,d0
        beq.s   .fast_done5
        tst.b   d0
        bne.s   .fast_low5
        lsr.w   #8,d0
        add.w   d0,d0
        move.w  (a3,d0.w),d1
        bra.s   .fast_store5
.fast_low5:
        cmpi.w  #255,d0
        bhi.s   .fast_both5
        add.w   d0,d0
        move.w  (a3,d0.w),d1
        addi.w  #$0808,d1
        bra.s   .fast_store5
.fast_both5:
        move.w  d0,d1
        lsr.w   #8,d1
        add.w   d1,d1
        move.w  (a3,d1.w),d1
        andi.w  #255,d0
        add.w   d0,d0
        move.w  (a3,d0.w),d0
        move.b  d0,d1
        addq.w  #8,d1
.fast_store5:
        move.w  #8,(a5)+
        move.w  d1,(a5)+                    ; relativo; solo indices presentes
.fast_translated5:
        add.w   d5,d1
        move.w  d1,8(a1)
        ori.w   #$0020,d4
.fast_done5:
        move.w  (a0)+,d0
        beq.s   .fast_done6
        tst.b   d0
        bne.s   .fast_low6
        lsr.w   #8,d0
        add.w   d0,d0
        move.w  (a3,d0.w),d1
        bra.s   .fast_store6
.fast_low6:
        cmpi.w  #255,d0
        bhi.s   .fast_both6
        add.w   d0,d0
        move.w  (a3,d0.w),d1
        addi.w  #$0808,d1
        bra.s   .fast_store6
.fast_both6:
        move.w  d0,d1
        lsr.w   #8,d1
        add.w   d1,d1
        move.w  (a3,d1.w),d1
        andi.w  #255,d0
        add.w   d0,d0
        move.w  (a3,d0.w),d0
        move.b  d0,d1
        addq.w  #8,d1
.fast_store6:
        move.w  #10,(a5)+
        move.w  d1,(a5)+                    ; relativo; solo indices presentes
.fast_translated6:
        add.w   d5,d1
        move.w  d1,10(a1)
        ori.w   #$0040,d4
.fast_done6:
        move.w  (a0)+,d0
        beq.s   .fast_done7
        tst.b   d0
        bne.s   .fast_low7
        lsr.w   #8,d0
        add.w   d0,d0
        move.w  (a3,d0.w),d1
        bra.s   .fast_store7
.fast_low7:
        cmpi.w  #255,d0
        bhi.s   .fast_both7
        add.w   d0,d0
        move.w  (a3,d0.w),d1
        addi.w  #$0808,d1
        bra.s   .fast_store7
.fast_both7:
        move.w  d0,d1
        lsr.w   #8,d1
        add.w   d1,d1
        move.w  (a3,d1.w),d1
        andi.w  #255,d0
        add.w   d0,d0
        move.w  (a3,d0.w),d0
        move.b  d0,d1
        addq.w  #8,d1
.fast_store7:
        move.w  #12,(a5)+
        move.w  d1,(a5)+                    ; relativo; solo indices presentes
.fast_translated7:
        add.w   d5,d1
        move.w  d1,12(a1)
        ori.w   #$0080,d4
.fast_done7:
        move.w  (a0)+,d0
        beq.s   .fast_done8
        tst.b   d0
        bne.s   .fast_low8
        lsr.w   #8,d0
        add.w   d0,d0
        move.w  (a3,d0.w),d1
        bra.s   .fast_store8
.fast_low8:
        cmpi.w  #255,d0
        bhi.s   .fast_both8
        add.w   d0,d0
        move.w  (a3,d0.w),d1
        addi.w  #$0808,d1
        bra.s   .fast_store8
.fast_both8:
        move.w  d0,d1
        lsr.w   #8,d1
        add.w   d1,d1
        move.w  (a3,d1.w),d1
        andi.w  #255,d0
        add.w   d0,d0
        move.w  (a3,d0.w),d0
        move.b  d0,d1
        addq.w  #8,d1
.fast_store8:
        move.w  #14,(a5)+
        move.w  d1,(a5)+                    ; relativo; solo indices presentes
.fast_translated8:
        add.w   d5,d1
        move.w  d1,14(a1)
        ori.w   #$0100,d4
.fast_done8:
        move.w  (a0)+,d0
        beq.s   .fast_done9
        tst.b   d0
        bne.s   .fast_low9
        lsr.w   #8,d0
        add.w   d0,d0
        move.w  (a3,d0.w),d1
        bra.s   .fast_store9
.fast_low9:
        cmpi.w  #255,d0
        bhi.s   .fast_both9
        add.w   d0,d0
        move.w  (a3,d0.w),d1
        addi.w  #$0808,d1
        bra.s   .fast_store9
.fast_both9:
        move.w  d0,d1
        lsr.w   #8,d1
        add.w   d1,d1
        move.w  (a3,d1.w),d1
        andi.w  #255,d0
        add.w   d0,d0
        move.w  (a3,d0.w),d0
        move.b  d0,d1
        addq.w  #8,d1
.fast_store9:
        move.w  #16,(a5)+
        move.w  d1,(a5)+                    ; relativo; solo indices presentes
.fast_translated9:
        add.w   d5,d1
        move.w  d1,16(a1)
        ori.w   #$0200,d4
.fast_done9:
        move.w  (a0)+,d0
        beq.s   .fast_done10
        tst.b   d0
        bne.s   .fast_low10
        lsr.w   #8,d0
        add.w   d0,d0
        move.w  (a3,d0.w),d1
        bra.s   .fast_store10
.fast_low10:
        cmpi.w  #255,d0
        bhi.s   .fast_both10
        add.w   d0,d0
        move.w  (a3,d0.w),d1
        addi.w  #$0808,d1
        bra.s   .fast_store10
.fast_both10:
        move.w  d0,d1
        lsr.w   #8,d1
        add.w   d1,d1
        move.w  (a3,d1.w),d1
        andi.w  #255,d0
        add.w   d0,d0
        move.w  (a3,d0.w),d0
        move.b  d0,d1
        addq.w  #8,d1
.fast_store10:
        move.w  #18,(a5)+
        move.w  d1,(a5)+                    ; relativo; solo indices presentes
.fast_translated10:
        add.w   d5,d1
        move.w  d1,18(a1)
        ori.w   #$0400,d4
.fast_done10:
        move.w  (a0)+,d0
        beq.s   .fast_done11
        tst.b   d0
        bne.s   .fast_low11
        lsr.w   #8,d0
        add.w   d0,d0
        move.w  (a3,d0.w),d1
        bra.s   .fast_store11
.fast_low11:
        cmpi.w  #255,d0
        bhi.s   .fast_both11
        add.w   d0,d0
        move.w  (a3,d0.w),d1
        addi.w  #$0808,d1
        bra.s   .fast_store11
.fast_both11:
        move.w  d0,d1
        lsr.w   #8,d1
        add.w   d1,d1
        move.w  (a3,d1.w),d1
        andi.w  #255,d0
        add.w   d0,d0
        move.w  (a3,d0.w),d0
        move.b  d0,d1
        addq.w  #8,d1
.fast_store11:
        move.w  #20,(a5)+
        move.w  d1,(a5)+                    ; relativo; solo indices presentes
.fast_translated11:
        add.w   d5,d1
        move.w  d1,20(a1)
        ori.w   #$0800,d4
.fast_done11:
        move.w  (a0)+,d0
        beq.s   .fast_done12
        tst.b   d0
        bne.s   .fast_low12
        lsr.w   #8,d0
        add.w   d0,d0
        move.w  (a3,d0.w),d1
        bra.s   .fast_store12
.fast_low12:
        cmpi.w  #255,d0
        bhi.s   .fast_both12
        add.w   d0,d0
        move.w  (a3,d0.w),d1
        addi.w  #$0808,d1
        bra.s   .fast_store12
.fast_both12:
        move.w  d0,d1
        lsr.w   #8,d1
        add.w   d1,d1
        move.w  (a3,d1.w),d1
        andi.w  #255,d0
        add.w   d0,d0
        move.w  (a3,d0.w),d0
        move.b  d0,d1
        addq.w  #8,d1
.fast_store12:
        move.w  #22,(a5)+
        move.w  d1,(a5)+                    ; relativo; solo indices presentes
.fast_translated12:
        add.w   d5,d1
        move.w  d1,22(a1)
        ori.w   #$1000,d4
.fast_done12:
        move.w  (a0)+,d0
        beq.s   .fast_done13
        tst.b   d0
        bne.s   .fast_low13
        lsr.w   #8,d0
        add.w   d0,d0
        move.w  (a3,d0.w),d1
        bra.s   .fast_store13
.fast_low13:
        cmpi.w  #255,d0
        bhi.s   .fast_both13
        add.w   d0,d0
        move.w  (a3,d0.w),d1
        addi.w  #$0808,d1
        bra.s   .fast_store13
.fast_both13:
        move.w  d0,d1
        lsr.w   #8,d1
        add.w   d1,d1
        move.w  (a3,d1.w),d1
        andi.w  #255,d0
        add.w   d0,d0
        move.w  (a3,d0.w),d0
        move.b  d0,d1
        addq.w  #8,d1
.fast_store13:
        move.w  #24,(a5)+
        move.w  d1,(a5)+                    ; relativo; solo indices presentes
.fast_translated13:
        add.w   d5,d1
        move.w  d1,24(a1)
        ori.w   #$2000,d4
.fast_done13:
        move.w  (a0)+,d0
        beq.s   .fast_done14
        tst.b   d0
        bne.s   .fast_low14
        lsr.w   #8,d0
        add.w   d0,d0
        move.w  (a3,d0.w),d1
        bra.s   .fast_store14
.fast_low14:
        cmpi.w  #255,d0
        bhi.s   .fast_both14
        add.w   d0,d0
        move.w  (a3,d0.w),d1
        addi.w  #$0808,d1
        bra.s   .fast_store14
.fast_both14:
        move.w  d0,d1
        lsr.w   #8,d1
        add.w   d1,d1
        move.w  (a3,d1.w),d1
        andi.w  #255,d0
        add.w   d0,d0
        move.w  (a3,d0.w),d0
        move.b  d0,d1
        addq.w  #8,d1
.fast_store14:
        move.w  #26,(a5)+
        move.w  d1,(a5)+                    ; relativo; solo indices presentes
.fast_translated14:
        add.w   d5,d1
        move.w  d1,26(a1)
        ori.w   #$4000,d4
.fast_done14:
        move.w  (a0)+,d0
        beq.s   .fast_done15
        tst.b   d0
        bne.s   .fast_low15
        lsr.w   #8,d0
        add.w   d0,d0
        move.w  (a3,d0.w),d1
        bra.s   .fast_store15
.fast_low15:
        cmpi.w  #255,d0
        bhi.s   .fast_both15
        add.w   d0,d0
        move.w  (a3,d0.w),d1
        addi.w  #$0808,d1
        bra.s   .fast_store15
.fast_both15:
        move.w  d0,d1
        lsr.w   #8,d1
        add.w   d1,d1
        move.w  (a3,d1.w),d1
        andi.w  #255,d0
        add.w   d0,d0
        move.w  (a3,d0.w),d0
        move.b  d0,d1
        addq.w  #8,d1
.fast_store15:
        move.w  #28,(a5)+
        move.w  d1,(a5)+                    ; relativo; solo indices presentes
.fast_translated15:
        add.w   d5,d1
        move.w  d1,28(a1)
        ori.w   #$8000,d4
.fast_done15:
        bra.w   .pack_epilogue
.return:
        movem.l (sp)+,d2-d7/a2-a6
        rts
        endif

        endif
