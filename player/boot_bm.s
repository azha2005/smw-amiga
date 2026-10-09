; BM1: bootblock propio, MFM directo, A501 obligatoria como en el juego.
; El bootblock se copia a C7F000; pila C7EF00, pista decodificada C7D000.
; El DMA de disco usa exclusivamente chip en 7A000 (13312 bytes).
        include "exec.i"
BM_CODE     equ $c7f000
BM_STACK    equ $c7ef00
BM_TRACK    equ $c7d000
BM_RAW      equ $7a000
BM_RAWLEN   equ 13312
bootblock:
        dc.b    "DOS",0
        dc.l    0
bb_stage2len: dc.l 0
        lea     CUSTOM,a4
        ; Detectar la expansion sin Exec ni escribir en datos del juego.
        move.l  #$13579bdf,$c7f000
        cmp.l   #$13579bdf,$c7f000
        bne     bm_fail
        move.l  #$2468ace0,$c7f000
        cmp.l   #$2468ace0,$c7f000
        bne     bm_fail
        ; P8: descartar ausencia y espejo de la expansion de 512 KB.
        move.l  #$13579bdf,$c00000
        move.l  #$2468ace0,$c80000
        cmp.l   #$13579bdf,$c00000
        bne     bm_fail
        lea     bm_trap(pc),a0
        move.l  a0,$80.w
        trap    #0
        move.w  #$2700,sr
        move.w  #$7fff,INTENA(a4)
        move.w  #$7fff,DMACON(a4)
        move.b  #$7f,$bfed01
        move.b  #$7f,$bfdd00
        lea     bootblock(pc),a0
        move.l  #BM_CODE,a1
        move.w  #1024/4-1,d0
.copy:  move.l  (a0)+,(a1)+
        dbf     d0,.copy
        move.l  #BM_STACK,sp
        jmp     BM_CODE+bm_start-bootblock
bm_trap:
        or.w    #$2000,(sp)
        rte
bm_start:
        ; TOD de CIA-A cuenta VBL PAL (50 Hz), no tiempo del host.
        bclr    #7,$bfef01
        clr.b   $bfea01
        clr.b   $bfe901
        clr.b   $bfe801
        lea     bm_loadsig(pc),a0
        move.l  a0,8(a0)
        lea     bm_cached(pc),a0
        move.w  #-1,(a0)
        or.b    #$f8,$bfd100
        and.b   #$7f,$bfd100                ; motor antes de seleccionar DF0
        and.b   #$f7,$bfd100
        move.w  #8000,d0                   ; ~512 ms: estabilizar motor
        bsr     bm_wait
        or.b    #6,$bfd100                 ; afuera, cara 0
        moveq   #83,d3
.home:  btst    #4,$bfe001                 ; /TK0
        beq.s   .at0
        bsr     bm_step
        dbf     d3,.home
        bra     bm_fail
.at0:   lea     bm_cyl(pc),a0
        clr.w   (a0)
        move.l  bb_stage2len(pc),d1
        lsr.l   #8,d1
        lsr.l   #1,d1
        moveq   #2,d0
        move.l  #$c00000,a0
        bsr     bm_read
        tst.l   d0
        bne     bm_fail
        bsr     bm_tod
        lea     bm_loadsig(pc),a0
        move.l  d0,12(a0)
        jmp     $c00000
; --- bm_read --- sectores crudos, con cache de pista y checksums MFM
; entrada: d0.w = primer sector, d1.w = cantidad, a0 = destino, a4 = CUSTOM
; salida: d0 = 0 o 1; preserva d2-d7/a2-a6
; registros destruidos: d0-d1/a0-a1
; ciclos: carga, medidos en WinUAE; no se ejecuta por frame
bm_read:
        movem.l d2-d7/a2-a6,-(sp)
        move.w  d0,d6
        move.w  d1,d7
        move.l  a0,a5
        subq.w  #1,d7
