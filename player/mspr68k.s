;----------------------------------------------------------------------
; mspr68k.s - Etapa 6b.4: Mario en sprites de hardware, a mano. Hace lo
; mismo que mario_sprite() de player/mspr.c (que queda como referencia y
; para los casos raros) en el caso de siempre: las entradas de OAM que se
; ven son de 16x16, estan en la misma X, sin volteo vertical y no se
; tapan entre si (Mario: arriba y abajo). Entonces cada linea de 16 px de
; una pareja de sprites sale de dos filas de tiles de la SNES sin
; convertir nada: en un tile de 4 bpp la fila r tiene los planos 0-1 en
; la palabra 2r y los 2-3 en la 16 + 2r, y MOVEP.W escribe los bytes de
; una palabra en direcciones alternas: el tile izquierdo en los bytes
; altos de DATA/DATB, el derecho en los bajos. Volteo horizontal: los
; tiles de gfx32f (los bytes con los bits al reves, tools/mkmario.py) y
; el izquierdo y el derecho cambiados.
;
; Lo incluye player/game.s (a4 = binstart: datos del C por (a4)).
;----------------------------------------------------------------------

; --- mspr_draw ---
; entrada:  a2 = buffer de 4 sprites de MSPR_WORDS palabras, a4 = binstart
; salida:   como mario_sprite(a2, $2C, $A0)
; registros destruidos: d0-d7/a0-a3/a5-a6 (guarda a2 y a4)
;
; Cache (MA1). Solo si a2 es g_spra o g_sprb (los dos buffers del juego,
; que se alternan: lo que se escribe es el que no se esta mostrando); un
; buffer suelto (gamecheck.py) dibuja siempre. Cada buffer tiene una ficha
; (mspr_kA / mspr_kB) de lo que dejo escrito la ultima vez:
;   nivel 1: los punteros de tiles (wm_0D85 + wm_Tile7FPtr, 22 B), la OAM
;            de Mario (16 B) y mario_osz (4 B) son los mismos bytes que la
;            ultima vez -> el buffer ya esta bien, incluso SPRxPOS/CTL
;            (la posicion sale de esos bytes): no se hace nada.
;   nivel 2: misma pose con otra posicion (la clave: n + las entradas con
;            la y relativa a la caja + los punteros) -> solo SPR0/SPR1 POS y
;            CTL; los datos no dependen de la posicion.
;   nivel 3: otra pose, pero es la que tiene el otro buffer -> se copian sus
;            datos (se lee, no se toca) y se escriben POS y CTL.
;   si no, se dibuja. Cualquier otro camino que escriba el buffer (el C, Mario
;   oculto) invalida las dos fichas (mspr_inval).
; Los accesos a la RAM de la SNES son por bytes o por palabras/largos a
; direcciones pares: wm_0D85 esta en una direccion impar (_ram + $0D85).
        ifne    (_ram-binstart)&1
        fail    "_ram tiene que estar en una direccion par (MA1)"
        endc
        ifne    (_mario_oam-binstart)&1
        fail    "_mario_oam tiene que estar en una direccion par (MA1)"
        endc
        ifne    (_mario_osz-binstart)&1
        fail    "_mario_osz tiene que estar en una direccion par (MA1)"
        endc
mspr_draw:
        lea     mspr_kA(pc),a5
        cmp.l   g_spra(pc),a2
        beq.s   .s1
        lea     mspr_kB(pc),a5
        cmp.l   g_sprb(pc),a2
        beq.s   .s1
        suba.l  a5,a5                       ; buffer suelto: sin cache
        bra.s   .go
.s1:    tst.w   (a5)                        ; nivel 1 (primero la OAM, que es lo que
        beq.s   .go                         ; mas cambia: falla en el primer largo)
        lea     26(a5),a1
        lea     _mario_oam(a4),a0
        moveq   #3,d0
