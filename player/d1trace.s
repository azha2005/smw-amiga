; D1 experimental: solo REPLAY/BENCH, DMA intacto, traza en slow.
D1_CAP      equ 4600
D1_ROW      equ 20
D1_HDR      equ 32
D1_EVENTS   equ D1_HDR+D1_CAP*D1_ROW
D1_EVENT    equ 12
D1_BYTES    equ D1_EVENTS+D1_CAP*D1_EVENT
D1_TBLO     equ $bfd600
D1_TBHI     equ $bfd700
D1_CRB      equ $bfdf00
; --- d1_timer_init ---
; entrada: timer A continuo de BENCH; salida: TB cuenta sus underflows
; registros destruidos: ninguno; ciclos: pendientes de medida cycle-exact
d1_timer_init:
        move.b  #0,D1_CRB
        move.b  #$ff,D1_TBLO
        move.b  #$ff,D1_TBHI
        move.b  #$51,D1_CRB
        rts
        ifd     D1TRACE
; --- d1_time ---
; salida: d0.l contador descendente TB:TA coherente
; registros destruidos: d0-d3; ciclos: pendientes de medida cycle-exact
d1_time:
.r:     moveq   #0,d0
        moveq   #0,d1
        moveq   #0,d2
        move.b  D1_TBHI,d1
        move.b  D1_TBLO,d2
        move.b  CIAB_TAHI,d3
        move.b  CIAB_TALO,d0
        cmp.b   CIAB_TAHI,d3
        bne.s   .r
        cmp.b   D1_TBLO,d2
        bne.s   .r
        cmp.b   D1_TBHI,d1
        bne.s   .r
        lsl.w   #8,d1
        move.b  d2,d1
        swap    d1
        lsl.w   #8,d3
        move.b  d0,d3
        move.w  d3,d1
        move.l  d1,d0
        rts
; --- d1_init ---
; salida: traza slow acotada; registros destruidos: ninguno
; ciclos: fuera del tramo medido (AllocMem)
d1_init:
        movem.l d0-d3/a0-a1/a6,-(sp)
        move.l  #D1_BYTES,d0
        move.l  #MEMF_FAST+MEMF_CLEAR,d1
        move.l  4.w,a6
        jsr     _LVOAllocMem(a6)
        lea     d1_ptr(pc),a0
        move.l  d0,(a0)
        beq.s   .bad
        cmp.l   #$c00000,d0
        blo.s   .bad
        move.l  d0,d1
        add.l   #D1_BYTES,d1
        cmp.l   #$c80000,d1
        bhi.s   .bad
        move.l  d0,a1
        move.l  #$44315452,(a1)
        move.w  #2,4(a1)
        move.w  #D1_ROW,6(a1)
        move.l  #D1_CAP,8(a1)
        move.l  d0,28(a1)
        move.w  gb_tpf(pc),20(a1)
        bsr     d1_time
        move.l  d0,-(sp)
        bsr     d1_time
        move.l  (sp)+,d1
        sub.l   d0,d1
        move.l  d1,24(a1)
.out:   movem.l (sp)+,d0-d3/a0-a1/a6
        rts
.bad:   move.w  #$0f00,COLOR00(a4)
        bra.s   .bad
; --- d1_tick_start ---
; entrada/salida: conserva registros; ciclos: pendientes cycle-exact
d1_tick_start:
        movem.l d0-d3/a0,-(sp)
        bsr     d1_time
        lea     d1_tick_t0(pc),a0
        move.l  d0,(a0)
        movem.l (sp)+,d0-d3/a0
        rts
; --- d1_photo_start ---
; entrada/salida: conserva registros; ciclos: pendientes cycle-exact
d1_photo_start:
        movem.l d0-d3/a0,-(sp)
        bsr     d1_time
        lea     d1_cap_t0(pc),a0
        move.l  d0,(a0)
        movem.l (sp)+,d0-d3/a0
        rts