.sector:
        moveq   #0,d2
        move.w  d6,d2
        divu    #11,d2
        cmp.w   bm_cached(pc),d2
        beq.s   .cached
        move.l  d2,-(sp)
        bsr     bm_loadtrack
        move.l  (sp)+,d2
        tst.w   d0
        bne.s   .error
        lea     bm_cached(pc),a1
        move.w  d2,(a1)
.cached:
        swap    d2
        lsl.w   #8,d2
        add.w   d2,d2
        move.l  #BM_TRACK,a0
        add.w   d2,a0
        move.w  #128-1,d1
.data:  move.l  (a0)+,(a5)+
        dbf     d1,.data
        addq.w  #1,d6
        dbf     d7,.sector
        moveq   #0,d0
        bra.s   .return
.error: moveq   #1,d0
.return: movem.l (sp)+,d2-d7/a2-a6
        rts
; --- bm_loadtrack --- mecanica + DMA de una pista AmigaDOS DD
; entrada: d2.w = pista 0..159, a4 = CUSTOM
; salida: d0 = 0 o 1 (timeout/checksum/sectores ausentes)
; registros destruidos: d0-d5/a0-a3 (preserva d6-d7/a5-a6)
; ciclos: carga, no frame
bm_loadtrack:
        move.w  d2,d4
        lsr.w   #1,d4
        move.w  d4,d3
        sub.w   bm_cyl(pc),d3
        beq.s   .side
        bclr    #1,$bfd100
        tst.w   d3
        bpl.s   .in
        neg.w   d3
        bset    #1,$bfd100
.in:    subq.w  #1,d3
.seek:  bsr     bm_step
        dbf     d3,.seek
        lea     bm_cyl(pc),a1
        move.w  d4,(a1)
.side:  bset    #2,$bfd100
        btst    #0,d2
        beq.s   .settle
        bclr    #2,$bfd100
.settle: move.w #235,d0                    ; ~15 ms tras mover/cambiar cara
        bsr     bm_wait
        moveq   #2,d5                     ; hasta tres lecturas
.retry: movem.l d2/d5,-(sp)
        move.w  #$8210,DMACON(a4)
        move.w  #$4000,$024(a4)           ; parar DMA previo
        move.l  #BM_RAW,$020(a4)
        move.w  #$7f00,$09e(a4)
        move.w  #$9500,$09e(a4)           ; MFM, WORDSYNC, FAST DD
        move.w  #$4489,$07e(a4)
        move.w  #2,INTREQ(a4)
        move.w  #$8000+BM_RAWLEN/2,$024(a4)
        move.w  #$8000+BM_RAWLEN/2,$024(a4)
        move.w  #8000,d3
.dma:   btst    #1,INTREQR+1(a4)
        bne.s   .decoded
        moveq   #1,d0
        bsr     bm_wait
        dbf     d3,.dma
        moveq   #1,d0
        bra.s   .stop
.decoded:
        bsr     bm_decode
.stop:  move.w  #$4000,$024(a4)
        move.w  #$0010,DMACON(a4)
        movem.l (sp)+,d2/d5
        tst.w   d0
        beq.s   .done
        dbf     d5,.retry
.done:  rts
; --- bm_decode --- validar cabecera/datos y ordenar los once sectores
; entrada: BM_RAW = pista DMA, d2.w = pista esperada
; salida: BM_TRACK = 11 x 512 bytes, d0 = 0 o 1
; registros destruidos: d0-d5/a0-a3
; ciclos: carga; probado contra pistas sinteticas en Musashi
bm_decode:
        move.l  #BM_RAW,a0
        move.l  #BM_RAW+BM_RAWLEN-1080,a3
        moveq   #0,d5
.scan:  cmp.l   a3,a0
        bhi     .end
        cmp.w   #$4489,(a0)+
        bne.s   .scan
.sync:  cmp.w   #$4489,(a0)
        bne.s   .header
        addq.l  #2,a0
        bra.s   .sync