.l1b:   cmpm.l  (a0)+,(a1)+
        dbne    d0,.l1b
        bne.s   .go
        lea     _mario_osz(a4),a0
        cmpm.l  (a0)+,(a1)+
        bne.s   .go
        lea     3(a5),a1                    ; (+3: como _ram+$0D85, el largo cae en par)
        lea     _ram+$0D85(a4),a0
        cmpm.b  (a0)+,(a1)+
        bne.s   .go
        moveq   #4,d0
.l1a:   cmpm.l  (a0)+,(a1)+
        dbne    d0,.l1a
        bne.s   .go
        cmpm.b  (a0)+,(a1)+
        bne.s   .go
        ifd     SPR_G5
        ; Exponer la clave exacta de ESTA ficha sin volver a normalizar OAM.
        lea     46(a5),a0
        lea     3(a5),a1
        moveq   #1,d0
        endc
        rts                                 ; nada ha cambiado
.go:    lea     _mario_oam(a4),a0
        lea     _mario_osz(a4),a1
        lea     mspr_ent(pc),a3             ; entradas que se ven: y, tile, prop
        moveq   #0,d7                       ; cuantas
        move.l  d7,(a3)                     ; entradas sin usar = 0 (van en la clave)
        move.l  d7,4(a3)
        move.l  d7,8(a3)
        move.l  d7,12(a3)
        move.w  #$7fff,d5                   ; by: la y mas chica
        move.w  #-$7fff,d6                  ; y1: la mas grande + 16
        moveq   #3,d4                       ; entrada
.e:     move.b  1(a0),d1                    ; y
        cmp.b   #$f0,d1
        beq.s   .next
        btst    #1,(a1)                     ; 16x16
        beq     .slow
        btst    #7,3(a0)                    ; sin volteo vertical
        bne     .slow
        moveq   #0,d0                       ; x: 9 bits con signo
        move.b  (a0),d0
        btst    #0,(a1)
        beq.s   .x8
        sub.w   #256,d0
.x8:    ext.w   d1                          ; y: $F1-$FF = -15..-1 (d1.b)
        cmp.w   #-16,d1                     ; (la y va a d1.w)
        blt.s   .ypos
        bra.s   .yok
.ypos:  and.w   #$ff,d1
.yok:   tst.w   d7
        bne.s   .same
        move.w  d0,d3                       ; d3 = la x de todas
        bra.s   .add
.same:  cmp.w   d0,d3
        bne     .slow
.add:   move.w  d1,(a3)+                    ; y
        move.b  2(a0),(a3)+                 ; tile
        move.b  3(a0),(a3)+                 ; prop
        cmp.w   d5,d1
        bge.s   .b1
        move.w  d1,d5
.b1:    add.w   #16,d1
        cmp.w   d6,d1
        ble.s   .b2
        move.w  d1,d6
.b2:    addq.w  #1,d7
.next:  addq.l  #4,a0
        addq.l  #1,a1
        dbf     d4,.e

        lea     mspr_n(pc),a0
        move.w  d7,(a0)
        beq     .none
        move.w  d6,d0                       ; alto
        sub.w   d5,d0
        cmp.w   #MSPR_H,d0
        bhi     .slow
        ; que no se tapen: |y_i - y_j| >= 16 para cada par
        lea     mspr_ent(pc),a0
        move.w  d7,d1
        subq.w  #2,d1
        bmi.s   .ov2
.ov:    move.w  (a0),d2
        lea     4(a0),a1
        move.w  d1,d4
.ov1:   move.w  (a1),d0
        sub.w   d2,d0
        bpl.s   .abs
        neg.w   d0
.abs:   cmp.w   #16,d0
        blo     .slow
        addq.l  #4,a1
        dbf     d4,.ov1
        addq.l  #4,a0
        dbf     d1,.ov
.ov2:
        lea     mspr_ent(pc),a0             ; la y de las entradas relativa a la caja
        move.w  d7,d0
        subq.w  #1,d0
