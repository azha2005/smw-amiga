; Prototipo de viabilidad B35: solo se ensambla en el microbench opt-in.
; No sustituye g5_plan ni se incluye en el juego.
;
; --- _g5_trans_sparse ---
; entrada: pila vbcc: +4 = usos, +8 = salida (255 registros de 10 B).
;          usos: 15 grupos, indice 1..15; count.w, color inicial.w,
;          count registros (fila.w, color.w, ultimo_x.w), filas ordenadas.
; salida: d0 = numero de transiciones; $FFFF si excede 255.
;         registros (idx.b, 0.b, color.w, desde.w, xult.w, hasta.w).
; registros destruidos: d0/d1/a0/a1; preserva d2-d7/a2-a6.
; ciclos: medidos por tools/g5plan_work.py, sin DMA, incluyen llamada/ABI.
; Sin tablas, direcciones absolutas, estado global ni registros con dueno.
        ifd SPR_G5
        ifd G5_TRANS_BENCH
        public _g5_trans_sparse
_g5_trans_sparse:
        move.l  4(sp),a0
        move.l  8(sp),a1
        movem.l d2-d7,-(sp)
        moveq   #0,d0
        moveq   #1,d1
.group:
        move.w  (a0)+,d6
        move.w  (a0)+,d3
        tst.w   d6
        beq.s   .next
        subq.w  #1,d6
        moveq   #-1,d4
        move.w  #$7fff,d5
.use:
        move.w  (a0)+,d2
        move.w  (a0)+,d7
        cmp.w   d3,d7
        beq.s   .same
        cmpi.w  #255,d0
        beq.s   .overflow
        move.b  d1,(a1)+
        clr.b   (a1)+
        move.w  d7,(a1)+
        move.w  d4,(a1)+
        move.w  d5,(a1)+
        move.w  d2,(a1)+
        move.w  d7,d3
        addq.w  #1,d0
.same:
        move.w  d2,d4
        move.w  (a0)+,d5
        dbra    d6,.use
.next:
        addq.w  #1,d1
        cmpi.w  #16,d1
        bne.s   .group
        movem.l (sp)+,d2-d7
        rts
.overflow:
        move.w  #$ffff,d0
        movem.l (sp)+,d2-d7
        rts
        endif
        endif