; --- d1_tick_end ---
; entrada: DC_NEW recien capturado; salida: contador TERMINADO
; registros destruidos: ninguno; ciclos: pendientes cycle-exact
d1_tick_end:
        movem.l d0-d3/a0-a1,-(sp)
        bsr     d1_time
        lea     d1_tick_last(pc),a0
        move.l  d1_tick_t0(pc),d1
        sub.l   d0,d1
        move.l  d1,(a0)
        move.l  d0,-(sp)
        move.l  d1,-(sp)
        move.l  d1_ptr(pc),a1
        move.l  a1,d0
        beq.s   .noevent
        moveq   #0,d0
        move.w  22(a1),d0
        cmp.w   #D1_CAP,d0
        blo.s   .evroom
        move.w  #1,18(a1)
        bra.s   .noevent
.evroom:
        mulu    #D1_EVENT,d0
        move.l  a1,a0
        add.l   #D1_EVENTS,a0
        adda.l  d0,a0
        moveq   #0,d0
        move.w  d1_completed(pc),d0
        addq.l  #1,d0
        move.l  d0,(a0)+
        move.l  (sp),(a0)+
        move.l  4(sp),(a0)+
        addq.w  #1,22(a1)
.noevent:
        addq.l  #8,sp
        lea     d1_completed(pc),a0
        addq.w  #1,(a0)
        move.w  dc_st+DC_NEW(pc),d1
        lsl.w   #2,d1
        lea     d1_photo_t0(pc),a1
        move.l  d1_cap_t0(pc),0(a1,d1.w)
        movem.l (sp)+,d0-d3/a0-a1
        rts
; --- d1_publish ---
; entrada: d7 foto; salida: duracion integrada, antes de DC_PEND atomico
; registros destruidos: ninguno; ciclos: pendientes cycle-exact
d1_publish:
        movem.l d0-d3/a0,-(sp)
        bsr     d1_time
        move.w  d7,d1
        lsl.w   #2,d1
        lea     d1_photo_t0(pc),a0
        move.l  0(a0,d1.w),d2
        sub.l   d0,d2
        lea     d1_photo_dt(pc),a0
        move.l  d2,0(a0,d1.w)
        movem.l (sp)+,d0-d3/a0
        rts
; --- d1_vbl ---
; entrada: despues dc_vb (FRONT ya puesto); salida: una fila por VBL
; registros destruidos: ninguno; ciclos: pendientes cycle-exact
d1_vbl:
        movem.l d0-d5/a0-a2,-(sp)
        move.l  d1_ptr(pc),a1
        move.l  a1,d0
        beq     .out
        move.l  12(a1),d4
        cmp.l   #D1_CAP,d4
        blo.s   .room
        move.w  #1,18(a1)
        bra     .out
.room:  bsr     d1_time
        move.l  d4,d5
        mulu    #D1_ROW,d5
        lea     D1_HDR(a1),a0
        adda.l  d5,a0
        move.l  d4,(a0)+
        move.w  d1_completed(pc),(a0)+
        move.w  dc_st+DC_FRONT(pc),d1
        move.w  d1,d2
        mulu    #DC_REC,d2
        lea     dc_rec(pc),a2
        move.w  R_FRAME(a2,d2.w),(a0)+
        lsl.w   #2,d1
        lea     d1_photo_dt(pc),a2
        move.l  0(a2,d1.w),(a0)+
        move.l  d1_tick_last(pc),(a0)+
        move.l  d0,(a0)+
        addq.l  #1,12(a1)
.out:   movem.l (sp)+,d0-d5/a0-a2
        rts
; --- d1_stop ---
; entrada: IRQ ya apagada gb_show; salida: dump marcado completo
; registros destruidos: ninguno; ciclos: fuera del tramo
d1_stop:
        move.l  a0,-(sp)
        move.l  d1_ptr(pc),a0
        move.l  d0,-(sp)
        move.l  a0,d0
        beq.s   .out
        move.w  #1,16(a0)
.out:   move.l  (sp)+,d0
        move.l  (sp)+,a0
        rts
        cnop    0,4
d1_ptr:        dc.l 0
d1_tick_t0:    dc.l 0
d1_cap_t0:     dc.l 0
d1_tick_last:  dc.l 0
d1_completed:  dc.w 0
        cnop    0,4
d1_photo_t0:   ds.l NSPRB
d1_photo_dt:   ds.l NSPRB
        endc