.nrm:   sub.w   d5,(a0)
        addq.l  #4,a0
        dbf     d0,.nrm
        ; --- cabeceras: SPR0/SPR1 (pareja), SPR2/SPR3 vacios -----------
        move.w  d6,d4
        sub.w   d5,d4                       ; d4 = n lineas
        move.w  d5,d0
        add.w   #$2c+1,d0                   ; vs (+1: la SNES dibuja una
        move.w  d0,d1                       ; linea mas abajo)
        add.w   d4,d1                       ; ve
        move.w  d3,d2
        add.w   #$a0,d2                     ; hs
        moveq   #0,d6                       ; POS
        move.b  d0,d6
        lsl.w   #8,d6
        move.w  d2,d7
        lsr.w   #1,d7
        move.b  d7,d6
        moveq   #0,d7                       ; CTL
        move.b  d1,d7
        lsl.w   #8,d7
        btst    #8,d0
        beq.s   .c1
        addq.w  #4,d7
.c1:    btst    #8,d1
        beq.s   .c2
        addq.w  #2,d7
.c2:    btst    #0,d2
        beq.s   .c3
        addq.w  #1,d7
.c3:    move.l  a2,a0                       ; SPR0
        lea     MSPR_WORDS*2(a2),a1         ; SPR1 (adosado)
        move.w  d6,(a0)+
        move.w  d7,(a0)+
        move.w  d6,(a1)+
        or.w    #$80,d7
        move.w  d7,(a1)+
        move.l  a5,d0                       ; (a5 = la ficha de este buffer, o 0)
        beq     .draw
        bsr     mspr_eq                     ; nivel 2: la misma pose en este buffer
        bne.s   .n2
        lea     26(a5),a1                   ; (la ficha vale y los punteros son los mismos:
        bra     .svo                        ; solo cambia la OAM)
.n2:    clr.w   (a5)                        ; la ficha se vuelve a poner al final (.ok)
        lea     46(a5),a1                   ; clave nueva: n + entradas (18 B)
        lea     mspr_n(pc),a0
        move.l  (a0)+,(a1)+
        move.l  (a0)+,(a1)+
        move.l  (a0)+,(a1)+
        move.l  (a0)+,(a1)+
        move.w  (a0)+,(a1)+
        lea     mspr_kB(pc),a6              ; nivel 3: la ficha del otro buffer
        cmp.l   a6,a5
        bne.s   .o1
        lea     mspr_kA(pc),a6
.o1:    move.l  a6,a5
        bsr     mspr_eq
        bne     .draw
        cmp.l   g_spra(pc),a2               ; es la pose del otro buffer: copiar sus datos
        bne.s   .o2
        move.l  g_sprb(pc),a3
        bra.s   .o3
.o2:    move.l  g_spra(pc),a3
.o3:    lea     4(a2),a0                    ; SPR0
        lea     4(a3),a1
        bsr.s   .cpy
        lea     MSPR_WORDS*2+4(a2),a0       ; SPR1
        lea     MSPR_WORDS*2+4(a3),a1
        bsr.s   .cpy
        clr.l   MSPR_WORDS*4(a2)            ; SPR2, SPR3: nada
        clr.l   MSPR_WORDS*6(a2)
        bra     .ok
; .cpy: (a1) -> (a0), n lineas + el final (d4 + 1 largos), de 8 en 8 con MOVEM
; (d0/d1/d2/d3/d5/d6/d7/a5/a6 libres; guarda d4/a2/a3)
.cpy:   move.w  d4,d0
        addq.w  #1,d0
.c8:    subq.w  #8,d0
        bmi.s   .cr
        movem.l (a1)+,d1/d2/d3/d5/d6/d7/a5/a6
        movem.l d1/d2/d3/d5/d6/d7/a5/a6,(a0)
        lea     32(a0),a0
        bra.s   .c8
.cr:    addq.w  #8-1,d0                     ; los que sobran
        bmi.s   .ce
