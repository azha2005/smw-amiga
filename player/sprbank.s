; --- sg3_load ---
; entrada: a2 = IOStdReq, d7 = hdr_data_off, a6 = ExecBase
; salida: d0 = 0 valido; 1 error. sg3_dma chip, sg3_tables slow.
; registros destruidos: d0-d1/a0-a1; conserva ABI vbcc
; ciclos: solo arranque; sin trabajo por frame (CRC completo y DoIO)
; Banco inmutable: G5 nunca escribe controles compartidos (P108).
; La estructura se verifica offline antes de empaquetar; CRC32 comprueba
; TODOS los bytes contra aquella estructura verificada, antes de publicar.
SG3_SCRATCH_BYTES equ 512
sg3_load:
        movem.l d2-d7/a2-a6,-(sp)
        move.l  #SG3_DMA_ALLOC,d0
        move.l  #MEMF_CHIP,d1
        jsr     _LVOAllocMem(a6)
        tst.l   d0
        beq     .bad
        move.l  d0,a3
        move.l  d0,d1
        and.l   #7,d1
        bne     .bad
        add.l   #SG3_DMA_ALLOC,d0
        cmp.l   #$80000,d0
        bhi     .bad
        move.l  a3,IO_DATA(a2)
        move.l  #SG3_DMA_ALLOC,IO_LENGTH(a2)
        move.l  d7,d0
        add.l   #SG3_DMA_REL,d0
        move.l  d0,IO_OFFSET(a2)
        bsr     sg3_read
        tst.l   d0
        bne     .bad
        move.l  a3,a0
        move.l  #SG3_DMA_BYTES,d1
        bsr     sg3_crc
        cmp.l   #SG3_DMA_CRC,d0
        bne     .bad
        move.l  a3,d6
        move.l  #SG3_TABLE_ALLOC,d0
        move.l  #MEMF_FAST,d1
        jsr     _LVOAllocMem(a6)
        tst.l   d0
        beq     .bad
        move.l  d0,a5
        move.l  d0,d1
        and.l   #7,d1
        bne     .bad
        cmp.l   #$c00000,d0
        blo     .bad
        add.l   #SG3_TABLE_ALLOC,d0
        cmp.l   #$c80000,d0
        bhi     .bad
        move.l  #SG3_SCRATCH_BYTES,d0
        move.l  #MEMF_CHIP,d1
        jsr     _LVOAllocMem(a6)
        tst.l   d0
        beq     .bad
        move.l  d0,a4
        move.l  d0,d1
        and.l   #7,d1
        bne     .bad
        add.l   #512,d0
        cmp.l   #$80000,d0
        bhi     .bad
        move.l  #SG3_TABLE_BYTES,d2
        move.l  a5,a3
        add.l   #SG3_TABLE_REL,d7
.sector:
        move.l  a4,IO_DATA(a2)
        move.l  #512,IO_LENGTH(a2)
        move.l  d7,IO_OFFSET(a2)
        bsr     sg3_read
        tst.l   d0
        bne     .bad
        move.l  #512,d3
        cmp.l   d3,d2
        bhs.s   .full
        move.l  d2,d3
.full:
        sub.l   d3,d2
        move.l  a4,a0
        subq.w  #1,d3
.copy:  move.b  (a0)+,(a3)+
        dbra    d3,.copy
        add.l   #512,d7
        tst.l   d2
        bne.s   .sector
        move.l  a4,a1
        move.l  #512,d0
        jsr     _LVOFreeMem(a6)
        move.l  a5,a0
        move.l  #SG3_TABLE_BYTES,d1
        bsr     sg3_crc
        cmp.l   #SG3_TABLE_CRC,d0
        bne.s   .bad
        cmp.l   #$53473346,(a5)             ; SG3F/2 exacto
        bne.s   .bad
        cmp.w   #2,4(a5)
        bne.s   .bad
        ; Publicar solo tras CRC de los dos ficheros.
        lea     sg3_dma(pc),a0
        move.l  d6,(a0)
        lea     sg3_tables(pc),a0
        move.l  a5,(a0)
        moveq   #0,d0
        movem.l (sp)+,d2-d7/a2-a6
        rts
.bad:
        moveq   #1,d0
        movem.l (sp)+,d2-d7/a2-a6
        rts

; --- sg3_read ---
; entrada: a2 IOStdReq listo; salida: d0 error DoIO
; registros destruidos: d0-d1/a0-a1; ciclos: arranque, E/S de disco
sg3_read:
        move.l  a2,a1
        move.w  #CMD_READ,IO_COMMAND(a1)
        jsr     _LVODoIO(a6)
        tst.l   d0
        bne.s   .out
        move.l  IO_ACTUAL(a2),d0
        cmp.l   IO_LENGTH(a2),d0
        beq.s   .ok
        moveq   #1,d0
        bra.s   .out
.ok:    moveq   #0,d0
.out:
        rts

; --- sg3_crc ---
; entrada: a0 bytes, d1 longitud; salida: d0 CRC32 IEEE
; registros destruidos: d0-d1/a0; ciclos: arranque (~bit a bit)
sg3_crc:
        movem.l d2-d3,-(sp)
        moveq   #-1,d0
.byte:
        moveq   #0,d2
        move.b  (a0)+,d2
        eor.l   d2,d0
        moveq   #7,d3
.bit:
        lsr.l   #1,d0
        bcc.s   .next
        eor.l   #$edb88320,d0
.next:
        dbra    d3,.bit
        subq.l  #1,d1
        bne.s   .byte
        not.l   d0
        movem.l (sp)+,d2-d3
        rts

        cnop    0,4
sg3_dma:       dc.l 0
sg3_tables:    dc.l 0
