;----------------------------------------------------------------------
; G0: banco de reuso de los ocho sprites a 256 px / DPF de seis planos.
; tools/g0bench.py genera los datos sinteticos, los casos y el comparador.
; Todo lo que lee el DMA se copia a chip y se reloca antes de tomar la A500.
; La CPU mide tambien copiar 1408 B de chip a chip con MOVEM, en pantalla
; y en el borrado vertical. Los resultados son barras binarias del copper.
;----------------------------------------------------------------------
        include "exec.i"
CIAB_TALO equ $bfd400
CIAB_TAHI equ $bfd500
CIAB_CRA  equ $bfde00
CIAB_ICR  equ $bfdd00

        bra.w entry
        dc.b "A5PL"
        dc.l 0,0
entry:
        move.l 4.w,a6
        lea CUSTOM,a4
        lea vars(pc),a5
        move.l #g0_blob_end-g0_blob+2816,d0
        move.l #MEMF_CHIP|MEMF_CLEAR,d1
        jsr _LVOAllocMem(a6)
        tst.l d0
        beq fail
        move.l d0,(a5)
        move.l d0,a1
        lea g0_blob(pc),a0
        move.w #(g0_blob_end-g0_blob)/4-1,d7
.copy: move.l (a0)+,(a1)+
        dbf d7,.copy
        lea g0_reloc(pc),a0
        move.l (a5),a2
        move.w #G0_NRELOC-1,d7
.reloc:
        move.l (a0)+,d1
        move.l (a0)+,d0
        add.l a2,d0
        move.l a2,a1
        add.l d1,a1
        swap d0
        move.w d0,(a1)
        swap d0
        move.w d0,4(a1)
        dbf d7,.reloc

        jsr _LVOForbid(a6)
        lea gfxname(pc),a1
        moveq #0,d0
        jsr _LVOOpenLibrary(a6)
        tst.l d0
        beq.s .nogfx
        move.l d0,a6
        sub.l a1,a1
        jsr _LVOLoadView(a6)
        jsr _LVOWaitTOF(a6)
        jsr _LVOWaitTOF(a6)
.nogfx:
        move.l 4.w,a6
        move.w #$7fff,INTENA(a4)
        move.w #$7fff,INTREQ(a4)
        move.w #$7fff,DMACON(a4)
        move.l (a5),COP1LC(a4)
        move.w #0,COPJMP1(a4)
        move.w #$83e0,DMACON(a4)
        move.b #$7f,CIAB_ICR
        move.b #0,CIAB_CRA
        move.b #$ff,CIAB_TALO
        move.b #$ff,CIAB_TAHI
        move.b #$11,CIAB_CRA
        move.w #$a55a,8(a5)
        move.w #80,d0
        bsr waitline
        move.w #81,d0
        bsr waitline
        move.w #80,d0
        bsr waitline
        bsr readtimer
        move.w d0,4(a5)
        move.w #81,d0
        bsr waitline
        move.w #80,d0
        bsr waitline
        bsr readtimer
        sub.w d0,4(a5)
        move.w 4(a5),10(a5)
        lea empty(pc),a3
        move.w #96,d6
        bsr measure
        move.w d4,12(a5)
        lea copy1408(pc),a3
        move.w #96,d6
        bsr measure
        move.w d4,14(a5)
        lea empty(pc),a3
        move.w #280,d6
        bsr measure
        move.w d4,16(a5)
        lea copy1408(pc),a3
        move.w #280,d6
        bsr measure
        move.w d4,18(a5)
        bsr publish
.forever:
        bra.s .forever
fail:
        move.w #$0f00,COLOR00(a4)
        bra.s fail

; --- waitline ---
; entrada: d0 = linea PAL
; salida: ninguna
; registros destruidos: d1
; ciclos: espera sincronizada; no entra en la medida de la copia
waitline:
.w:     move.l VPOSR(a4),d1
        lsr.l #8,d1
        and.w #$1ff,d1
        cmp.w d0,d1
        bne.s .w
        rts

; --- readtimer ---
; entrada: ninguna
; salida: d0 = timer CIA-B
; registros destruidos: d1-d2
; ciclos: coste incluido en empty y restado por el lector
readtimer:
.r:     moveq #0,d0
        move.b CIAB_TAHI,d0
        move.b CIAB_TALO,d1
        move.b CIAB_TAHI,d2
        cmp.b d0,d2
        bne.s .r
        lsl.w #8,d0
        move.b d1,d0
        rts

measure:
        moveq #0,d4
        moveq #31,d7
.loop:
        move.w d6,d0
        bsr waitline
        bsr readtimer
        move.w d0,6(a5)
        movem.l d4-d7/a3,-(sp)
        jsr (a3)
        movem.l (sp)+,d4-d7/a3
        bsr readtimer
        move.w 6(a5),d1
        sub.w d0,d1
        cmp.w d4,d1
        bls.s .no
        move.w d1,d4
.no:
        move.w d6,d0
        addq.w #1,d0
        bsr waitline
        dbf d7,.loop
        rts
empty:
        rts

; --- copy1408 ---
; entrada: a5 = variables con la base de chip
; salida: ninguna
; registros destruidos: d0-d7/a0-a1
; ciclos: medidos con CIA-B en pantalla y en el borrado vertical
copy1408:
        move.l (a5),a0
        add.l #g0_blob_end-g0_blob,a0
        lea 1408(a0),a1
        rept 44
        movem.l (a0)+,d0-d7
        movem.l d0-d7,(a1)
        lea 32(a1),a1
        endr
        rts

; --- publish ---
; entrada: a5 = variables; g0_bits = offsets de los MOVE de las barras
; salida: ninguna
; registros destruidos: d0-d2/d6-d7/a0-a2
; ciclos: fuera de la medida; se publica despues de terminar las 128 copias
publish:
        lea g0_bits(pc),a0
        bsr.s .rows
        lea g0_bits_second(pc),a0
.rows:
        lea 8(a5),a1
        moveq #5,d7
.row:
        move.w (a1)+,d0
        moveq #15,d6
.bit:
        move.l (a0)+,d1
        move.l (a5),a2
        add.l d1,a2
        moveq #0,d2
        add.w d0,d0
        bcc.s .zero
        move.w #$0fff,d2
.zero:
        move.w d2,(a2)
        dbf d6,.bit
        dbf d7,.row
        rts
gfxname:
        dc.b "graphics.library",0
        even
vars:
        ds.b 20
        cnop 0,4
        include "work/bench_g0_data.i"