.cl:    move.l  (a1)+,(a0)+
        dbf     d0,.cl
.ce:    rts
.draw:  move.w  d4,d0                       ; el final de SPR0 y SPR1 en 0
        lsl.w   #2,d0
        lea     4(a2,d0.w),a0
        clr.l   (a0)
        lea     MSPR_WORDS*2(a0),a1
        clr.l   (a1)
        clr.l   MSPR_WORDS*4(a2)            ; SPR2, SPR3: nada
        clr.l   MSPR_WORDS*6(a2)
        move.w  mspr_n(pc),d0               ; las entradas no se tapan: si 16 * n
        lsl.w   #4,d0                       ; es el alto de la caja no queda
        cmp.w   d4,d0                       ; ninguna linea sin cubrir y no hace
        beq.s   .cleared                    ; falta poner las lineas en 0
        lea     4(a2),a0                    ; lineas en 0
        lea     MSPR_WORDS*2+4(a2),a1
        move.w  d4,d0
        subq.w  #1,d0
.clr:   clr.l   (a0)+
        clr.l   (a1)+
        dbf     d0,.clr
.cleared:

        ; --- cada entrada: 16 lineas desde y - by -----------------------
        lea     mspr_ent(pc),a6
        moveq   #0,d7                       ; entrada
.ent:   cmp.w   mspr_n(pc),d7
        bhs     .ok
        move.w  (a6)+,d0                    ; y (ya relativa a la caja)
        lsl.w   #2,d0
        lea     4(a2,d0.w),a0               ; a0 = linea en SPR0
        lea     MSPR_WORDS*2(a0),a1         ; a1 = en SPR1
        moveq   #0,d6
        move.b  (a6)+,d6                    ; tile
        move.b  (a6)+,d2                    ; prop
        movem.l d5/d7/a6,-(sp)
        moveq   #0,d4                       ; fila de tiles (0: arriba, 16)
        ; camino corto (lo de siempre): tile par de 0 a 8 (los punteros de
        ; wm_0D85; la fila de abajo, t + 16, es el puntero + 10). El
        ; izquierdo y el derecho (t, t+1) son las dos mitades de lo que
        ; apunta el mismo puntero (+0 y +32): una busqueda en vez de dos
        ; (mspr_tile). d7 = 0: no vale (todo por el camino general, .gen),
        ; 1 / -1: sin voltear / volteado; a6 = puntero de la fila de la
        ; media pasada; d5 = donde empieza gfx32 (o gfx32f).
        moveq   #0,d7
        cmp.w   #8,d6
        bhi.s   .nofast
        btst    #0,d6
        bne.s   .nofast
        lea     _ram+$0D85(a4),a6
        add.w   d6,a6                       ; 2 * (t / 2)
        move.l  a4,d5
        btst    #6,d2
        bne.s   .fvf
        add.l   #gfx32-binstart,d5
        moveq   #1,d7
        bra.s   .nofast
.fvf:   add.l   #gfx32f-binstart,d5
        moveq   #-1,d7
.nofast:
.half:  tst.w   d7
        beq.s   .gen
        moveq   #0,d0                       ; R16 (la SNES: bajo primero)
        move.b  1(a6),d0
        lsl.w   #8,d0
        move.b  (a6),d0
        sub.w   #$2000,d0                   ; GFX32 en $7E:2000
        bcs.s   .gen
        cmp.w   #$5d00-64,d0                ; (los dos tiles: +0 y +32)
        bhi.s   .gen
        move.l  d5,a5
        add.w   d0,a5
        tst.w   d7
        bmi.s   .fv
        lea     32(a5),a3                   ; izquierdo: +0 (a5), derecho: +32
        bra.s   .rows
.fv:    move.l  a5,a3                       ; volteado: al reves
        add.w   #32,a5                      ; izquierdo: +32, derecho: +0
        bra.s   .rows