.header:
        move.l  a0,a2
        bsr     bm_long
        move.l  d0,d1
        swap    d1
        cmp.b   d2,d1
        bne.s   .scan
        lsr.w   #8,d1
        cmp.b   #$ff,d1
        bne.s   .scan
        lsr.w   #8,d0
        and.w   #255,d0
        cmp.w   #11,d0
        bhs.s   .scan
        move.w  d0,-(sp)
        move.l  a2,a1
        moveq   #0,d4
        moveq   #10-1,d3
.hcrc:  move.l  (a1)+,d0
        eor.l   d0,d4
        dbf     d3,.hcrc
        and.l   #$55555555,d4
        move.l  a1,a0
        bsr     bm_long
        cmp.l   d4,d0
        bne.s   .bad
        addq.l  #8,a0
        bsr     bm_long
        move.l  d0,d4                     ; checksum de datos decodificado
        lea     8(a0),a1
        move.l  a1,a0
        moveq   #0,d0
        move.w  #256-1,d3
.dcrc:  move.l  (a1)+,d1
        eor.l   d1,d0
        dbf     d3,.dcrc
        and.l   #$55555555,d0
        cmp.l   d4,d0
        bne.s   .bad
        move.w  (sp),d1
        bset    d1,d5
        lsl.w   #8,d1
        add.w   d1,d1
        move.l  #BM_TRACK,a1
        add.w   d1,a1
        move.w  #128-1,d3
.unmfm: move.l  (a0)+,d0
        and.l   #$55555555,d0
        add.l   d0,d0
        move.l  508(a0),d1
        and.l   #$55555555,d1
        or.l    d1,d0
        move.l  d0,(a1)+
        dbf     d3,.unmfm
.bad:   addq.l  #2,sp
        lea     1080(a2),a0
        bra     .scan
.end:   moveq   #0,d0
        cmp.w   #$7ff,d5
        beq.s   .ok
        moveq   #1,d0
.ok:    rts
; --- bm_long --- un longword impar/par contiguo (cabeceras/checksums)
; entrada: a0; salida d0; registros destruidos: d0-d1; ciclos: carga
bm_long:
        move.l  (a0),d0
        and.l   #$55555555,d0
        add.l   d0,d0
        move.l  4(a0),d1
        and.l   #$55555555,d1
        or.l    d1,d0
        rts
; --- bm_step/bm_wait --- pulso STEP y espera por lineas PAL
; entrada: bm_wait d0.w = lineas; salida ninguna
; registros destruidos: d0-d1; ciclos: espera hardware, 64 us por linea
bm_step:
        bclr    #0,$bfd100
        bset    #0,$bfd100
        moveq   #48,d0
bm_wait:
        subq.w  #1,d0
.line:  move.b  VHPOSR(a4),d1
.wait:  cmp.b   VHPOSR(a4),d1
        beq.s   .wait
        dbf     d0,.line
        rts
; --- bm_tod --- contador de VBL de CIA-A, lectura con latch
; entrada: ninguna; salida: d0 = ticks PAL desde el inicio del loader
; registros destruidos: d0; ciclos: carga, no frame
bm_tod:
        moveq   #0,d0
        move.b  $bfea01,d0
        lsl.l   #8,d0
        move.b  $bfe901,d0
        lsl.l   #8,d0
        move.b  $bfe801,d0
        rts
; --- bm_motoroff --- apagar DF0 y registrar fin de datos del nivel
; entrada: ninguna; salida: ninguna
; registros destruidos: d0/a0; ciclos: carga, no frame
bm_motoroff:
        or.b    #$f8,$bfd100
        bsr     bm_tod
        lea     bm_loadsig(pc),a0
        move.l  d0,16(a0)
        rts
bm_fail:
        move.w  #$7fff,INTENA(a4)
        move.w  #$7fff,DMACON(a4)
        move.w  #$f00,COLOR00(a4)
.halt:  bra.s   .halt
bm_cached: dc.w -1
bm_cyl: dc.w 0
bm_loadsig: dc.b "BMLOAD!!"
        dc.l    0,0,0                    ; self, fin stage2, fin datos
bm_end:
        ifgt    bm_end-bootblock-1024
        fail    "BM1: el bootblock MFM supera 1024 bytes"
        endc