.gen:   move.w  d6,d0                       ; izquierdo: t + 16 fila
        add.w   d4,d0
        move.w  d0,d1
        addq.w  #1,d1                       ; derecho: + 1
        btst    #6,d2
        beq.s   .nf
        exg     d0,d1                       ; volteado: al reves
.nf:    bsr     mspr_tile
        beq     .slowp                      ; (no es de Mario)
        move.l  a3,a5                       ; a5 = izquierdo
        move.w  d1,d0
        bsr     mspr_tile
        beq     .slowp
                                            ; a3 = derecho
.rows:  ; las 8 filas del tile (desenrolladas: los desplazamientos van fijos)
mrow    set     0
        rept    8
        move.w  (a5)+,d1                    ; planos 0-1
        movep.w d1,mrow*4(a0)
        move.w  (a3)+,d1
        movep.w d1,mrow*4+1(a0)
        move.w  14(a5),d1                   ; planos 2-3
        movep.w d1,mrow*4(a1)
        move.w  14(a3),d1
        movep.w d1,mrow*4+1(a1)
mrow    set     mrow+1
        endr
        lea     32(a0),a0
        lea     32(a1),a1
        lea     10(a6),a6                   ; (fila 1: puntero + 10)
        add.w   #16,d4
        cmp.w   #32,d4
        blo     .half
        movem.l (sp)+,d5/d7/a6
        addq.w  #1,d7
        bra     .ent
.ok:    lea     mspr_kA(pc),a1              ; la ficha de este buffer: lo que quedo escrito
        cmp.l   g_spra(pc),a2
        beq.s   .sv
        lea     mspr_kB(pc),a1
        cmp.l   g_sprb(pc),a2
        bne.s   .rts
.sv:    move.w  #1,(a1)+
        addq.l  #1,a1                       ; a1 = ficha + 3
        lea     _ram+$0D85(a4),a0
        move.b  (a0)+,(a1)+
        movem.l (a0)+,d0-d4                 ; (con MOVEM: los dos en direcciones pares)
        movem.l d0-d4,(a1)
        lea     20(a1),a1
        move.b  (a0)+,(a1)+
        addq.l  #1,a1
.svo:   lea     _mario_oam(a4),a0
        movem.l (a0)+,d0-d3
        movem.l d0-d3,(a1)
        lea     16(a1),a1
        lea     _mario_osz(a4),a0
        move.l  (a0)+,(a1)+
.rts:
        ifd     SPR_G5
        ; Tambien vale para el buffer suelto: no hubo cache, pero mspr_n
        ; guarda la pose normalizada de esta llamada. Los punteros son CPU.
        lea     mspr_n(pc),a0
        lea     _ram+$0D85(a4),a1
        moveq   #1,d0
        endc
        rts

.none:  bsr.s   mspr_inval
        clr.l   (a2)                        ; Mario no se ve
        clr.l   MSPR_WORDS*2(a2)
        clr.l   MSPR_WORDS*4(a2)
        clr.l   MSPR_WORDS*6(a2)
        ifd     SPR_G5
        moveq   #0,d0                       ; sin clave: Mario oculto
        endc
        rts

.slowp: movem.l (sp)+,d5/d7/a6
.slow:  bsr.s   mspr_inval
        lea     mspr_slow(pc),a0            ; el caso raro: el C
        addq.w  #1,(a0)
        pea     $a0.w                       ; hx0
        pea     $2c.w                       ; vy0
        move.l  a2,-(sp)
        move.l  a4,a0
        add.l   #_mario_sprite-binstart,a0
        jsr     (a0)
        lea     12(sp),sp
        ifd     SPR_G5
        moveq   #0,d0                       ; sin clave: camino general del C
        endc
        rts

; mspr_inval: los buffers van a quedar escritos por otro camino: las dos
; fichas dejan de valer. Destruye a0.
mspr_inval:
        lea     mspr_kA(pc),a0
        clr.w   (a0)
        lea     mspr_kB(pc),a0
        clr.w   (a0)
        rts

; mspr_eq: a5 = una ficha. Z = 1 si el buffer de esa ficha tiene la pose
; de ahora (la ficha vale, la clave de mspr_n/mspr_ent es igual y los
; punteros de tiles tambien). Destruye d0/a0/a1.
mspr_eq:
        tst.w   (a5)
        bne.s   .v
        moveq   #1,d0                       ; Z = 0
        rts
.v:     lea     46(a5),a1
        lea     mspr_n(pc),a0
        moveq   #3,d0
.k:     cmpm.l  (a0)+,(a1)+
        dbne    d0,.k
        bne.s   .r
        cmpm.w  (a0)+,(a1)+
        bne.s   .r
        lea     3(a5),a1
        lea     _ram+$0D85(a4),a0
        cmpm.b  (a0)+,(a1)+
        bne.s   .r
        moveq   #4,d0
.p:     cmpm.l  (a0)+,(a1)+
        dbne    d0,.p
        bne.s   .r
        cmpm.b  (a0)+,(a1)+
.r:     rts

; mspr_tile: d0.w = tile de la VRAM de sprites -> a3 = sus 32 bytes en
; gfx32 (o gfx32f si d2 bit 6: volteado); Z = 1 si no es de Mario.
; Como vram_tile() de mspr.c. Destruye d0, a3 (guarda d1).
mspr_tile:
        move.l  d1,-(sp)
        cmp.w   #$7f,d0
        bne.s   .t1
        lea     _ram+$0D99(a4),a3           ; wm_Tile7FPtr
        moveq   #0,d1
        bra.s   .ptr
.t1:    cmp.w   #$20,d0
        bhs.s   .no
        move.w  d0,d1
        and.w   #15,d1
        cmp.w   #10,d1
        bhs.s   .no
        lsr.w   #1,d1
        add.w   d1,d1                       ; 2 * puntero
        btst    #4,d0
        beq.s   .r0
        add.w   #10,d1                      ; fila 1: wm_0D85 + 10
.r0:    lea     _ram+$0D85(a4),a3
        add.w   d1,a3
        moveq   #0,d1
        btst    #0,d0
        beq.s   .ptr
        moveq   #32,d1                      ; la segunda mitad
.ptr:   moveq   #0,d0                       ; R16 (la SNES: bajo primero)
        move.b  1(a3),d0
        lsl.w   #8,d0
        move.b  (a3),d0
        add.w   d1,d0
        sub.w   #$2000,d0                   ; GFX32 en $7E:2000
        bcs.s   .no
        cmp.w   #$5d00-32,d0
        bhi.s   .no
        move.l  a4,a3
        btst    #6,d2
        bne.s   .fl
        add.l   #gfx32-binstart,a3
        bra.s   .ad
.fl:    add.l   #gfx32f-binstart,a3
.ad:    add.w   d0,a3
        move.l  (sp)+,d1
        moveq   #1,d0                       ; Z = 0
        rts
.no:    move.l  (sp)+,d1
        moveq   #0,d0                       ; Z = 1
        rts

MSPR_H      equ 40                          ; mario.h: MSPR_LINES
mspr_n:     dc.w    0                       ; la clave de la pose de ahora: cuantas entradas
mspr_ent:   ds.w    4*2                     ; y (relativa), tile + prop (4 entradas)
; una ficha por buffer: +0 vale (1) / no (0); +3 punteros de tiles (22 B:
; el primer byte en +3 para que los largos caigan en direcciones pares, como
; en _ram+$0D85), +26 mario_oam (16 B), +42 mario_osz (4 B); +46 clave
; (n + 4 entradas, 18 B); 64 B
mspr_kA:    ds.w    32                      ; la de g_spra
mspr_kB:    ds.w    32                      ; la de g_sprb
mspr_slow:  dc.w    0                       ; veces que fue al C
        even
