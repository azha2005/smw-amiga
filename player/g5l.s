;----------------------------------------------------------------------
; g5l.s - G5L: el Rex en los sprites 4-7 con un plan de color por filas
; (docs/informe-g5l.md; referencia: tools/g5l.py, que tiene que dar las
; mismas palabras en la lista: python tools/g5l.py game).
;
; Modelo de copper: el de G2T-A (tools/g2t_ref.py, medido en WinUAE). El
; plan no mira pixeles: mascaras de indices por fila (Mario desde sus
; fichas de GFX32, el Rex desde la tabla G5L2) y el borde derecho de cada
; figura. Las recargas de COLOR17-31 van al final del segmento de la fila,
; en el borrado horizontal (WAIT $D0), con una capacidad que no necesita
; leer la lista: 12 - nb sin cargas, 10 - nb con cargas (nb = el borrado
; de la fila siguiente). Lo que no entra se coloca con el plan exacto de
; g2t_ref.schedule recorriendo solo ese segmento.
;
; La lista que se escribe guarda sufijos de hace dos frames en las lineas
; que build_mid no reescribio: g5l_clean los quita (repone el salto) si
; las dos primeras palabras largas siguen siendo las nuestras. build_mid
; nunca escribe COLOR16-31, asi que no hay falso positivo; el relleno de
; una cadena es MOVE COLOR16 (no se ve: el indice 0 de un sprite).
;----------------------------------------------------------------------
G5L_MAXREX  equ 4
G5L_MAXT    equ 6
G5L_RECSZ   equ 6+5*G5L_MAXT                ; .b ranura .b n .w x .w y fichas
; la foto (dc_rec + R_G5L)
G5F_MOAM    equ 0                           ; mario_oam (16)
G5F_MOSZ    equ 16                          ; mario_osz (4)
G5F_PTRS    equ 20                          ; RAM $0D84..$0D9B (24): $0D85+o en +1+o
G5F_CAMX    equ 44
G5F_CAMY    equ 46
G5F_NREX    equ 48
G5F_REX     equ 50
G5F_SIZE    equ G5F_REX+G5L_MAXREX*G5L_RECSZ
        ifne    G5F_SIZE-194
        fail    "G5F_SIZE distinto del DC_REC de game.s"
        endc

G5L_MAXTR   equ 200                         ; transiciones
G5L_NPOOL   equ 32                          ; segmentos con sufijo
G5L_VBLN    equ 15
G5L_NONE    equ $8000                       ; "sin carga" en last
G5L_WRAP    equ 255-$2c                     ; el segmento que cruza la 255
G5L_RSTR    equ 136                         ; un flujo del bufer: POS/CTL, 32 filas, fin
        ifnd    G5L_MAXPL
G5L_MAXPL   equ 1                           ; G4-2: Rex ubicados por foto; 2 con -DG5L_MAXPL=2
        endc                                ; (apagado: empeora D1, informe-g4-2-1010.md)
G5L_CSTR    equ 264                         ; flujo de cadena: 2 x 32 filas, POS/CTL, fin
        ifeq    G5L_MAXPL-1
G5L_LBLK    equ 4*G5L_RSTR                  ; por lista: las bandas del Rex
        else
G5L_LBLK    equ 4*(2*G5L_RSTR+G5L_CSTR)     ; por lista: bandas del Rex 0 y 1, cadena
        endc
        ifd     CUSHION
G5L_RBUF_SIZE equ 3*G5L_LBLK                ; tres listas (chip)
        else
G5L_RBUF_SIZE equ 2*G5L_LBLK                ; dos listas (chip)
        endc
G5L_NRUN    equ 96                          ; tramos de un indice (g5l_sweepn)
; candidato (GV_CAND, g5l_choose: por fila y ranura)
CA_R0       equ 0
CA_X0       equ 2
CA_VL       equ 4                           ; .l lista de variantes
CA_NV       equ 8
CA_SL       equ 10                          ; ranura
CA_H        equ 12                          ; alto (la primera variante)
CA_DEAD     equ 14                          ; .b sin variante (bob 'color')
CASZ        equ 16
; Rex ubicado (GV_RX, camino de varios)
RX_R0       equ 0
RX_X0       equ 2
RX_SLOT     equ 4
RX_XR       equ 6                           ; borde derecho (<= 255)
RX_VAR      equ 8                           ; .l
RX_NREM     equ 12
RX_RH       equ 14
RX_NG       equ 16
RX_DM       equ 18                          ; .w indices con un grupo de otro color que Mario
RX_IXS      equ 20                          ; 16 .b: primer grupo de cada indice
RX_IXN      equ 36                          ; 16 .b: cuantos
RX_REM      equ 52                          ; G5L_NREM x 8 (GV_REM)
RX_G        equ RX_REM+8*G5L_NREM           ; RX_NG x (.b i, .b 0, .w color, .l filas)
RX_MSH      equ 252                         ; .w r0 - fila 0 de la cache de Mario
RXSZ        equ 256                         ; (lsl #8)
G5L_NREM    equ 5                           ; bandas reasignadas
        ifgt    RX_G+8*(15+G5L_NREM)-RX_MSH
        fail    "G4-2: RX_G no tiene lugar para 15 grupos + las bandas"
        endc
; entrada del pool
P_S         equ 0                           ; .w segmento
P_N         equ 2                           ; .b MOVE
P_WALK      equ 3                           ; .b recorrido
P_MAXN      equ 4                           ; .w el mayor need (clr.l P_N lo borra)
P_LAST      equ 6                           ; .w
P_FREE      equ 8                           ; .w
P_J         equ 10                          ; .l salto
P_MV        equ 14                          ; 9 x (.w registro, .w color, .w need, .w 0)
PSZ         equ 128                         ; (lsl #7)
; transicion (GV_TRB): .b i .b duenos .w color .w desde .w hasta
; variables (g5l_v)
GV_NB       equ 0                           ; 224 B: nb de cada linea
GV_SEGIX    equ GV_NB+LINES                 ; 224 B: entrada del pool + 1
GV_E        equ GV_SEGIX+LINES              ; 8 .w: bordes por duenos (bit 0 Mario, k+1 Rex k)
GV_TRB      equ GV_E+16                      ; 5 cubetas x G5L_MAXTR transiciones
GV_VBL      equ GV_TRB+5*8*G5L_MAXTR        ; 15 x (.w registro, .w color)
GV_POOL     equ GV_VBL+4*G5L_VBLN
GV_RECA     equ GV_POOL+PSZ*G5L_NPOOL       ; .w n + n x (.l J, .l w0, .l w1, .w s)
GV_RECB     equ GV_RECA+2+16*G5L_NPOOL
        ifd     CUSHION
GV_RECC     equ GV_RECB+2+16*G5L_NPOOL      ; la C (game.s -DCUSHION)
GV_KEY      equ GV_RECC+2+16*G5L_NPOOL      ; clave del Rex: 4 B por ficha
        else
GV_KEY      equ GV_RECB+2+16*G5L_NPOOL      ; clave del Rex: 4 B por ficha
        endc
GV_ENT      equ GV_KEY+4*G5L_MAXT           ; 4 x (.w ex, .w ey, .b tile, .b attr, .w nt)
GV_MISS     equ GV_ENT+32                   ; .l transiciones para el pase 2
GV_BP       equ GV_MISS+4*G5L_MAXTR         ; 5 .l: fin de cada cubeta
GV_BS       equ GV_BP+20                    ; 5 .l: su principio (g5l_init)
GV_ROOM     equ GV_BS+20                    ; 224 B: lugar a ciegas que queda
GV_CAPNL    equ GV_ROOM+LINES               ; 224 B: 12 - nb siguiente, o 0
GV_WK       equ GV_CAPNL+LINES              ; 224 B: sello del recorrido
GV_W        equ GV_WK+LINES                 ; 224 x (.w last, .w free, .l J)
GV_TAB      equ GV_W+8*LINES                ; .l tabla
GV_TT       equ GV_TAB+4                    ; .l fichas traspuestas de la tabla
GV_LIST     equ GV_TT+4                     ; .l lista
GV_REC      equ GV_LIST+4                   ; .l registros de esa lista
GV_VAR      equ GV_REC+4                    ; .l variante (la limpia)
GV_COL      equ GV_VAR+4                    ; .l paleta de Mario (16 .w)
GV_VLIST    equ GV_COL+4                    ; .l variantes de la forma
GV_RBUF     equ GV_VLIST+4                  ; .l bufer de chip de esta lista
GV_WBASE    equ GV_RBUF+4                   ; .w fila de la fila 0 de la cache
GV_XM       equ GV_WBASE+2
GV_NV       equ GV_XM+2
GV_NP       equ GV_NV+2
GV_R0       equ GV_NP+2
GV_X0       equ GV_R0+2
GV_NVAR     equ GV_X0+2
GV_SLOT     equ GV_NVAR+2
GV_TMP      equ GV_SLOT+2                   ; .l
GV_TMP2     equ GV_TMP+4                    ; .l
; depuracion (tools/g5l.py game)
GV_DSLOT    equ GV_TMP2+4                   ; .w ranura dibujada o -1
GV_DVAR     equ GV_DSLOT+2                  ; .w offset de la variante
GV_DFAIL    equ GV_DVAR+2                   ; .w frames sin plan
GV_DPASS2   equ GV_DFAIL+2                  ; .w transiciones del pase 2
GV_DWALK    equ GV_DPASS2+2                 ; .w segmentos recorridos
GV_MCUR     equ GV_DWALK+2                  ; .l entrada de la cache de Mario (0: no)
GV_BX       equ GV_MCUR+4                   ; .w
GV_NULLA    equ GV_BX+2                     ; .b lista A con el bloque VBL nulo
GV_NULLB    equ GV_NULLA+1                  ; .b lista B
GV_WSTAMP   equ GV_NULLB+1                  ; .b sello de este frame (g5l_wcache)
GV_NULLC    equ GV_WSTAMP+1                 ; .b lista C (-DCUSHION)
GV_MORD     equ GV_WSTAMP+2                 ; 4 B: orden LRU de la cache
GV_KBUF     equ GV_MORD+4                   ; 52 B: clave de la pose de Mario
GV_BITS     equ GV_KBUF+52                  ; 256 x (.b bit mas alto, .b mas bajo)
GV_REV      equ GV_BITS+512                 ; 256 B: el byte al reves (volteo V)
GV_AF       equ GV_REV+256                  ; 256 B: banderas de la clave por atributo
GV_WNONE    equ GV_AF+256                  ; .l 0, .w -1, .w -1: g5l_mrow sin Mario
GV_IM       equ GV_WNONE+8                  ; .w indices con entradas en GV_IG
GV_MSH      equ GV_IM+2                     ; .w r0 - fila 0 de la cache
GV_MV       equ GV_MSH+2                    ; .l filas r0..r0+31 en pantalla
GV_VIS      equ GV_MV+4                     ; .l filas del Rex en pantalla
GV_OCC      equ GV_VIS+4                    ; 16 .l: filas del Rex por indice
GV_NREM     equ GV_OCC+64                   ; .w bandas
GV_RH       equ GV_NREM+2                   ; .w mitades del bufer (bit h: planos 2h, 2h+1)
GV_REM      equ GV_RH+2                   ; G5L_NREM x (.b ic, .b f, .b grupo, .b 0, .l filas)
GV_SE       equ GV_REM+8*G5L_NREM           ; 1 + 6 x (.w color, .w 0, .l filas, .l del Rex)
GV_SMW      equ GV_SE+7*12                   ; .l filas de Mario del indice (r0)
GV_SB       equ GV_SMW+4                    ; .w ultima fila de Mario antes de r0 (-1)
GV_SA       equ GV_SB+2                     ; .w primera despues de r0 + 31 (-1)
GV_PNVA     equ GV_SA+2                     ; .b colores de partida en la lista A
GV_PNVB     equ GV_PNVA+1                   ; .b en la B
GV_RKA      equ GV_PNVB+1                   ; clave del bufer de la lista A: .l variante,
GV_RKB      equ GV_RKA+46                   ; .w bandas, GV_REM (g5l_patch); la B
        ifd     CUSHION
GV_RKC      equ GV_RKB+46                   ; la C
GV_PNVC     equ GV_RKC+46                   ; .b colores de partida en la C
GV_VMAP     equ GV_PNVC+2                   ; .w libre (era el mapa de g5l_plan; G4-B)
        else
GV_VMAP     equ GV_RKB+46                   ; .w libre (era el mapa de g5l_plan; G4-B)
        endc
GV_NEED     equ GV_VMAP+2                   ; 8 .w: choques de cada variante (-1: sin
                                            ; calcular, $7FFF: probada)
GV_FM       equ GV_NEED+16                  ; .w variante x 4 del camino rapido
GV_MWB      equ GV_FM+2                     ; .l MC_W - 8 de la entrada de Mario (o GV_WZ)
GV_WZ       equ GV_MWB+4                    ; 15 x (.l 0, .w -1, .w -1): sin Mario
GV_LM       equ GV_WZ+15*8                  ; 33 .l: (1 << n) - 1
GV_IG       equ GV_LM+33*4                  ; 16 x IGSZ: grupos del Rex por indice
GV_MC       equ GV_IG+16*IGSZ               ; 4 entradas de la cache de Mario
GV_PK       equ GV_MC+4*MCSZ                ; 64 B: clave del plan (g5l_pckey)
GV_PCNX     equ GV_PK+64                    ; .w entrada que se reemplaza (x PCSZ)
GV_PC       equ GV_PCNX+2                   ; PC_N entradas de la cache del plan
GV_RKS      equ GV_PC+PC_N*PCSZ             ; 46 B: ultimo parche, compartido
GV_RSBUF    equ GV_RKS+46                   ; .l lista que conserva ese parche
GV_RK2      equ GV_RSBUF+4                  ; 3 x 46 B: clave del bufer del Rex 1 (A, B, C)
GV_RKP      equ GV_RK2+3*46                 ; .l la clave que mira g5l_patch
GV_RK0P     equ GV_RKP+4                    ; .l la del Rex 0 en esta lista
GV_RK2P     equ GV_RK0P+4                   ; .l la del Rex 1
GV_PBUF     equ GV_RK2P+4                   ; .l bufer que parchea g5l_patch
GV_NC       equ GV_PBUF+4                   ; .w candidatos
GV_NPL      equ GV_NC+2                     ; .w Rex ubicados
GV_CI       equ GV_NPL+2                    ; .w contador
GV_LB       equ GV_CI+2                     ; .w fin (excluido) del ultimo ubicado
GV_CAND     equ GV_LB+2                     ; G5L_MAXREX x CASZ
GV_EN       equ GV_CAND+G5L_MAXREX*CASZ     ; 2 x (.l filas, .w pos, .w ctl, .w n, .w 0)
GV_RUNS     equ GV_EN+24                    ; G5L_NRUN x (.w a, .b tipo, .b dueno, .w b, .w color)
GV_RX       equ GV_RUNS+8*G5L_NRUN          ; G5L_MAXPL x RXSZ
GV_SWI      equ GV_RX+G5L_MAXPL*RXSZ       ; .w indices que quedan (g5l_sweepn)
GV_SWM      equ GV_SWI+2                    ; .l filas 0..31, .l 32..63 de Mario
GV_SWS      equ GV_SWM+8                    ; .l separadores del grupo
GV_SWG      equ GV_SWS+4                    ; .l filas del grupo que quedan
GV_EV       equ GV_SWG+4                    ; G5L_MAXPL x (.w POS, .w CTL sin la x, .w filas, .w 4 + 4 clip)
GV_CKP      equ GV_EV+8*G5L_MAXPL           ; .l claves de las cadenas de esta lista
GV_CK       equ GV_CKP+4                    ; 3 listas x 4 flujos x (.l filas 1, .l filas 2, .w n1, .w n2)
GV_PSF      equ GV_CK+3*4*12                ; .b G4-2o: g5l_picksel sin g5l_plan si no choca
GV_SWE      equ GV_PSF+2                    ; .l fin de los tramos de Mario (g5l_sweepn)
GV_SIZE     equ GV_SWE+4
        ifgt    G5L_MAXPL-2
        fail    "G4-2: g5l_edges y la cadena son para dos Rex como mucho"
        endc
; entrada de la cache de Mario
MC_KEY      equ 0                           ; 52 B: .w n, 4 x 6 B, 24 B punteros, 2
MC_XREL     equ 52                          ; .w borde derecho - bx
MC_MM       equ 54                          ; 15 x (.l filas 32..63, .l 0..31) por indice
                                            ; (64 bits big endian: g5l_mfill)
MC_FL       equ MC_MM+15*8                  ; 15 x (.b primera fila, .b ultima; $FF: ninguna)
MC_R0       equ MC_FL+30                    ; .w r0 de MC_W ($8000: ninguno)
MC_MSHK     equ MC_R0+2                     ; .w y su r0 - fila 0
MC_WOK      equ MC_MSHK+2                   ; .w indices de MC_W calculados
MC_BOK      equ MC_WOK+2                    ; .w indices con B y A calculados
MC_W        equ MC_BOK+2                    ; 15 x (.l Mw, .w B, .w A): g5l_mrow, g5l_mba
MC_RV       equ MC_W+15*8                   ; .w G4-2o: indices con sus tramos en MC_RS
MC_RN       equ MC_RV+2                     ; 16 .b cuantos tramos (por indice)
MC_RS       equ MC_RN+16                    ; 16 x 32 x (.b primera, .b ultima): los
                                            ; tramos (filas desde la 0, sin recortar)
MCSZ        equ MC_RS+16*64
; grupos de un indice (GV_IG): .w n, .w 0, n x (.w color, .w grupo de la
; tabla, .l filas); el primero es el de la variante limpia
IGSZ        equ 64
; cache del plan (g5l_pcget/g5l_pcput): por entrada la clave (64 B), y lo
; que leen place/patch/emit del camino completo: GV_VAR, GV_NREM, los
; bytes de cada cubeta, GV_REM y las transiciones (hasta PC_NTR)
PC_N        equ 4
PC_NTR      equ 80
PC_VAR      equ 64
PC_NREM     equ 68
PC_LEN      equ 70                          ; 5 .w
PC_REM      equ 80                          ; 8 * G5L_NREM
PC_TRB      equ PC_REM+8*G5L_NREM
PCSZ        equ PC_TRB+8*PC_NTR

; LOWB: d1 = el bit mas bajo de d0 (no 0); a1 = GV_BITS. Destruye d0.
LOWB    macro
        moveq   #0,d1
        tst.w   d0
        bne.s   .a\@
        swap    d0
        moveq   #16,d1
.a\@:   tst.b   d0
        bne.s   .b\@
        lsr.w   #8,d0
        addq.w  #8,d1
.b\@:   and.w   #$ff,d0
        add.w   d0,d0
        add.b   1(a1,d0.w),d1
        endm
; HIGHB: d1 = el bit mas alto de d0 (no 0); a1 = GV_BITS. Destruye d0.
; MWLD: d0.l = Mw del indice d1 (lo de g5l_mrow, ya calculado en MC_W
; por g5l_mwall, o 0 sin Mario). Destruye a0.
MWLD    macro
        move.w  d1,d0
        lsl.w   #3,d0
        move.l  GV_MWB(a6),a0
        move.l  (a0,d0.w),d0
        endm

HIGHB   macro
        moveq   #0,d1
        swap    d0
        tst.w   d0
        bne.s   .a\@
        swap    d0
        bra.s   .c\@
.a\@:   moveq   #16,d1
.c\@:   cmp.w   #$ff,d0
        bls.s   .b\@
        lsr.w   #8,d0
        addq.w  #8,d1
.b\@:   and.w   #$ff,d0
        add.w   d0,d0
        add.b   (a1,d0.w),d1
        endm

; TRB: la transicion (d2 = i, d5 = duenos, d3 = color, d4 = desde, d0 =
; hasta) al final de su cubeta: 0 = sin uso anterior, 1..4 = min(hasta -
; desde, 4) (el orden del pase 1 de g5l_place). Destruye a2/a3.
TRB     macro
        move.w  d0,a3
        tst.w   d4
        bmi.s   .z\@
        sub.w   d4,a3
        cmp.w   #4,a3
        bls.s   .y\@
        move.w  #4,a3
        bra.s   .y\@
.z\@:   sub.l   a3,a3
.y\@:   add.w   a3,a3
        add.w   a3,a3
        add.l   a6,a3
        move.l  GV_BP(a3),a2
        move.b  d2,(a2)+
        move.b  d5,(a2)+
        move.w  d3,(a2)+
        move.w  d4,(a2)+
        move.w  d0,(a2)+
        move.l  a2,GV_BP(a3)
        endm

;----------------------------------------------------------------------
; --- g5l_capture --- (la interrupcion, dc_capture) lo que el plan lee de
; la logica: OAM de Mario, punteros de GFX32, camara y los objetos con
; fichas de los tipos de la tabla (G4-B: el mapa de bits de la G5L3)
; entrada:  a1 = foto (dc_rec + DC_REC * i), a4 = binstart
; salida:   R_G5L de la foto
; registros destruidos: d0-d1/a0 (preserva el resto)
; ciclos:   tools/g5l.py game
;----------------------------------------------------------------------
        ifne    _mario_osz-_mario_oam-16
        fail    "G5L: mario_oam y mario_osz tienen que ir seguidos (captura)"
        endc
        ifne    ((_mario_oam-binstart)|(_ram-binstart))&1
        fail    "G5L: mario_oam y ram en direccion par (captura con .l)"
        endc
g5l_capture:
        movem.l d2-d5/a1-a3/a5,-(sp)
        move.l  a4,a5
        add.l   #g5l_table-binstart,a5
        add.w   10(a5),a5                   ; G5L3: los ordenes y detras
        lea     16*16(a5),a5                ; a5 = los tipos (256 bits)
        lea     R_G5L(a1),a1
        lea     _mario_oam(a4),a0           ; mario_oam y mario_osz: seguidos
        move.l  (a0)+,(a1)+                 ; y en direccion par (ver arriba)
        move.l  (a0)+,(a1)+
        move.l  (a0)+,(a1)+
        move.l  (a0)+,(a1)+
        move.l  (a0)+,(a1)+
        lea     _ram+$0D84(a4),a0           ; los punteros de GFX32 (+ 1 B)
        move.l  (a0)+,(a1)+
        move.l  (a0)+,(a1)+
        move.l  (a0)+,(a1)+
        move.l  (a0)+,(a1)+
        move.l  (a0)+,(a1)+
        move.l  (a0)+,(a1)+
        lea     _ram(a4),a2                 ; a2 = RAM de la SNES
        move.b  $1B(a2),(a1)+               ; camara X (big endian)
        move.b  $1A(a2),(a1)+
        move.b  $1D(a2),(a1)+               ; camara Y
        move.b  $1C(a2),(a1)+
        move.l  a1,a3                       ; a3 = nrex
        clr.w   (a1)+                       ; nrex, relleno
        moveq   #0,d2                       ; d2 = ranura
        moveq   #0,d3                       ; d3 = Rex copiados
.k:     lea     _spr_oam_n(a4),a0
        moveq   #0,d4
        move.b  (a0,d2.w),d4                ; P40 ok (0..11)
        beq     .nk
        move.w  d2,d0
        add.w   #wm_SpriteNum,d0
        moveq   #0,d1
        move.b  (a2,d0.w),d1                ; d1 = tipo
        move.w  d1,d0
        lsr.w   #3,d0
        btst    d1,(a5,d0.w)                ; (bit = tipo & 7)
        beq     .nk
        cmp.w   #G5L_MAXREX,d3
        bhs     .end
        lea     _spr_oam_first(a4),a0
        moveq   #0,d5
        move.b  (a0,d2.w),d5
        lsr.w   #2,d5
        add.w   #64,d5                      ; d5 = ranura OAM
        move.l  a1,a0                       ; a0 = registro
        addq.l  #6,a1                       ; a1 = sus fichas
        moveq   #0,d1                       ; d1 = fichas visibles
        subq.w  #1,d4
.t:     cmp.w   #128,d5
        bhs.s   .te
        move.w  d5,d0
        lsl.w   #2,d0
        add.w   #$200,d0                    ; la entrada OAM (< $400)
        cmp.b   #$F0,1(a2,d0.w)
        beq.s   .tn
        cmp.w   #G5L_MAXT,d1
        bhs.s   .tn
        move.b  (a2,d0.w),(a1)+
        move.b  1(a2,d0.w),(a1)+
        move.b  2(a2,d0.w),(a1)+
        move.b  3(a2,d0.w),(a1)+
        move.w  d5,d0
        add.w   #$420,d0
        move.b  (a2,d0.w),(a1)+             ; tamano / X alta
        addq.w  #1,d1
.tn:    addq.w  #1,d5
        dbf     d4,.t
.te:    tst.w   d1
        beq.s   .none
        move.b  d2,(a0)+                    ; ranura
        move.b  d1,(a0)+                    ; fichas
        move.w  d2,d0
        add.w   #wm_SpriteXHi,d0
        move.b  (a2,d0.w),(a0)+
        move.w  d2,d0
        add.w   #wm_SpriteXLo,d0
        move.b  (a2,d0.w),(a0)+
        move.w  d2,d0
        add.w   #wm_SpriteYHi,d0
        move.b  (a2,d0.w),(a0)+
        move.w  d2,d0
        add.w   #wm_SpriteYLo,d0
        move.b  (a2,d0.w),(a0)+
        lea     G5L_RECSZ-6(a0),a1
        addq.w  #1,d3
        bra.s   .nk
.none:  move.l  a0,a1                       ; sin fichas: no cuenta
.nk:    addq.w  #1,d2
        cmp.w   #12,d2
        blo     .k
.end:   move.b  d3,(a3)
        movem.l (sp)+,d2-d5/a1-a3/a5
        rts

;----------------------------------------------------------------------
; --- g5l_init --- (dc_init, tras scroll_init) nb de cada linea y sin
; sufijos en las listas recien armadas
; registros destruidos: d0-d1/a0-a1
;----------------------------------------------------------------------
g5l_init:
        move.l  a6,-(sp)
        lea     g5l_v(pc),a6
        GETBASE a0
        add.l   #ldoff-binstart,a0
        lea     GV_NB(a6),a1
        move.w  #LINES-1,d1
.l:     move.w  (a0)+,d0
        subq.w  #8,d0
        lsr.w   #2,d0
        move.b  d0,(a1)+
        dbf     d1,.l
        clr.w   GV_RECA(a6)
        clr.w   GV_RECB(a6)
        ifd     CUSHION
        clr.w   GV_RECC(a6)
        clr.b   GV_NULLC(a6)
        move.b  #G5L_VBLN,GV_PNVC(a6)
        clr.l   GV_RKC(a6)
        endc
        clr.w   GV_NP(a6)
        lea     GV_SEGIX(a6),a1
        moveq   #LINES/4-1,d1
.z:     clr.l   (a1)+
        dbf     d1,.z
        lea     GV_PC(a6),a0                ; cache del plan vacia
        moveq   #PC_N-1,d1
.pz:    move.w  #-1,(a0)
        lea     PCSZ(a0),a0
        dbf     d1,.pz
        clr.w   GV_PCNX(a6)
        lea     GV_TRB(a6),a0               ; principio de cada cubeta
        lea     GV_BS(a6),a1
        moveq   #5-1,d1
.bs:    move.l  a0,(a1)+
        lea     8*G5L_MAXTR(a0),a0
        dbf     d1,.bs
        lea     GV_CAPNL(a6),a1             ; 12 - nb de la fila siguiente; 0
        moveq   #0,d1                       ; en el cruce de la 255, la ultima
.cp:    moveq   #0,d0                       ; fila o nb fuera de 7..9
        cmp.w   #G5L_WRAP,d1
        beq.s   .cp1
        cmp.w   #LINES-1,d1
        bhs.s   .cp1
        move.b  GV_NB+1(a6,d1.w),d0
        subq.w  #7,d0
        cmp.w   #2,d0
        bls.s   .cp2
        moveq   #0,d0
        bra.s   .cp1
.cp2:   neg.w   d0
        addq.w  #5,d0
.cp1:   move.b  d0,(a1)+
        addq.w  #1,d1
        cmp.w   #LINES,d1
        blo.s   .cp
        lea     GV_WK(a6),a1                ; sin recorridos
        moveq   #LINES/4-1,d1
.wk:    clr.l   (a1)+
        dbf     d1,.wk
        clr.b   GV_WSTAMP(a6)
        lea     GV_ROOM(a6),a1
        moveq   #LINES/4-1,d1
.rm:    clr.l   (a1)+
        dbf     d1,.rm
        GETBASE a0                          ; (detras de g5l_v: a mas de
        add.l   #g5l_table-binstart,a0      ; 32 KB con -DCUSHION)
        move.l  a0,GV_TAB(a6)
        move.l  12(a0),d0                   ; las fichas traspuestas, tras las
        add.l   a0,d0                       ; mascaras (744 x 16 B)
        add.l   #744*16,d0
        move.l  d0,GV_TT(a6)
        move.w  #-1,GV_DSLOT(a6)
        clr.w   GV_NULLA(a6)                ; (y GV_NULLB)
        move.l  #$00010203,GV_MORD(a6)
        lea     GV_MC(a6),a0                ; claves invalidas (n = 0)
        moveq   #4-1,d1
.mc:    clr.w   (a0)
        lea     MCSZ(a0),a0
        dbf     d1,.mc
        movem.l d2-d3,-(sp)
        lea     GV_BITS(a6),a0              ; por byte: bit mas alto y mas bajo
        moveq   #0,d1                       ; y al reves (volteo V)
.bt:    moveq   #7,d2
.bh:    btst    d2,d1
        dbne    d2,.bh
        move.b  d2,(a0)+
        moveq   #0,d2
.bl:    btst    d2,d1
        bne.s   .bl1
        addq.w  #1,d2
        cmp.w   #8,d2
        blo.s   .bl
.bl1:   move.b  d2,(a0)+
        moveq   #0,d0
        moveq   #0,d3
        moveq   #0,d2
.br:    add.w   d0,d0
        btst    d2,d1
        beq.s   .br1
        addq.w  #1,d0
        addq.w  #1,d3
.br1:   addq.w  #1,d2
        cmp.w   #8,d2
        blo.s   .br
        lea     GV_REV(a6),a1
        move.b  d0,(a1,d1.w)
        addq.w  #1,d1
        cmp.w   #256,d1
        blo.s   .bt
        move.b  #G5L_VBLN,GV_PNVA(a6)       ; (no se sabe: reescribir todo)
        move.b  #G5L_VBLN,GV_PNVB(a6)
        clr.l   GV_RKA(a6)                  ; los buferes sin parche
        clr.l   GV_RKB(a6)
        clr.l   GV_RKS(a6)                  ; cache compartida sin fuente
        clr.l   GV_RK2(a6)                  ; G4-2: los del Rex 1 sin parche
        clr.l   GV_RK2+46(a6)
        clr.l   GV_RK2+92(a6)
        lea     GV_CK(a6),a0                ; y las cadenas sin clave
        moveq   #3*4*3-1,d1
.ck:    clr.l   (a0)+
        dbf     d1,.ck
        clr.l   GV_WNONE(a6)
        move.l  #-1,GV_WNONE+4(a6)
        lea     GV_WZ(a6),a0
        moveq   #15-1,d1
.wz:    clr.l   (a0)+
        move.l  #-1,(a0)+
        dbf     d1,.wz
        lea     GV_AF(a6),a0                ; banderas de la clave del Rex:
        moveq   #0,d1                       ; X, volteo H y V, paleta
.af:    moveq   #1,d0                       ; (tools/g5l.py rex_key)
        and.w   d1,d0
        btst    #6,d1
        beq.s   .af1
        addq.w  #4,d0
.af1:   tst.b   d1
        bpl.s   .af2
        addq.w  #8,d0
.af2:   move.w  d1,d2
        lsr.w   #1,d2
        and.w   #7,d2
        lsl.w   #4,d2
        or.w    d2,d0
        move.b  d0,(a0)+
        addq.w  #1,d1
        cmp.w   #256,d1
        blo.s   .af
        lea     GV_LM(a6),a0                ; (1 << n) - 1, n = 0..32
        moveq   #0,d0
        moveq   #33-1,d1
.lm:    move.l  d0,(a0)+
        add.l   d0,d0
        addq.l  #1,d0
        dbf     d1,.lm
        movem.l (sp)+,d2-d3
        move.l  (sp)+,a6
        rts

;----------------------------------------------------------------------
; --- g5l_render --- (render, tras build_mid) el Rex de la foto en V_BACK
; entrada:  a0 = foto (dc_rec + DC_REC * i), a5 = vars del scroll
; salida:   bloque VBL, sufijos de V_BACK y (con bandas) su bufer de chip
; registros destruidos: d0-d1/a0-a1 (preserva d2-d7/a2-a6)
; ciclos:   tools/g5l.py game (Musashi); WinUAE: GBR 16/17 con -DBENCH
;----------------------------------------------------------------------
g5l_render:
        movem.l d2-d7/a2-a6,-(sp)
        lea     g5l_v(pc),a6
        move.l  a0,a4                       ; a4 = foto
        move.l  V_BACK(a5),a2
        move.l  a2,GV_LIST(a6)
        lea     GV_RECA(a6),a3
        lea     GV_RKA(a6),a1               ; claves de los buferes de bandas
        lea     GV_RK2(a6),a0               ; (Rex 0 y Rex 1) de la lista
        moveq   #0,d1                       ; y de sus cadenas
        move.l  g5l_rbuf(pc),d0             ; bufer de la lista A
        cmp.l   V_COP(a5),a2
        beq.s   .ra
        lea     GV_RECB(a6),a3
        lea     GV_RKB(a6),a1
        lea     46(a0),a0
        moveq   #48,d1
        add.l   #G5L_LBLK,d0                ; el de la B
        ifd     CUSHION
        cmp.l   V_COP2(a5),a2
        beq.s   .ra
        lea     GV_RECC(a6),a3
        lea     GV_RKC(a6),a1
        lea     46(a0),a0
        moveq   #96,d1
        add.l   #G5L_LBLK,d0                ; el de la C
        endc
.ra:    move.l  a3,GV_REC(a6)
        move.l  a6,d2
        add.l   #GV_CK,d2
        add.l   d1,d2
        move.l  d2,GV_CKP(a6)
        move.l  d0,GV_RBUF(a6)
        move.l  d0,GV_PBUF(a6)              ; (el Rex 0: el principio del bloque)
        move.l  a1,GV_RKP(a6)
        move.l  a1,GV_RK0P(a6)
        move.l  a0,GV_RK2P(a6)
        addq.b  #1,GV_WSTAMP(a6)            ; recorridos de este frame
        bne.s   .st
        move.b  #1,GV_WSTAMP(a6)            ; (vuelta: borrar los sellos)
        lea     GV_WK(a6),a0
        moveq   #LINES/4-1,d0
.wk:    clr.l   (a0)+
        dbf     d0,.wk
.st:    sf      GV_PSF(a6)                  ; (el camino de un Rex: con g5l_plan)
        bsr     g5l_clean
        moveq   #0,d0
        move.b  R_PAL(a4),d0
        lsl.w   #5,d0
        GETBASE a0
        add.l   #mario_pals-binstart,a0
        add.w   d0,a0
        move.l  a0,GV_COL(a6)
        lea     R_G5L(a4),a4                ; a4 = foto G5L
        move.w  #-1,GV_DSLOT(a6)
        bsr     g5l_choose                  ; candidatos (Mario solo si hay)
        tst.w   d0
        beq    .none
        ifd     DELAYG
        move.w  #DELAYG-1,d0                ; calibracion: DELAYG x 10 ciclos
.dly:   dbf     d0,.dly                     ; en las fotos con Rex, sin dibujarlo
        bra.s   .none
        endc
        bsr     g5l_mario
        bsr     g5l_geo                     ; G4-2: si entran dos, el camino
        cmp.w   #1,d0                       ; de varios
        bhi     .multi
        bsr     g5l_rexmw
        tst.l   GV_MCUR(a6)                 ; sin Mario el camino rapido no
        beq.s   .nq                         ; falla: sin cache
        bsr     g5l_pcget
        beq     .swd                        ; el plan de una foto igual
.nq:
        lea     GV_NEED(a6),a2              ; ninguna calculada
        moveq   #-1,d0
        move.l  d0,(a2)+
        move.l  d0,(a2)+
        move.l  d0,(a2)+
        move.l  d0,(a2)
        clr.w   GV_FM(a6)                   ; camino rapido: la primera
.fm:    move.w  GV_FM(a6),d0
        move.l  GV_VLIST(a6),a0
        move.l  (a0,d0.w),a0
        add.l   GV_TAB(a6),a0
        move.l  a0,GV_VAR(a6)
        bsr     g5l_fast
        beq     .swd                        ; sin g5l_plan ni g5l_sweep
        addq.w  #4,GV_FM(a6)
        move.w  GV_NVAR(a6),d0
        lsl.w   #2,d0
        cmp.w   GV_FM(a6),d0
        bhi.s   .fm
.sel:   bsr     g5l_picksel
        bne     .selx
        bsr     g5l_sweep
        tst.l   GV_MCUR(a6)
        beq.s   .swd
        bsr     g5l_pcput
.swd:
        bsr     g5l_place
        tst.w   d0
        bne     .fail
        bsr     g5l_nullflag
        clr.b   (a0)                        ; esta lista deja de ser nula
        move.l  GV_VAR(a6),d0
        sub.l   GV_TAB(a6),d0
        move.w  d0,GV_DVAR(a6)
        move.w  GV_SLOT(a6),GV_DSLOT(a6)
        bsr     g5l_patch
        bsr     g5l_emit
        bsr     g5l_unpool
        bra     .x
.selx:  cmp.w   #1,GV_NC(a6)                ; G4-2: el primero sin variante
        bls     .fail                       ; (bob 'color'): los demas
        lea     GV_CAND(a6),a0
        st      CA_DEAD(a0)
; G4-2: varios Rex (tools/g5l.py plan_frame_n). Los candidatos en orden;
; uno entra si queda una linea libre tras el ultimo ubicado (encadenado DMA
; en los pares 4-5 y 6-7) y hay lugar (G5L_MAXPL); su variante y bandas
; contra Mario (sin filas compartidas con otro Rex, solo Mario cuenta).
; Despues las transiciones de todos y el plazo; si no entra, el ultimo
; ubicado se cae y se repite.
.multi: clr.w   GV_NPL(a6)
        clr.w   GV_CI(a6)
        st      GV_PSF(a6)                  ; G4-2o: sin choques, sin g5l_plan
.mc:    move.w  GV_CI(a6),d7
        cmp.w   GV_NC(a6),d7
        bhs     .mdone
        addq.w  #1,GV_CI(a6)
        lea     GV_CAND(a6),a0
        lsl.w   #4,d7
        add.w   d7,a0
        tst.b   CA_DEAD(a0)
        bne.s   .mc
        move.w  CA_R0(a0),d0                ; a = max(r0, 0)
        bpl.s   .m1
        moveq   #0,d0
.m1:    move.w  GV_NPL(a6),d1
        beq.s   .m2
        cmp.w   #G5L_MAXPL,d1
        bhs.s   .mc                         ; bob 'canal'
        cmp.w   GV_LB(a6),d0
        ble.s   .mc                         ; sin linea libre: bob 'canal'
.m2:    move.w  CA_R0(a0),GV_R0(a6)
        move.w  CA_X0(a0),GV_X0(a6)
        move.l  CA_VL(a0),GV_VLIST(a6)
        move.w  CA_NV(a0),GV_NVAR(a6)
        move.w  CA_SL(a0),GV_SLOT(a6)
        bsr     g5l_rexmw
        lea     GV_NEED(a6),a2              ; ninguna calculada
        moveq   #-1,d0
        move.l  d0,(a2)+
        move.l  d0,(a2)+
        move.l  d0,(a2)+
        move.l  d0,(a2)
        bsr     g5l_picksel
        bmi.s   .mf
        bne     .mc                         ; bob 'color'
        bsr     g5l_rxsave
        bra.s   .mn
.mf:    bsr     g5l_rxsavef                 ; sin choques: de la tabla
.mn:    addq.w  #1,GV_NPL(a6)
        bra     .mc
.mdone: tst.w   GV_NPL(a6)
        beq     .fail
.mpl:   bsr     g5l_sweepn
        bsr     g5l_unpool
        bsr     g5l_edges
        bsr     g5l_place_e
        tst.w   d0
        beq.s   .mok
        subq.w  #1,GV_NPL(a6)               ; bob 'plazo': el ultimo
        bne.s   .mpl
        bra     .fail
.mok:   bsr     g5l_nullflag
        clr.b   (a0)
        lea     GV_RX(a6),a0
        move.l  RX_VAR(a0),d0
        sub.l   GV_TAB(a6),d0
        move.w  d0,GV_DVAR(a6)
        move.w  RX_SLOT(a0),GV_SLOT(a6)     ; (g5l_emitc: GV_DSLOT)
        clr.w   GV_CI(a6)
.mp:    move.w  GV_CI(a6),d0
        cmp.w   GV_NPL(a6),d0
        bhs.s   .mpe
        bsr     g5l_rxload
        bsr     g5l_patch
        move.w  GV_CI(a6),d0
        lsl.w   #8,d0
        lea     GV_RX(a6),a0
        move.w  GV_RH(a6),RX_RH(a0,d0.w)    ; P40 ok (0 o 256)
        addq.w  #1,GV_CI(a6)
        bra.s   .mp
.mpe:   bsr     g5l_emitn
        bsr     g5l_unpool
        bra     .x
.fail:  addq.w  #1,GV_DFAIL(a6)
.none:  move.w  #-1,GV_DSLOT(a6)
        bsr     g5l_unpool
        bsr     g5l_vblnull
.x:     movem.l (sp)+,d2-d7/a2-a6
        rts

;----------------------------------------------------------------------
; --- g5l_picksel --- la variante limpia que menos choca con Mario (la
; primera si empatan; la primera sin choque corta la busqueda); si
; g5l_plan no encuentra banda, la siguiente en ese orden (tools/g5l.py
; plan_frame). GV_NEED: -1 sin calcular, $7fff ya probada.
; entrada:  GV_VLIST/NVAR/MV/COL, GV_NEED, la cache de Mario, a6 = g5l_v
; salida:   d0 = 0 (Z) y GV_VAR/VMAP y lo de g5l_plan; 1 (NZ) ninguna;
;           -1 (N) con GV_PSF: GV_VAR/VMAP sin choques, sin g5l_plan
;           (G4-2o: g5l_rxsavef)
; registros destruidos: d0-d7/a0-a5
;----------------------------------------------------------------------
g5l_picksel:
.sel:   lea     GV_NEED(a6),a2
        move.w  GV_NVAR(a6),d7
        add.w   d7,d7
        moveq   #-1,d4                      ; la mejor (m x 2)
        move.w  #$7fff,d3                   ; sus choques
        moveq   #0,d5                       ; m x 2
.sc:    move.w  (a2,d5.w),d0
        bpl.s   .kn
        move.w  d5,d0                       ; sin calcular
        add.w   d0,d0
        move.l  GV_VLIST(a6),a0
        move.l  (a0,d0.w),a0
        add.l   GV_TAB(a6),a0
        moveq   #0,d0
        tst.l   GV_MCUR(a6)
        beq.s   .ks                         ; sin Mario nada choca
        bsr     g5l_need
.ks:    move.w  d0,(a2,d5.w)
.kn:    cmp.w   d3,d0
        bge.s   .nx
        move.w  d0,d3
        move.w  d5,d4
        tst.w   d0
        beq.s   .go
.nx:    addq.w  #2,d5
        cmp.w   d7,d5
        blo.s   .sc
.go:    tst.w   d4
        bmi.s   .fail                       ; todas probadas
        move.w  #$7fff,(a2,d4.w)
        move.w  d4,d0
        add.w   d0,d0
        move.l  GV_VLIST(a6),a0
        move.l  (a0,d0.w),a0
        add.l   GV_TAB(a6),a0
        move.l  a0,GV_VAR(a6)
        tst.w   d3                          ; G4-2o: sin choques y en el camino
        bne.s   .pl                         ; de varios: sin bandas, no hace
        tst.b   GV_PSF(a6)                  ; falta g5l_plan
        beq.s   .pl
        moveq   #-1,d0
        rts
.pl:    bsr     g5l_plan                    ; grupos y bandas
        bne     .sel
        moveq   #0,d0
        rts
.fail:  moveq   #1,d0
        rts

;----------------------------------------------------------------------
; --- g5l_rexmw --- lo de Mario para el r0 de GV_R0: GV_MSH/MV, MC_W
; (vale para el mismo r0 y r0 - by) y GV_MWB (MWLD)
; registros destruidos: d0-d5/a0-a2
;----------------------------------------------------------------------
g5l_rexmw:
        bsr     g5l_mvis
        move.l  GV_MCUR(a6),d0
        beq.s   .nm
        move.l  d0,a0
        move.w  GV_R0(a6),d0
        move.w  GV_MSH(a6),d1
        cmp.w   MC_R0(a0),d0
        bne.s   .mk
        cmp.w   MC_MSHK(a0),d1
        beq.s   .nm
.mk:    move.w  d0,MC_R0(a0)
        move.w  d1,MC_MSHK(a0)
        clr.l   MC_WOK(a0)                  ; (y MC_BOK)
        bsr     g5l_mwall
.nm:    move.l  GV_MCUR(a6),d0
        beq.s   .nz
        add.l   #MC_W-8,d0
        bra.s   .nw
.nz:    lea     GV_WZ-8(a6),a0
        move.l  a0,d0
.nw:    move.l  d0,GV_MWB(a6)
        rts

;----------------------------------------------------------------------
; --- g5l_geo --- G4-2: cuantos candidatos vivos entrarian por canal (el
; primero, y cada uno con una linea libre tras el anterior), hasta
; G5L_MAXPL. Uno solo: el camino de siempre.
; salida:   d0
; registros destruidos: d0-d3/a0
;----------------------------------------------------------------------
g5l_geo:
        moveq   #0,d0
        moveq   #0,d2                       ; fin (excluido) del ultimo
        lea     GV_CAND(a6),a0
        move.w  GV_NC(a6),d1
        bra.s   .g9
.g:     tst.b   CA_DEAD(a0)
        bne.s   .gn
        move.w  CA_R0(a0),d3
        bpl.s   .g1
        moveq   #0,d3
.g1:    tst.w   d0
        beq.s   .g2
        cmp.w   d2,d3
        ble.s   .gn
.g2:    addq.w  #1,d0
        cmp.w   #G5L_MAXPL,d0
        bhs.s   .x
        move.w  CA_R0(a0),d2
        add.w   CA_H(a0),d2
        cmp.w   #LINES,d2
        ble.s   .gn
        move.w  #LINES,d2
.gn:    lea     CASZ(a0),a0
.g9:    dbf     d1,.g
.x:     rts

;----------------------------------------------------------------------
; --- g5l_rxsave --- G4-2: el Rex de GV_R0/X0/SLOT/VAR/MSH y lo de
; g5l_plan (bandas; grupos en orden de indice, con el primero y cuantos de
; cada indice, y los indices con algun grupo de otro color que Mario) al
; registro GV_NPL; GV_LB = su fin (excluido) en pantalla
; registros destruidos: d0-d6/a0-a4
;----------------------------------------------------------------------
g5l_rxsave:
        move.w  GV_NPL(a6),d0
        lsl.w   #8,d0
        lea     GV_RX(a6),a3
        add.w   d0,a3                       ; a3 = registro
        move.w  GV_R0(a6),RX_R0(a3)
        move.w  GV_X0(a6),RX_X0(a3)
        move.w  GV_SLOT(a6),RX_SLOT(a3)
        move.w  GV_MSH(a6),RX_MSH(a3)
        move.l  GV_VAR(a6),a0
        move.l  a0,RX_VAR(a3)
        moveq   #0,d0
        move.b  8(a0),d0                    ; borde derecho
        add.w   GV_X0(a6),d0
        cmp.w   #255,d0
        ble.s   .r1
        move.w  #255,d0
.r1:    move.w  d0,RX_XR(a3)
        moveq   #0,d0
        move.b  5(a0),d0
        add.w   GV_R0(a6),d0
        cmp.w   #LINES,d0
        ble.s   .r2
        move.w  #LINES,d0
.r2:    move.w  d0,GV_LB(a6)
        move.w  GV_NREM(a6),d0              ; las bandas que hay
        move.w  d0,RX_NREM(a3)
        beq.s   .rc9
        lea     GV_REM(a6),a0
        lea     RX_REM(a3),a2
        add.w   d0,d0
        subq.w  #1,d0
.rc:    move.l  (a0)+,(a2)+
        dbf     d0,.rc
.rc9:   clr.l   RX_IXN(a3)
        clr.l   RX_IXN+4(a3)
        clr.l   RX_IXN+8(a3)
        clr.l   RX_IXN+12(a3)
        lea     RX_G(a3),a2
        lea     GV_BITS(a6),a1
        move.l  GV_COL(a6),a4
        moveq   #0,d2                       ; grupos
        moveq   #0,d4                       ; indices de otro color
        move.w  GV_IM(a6),d6                ; indices que quedan
.ri:    move.w  d6,d0
        beq.s   .re
        LOWB                                ; d1 = indice
        bclr    d1,d6
        move.b  d2,RX_IXS(a3,d1.w)          ; P40 ok (1..15)
        move.w  d1,d0
        add.w   d0,d0
        move.w  (a4,d0.w),d5                ; color de Mario
        lsl.w   #5,d0                       ; IGSZ
        lea     GV_IG(a6),a0
        add.w   d0,a0
        move.w  (a0),d3                     ; sus grupos
        addq.l  #4,a0
        bra.s   .rg9
.rg:    move.l  4(a0),d0
        beq.s   .rgn
        move.b  d1,(a2)+
        clr.b   (a2)+
        move.w  (a0),(a2)+
        move.l  d0,(a2)+
        addq.w  #1,d2
        addq.b  #1,RX_IXN(a3,d1.w)          ; P40 ok
        cmp.w   (a0),d5
        beq.s   .rgn
        bset    d1,d4
.rgn:   addq.l  #8,a0
.rg9:   dbf     d3,.rg
        bra.s   .ri
.re:    move.w  d2,RX_NG(a3)
        move.w  d4,RX_DM(a3)
        rts

;----------------------------------------------------------------------
; --- g5l_rxsavef --- G4-2o: g5l_rxsave sin g5l_plan, para una variante
; sin choques con Mario (g5l_picksel con GV_PSF): sin bandas y con los
; grupos de la tabla en pantalla (lo que daria g5l_plan; como g5l_fast,
; van por indice creciente)
; entrada:  GV_R0/X0/SLOT/VAR/MSH/MV/COL, a6 = g5l_v
; registros destruidos: d0-d7/a0-a4
;----------------------------------------------------------------------
g5l_rxsavef:
        move.w  GV_NPL(a6),d0
        lsl.w   #8,d0
        lea     GV_RX(a6),a3
        add.w   d0,a3                       ; a3 = registro
        move.w  GV_R0(a6),RX_R0(a3)
        move.w  GV_X0(a6),RX_X0(a3)
        move.w  GV_SLOT(a6),RX_SLOT(a3)
        move.w  GV_MSH(a6),RX_MSH(a3)
        move.l  GV_VAR(a6),a0
        move.l  a0,RX_VAR(a3)
        moveq   #0,d0
        move.b  8(a0),d0                    ; borde derecho
        add.w   GV_X0(a6),d0
        cmp.w   #255,d0
        ble.s   .r1
        move.w  #255,d0
.r1:    move.w  d0,RX_XR(a3)
        moveq   #0,d0
        move.b  5(a0),d0                    ; alto
        move.w  d0,d1
        add.w   GV_R0(a6),d0
        cmp.w   #LINES,d0
        ble.s   .r2
        move.w  #LINES,d0
.r2:    move.w  d0,GV_LB(a6)
        clr.w   RX_NREM(a3)
        lsl.w   #2,d1
        lea     GV_LM(a6),a1
        move.l  (a1,d1.w),d6
        and.l   GV_MV(a6),d6                ; d6 = filas en pantalla
        moveq   #0,d0
        move.b  6(a0),d0
        lsl.w   #3,d0
        moveq   #0,d7
        move.b  9(a0),d7
        lea     12(a0,d0.w),a4              ; a4 = grupos (.b i .b 0 .w color .l filas)
        clr.l   RX_IXN(a3)
        clr.l   RX_IXN+4(a3)
        clr.l   RX_IXN+8(a3)
        clr.l   RX_IXN+12(a3)
        lea     RX_G(a3),a2
        move.l  GV_COL(a6),a1
        moveq   #0,d2                       ; grupos
        moveq   #0,d4                       ; indices de otro color
        bra.s   .g9
.g:     move.l  4(a4),d0
        and.l   d6,d0
        beq.s   .gn                         ; fuera de la pantalla
        moveq   #0,d1
        move.b  (a4),d1                     ; d1 = indice
        tst.b   RX_IXN(a3,d1.w)             ; P40 ok (1..15)
        bne.s   .g1
        move.b  d2,RX_IXS(a3,d1.w)          ; P40 ok: el primero del indice
.g1:    addq.b  #1,RX_IXN(a3,d1.w)          ; P40 ok
        move.b  d1,(a2)+                    ; .b i .b 0 (como g5l_rxsave)
        clr.b   (a2)+
        move.w  2(a4),(a2)+                 ; color
        move.l  d0,(a2)+
        addq.w  #1,d2
        move.w  d1,d3
        add.w   d3,d3
        move.w  (a1,d3.w),d3                ; color de Mario
        cmp.w   2(a4),d3
        beq.s   .gn
        bset    d1,d4
.gn:    addq.l  #8,a4
.g9:    dbf     d7,.g
        move.w  d2,RX_NG(a3)
        move.w  d4,RX_DM(a3)
        rts

;----------------------------------------------------------------------
; --- g5l_rxload --- G4-2: el Rex d0 en GV_VAR/NREM/REM para g5l_patch,
; con su bufer (GV_RBUF + 4 x G5L_RSTR x k) y su clave
; registros destruidos: d1/a0-a1
;----------------------------------------------------------------------
g5l_rxload:
        move.w  d0,d1
        lsl.w   #8,d1
        lea     GV_RX(a6),a0
        add.w   d1,a0
        move.l  RX_VAR(a0),GV_VAR(a6)
        move.w  RX_NREM(a0),d1              ; las bandas que hay
        move.w  d1,GV_NREM(a6)
        beq.s   .c9
        lea     RX_REM(a0),a0
        lea     GV_REM(a6),a1
        add.w   d1,d1
        subq.w  #1,d1
.c:     move.l  (a0)+,(a1)+
        dbf     d1,.c
.c9:    move.l  GV_RK0P(a6),GV_RKP(a6)
        move.l  GV_RBUF(a6),d1
        tst.w   d0
        beq.s   .x
        move.l  GV_RK2P(a6),GV_RKP(a6)
        add.l   #4*G5L_RSTR,d1
.x:     move.l  d1,GV_PBUF(a6)
        rts

;----------------------------------------------------------------------
; --- g5l_sweepn --- G4-2: las transiciones de varios Rex (tools/g5l.py
; sweep_n). Por indice con algun grupo de otro color que Mario: los tramos
; de Mario (sus 64 filas de la cache, recortadas a la pantalla) y los de
; cada Rex, ordenados por (fila, Mario primero, Rex en su orden); una
; transicion donde cambia el color, desde el ultimo uso. Los tramos de un
; grupo sin nada entre ellos (filas de Mario o de otro grupo del indice en
; la ventana del Rex; los otros Rex no comparten filas) van juntos en un
; bloque: el mismo resultado con menos tramos.
; entrada:  GV_NPL Rex en GV_RX, GV_COL, la cache de Mario, a6 = g5l_v
; salida:   las cubetas (GV_BP)
; registros destruidos: d0-d7/a0-a5
;----------------------------------------------------------------------
g5l_sweepn:
        lea     GV_BS(a6),a2                ; cubetas vacias
        lea     GV_BP(a6),a3
        move.l  (a2)+,(a3)+
        move.l  (a2)+,(a3)+
        move.l  (a2)+,(a3)+
        move.l  (a2)+,(a3)+
        move.l  (a2)+,(a3)+
        lea     GV_BITS(a6),a1
        moveq   #0,d0                       ; los indices de otro color
        lea     GV_RX+RX_DM(a6),a0
        move.w  GV_NPL(a6),d1
        subq.w  #1,d1
.dm:    or.w    (a0),d0
        lea     RXSZ(a0),a0
        dbf     d1,.dm
        move.w  d0,GV_SWI(a6)
.idx:   move.w  GV_SWI(a6),d0
        beq     .x
        LOWB
        move.w  d1,d2                       ; d2 = i
        move.w  GV_SWI(a6),d0
        bclr    d2,d0
        move.w  d0,GV_SWI(a6)
        move.w  d2,d0
        add.w   d0,d0
        move.l  GV_COL(a6),a0
        move.w  (a0,d0.w),d3                ; d3 = color de Mario
        clr.l   GV_SWM(a6)                  ; las 64 filas de Mario con i
        clr.l   GV_SWM+4(a6)
        move.l  GV_MCUR(a6),d1
        beq.s   .nm
        move.l  d1,a5
        lea     MC_FL-2(a5),a3
        cmp.b   #$ff,(a3,d0.w)              ; P40 ok (2..30)
        beq.s   .nm                         ; Mario no usa el indice
        lsl.w   #2,d0
        lea     MC_MM-8(a5,d0.w),a3
        move.l  4(a3),GV_SWM(a6)            ; 0..31
        move.l  (a3),GV_SWM+4(a6)           ; 32..63
.nm:    lea     GV_RUNS(a6),a4              ; a4 = tramos
        move.l  GV_SWM(a6),d4               ; primero los tramos de Mario
        move.l  GV_SWM+4(a6),d5
        move.l  d4,d0
        or.l    d5,d0
        beq     .mf                         ; no usa el indice
        move.l  GV_MCUR(a6),a5              ; G4-2o: sus tramos (relativos a la
        lea     MC_RS(a5),a2                ; fila 0, sin recortar) van en la
        move.w  d2,d0                       ; cache de Mario la primera vez
        lsl.w   #6,d0
        add.w   d0,a2                       ; a2 = los del indice
        move.w  MC_RV(a5),d0
        btst    d2,d0
        bne     .mk
        move.l  a2,a0
        moveq   #0,d6                       ; cuantos
        moveq   #0,d7                       ; 0: la mitad baja, 32: la alta
.mh:    tst.l   d4
        bne.s   .mr
        tst.w   d7
        bne     .mv
        move.l  d5,d4
        moveq   #0,d5
        moveq   #32,d7
        bra.s   .mh
.mr:    move.l  d4,d0
        LOWB
        add.w   d7,d1
        move.b  d1,(a0)+                    ; a
        move.l  d4,d0
        neg.l   d0
        and.l   d4,d0
        add.l   d4,d0
        and.l   d0,d4
        tst.l   d0
        bne.s   .m1
        tst.w   d7                          ; hasta la 31 de la mitad baja: sigue
        bne.s   .m0                         ; en la alta si tiene la 32
        btst    #0,d5
        beq.s   .m0
        moveq   #1,d0
        add.l   d5,d0
        and.l   d0,d5
        tst.l   d0
        bne.s   .m3
        moveq   #64,d1
        bra.s   .m2
.m3:    LOWB
        add.w   #32,d1
        bra.s   .m2
.m0:    moveq   #32,d1
        add.w   d7,d1
        bra.s   .m2
.m1:    LOWB
        add.w   d7,d1
.m2:    subq.w  #1,d1
        move.b  d1,(a0)+                    ; b
        addq.w  #1,d6
        bra     .mh
.mv:    lea     MC_RN(a5),a0
        move.b  d6,(a0,d2.w)                ; P40 ok (1..15)
        move.w  MC_RV(a5),d0
        bset    d2,d0
        move.w  d0,MC_RV(a5)
.mk:    moveq   #0,d6
        lea     MC_RN(a5),a0
        move.b  (a0,d2.w),d6                ; P40 ok
        move.w  GV_WBASE(a6),d7             ; d7 = fila de la 0
        bra.s   .q9
.q:     moveq   #0,d0
        move.b  (a2)+,d0
        add.w   d7,d0                       ; a
        moveq   #0,d1
        move.b  (a2)+,d1
        add.w   d7,d1                       ; b
        bmi.s   .q9                         ; todo arriba de la pantalla
        cmp.w   #LINES,d0
        bge.s   .mf                         ; todo abajo (y los que siguen)
        tst.w   d0
        bpl.s   .q1
        moveq   #0,d0
.q1:    cmp.w   #LINES-1,d1
        ble.s   .q2
        move.w  #LINES-1,d1
.q2:    move.w  d0,(a4)+
        move.w  #$0001,(a4)+                ; tipo 0, dueno 1
        move.w  d1,(a4)+
        move.w  d3,(a4)+
.q9:    dbf     d6,.q
.mf:    move.l  a4,GV_SWE(a6)               ; (su fin)
; G4-2o: cada Rex con un solo grupo del indice y ningun tramo de Mario
; entre su primera y su ultima fila: un bloque (lo mismo que .grp sin
; separadores en el bloque). Si alguno no, el camino general.
        moveq   #0,d7                       ; d7 = Rex k
        lea     GV_RX(a6),a3
.f:     cmp.w   GV_NPL(a6),d7
        bhs     .sort
        move.b  RX_IXN(a3,d2.w),d5          ; P40 ok (1..15)
        beq     .fn
        cmp.b   #1,d5
        bne     .fg                         ; varios grupos
        moveq   #0,d0
        move.b  RX_IXS(a3,d2.w),d0          ; P40 ok
        lsl.w   #3,d0
        lea     RX_G(a3,d0.w),a2            ; a2 = el grupo
        move.l  4(a2),d0
        LOWB
        move.w  d1,d6
        add.w   RX_R0(a3),d6                ; d6 = a
        move.l  4(a2),d0
        HIGHB
        add.w   RX_R0(a3),d1                ; d1 = b
        lea     GV_RUNS(a6),a0              ; Mario entre a y b?
.fo:    cmp.l   GV_SWE(a6),a0
        bhs.s   .fk
        cmp.w   (a0),d1
        blt.s   .fk                         ; empieza despues de b (en orden)
        cmp.w   4(a0),d6
        ble     .fg                         ; termina en a o despues: se solapa
        addq.l  #8,a0
        bra.s   .fo
.fk:    move.w  d6,(a4)+                    ; a
        move.b  d7,d0
        addq.b  #1,d0
        move.b  d0,(a4)+                    ; tipo 1 + k
        moveq   #2,d0
        lsl.b   d7,d0
        move.b  d0,(a4)+                    ; dueno 2 << k
        move.w  d1,(a4)+                    ; b
        move.w  2(a2),(a4)+                 ; color
.fn:    addq.w  #1,d7
        lea     RXSZ(a3),a3
        bra     .f
.fg:    move.l  GV_SWE(a6),a4               ; el general: sin los bloques
        moveq   #0,d7                       ; rapidos, d7 = Rex k
.rex:   cmp.w   GV_NPL(a6),d7
        bhs     .sort
        move.w  d7,d0
        lsl.w   #8,d0
        lea     GV_RX(a6),a3
        add.w   d0,a3                       ; a3 = registro
        moveq   #0,d5
        move.b  RX_IXN(a3,d2.w),d5          ; P40 ok: sus grupos del indice
        beq     .rnx
        move.l  GV_SWM(a6),d4               ; d4 = Mario en las 32 filas desde r0
        move.l  GV_SWM+4(a6),d6
        move.l  d4,d0
        or.l    d6,d0
        beq.s   .sv                         ; (Mario no usa el indice: 0)
        move.w  RX_MSH(a3),d0
        tst.w   d0
        bmi.s   .sl
        cmp.w   #32,d0
        bhs.s   .sb
        lsr.l   d0,d4
        moveq   #32,d1
        sub.w   d0,d1
        lsl.l   d1,d6                       ; (32: queda 0)
        or.l    d6,d4
        bra.s   .sv
.sb:    sub.w   #32,d0
        cmp.w   #32,d0
        bhs.s   .sz
        lsr.l   d0,d6
        move.l  d6,d4
        bra.s   .sv
.sl:    neg.w   d0
        cmp.w   #32,d0
        bhs.s   .sz
        lsl.l   d0,d4
        bra.s   .sv
.sz:    moveq   #0,d4
.sv:    moveq   #0,d0
        move.b  RX_IXS(a3,d2.w),d0          ; P40 ok
        lsl.w   #3,d0
        lea     RX_G(a3,d0.w),a2            ; a2 = sus grupos
        move.l  a2,a0
        moveq   #0,d6                       ; d6 = todas sus filas con i
        move.w  d5,d1
        subq.w  #1,d1
.u:     or.l    4(a0),d6
        addq.l  #8,a0
        dbf     d1,.u
        move.w  RX_R0(a3),a5                ; a5 = r0
.grp:   move.l  4(a2),d0                    ; separadores: Mario y los otros
        move.l  d0,GV_SWG(a6)               ; grupos del indice
        not.l   d0
        and.l   d6,d0
        or.l    d4,d0
        bne.s   .gs
        clr.l   GV_SWG(a6)                  ; sin separadores: un bloque con
        move.l  4(a2),d0                    ; todo el grupo
        LOWB
        move.w  d1,(a4)
        move.l  4(a2),d0
        bra.s   .bh
.gs:    move.l  d0,GV_SWS(a6)
.blk:   move.l  GV_SWG(a6),d0
        beq     .gnx
        LOWB                                ; d1 = s
        move.w  d1,(a4)
        moveq   #-2,d0
        lsl.l   d1,d0                       ; las filas despues de s
        and.l   GV_SWS(a6),d0
        beq.s   .ball
        LOWB                                ; d1 = el primer separador
        lsl.w   #2,d1
        lea     GV_LM(a6),a0
        move.l  (a0,d1.w),d0                ; P40 ok: filas antes de el
        and.l   GV_SWG(a6),d0               ; d0 = el bloque
        bra.s   .bb
.ball:  move.l  GV_SWG(a6),d0
.bb:    eor.l   d0,GV_SWG(a6)
.bh:    HIGHB                               ; d1 = su ultima fila
        add.w   a5,d1
        move.w  (a4),d0
        add.w   a5,d0
        move.w  d0,(a4)+                    ; a
        move.b  d7,d0
        addq.b  #1,d0
        move.b  d0,(a4)+                    ; tipo 1 + k
        moveq   #2,d0
        lsl.b   d7,d0
        move.b  d0,(a4)+                    ; dueno 2 << k
        move.w  d1,(a4)+                    ; b
        move.w  2(a2),(a4)+                 ; color
        bra     .blk
.gnx:   addq.l  #8,a2
        subq.w  #1,d5
        bne     .grp
.rnx:   addq.w  #1,d7
        bra     .rex
.sort:  lea     GV_RUNS+8(a6),a0            ; insercion por (fila, tipo)
.s1:    cmp.l   a4,a0
        bhs.s   .s9
        move.l  (a0),d0
        move.l  4(a0),d1
        move.l  a0,a2
.s2:    cmp.l   -8(a2),d0
        bhs.s   .s3
        move.l  -8(a2),(a2)
        move.l  -4(a2),4(a2)
        subq.l  #8,a2
        lea     GV_RUNS(a6),a3
        cmp.l   a3,a2
        bhi.s   .s2
.s3:    move.l  d0,(a2)
        move.l  d1,4(a2)
        addq.l  #8,a0
        bra.s   .s1
.s9:    move.l  a4,a5                       ; a5 = fin
        lea     GV_RUNS(a6),a4
        moveq   #-1,d4                      ; ultimo uso: ninguno
        moveq   #0,d5
.w:     cmp.l   a5,a4
        bhs     .idx
        move.w  6(a4),d0
        cmp.w   d3,d0
        beq.s   .ws
        move.w  d0,d3
        move.w  (a4),d0
        TRB
.ws:    move.w  4(a4),d0
        cmp.w   d4,d0
        blt.s   .wn
        beq.s   .we
        move.w  d0,d4
        moveq   #0,d5
.we:    or.b    3(a4),d5
.wn:    addq.l  #8,a4
        bra.s   .w
.x:     rts

;----------------------------------------------------------------------
; --- g5l_edges --- G4-2: GV_E de los GV_NPL Rex (1 o 2): E[m] = el mayor
; borde derecho de los duenos de m + 1 (bit 0 Mario, k + 1 el Rex k; 0 sin
; duenos). tools/g5l.py EMap
; registros destruidos: d0-d4/a0
;----------------------------------------------------------------------
g5l_edges:
        lea     GV_E(a6),a0
        move.w  GV_XM(a6),d0                ; Mario (-1 sin Mario)
        move.w  GV_RX+RX_XR(a6),d1          ; Rex 0
        clr.w   (a0)+                       ; E[0]
        move.w  d0,d2
        addq.w  #1,d2
        move.w  d2,(a0)+                    ; E[1]
        move.w  d1,d2
        addq.w  #1,d2
        move.w  d2,(a0)+                    ; E[2]
        move.w  d0,d2                       ; d2 = max(M, R0)
        cmp.w   d1,d2
        bge.s   .e1
        move.w  d1,d2
.e1:    move.w  d2,d3
        addq.w  #1,d3
        move.w  d3,(a0)+                    ; E[3]
        cmp.w   #2,GV_NPL(a6)
        blo.s   .x
        move.w  GV_RX+RXSZ+RX_XR(a6),d3     ; Rex 1
        move.w  d3,d4
        addq.w  #1,d4
        move.w  d4,(a0)+                    ; E[4]
        move.w  d0,d4
        cmp.w   d3,d4
        bge.s   .e2
        move.w  d3,d4
.e2:    addq.w  #1,d4
        move.w  d4,(a0)+                    ; E[5]
        move.w  d1,d4
        cmp.w   d3,d4
        bge.s   .e3
        move.w  d3,d4
.e3:    addq.w  #1,d4
        move.w  d4,(a0)+                    ; E[6]
        cmp.w   d3,d2
        bge.s   .e4
        move.w  d3,d2
.e4:    addq.w  #1,d2
        move.w  d2,(a0)                     ; E[7]
.x:     rts

;----------------------------------------------------------------------
; --- g5l_pcget --- la cache del plan: si una foto anterior tuvo la misma
; clave (g5l_pckey), su resultado de need/plan/sweep. Nada de eso depende
; de la x (g5l_place la usa con GV_E/GV_X0/GV_XM de esta foto)
; entrada:  a6 = g5l_v, GV_MSH/GV_R0/GV_COL/GV_VLIST, GV_KBUF
; salida:   d0 = 0 (Z) y GV_VAR, GV_NREM, GV_REM y las cubetas; 1 (NZ) no
; registros destruidos: d0-d3/a0-a4
;----------------------------------------------------------------------
g5l_pcget:
        bsr     g5l_pckey
        lea     GV_PC(a6),a2
        moveq   #PC_N-1,d2
.e:     lea     GV_PK(a6),a0
        move.l  a2,a1
        moveq   #16-1,d1
.c:     cmpm.l  (a0)+,(a1)+
        bne.s   .n
        dbf     d1,.c
        move.l  PC_VAR(a2),GV_VAR(a6)
        move.w  PC_NREM(a2),GV_NREM(a6)
        lea     PC_REM(a2),a0
        lea     GV_REM(a6),a1
        rept    2*G5L_NREM                  ; R1: desenrollado
        move.l  (a0)+,(a1)+
        endr
        lea     PC_LEN(a2),a3               ; las cubetas
        lea     PC_TRB(a2),a0
        lea     GV_BS(a6),a4
        moveq   #5-1,d3
.b:     move.l  (a4)+,a1
        move.w  (a3)+,d1
        beq.s   .be
        lsr.w   #2,d1
        subq.w  #1,d1
.bc:    move.l  (a0)+,(a1)+
        dbf     d1,.bc
.be:    move.l  a1,GV_BP-GV_BS-4(a4)
        dbf     d3,.b
        moveq   #0,d0
        rts
.n:     lea     PCSZ(a2),a2
        dbf     d2,.e
        moveq   #1,d0
        rts

;----------------------------------------------------------------------
; --- g5l_pcput --- guardar el resultado del camino completo en la cache
; del plan (la entrada GV_PCNX, rotando); no si las transiciones no caben
; entrada:  a6 = g5l_v, GV_PK (de g5l_pcget en este frame)
; registros destruidos: d0-d3/a0-a4
;----------------------------------------------------------------------
g5l_pcput:
        lea     GV_BP(a6),a0                ; bytes de las cubetas
        moveq   #0,d0
        moveq   #5-1,d1
.s:     move.l  (a0),d2
        sub.l   GV_BS-GV_BP(a0),d2
        add.l   d2,d0
        addq.l  #4,a0
        dbf     d1,.s
        cmp.l   #8*PC_NTR,d0
        bhi     .x
        lea     GV_PC(a6),a2
        move.w  GV_PCNX(a6),d0
        add.w   d0,a2
        add.w   #PCSZ,d0
        cmp.w   #PC_N*PCSZ,d0
        blo.s   .w
        moveq   #0,d0
.w:     move.w  d0,GV_PCNX(a6)
        lea     GV_PK(a6),a0
        move.l  a2,a1
        rept    16                          ; R1: desenrollado
        move.l  (a0)+,(a1)+
        endr
        move.l  GV_VAR(a6),PC_VAR(a2)
        move.w  GV_NREM(a6),PC_NREM(a2)
        lea     GV_REM(a6),a0
        lea     PC_REM(a2),a1
        rept    2*G5L_NREM
        move.l  (a0)+,(a1)+
        endr
        lea     PC_LEN(a2),a3
        lea     PC_TRB(a2),a1
        lea     GV_BP(a6),a4
        moveq   #5-1,d3
.b:     move.l  GV_BS-GV_BP(a4),a0
        move.l  (a4)+,d1
        sub.l   a0,d1
        move.w  d1,(a3)+
        beq.s   .be
        lsr.w   #2,d1
        subq.w  #1,d1
.bc:    move.l  (a0)+,(a1)+
        dbf     d1,.bc
.be:    dbf     d3,.b
.x:     rts

; --- g5l_pckey --- GV_PK = .l GV_VLIST, .w GV_R0, .w GV_MSH, .l GV_COL,
; GV_KBUF (52 B). Lo que cambia de una foto a otra va primero: g5l_pcget
; falla en la primera .l en vez de la ~7a (R1). La primera palabra nunca
; es -1 (la entrada vacia): VLIST es una direccion absoluta.
; registros destruidos: a0-a1
g5l_pckey:
        lea     GV_PK(a6),a1
        move.l  GV_VLIST(a6),(a1)+
        move.w  GV_R0(a6),(a1)+
        move.w  GV_MSH(a6),(a1)+
        move.l  GV_COL(a6),(a1)+
        lea     GV_KBUF(a6),a0
        rept    13
        move.l  (a0)+,(a1)+
        endr
        rts

;----------------------------------------------------------------------
; --- g5l_clean --- los sufijos que esta lista tiene de hace dos frames
; entrada:  a2 = lista, a3 = registros, a6 = g5l_v
; registros destruidos: d0-d2/a0-a1
;----------------------------------------------------------------------
g5l_clean:
        move.w  (a3),d2
        beq.s   .x
        clr.w   (a3)
        lea     2(a3),a1
        subq.w  #1,d2
.l:     move.l  (a1)+,a0                    ; J
        move.l  (a1)+,d0                    ; w0
        move.l  (a1)+,d1                    ; w1
        cmp.l   (a0),d0
        bne.s   .n
        cmp.l   4(a0),d1
        bne.s   .n
        moveq   #0,d0
        move.w  (a1),d0                     ; s
        addq.w  #1,d0
        lsl.l   #8,d0                       ; SEG = 256
        add.l   a2,d0
        add.l   #CL_LINES,d0                ; el segmento siguiente
        move.w  #$0084,(a0)+
        swap    d0
        move.w  d0,(a0)+
        move.w  #$0086,(a0)+
        swap    d0
        move.w  d0,(a0)+
        move.l  #$008a0000,(a0)
.n:     addq.l  #4,a1
        dbf     d2,.l
.x:     rts

;----------------------------------------------------------------------
; --- g5l_mario --- tramos por indice de Mario (como mspr.c), con una
; cache LRU de 4 poses: la clave es la pose relativa a su caja y los
; punteros de GFX32; el resultado, relativo a la fila by + 1
; entrada:  a4 = foto G5L, a6 = g5l_v
; salida:   GV_MCUR (0: Mario no cuenta), GV_WBASE, GV_XM
; registros destruidos: d0-d7/a0-a3
;----------------------------------------------------------------------
g5l_mario:
        clr.l   GV_MCUR(a6)
        move.w  #-1,GV_XM(a6)
        lea     GV_ENT(a6),a1
        moveq   #0,d7                       ; d7 = entradas
        move.w  #1000,d2                    ; bx
        move.w  #1000,d3                    ; by
        move.w  #-1000,d4                   ; x1
        move.w  #-1000,d5                   ; y1
        moveq   #0,d6                       ; e
.e:     move.w  d6,d0
        lsl.w   #2,d0
        moveq   #0,d1
        move.b  1(a4,d0.w),d1               ; y
        cmp.w   #$F0,d1
        beq     .en
        blo.s   .ey
        sub.w   #256,d1
.ey:    move.w  d1,2(a1)                    ; ey
        moveq   #0,d1
        move.b  (a4,d0.w),d1                ; x
        btst    #0,G5F_MOSZ(a4,d6.w)
        beq.s   .ex
        sub.w   #256,d1                     ; (x | $100) - 512
.ex:    move.w  d1,(a1)                     ; ex
        move.b  2(a4,d0.w),4(a1)            ; tile
        move.b  3(a4,d0.w),5(a1)            ; attr
        moveq   #1,d0
        btst    #1,G5F_MOSZ(a4,d6.w)
        beq.s   .nt
        moveq   #2,d0
.nt:    move.w  d0,6(a1)
        lsl.w   #3,d0                       ; tamano
        cmp.w   (a1),d2
        ble.s   .b1
        move.w  (a1),d2
.b1:    cmp.w   2(a1),d3
        ble.s   .b2
        move.w  2(a1),d3
.b2:    move.w  (a1),d1
        add.w   d0,d1
        cmp.w   d1,d4
        bge.s   .b3
        move.w  d1,d4
.b3:    move.w  2(a1),d1
        add.w   d0,d1
        cmp.w   d1,d5
        bge.s   .b4
        move.w  d1,d5
.b4:    addq.l  #8,a1
        addq.w  #1,d7
.en:    addq.w  #1,d6
        cmp.w   #4,d6
        blo     .e
        tst.w   d7
        beq     .x
        sub.w   d2,d4
        cmp.w   #32,d4
        bgt     .x
        sub.w   d3,d5
        cmp.w   #40,d5
        bgt     .x
        move.w  d3,d0
        addq.w  #1,d0
        move.w  d0,GV_WBASE(a6)
        move.w  d2,GV_BX(a6)
        ; la clave: n, entradas relativas, punteros
        lea     GV_KBUF(a6),a0
        moveq   #0,d0                       ; R1: 12 ciclos por .l (clr.l 20 + dbf)
        rept    13
        move.l  d0,(a0)+
        endr
        lea     GV_KBUF(a6),a0
        move.w  d7,(a0)+
        lea     GV_ENT(a6),a1
        move.w  d7,d6
        subq.w  #1,d6
.kk:    move.w  (a1),d0
        sub.w   d2,d0
        move.b  d0,(a0)+                    ; dx
        move.w  2(a1),d0
        sub.w   d3,d0
        move.b  d0,(a0)+                    ; dy
        move.b  4(a1),(a0)+                 ; tile
        move.b  5(a1),(a0)+                 ; attr
        move.b  7(a1),(a0)+                 ; nt
        addq.l  #1,a0
        addq.l  #8,a1
        dbf     d6,.kk
        lea     GV_KBUF+26(a6),a0
        lea     G5F_PTRS(a4),a1             ; (par: foto + 28)
        move.l  (a1)+,(a0)+
        move.l  (a1)+,(a0)+
        move.l  (a1)+,(a0)+
        move.l  (a1)+,(a0)+
        move.l  (a1)+,(a0)+
        move.l  (a1)+,(a0)+
        clr.b   GV_KBUF+26(a6)              ; $0D84 y $0D9B no son punteros:
        clr.b   GV_KBUF+49(a6)              ; fuera de la clave
        ; y solo los pares de punteros que leen las fichas de las entradas
        ; (g5l_gtile): una ficha animada que Mario no muestra (avanza una
        ; ficha por frame) hacia fallar la cache en cada foto
        moveq   #0,d4                       ; d4 = pares usados (bit = par)
        lea     GV_ENT(a6),a1
        move.w  d7,d6
        subq.w  #1,d6
.pu:    moveq   #0,d0
        move.b  4(a1),d0                    ; ficha
        bsr    .pt
        cmp.w   #2,6(a1)
        bne.s   .pn
        addq.w  #1,d0                       ; 16 x 16: t + 1, t + 16, t + 17
        bsr    .pt
        add.w   #15,d0
        bsr    .pt
        addq.w  #1,d0
        bsr    .pt
.pn:    addq.l  #8,a1
        dbf     d6,.pu
        lea     GV_KBUF+27(a6),a0           ; los otros pares, a cero
        moveq   #0,d3
.pc:    btst    d3,d4
        bne.s   .pk
        clr.b   (a0)
        clr.b   1(a0)
.pk:    addq.l  #2,a0
        addq.w  #1,d3
        cmp.w   #11,d3
        blo.s   .pc
        ; buscar en la cache, en orden LRU
        lea     GV_MORD(a6),a2
        moveq   #4-1,d6
.cs:    moveq   #0,d0
        move.b  (a2)+,d0
        mulu    #MCSZ,d0
        lea     GV_MC(a6),a0
        add.l   d0,a0                       ; a0 = entrada
        move.l  a0,a3
        lea     GV_KBUF(a6),a1
        moveq   #13-1,d1
.cc:    cmpm.l  (a0)+,(a1)+
        bne.s   .cn
        dbf     d1,.cc
        bra.s   .hit
.cn:    dbf     d6,.cs
        ; fallo: la ultima del orden
        lea     GV_MORD+3(a6),a2
        moveq   #0,d0
        move.b  (a2),d0
        mulu    #MCSZ,d0
        lea     GV_MC(a6),a3
        add.l   d0,a3
        addq.l  #1,a2
        bsr     g5l_mfill
.hit:   ; a2 = detras del indice encontrado en GV_MORD: llevarlo al frente
        subq.l  #1,a2
        move.b  (a2),d0
        lea     GV_MORD(a6),a0
.mv:    cmp.l   a0,a2
        beq.s   .mv2
        move.b  -1(a2),(a2)
        subq.l  #1,a2
        bra.s   .mv
.mv2:   move.b  d0,(a0)
        move.l  a3,GV_MCUR(a6)
        move.w  GV_BX(a6),d0                ; xm = min(255, bx + xrel)
        add.w   MC_XREL(a3),d0
        cmp.w   #255,d0
        ble.s   .xm
        move.w  #255,d0
.xm:    move.w  d0,GV_XM(a6)
.x:     rts
; .pt: d0 = ficha de la VRAM (& 255): su par de punteros a d4 (como
; g5l_gtile: $7F el 10; t < $20 con (t & 15) < 10 el (t & 15) / 2, + 5
; en la fila de abajo). Destruye d1/d3
.pt:    move.w  d0,d1
        and.w   #255,d1
        cmp.w   #$7F,d1
        bne.s   .p1
        bset    #10,d4
        rts
.p1:    cmp.w   #$20,d1
        bhs.s   .p9
        move.w  d1,d3
        and.w   #15,d3
        cmp.w   #10,d3
        bhs.s   .p9
        lsr.w   #1,d3
        btst    #4,d1
        beq.s   .p2
        addq.w  #5,d3
.p2:    bset    d3,d4
.p9:    rts

; --- g5l_mfill --- calcular la entrada a3 de la cache para GV_KBUF/GV_ENT:
; por indice, las filas 0..63 (desde by + 1) en que Mario lo usa, de las
; fichas traspuestas de la tabla (por ficha de GFX32: pares indice x 8,
; filas 0..7); con volteo V, las filas al reves. a4 = foto G5L.
; registros destruidos: d0-d7/a0-a1 (preserva a2/a3)
g5l_mfill:
        movem.l a2-a3/a5,-(sp)
        move.l  a3,a0                       ; la clave
        lea     GV_KBUF(a6),a1
        moveq   #13-1,d0
.ck:    move.l  (a1)+,(a0)+
        dbf     d0,.ck
        move.w  #-1,MC_XREL(a3)
        move.w  #$8000,MC_R0(a3)            ; MC_W sin calcular
        clr.w   MC_RV(a3)                   ; (y sus tramos)
        lea     MC_MM(a3),a0                ; mascaras a 0
        moveq   #15-1,d0
.z:     clr.l   (a0)+
        clr.l   (a0)+
        dbf     d0,.z
        lea     GV_ENT(a6),a1
        move.w  GV_KBUF(a6),d7
        subq.w  #1,d7
.ent:   move.w  6(a1),d4                    ; nt
        move.w  (a1),d0                     ; xrel = max(ex - bx + 8 nt - 1)
        sub.w   GV_BX(a6),d0
        move.w  d4,d1
        lsl.w   #3,d1
        add.w   d1,d0
        subq.w  #1,d0
        cmp.w   MC_XREL(a3),d0
        ble.s   .xr
        move.w  d0,MC_XREL(a3)
.xr:    moveq   #0,d6                       ; ty
.ty:    moveq   #0,d5                       ; tx
.tx:    moveq   #0,d0
        move.b  4(a1),d0                    ; tile + (hf ? nt-1-tx : tx)
        move.w  d5,d1
        btst    #6,5(a1)
        beq.s   .h0
        move.w  d4,d1
        subq.w  #1,d1
        sub.w   d5,d1
.h0:    add.w   d1,d0
        move.w  d6,d1                       ; + 16 (vf ? nt-1-ty : ty)
        tst.b   5(a1)
        bpl.s   .v0
        move.w  d4,d1
        subq.w  #1,d1
        sub.w   d6,d1
.v0:    lsl.w   #4,d1
        add.w   d1,d0
        and.w   #255,d0
        bsr     g5l_gtile                   ; d0 = ficha*16 o -1
        bmi     .tn
        lsr.l   #3,d0                       ; ficha*2: su offset en la traspuesta
        move.l  GV_TT(a6),a0
        move.w  (a0,d0.l),d0
        add.w   d0,a0                       ; a0 = n, n x (indice, filas)
        move.w  2(a1),d2                    ; j = ey - by + 8 ty (fila de la cache)
        addq.w  #1,d2
        sub.w   GV_WBASE(a6),d2
        move.w  d6,d0
        lsl.w   #3,d0
        add.w   d0,d2
        moveq   #0,d3
        move.b  (a0)+,d3                    ; pares
        subq.w  #1,d3
        bmi     .tn
        ; las filas j..j+7: el byte de filas desplazado j & 15, en el .l que
        ; empieza en la palabra de las filas 16 (w + 1)..: con las 64 filas
        ; big endian (.l 32..63, .l 0..31) la palabra w = j >> 4 esta en
        ; 6 - 2w y ese .l en 4 - 2w (w = 3: 2 B antes, que reciben ceros)
        move.w  d2,d0
        lsr.w   #4,d0
        add.w   d0,d0
        neg.w   d0
        lea     MC_MM-8+4(a3),a5
        add.w   d0,a5                       ; a5 = mascaras - 8 (indice x 8)
        and.w   #15,d2                      ; d2 = desplazamiento
        tst.b   5(a1)
        bmi.s   .pv
.pn:    moveq   #0,d1
        move.b  (a0)+,d1                    ; indice x 8
        moveq   #0,d0
        move.b  (a0)+,d0                    ; filas 0..7 de la ficha
        lsl.l   d2,d0
        or.l    d0,(a5,d1.w)
        dbf     d3,.pn
        bra.s   .tn
.pv:    lea     GV_REV(a6),a2               ; volteo V: las filas al reves
.pv1:   moveq   #0,d1
        move.b  (a0)+,d1
        moveq   #0,d0
        move.b  (a0)+,d0
        move.b  (a2,d0.w),d0
        lsl.l   d2,d0
        or.l    d0,(a5,d1.w)
        dbf     d3,.pv1
.tn:    addq.w  #1,d5
        cmp.w   d4,d5
        blo     .tx
        addq.w  #1,d6
        cmp.w   d4,d6
        blo     .ty
        addq.l  #8,a1
        dbf     d7,.ent
        lea     MC_MM(a3),a0                ; primera y ultima fila de cada indice
        lea     MC_FL(a3),a2
        lea     GV_BITS(a6),a1
        moveq   #15-1,d2
.fl:    move.l  (a0)+,d4                    ; filas 32..63
        move.l  (a0)+,d3                    ; 0..31
        move.l  d3,d0
        or.l    d4,d0
        bne.s   .fl1
        st      (a2)+
        st      (a2)+
        bra    .fl9
.fl1:   move.l  d3,d0
        beq.s   .fl2
        LOWB
        bra.s   .fl3
.fl2:   move.l  d4,d0
        LOWB
        add.w   #32,d1
.fl3:   move.b  d1,(a2)+
        move.l  d4,d0
        beq.s   .fl4
        HIGHB
        add.w   #32,d1
        bra.s   .fl5
.fl4:   move.l  d3,d0
        HIGHB
.fl5:   move.b  d1,(a2)+
.fl9:   dbf     d2,.fl
        movem.l (sp)+,a2-a3/a5
        rts

; --- g5l_gtile --- d0 = ficha de la VRAM de sprites de Mario (0..255) ->
; d0.l = 16 * ficha de GFX32, o -1 (N) si no hay. a4 = foto G5L.
; registros destruidos: d0-d1
g5l_gtile:
        cmp.w   #$7F,d0
        bne.s   .a
        moveq   #0,d0
        move.b  G5F_PTRS+22(a4),d0
        lsl.w   #8,d0
        move.b  G5F_PTRS+21(a4),d0
        bra.s   .c
.a:     cmp.w   #$20,d0
        bhs.s   .no
        move.w  d0,d1
        and.w   #15,d1
        cmp.w   #10,d1
        bhs.s   .no
        lsr.w   #1,d1
        add.w   d1,d1                       ; ((t & 15) >> 1) * 2
        btst    #4,d0
        beq.s   .a1
        add.w   #10,d1
.a1:    and.w   #1,d0
        lsl.w   #5,d0                       ; (t & 1) * 32
        move.w  d0,-(sp)
        moveq   #0,d0
        move.b  G5F_PTRS+2(a4,d1.w),d0
        lsl.w   #8,d0
        move.b  G5F_PTRS+1(a4,d1.w),d0
        add.w   (sp)+,d0
.c:     sub.w   #$2000,d0
        bcs.s   .no
        cmp.w   #$5D00-32,d0
        bhi.s   .no
        and.l   #$ffff,d0
        lsr.l   #5,d0
        lsl.l   #4,d0
        rts
.no:    moveq   #-1,d0
        rts

;----------------------------------------------------------------------
; --- g5l_choose --- el Rex visible mas alto (fila, ranura) con forma en
; la tabla. G5L-N: la clave va normalizada (dx, dy menos su minimo como
; s8); ese minimo se suma a sx/sy, que es el origen de las variantes.
; entrada:  a4 = foto G5L, a6 = g5l_v
; salida:   d0 = candidatos (GV_NC, en GV_CAND por fila y ranura) y el
;           primero en GV_R0/X0/VLIST/NVAR/SLOT; 0 si no hay
; registros destruidos: d0-d7/a0-a3
;----------------------------------------------------------------------
g5l_choose:
        clr.w   GV_NC(a6)
        moveq   #0,d0
        move.b  G5F_NREX(a4),d0
        beq     .none
        move.w  d0,GV_TMP2(a6)              ; Rex que quedan
        lea     G5F_REX(a4),a1
.rex:   moveq   #0,d6
        move.b  1(a1),d6                    ; d6 = fichas
        move.w  2(a1),d4
        sub.w   G5F_CAMX(a4),d4             ; d4 = sx
        move.w  4(a1),d5
        sub.w   G5F_CAMY(a4),d5             ; d5 = sy
        ; G5L-N: el minimo de dx y dy (s8) de las fichas, sumado a sx/sy
        lea     6(a1),a0
        move.w  d6,d2
        subq.w  #1,d2
        moveq   #127,d1                     ; d1 = min dx
        moveq   #127,d3                     ; d3 = min dy
.mn:    move.b  (a0)+,d0
        sub.b   d4,d0
        cmp.b   d1,d0
        bge.s   .m1
        move.b  d0,d1
.m1:    move.b  (a0)+,d0
        sub.b   d5,d0
        cmp.b   d3,d0
        bge.s   .m2
        move.b  d0,d3
.m2:    addq.l  #3,a0                       ; tile, attr, hi
        dbf     d2,.mn
        ext.w   d1
        add.w   d1,d4                       ; d4 = sx + min dx
        ext.w   d3
        add.w   d3,d5                       ; d5 = sy + min dy
        ; clave: dx, dy, tile, banderas; la prioridad de todas igual
        lea     6(a1),a0
        lea     GV_KEY(a6),a2
        lea     GV_AF(a6),a3
        move.w  d6,d7                       ; d7 = suma (hash: mod 64)
        moveq   #0,d3
        move.b  3(a0),d3
        and.b   #$30,d3                     ; la prioridad de la primera
        move.w  d6,d2
        subq.w  #1,d2
.k:     move.b  (a0)+,d0                    ; x
        sub.b   d4,d0
        move.b  d0,(a2)+
        add.b   d0,d7
        move.b  (a0)+,d0                    ; y
        sub.b   d5,d0
        move.b  d0,(a2)+
        add.b   d0,d7
        move.b  (a0)+,d0                    ; tile
        move.b  d0,(a2)+
        add.b   d0,d7
        moveq   #0,d1
        move.b  (a0)+,d1                    ; attr
        move.b  (a3,d1.w),d0                ; sus banderas (GV_AF)
        and.b   #$30,d1
        cmp.b   d1,d3
        bne     .nx                         ; prioridades mixtas: no
        moveq   #2,d1
        and.b   (a0)+,d1                    ; hi: tamano
        or.b    d1,d0
        move.b  d0,(a2)+
        add.b   d0,d7
        dbf     d2,.k
        lsr.w   #4,d3                       ; d3 = prioridad (0..3)
        ; la forma
        and.w   #63,d7
        add.w   d7,d7
        move.l  GV_TAB(a6),a3
        moveq   #0,d0
        move.w  16(a3,d7.w),d0
.ch:    tst.w   d0
        beq     .nx
        move.l  GV_TAB(a6),a3
        lea     (a3,d0.l),a0                ; a0 = forma
        moveq   #0,d1
        move.b  2(a0),d1
        cmp.w   d6,d1
        bne     .cn
        moveq   #0,d1
        move.b  3(a0),d1
        cmp.w   d1,d3
        bne     .cn
        lea     6(a0),a2
        lea     GV_KEY(a6),a3
        move.w  d6,d1
        subq.w  #1,d1
.cc:    cmpm.b  (a2)+,(a3)+
        bne     .cn
        cmpm.b  (a2)+,(a3)+
        bne     .cn
        cmpm.b  (a2)+,(a3)+
        bne     .cn
        cmpm.b  (a2)+,(a3)+
        bne     .cn
        dbf     d1,.cc
        ; encontrada: a2 = lista de variantes, a0 = forma
        move.l  GV_TAB(a6),a3
        move.l  (a2),d0
        lea     (a3,d0.l),a3                ; a3 = la primera variante
        move.w  d4,d0
        add.w   (a3),d0                     ; x0 = sx + ox
        move.w  d5,d1
        add.w   2(a3),d1
        addq.w  #1,d1                       ; r0 = sy + oy + 1
        moveq   #0,d2
        move.b  5(a3),d2                    ; alto
        add.w   d1,d2
        ble.s   .nx
        cmp.w   #LINES,d1
        bge.s   .nx
        moveq   #0,d2
        move.b  4(a3),d2                    ; ancho
        add.w   d0,d2
        ble.s   .nx
        cmp.w   #256,d0
        bge.s   .nx
        ; G4-2: a GV_CAND por (r0, ranura); las ranuras llegan en orden,
        ; asi que con el mismo r0 va detras
        moveq   #0,d4
        move.b  5(a3),d4                    ; alto
        moveq   #0,d5
        move.b  (a1),d5                     ; ranura
        move.w  GV_NC(a6),d2
        lea     GV_CAND(a6),a3
        move.w  d2,d7
        lsl.w   #4,d7
        add.w   d7,a3                       ; a3 = el final
.ins:   tst.w   d2
        beq.s   .put
        cmp.w   CA_R0-CASZ(a3),d1
        bge.s   .put
        move.l  -16(a3),(a3)
        move.l  -12(a3),4(a3)
        move.l  -8(a3),8(a3)
        move.l  -4(a3),12(a3)
        lea     -CASZ(a3),a3
        subq.w  #1,d2
        bra.s   .ins
.put:   move.w  d1,CA_R0(a3)
        move.w  d0,CA_X0(a3)
        move.l  a2,CA_VL(a3)
        move.w  4(a0),CA_NV(a3)
        move.w  d5,CA_SL(a3)
        move.w  d4,CA_H(a3)
        clr.w   CA_DEAD(a3)
        addq.w  #1,GV_NC(a6)
        bra.s   .nx
.cn:    move.w  (a0),d0                     ; siguiente del cubo
        bra     .ch
.nx:    lea     G5L_RECSZ(a1),a1
        subq.w  #1,GV_TMP2(a6)
        bne     .rex
        move.w  GV_NC(a6),d0                ; el primero, para el camino de uno
        beq.s   .none
        lea     GV_CAND(a6),a0
        move.w  CA_R0(a0),GV_R0(a6)
        move.w  CA_X0(a0),GV_X0(a6)
        move.w  CA_SL(a0),GV_SLOT(a6)
        move.l  CA_VL(a0),GV_VLIST(a6)
        move.w  CA_NV(a0),GV_NVAR(a6)
        rts
.none:  moveq   #0,d0
        rts

; --- g5l_mrow --- d0.l = las filas r0..r0+31 de Mario con el indice d1
; en pantalla (Mw) y a0 = su entrada en la cache (.l Mw, .w B, .w A; B y
; A los pone g5l_mba). Se guarda mientras r0 y r0 - by no cambien
; (MC_WOK; g5l_render). Sin Mario: Mw = 0 (y B = A = -1).
; Preserva d1-d7/a1-a6.
g5l_mrow:
        move.l  GV_MCUR(a6),d0
        beq.s   .none
        move.l  d0,a0
        move.w  MC_WOK(a0),d0
        btst    d1,d0
        beq.s   .calc
        move.w  d1,d0
        lsl.w   #3,d0
        lea     MC_W-8(a0),a0
        add.w   d0,a0
        move.l  (a0),d0
        rts
.none:  lea     GV_WNONE(a6),a0
        moveq   #0,d0
        rts
.calc:  bset    d1,d0
        move.w  d0,MC_WOK(a0)
        movem.l d1-d3/a1,-(sp)
        move.w  d1,d0
        lsl.w   #3,d0
        lea     MC_MM-8(a0,d0.w),a1         ; a1 = sus 64 filas
        lea     MC_W-8(a0),a0
        add.w   d0,a0                       ; a0 = su entrada
        move.l  4(a1),d2                    ; filas 0..31 de la cache
        move.l  (a1),d3                     ; 32..63
        move.w  GV_MSH(a6),d0
        bmi.s   .l
        cmp.w   #32,d0
        bhs.s   .b
        lsr.l   d0,d2
        moveq   #32,d1
        sub.w   d0,d1
        lsl.l   d1,d3                       ; (32: queda 0)
        or.l    d3,d2
        bra.s   .v
.b:     sub.w   #32,d0
        cmp.w   #32,d0
        bhs.s   .z
        lsr.l   d0,d3
        move.l  d3,d2
        bra.s   .v
.l:     neg.w   d0
        cmp.w   #32,d0
        bhs.s   .z
        lsl.l   d0,d2
.v:     and.l   GV_MV(a6),d2
        bra.s   .s
.z:     moveq   #0,d2
.s:     move.l  d2,(a0)
        move.l  d2,d0
        movem.l (sp)+,d1-d3/a1
        rts

; --- g5l_mrowba --- g5l_mrow y g5l_mba juntos (el barrido): d0.l = Mw,
; GV_SB y GV_SA. Una sola comprobacion de la cache si ya estan (MC_BOK
; implica MC_WOK: g5l_mba solo se llama desde aqui). Preserva d1-d7/a1-a6.
g5l_mrowba:
        move.l  GV_MCUR(a6),d0
        beq.s   .none
        move.l  d0,a0
        move.w  MC_BOK(a0),d0
        btst    d1,d0
        beq.s   .calc
        move.w  d1,d0
        lsl.w   #3,d0
        lea     MC_W-8(a0),a0
        add.w   d0,a0
        move.l  4(a0),GV_SB(a6)             ; (y GV_SA)
        move.l  (a0),d0
        rts
.none:  move.l  #-1,GV_SB(a6)
        moveq   #0,d0
        rts
.calc:  bsr     g5l_mrow
        move.l  d0,-(sp)
        bsr     g5l_mba
        move.l  (sp)+,d0
        rts

; --- g5l_mwall --- Mw de los 15 indices de la entrada a0 de la cache para
; este r0, todos de una vez (lo de g5l_mrow): MC_W y MC_WOK
; registros destruidos: d0-d5/a1-a2
g5l_mwall:
        lea     MC_MM(a0),a1                ; (.l filas 32..63, .l 0..31)
        lea     MC_W(a0),a2
        move.l  GV_MV(a6),d5
        moveq   #15-1,d4
        move.w  GV_MSH(a6),d0
        bmi.s   .l
        cmp.w   #32,d0
        bhs.s   .b
        moveq   #32,d1
        sub.w   d0,d1
.m:     move.l  (a1)+,d3
        move.l  (a1)+,d2
        lsr.l   d0,d2
        lsl.l   d1,d3                       ; (32: queda 0)
        or.l    d3,d2
        and.l   d5,d2
        move.l  d2,(a2)
        addq.l  #8,a2
        dbf     d4,.m
        bra.s   .x
.b:     sub.w   #32,d0
        cmp.w   #32,d0
        bhs.s   .z
.b1:    move.l  (a1),d3
        addq.l  #8,a1
        lsr.l   d0,d3
        and.l   d5,d3
        move.l  d3,(a2)
        addq.l  #8,a2
        dbf     d4,.b1
        bra.s   .x
.l:     neg.w   d0
        cmp.w   #32,d0
        bhs.s   .z
.l1:    move.l  4(a1),d2
        addq.l  #8,a1
        lsl.l   d0,d2
        and.l   d5,d2
        move.l  d2,(a2)
        addq.l  #8,a2
        dbf     d4,.l1
        bra.s   .x
.z:     clr.l   (a2)
        addq.l  #8,a2
        dbf     d4,.z
.x:     move.w  #$fffe,MC_WOK(a0)           ; indices 1..15
        rts

; --- g5l_mba --- GV_SB / GV_SA del indice d1: la ultima fila de Mario
; antes de r0 y la primera despues de r0 + 31, en pantalla (-1: ninguna),
; guardadas en su entrada de la cache (MC_BOK) como Mw. De la mascara de
; 64 filas: M = GV_MSH, primera F y ultima L de MC_FL.
; Preserva d1-d7/a0-a6.
g5l_mba:
        move.l  a0,-(sp)
        move.l  GV_MCUR(a6),d0
        beq.s   .none
        move.l  d0,a0
        move.w  MC_BOK(a0),d0
        btst    d1,d0
        beq.s   .calc
        move.w  d1,d0
        lsl.w   #3,d0
        lea     MC_W-4(a0),a0
        add.w   d0,a0
        move.l  (a0),GV_SB(a6)              ; (y GV_SA)
        move.l  (sp)+,a0
        rts
.none:  move.l  #-1,GV_SB(a6)
        move.l  (sp)+,a0
        rts
.calc:  bset    d1,d0
        move.w  d0,MC_BOK(a0)
        movem.l d1-d5/a1-a3,-(sp)
        move.l  a0,a3                       ; a3 = entrada de la cache
        move.w  d1,d0
        lsl.w   #3,d0
        lea     MC_W-8(a3),a0
        add.w   d0,a0                       ; a0 = la del indice
        moveq   #-1,d0
        move.l  d0,4(a0)
        add.w   d1,d1
        lea     MC_FL-2(a3),a2
        moveq   #0,d0
        move.b  (a2,d1.w),d0                ; F
        cmp.b   #$ff,d0
        beq     .x                          ; Mario no usa el indice
        moveq   #0,d4
        move.b  1(a2,d1.w),d4               ; L
        lsl.w   #2,d1
        lea     MC_MM-8(a3,d1.w),a3         ; a3 = sus 64 filas
        lea     GV_BITS(a6),a1
        lea     GV_LM(a6),a2
        move.w  GV_MSH(a6),d1               ; M
        cmp.w   d1,d4
        blt     .bonly                      ; todas antes de r0
        move.w  d1,d5
        add.w   #32,d5
        cmp.w   d5,d0
        bge     .aonly                      ; todas despues de r0 + 31
        cmp.w   d1,d0                       ; B: la mas alta < M
        bge    .ma
        move.w  d1,d5
        cmp.w   #32,d5
        blt.s   .b1
        move.w  d5,d0
        sub.w   #32,d0
        lsl.w   #2,d0
        move.l  (a2,d0.w),d0
        and.l   (a3),d0
        beq.s   .b0
        HIGHB
        add.w   #32,d1
        bra.s   .b2
.b0:    move.l  4(a3),d0
        HIGHB
        bra.s   .b2
.b1:    move.w  d5,d0
        lsl.w   #2,d0
        move.l  (a2,d0.w),d0
        and.l   4(a3),d0
        HIGHB
.b2:    add.w   GV_WBASE(a6),d1
        bmi.s   .b3                         ; (fuera por arriba)
        move.w  d1,4(a0)
.b3:    move.w  d5,d1
.ma:    move.w  d1,d5                       ; A: la mas baja >= M + 32
        add.w   #32,d5
        cmp.w   d5,d4
        blt    .x
        cmp.w   #32,d5
        bge.s   .a1
        move.w  d5,d0
        lsl.w   #2,d0
        move.l  (a2,d0.w),d0
        not.l   d0
        and.l   4(a3),d0
        beq.s   .a0
        LOWB
        bra.s   .a2
.a0:    move.l  (a3),d0
        LOWB
        add.w   #32,d1
        bra.s   .a2
.a1:    move.w  d5,d0
        sub.w   #32,d0
        lsl.w   #2,d0
        move.l  (a2,d0.w),d0
        not.l   d0
        and.l   (a3),d0
        LOWB
        add.w   #32,d1
.a2:    add.w   GV_WBASE(a6),d1
        cmp.w   #LINES,d1
        bhs.s   .x                          ; (fuera por abajo)
        move.w  d1,6(a0)
.x:     move.l  4(a0),GV_SB(a6)             ; (y GV_SA)
        movem.l (sp)+,d1-d5/a1-a3
        move.l  (sp)+,a0
        rts
.bonly: add.w   GV_WBASE(a6),d4             ; B = L
        bmi.s   .x
        move.w  d4,4(a0)
        bra.s   .x
.aonly: add.w   GV_WBASE(a6),d0             ; A = F
        cmp.w   #LINES,d0
        bhs.s   .x
        move.w  d0,6(a0)
        bra.s   .x

; --- g5l_mvis --- GV_MSH y GV_MV del frame (r0 y la caja de Mario)
; registros destruidos: d0-d2
g5l_mvis:
        move.w  GV_R0(a6),d0
        move.w  d0,d1
        sub.w   GV_WBASE(a6),d1
        move.w  d1,GV_MSH(a6)
        moveq   #-1,d2                      ; filas r0 + k fuera de 0..223
        tst.w   d0
        bpl.s   .a
        move.w  d0,d1
        neg.w   d1
        cmp.w   #32,d1
        bhs.s   .z
        lsl.l   d1,d2
.a:     move.w  #LINES-1,d1
        sub.w   d0,d1                       ; ultima k valida
        bmi.s   .z
        cmp.w   #31,d1
        bhs.s   .x
        moveq   #31,d0
        sub.w   d1,d0
        moveq   #-1,d1
        lsr.l   d0,d1
        and.l   d1,d2
        bra.s   .x
.z:     moveq   #0,d2
.x:     move.l  d2,GV_MV(a6)
        rts


;----------------------------------------------------------------------
; --- g5l_fast --- g5l_plan + g5l_sweep juntos para la variante GV_VAR si
; no choca con Mario (g5l_need = 0: ningun indice en que el Rex tenga
; otro color que Mario lo usa en sus filas). Entonces g5l_render la elige
; si es la primera asi, no hay bandas y cada indice tiene un solo grupo:
; si Mario no tiene filas en la ventana, las dos transiciones del camino
; rapido de g5l_sweep; si las tiene, su recorrido general con dos
; conjuntos (Mario y el grupo). Los grupos de la tabla van por indice
; creciente, como GV_IM.
; entrada:  GV_VAR, GV_MV, GV_R0, GV_COL, la cache de Mario, a6 = g5l_v
; salida:   d0 = 0 (Z) y las cubetas; 1 (NZ) choca, y sus choques en
;           GV_NEED (variante GV_FM / 4)
; registros destruidos: d0-d7/a0-a5
;----------------------------------------------------------------------
g5l_fast:
        move.l  GV_VAR(a6),a0
        moveq   #0,d0
        move.b  5(a0),d0                    ; alto
        lsl.w   #2,d0
        lea     GV_LM(a6),a1
        move.l  (a1,d0.w),d6
        and.l   GV_MV(a6),d6                ; d6 = filas en pantalla
        moveq   #0,d0
        move.b  6(a0),d0
        lsl.w   #3,d0
        moveq   #0,d7
        move.b  9(a0),d7
        lea     12(a0,d0.w),a4              ; a4 = grupos (.b i .b 0 .w color .l filas)
        move.l  GV_COL(a6),a5
        move.l  a4,a2                       ; choques (como g5l_need)
        move.w  d7,d5
        moveq   #0,d2
        bra.s   .c9
.c:     moveq   #0,d1
        move.b  (a2),d1
        cmp.w   #2,d1
        bls.s   .cn                         ; blanco y negro
        move.w  d1,d0
        add.w   d0,d0
        move.w  (a5,d0.w),d0
        cmp.w   2(a2),d0
        beq.s   .cn
        move.l  4(a2),d4
        and.l   d6,d4
        beq.s   .cn
        MWLD
        and.l   d4,d0
        beq.s   .cn
        addq.w  #1,d2
.cn:    addq.l  #8,a2
.c9:    dbf     d5,.c
        tst.w   d2
        bne     .no
        lea     GV_BS(a6),a2                ; cubetas vacias
        lea     GV_BP(a6),a3
        move.l  (a2)+,(a3)+
        move.l  (a2)+,(a3)+
        move.l  (a2)+,(a3)+
        move.l  (a2)+,(a3)+
        move.l  (a2)+,(a3)+
        clr.w   GV_NREM(a6)
        lea     GV_BITS(a6),a1
        bra     .g9
.g:     move.l  4(a4),d0
        and.l   d6,d0
        beq     .gn
        moveq   #0,d2
        move.b  (a4),d2                     ; d2 = i
        move.w  d2,d1
        add.w   d1,d1
        move.w  (a5,d1.w),d3                ; d3 = color de Mario
        cmp.w   2(a4),d3
        beq     .gn                         ; del color de Mario: nada
        move.w  d2,d1
        bsr     g5l_mrowba                  ; Mw, GV_SB, GV_SA
        tst.l   d0
        bne     .gw                         ; Mario en la ventana
        move.l  4(a4),d0                    ; de su color desde su primera fila
        and.l   d6,d0
        LOWB
        move.w  d1,d0
        add.w   GV_R0(a6),d0
        move.w  GV_SB(a6),d4
        smi     d5
        addq.b  #1,d5                       ; (B: Mario; -1: nadie)
        ext.w   d5
        move.w  d3,-(sp)
        move.w  2(a4),d3
        TRB
        move.w  (sp)+,d3
        move.w  GV_SA(a6),d0
        bmi.s   .gn
        move.w  d0,-(sp)                    ; y de vuelta al de Mario en A
        move.l  4(a4),d0
        and.l   d6,d0
        HIGHB
        move.w  d1,d4
        add.w   GV_R0(a6),d4
        moveq   #2,d5
        move.w  (sp)+,d0
        TRB
.gn:    addq.l  #8,a4
.g9:    dbf     d7,.g
        moveq   #0,d0
        rts
.no:    move.w  GV_FM(a6),d0                ; sus choques (g5l_render)
        lsr.w   #1,d0
        lea     GV_NEED(a6),a0
        move.w  d2,(a0,d0.w)
        moveq   #1,d0
        rts
; el recorrido general de g5l_sweep con las entradas Mario (GV_TMP, color
; de Mario en (sp)) y el grupo (GV_TMP2, color 2(a4)): d6 = filas que
; quedan, d7 = las de la entrada actual, a0 = 1 (Mario) o 2 (el grupo)
.gw:    movem.l d6-d7,-(sp)
        move.l  d0,GV_TMP(a6)               ; M
        move.l  4(a4),d7
        and.l   d6,d7
        move.l  d7,GV_TMP2(a6)              ; R
        move.l  d0,d6
        or.l    d7,d6
        move.w  d3,-(sp)
        moveq   #0,d5
        move.w  GV_SB(a6),d4
        bmi.s   .wk
        moveq   #1,d5
.wk:    move.l  d6,d0
        beq     .we
        LOWB                                ; la primera que queda
        move.l  GV_TMP(a6),d7
        btst    d1,d7
        beq.s   .wr
        move.w  #1,a0                       ; de Mario
        cmp.w   (sp),d3
        beq.s   .ws
        move.w  (sp),d3
        bra.s   .wt
.wr:    move.l  GV_TMP2(a6),d7              ; del grupo
        move.w  #2,a0
        cmp.w   2(a4),d3
        beq.s   .ws
        move.w  2(a4),d3
.wt:    move.w  d1,d0
        add.w   GV_R0(a6),d0                ; hasta
        TRB
.ws:    move.l  d7,d0                       ; hasta la primera de otro color
        not.l   d0
        and.l   d6,d0
        beq.s   .wl
        LOWB                                ; d1 = esa fila
        moveq   #-1,d0
        lsl.l   d1,d0
        and.l   d0,d6
        not.l   d0
        and.l   d7,d0
        bra.s   .wh
.wl:    moveq   #0,d6
        move.l  d7,d0
.wh:    HIGHB                               ; d1 = la ultima de este color
        move.w  d1,d4
        add.w   GV_R0(a6),d4
        moveq   #0,d5
        move.l  GV_TMP(a6),d0
        btst    d1,d0
        beq.s   .w1
        moveq   #1,d5
.w1:    cmp.w   #2,a0
        bne     .wk
        addq.w  #2,d5
        bra     .wk
.we:    move.w  (sp)+,d0                    ; vuelta al color de Mario
        cmp.w   d0,d3
        beq.s   .wx
        move.w  d0,d3
        move.w  GV_SA(a6),d0
        bmi.s   .wx
        TRB
.wx:    movem.l (sp)+,d6-d7
        bra     .gn

;----------------------------------------------------------------------
; --- g5l_need --- cuantos colores de la variante chocan con Mario en su
; indice: en pantalla, en filas en que Mario lo usa con otro color
; (tools/g5l.py band_need)
; entrada:  a0 = variante, GV_MV, GV_COL, la cache de Mario, a6 = g5l_v
; salida:   d0 = choques
; registros destruidos: d0-d1/a0-a1
;----------------------------------------------------------------------
g5l_need:
        movem.l d2-d5/a2,-(sp)
        moveq   #0,d0
        move.b  5(a0),d0                    ; alto
        lsl.w   #2,d0
        lea     GV_LM(a6),a1
        move.l  (a1,d0.w),d4
        and.l   GV_MV(a6),d4                ; d4 = filas en pantalla
        moveq   #0,d0
        move.b  6(a0),d0
        lsl.w   #3,d0
        moveq   #0,d3
        move.b  9(a0),d3
        lea     12(a0,d0.w),a2              ; a2 = grupos (.b i .b 0 .w color .l filas)
        moveq   #0,d2
        move.l  GV_COL(a6),a1
        bra.s   .n9
.n:     moveq   #0,d1
        move.b  (a2),d1
        cmp.w   #2,d1
        bls.s   .nn                         ; blanco y negro
        move.w  d1,d0
        add.w   d0,d0
        move.w  (a1,d0.w),d0
        cmp.w   2(a2),d0
        beq.s   .nn                         ; Mario lo usa con ese color
        move.l  4(a2),d5
        and.l   d4,d5
        beq.s   .nn
        MWLD
        and.l   d5,d0
        beq.s   .nn
        addq.w  #1,d2
.nn:    addq.l  #8,a2
.n9:    dbf     d3,.n
        move.w  d2,d0
        movem.l (sp)+,d2-d5/a2
        rts

;----------------------------------------------------------------------
; --- g5l_plan --- G5L-R: los grupos (indice, color) de la variante limpia
; en pantalla, por indice (GV_IG), y las bandas que pasan un color propio
; del Rex a otro indice donde Mario usa el suyo con otro color
; (tools/g5l.py band_assign)
; entrada:  GV_VAR, GV_MV, GV_COL, la cache de Mario, a6 = g5l_v
; salida:   d0 = 0 (Z) y GV_VIS/IG/IM/OCC/REM/NREM; 1 (NZ) sin indice
;           libre para una banda
; registros destruidos: d0-d7/a0-a5
;----------------------------------------------------------------------
g5l_plan:
        move.l  GV_VAR(a6),a0
        moveq   #0,d0
        move.b  5(a0),d0                    ; alto
        lea     GV_LM(a6),a1
        lsl.w   #2,d0
        move.l  (a1,d0.w),d6
        and.l   GV_MV(a6),d6                ; d6 = filas en pantalla
        move.l  d6,GV_VIS(a6)
        lea     GV_OCC(a6),a1
        moveq   #0,d0
        rept    16
        move.l  d0,(a1)+
        endr
        clr.w   GV_NREM(a6)
        moveq   #0,d0
        move.b  6(a0),d0
        lsl.w   #3,d0
        moveq   #0,d7
        move.b  9(a0),d7                    ; grupos de la tabla
        lea     12(a0,d0.w),a0              ; a0 = grupos (.b i .b 0 .w color .l filas)
        lea     GV_OCC(a6),a2
        lea     GV_IG(a6),a3
        moveq   #0,d5                       ; indices en pantalla
        moveq   #0,d4                       ; grupo de la tabla
        bra.s   .g9
.g:     move.l  4(a0),d1
        and.l   d6,d1
        beq.s   .gn
        moveq   #0,d0
        move.b  (a0),d0
        bset    d0,d5
        move.w  d0,d2
        lsl.w   #6,d2                       ; IGSZ
        lea     (a3,d2.w),a1
        move.w  #1,(a1)+                    ; (la limpia: un grupo por indice)
        clr.w   (a1)+
        move.w  2(a0),(a1)+
        move.w  d4,(a1)+
        move.l  d1,(a1)
        lsl.w   #2,d0
        move.l  d1,(a2,d0.w)
.gn:    addq.l  #8,a0
        addq.w  #1,d4
.g9:    dbf     d7,.g
        move.w  d5,GV_IM(a6)
        tst.l   GV_MCUR(a6)
        beq     .ok                         ; sin Mario nada choca
        move.l  GV_VAR(a6),a0               ; G5L3: los del mapa de la
        moveq   #0,d0                       ; variante (nibble alto del .b
        move.b  7(a0),d0                    ; 7: mapa x 16), en la tabla
        and.w   #$f0,d0
        move.l  GV_TAB(a6),a5
        add.w   10(a5),d0
        add.w   d0,a5
        lea     GV_BITS(a6),a1
.ic:    moveq   #0,d2
        move.b  (a5)+,d2                    ; d2 = ic (0: fin)
        beq     .ok
        move.w  GV_IM(a6),d0
        btst    d2,d0
        beq.s   .ic                         ; no esta en pantalla
        move.w  d2,d0
        lsl.w   #6,d0
        lea     GV_IG+4(a6),a4
        add.w   d0,a4                       ; a4 = su grupo limpio
        move.w  (a4),d3                     ; d3 = c
        move.w  d2,d0
        add.w   d0,d0
        move.l  GV_COL(a6),a0
        cmp.w   (a0,d0.w),d3
        beq.s   .ic                         ; Mario lo usa con ese mismo color
        move.w  d2,d1
        MWLD
        move.l  4(a4),d7                    ; d7 = rc
        and.l   d7,d0                       ; k: filas en que chocan
        beq.s   .ic
        move.l  d0,d6
        LOWB                                ; d1 = primera fila de k
        moveq   #-1,d4
        lsl.l   d1,d4                       ; d4 = filas >= esa
        move.l  d6,d0
        HIGHB                               ; d1 = ultima
        moveq   #-2,d5
        lsl.l   d1,d5
        not.l   d5                          ; d5 = filas <= esa
        and.l   d7,d4                       ; d4 = desde la primera de k
        and.l   d4,d5                       ; d5 = de la primera a la ultima
        bsr     .find
        bmi     .fail
.got:   move.l  d6,d1                       ; d0 = f, d6 = banda
        not.l   d1
        and.l   d1,4(a4)                    ; el grupo de ic sin la banda
        lea     GV_OCC(a6),a0
        move.w  d2,d4
        lsl.w   #2,d4
        and.l   d1,(a0,d4.w)
        move.w  d0,d4
        lsl.w   #2,d4
        or.l    d6,(a0,d4.w)
        move.w  d0,d4                       ; grupo nuevo de f: (c, el de la tabla)
        lsl.w   #6,d4
        lea     GV_IG(a6),a0
        add.w   d4,a0
        move.w  GV_IM(a6),d4
        bset    d0,d4
        bne.s   .g1
        clr.w   (a0)                        ; f no tenia grupos
        move.w  d4,GV_IM(a6)
.g1:    move.w  (a0),d4
        addq.w  #1,(a0)
        lsl.w   #3,d4
        lea     4(a0,d4.w),a0
        move.w  d3,(a0)+
        move.w  2(a4),(a0)+
        move.l  d6,(a0)
        move.w  GV_NREM(a6),d1              ; la banda (g5l_patch)
        addq.w  #1,GV_NREM(a6)
        lsl.w   #3,d1
        lea     GV_REM(a6),a0
        add.w   d1,a0
        move.b  d2,(a0)+
        move.b  d0,(a0)+
        move.b  3(a4),(a0)+
        clr.b   (a0)+
        move.l  d6,(a0)
        bra     .ic
.ok:    moveq   #0,d0
        rts
.fail:  moveq   #1,d0
        rts

; d0 = f y d6 = su banda: de las tres (d7 = todas las filas de ic, d4 =
; desde la primera de k, d5 = de la primera a la ultima), la primera que
; admite algun indice, y en ella el primero de BAND_PREF (d2 = ic, d3 = c):
; no es ic, el Rex no lo usa en la banda y Mario tampoco (o con el color
; c). Una pasada: las bandas van de mas a menos filas. -1 (N) si no hay.
; Destruye d1/a0/a2-a3 y GV_TMP.
.find:  move.l  #-1,GV_TMP(a6)              ; el primero que vale con d4 / con d5
        lea     .pref(pc),a2
        lea     13(a2),a3
.fl:    cmp.l   a3,a2
        beq.s   .fe
        moveq   #0,d1
        move.b  (a2)+,d1                    ; g
        cmp.w   d2,d1
        beq.s   .fl
        move.w  d1,d0
        add.w   d0,d0
        move.l  GV_COL(a6),a0
        cmp.w   (a0,d0.w),d3
        beq.s   .f1                         ; Mario lo usa con el color c
        MWLD
        bra.s   .f2
.f1:    moveq   #0,d0
.f2:    move.w  d1,d6
        lsl.w   #2,d6
        lea     GV_OCC(a6),a0
        or.l    (a0,d6.w),d0                ; d0 = filas en que g no vale
        move.l  d0,d6
        and.l   d7,d6
        beq.s   .ok1                        ; vale con todas: este
        tst.w   GV_TMP(a6)
        bpl.s   .f3
        move.l  d0,d6
        and.l   d4,d6
        bne.s   .f3
        move.w  d1,GV_TMP(a6)
.f3:    tst.w   GV_TMP+2(a6)
        bpl.s   .fl
        and.l   d5,d0
        bne.s   .fl
        move.w  d1,GV_TMP+2(a6)
        bra.s   .fl
.ok1:   move.l  d7,d6
        move.w  d1,d0
        rts
.fe:    move.l  d4,d6
        move.w  GV_TMP(a6),d0
        bpl.s   .fx
        move.l  d5,d6
        move.w  GV_TMP+2(a6),d0
.fx:    rts

.pref:  dc.b    7,15,4,6,14,9,13,8,12,11,5,10,3 ; tools/g5l.py BAND_PREF
        even

;----------------------------------------------------------------------
; --- g5l_sweep --- las transiciones de los grupos de g5l_plan (tools/
; g5l.py sweep), por mascaras: por indice, las filas de cada color (el de
; Mario: sus filas y los grupos de ese color) en orden; una transicion
; donde cambia el color, desde la ultima fila anterior, y la vuelta al de
; Mario en su primera fila despues de r0 + 31. Mismo resultado que
; mezclar tramos: tras g5l_plan ningun grupo de otro color se cruza con
; Mario. Caminos rapidos: un solo grupo y Mario sin filas en la ventana.
; entrada:  a6 = g5l_v (GV_R0, GV_IG/IM, GV_COL, la cache de Mario)
; salida:   las cubetas (GV_BP)
; registros destruidos: d0-d7/a0-a5
;
; d2 = i, d3 = color actual, d4 = ultima fila, d5 = duenos, d6 = filas
; que quedan, d7 = indices que quedan; a0 = entrada, a1 = GV_BITS, a4 =
; fin de las entradas (o los grupos del indice), a5 = r0
;----------------------------------------------------------------------
g5l_sweep:
        lea     GV_BS(a6),a2                ; cubetas vacias
        lea     GV_BP(a6),a3
        move.l  (a2)+,(a3)+
        move.l  (a2)+,(a3)+
        move.l  (a2)+,(a3)+
        move.l  (a2)+,(a3)+
        move.l  (a2)+,(a3)+
        lea     GV_BITS(a6),a1
        move.w  GV_R0(a6),a5
        move.w  GV_IM(a6),d7
.idx:   move.w  d7,d0
        beq     .x
        LOWB
        move.w  d1,d2                       ; d2 = i
        bclr    d2,d7
        move.w  d2,d0
        add.w   d0,d0
        move.l  GV_COL(a6),a0
        move.w  (a0,d0.w),d3                ; d3 = color de Mario
        move.w  d2,d0
        lsl.w   #6,d0
        lea     GV_IG(a6),a4
        add.w   d0,a4                       ; a4 = grupos del indice
        move.w  (a4),d6
        subq.w  #1,d6
        bne     .many
        move.l  8(a4),d0                    ; un solo grupo
        beq.s   .idx
        cmp.w   4(a4),d3
        beq.s   .idx                        ; del color de Mario: nada
        move.w  d2,d1
        bsr     g5l_mrowba                  ; Mw, GV_SB, GV_SA
        move.l  d0,GV_SMW(a6)
        bne     .gen                        ; Mario en la ventana
        move.l  8(a4),d0                    ; de su color desde su primera fila
        LOWB
        move.w  d1,d0
        add.w   a5,d0
        move.w  GV_SB(a6),d4
        smi     d5
        addq.b  #1,d5                       ; (B: Mario; -1: nadie)
        ext.w   d5
        move.w  d3,-(sp)
        move.w  4(a4),d3
        TRB
        move.w  (sp)+,d3
        move.w  GV_SA(a6),d0
        bmi     .idx
        move.w  d0,-(sp)                    ; y de vuelta al de Mario en A
        move.l  8(a4),d0
        HIGHB
        move.w  d1,d4
        add.w   a5,d4
        moveq   #2,d5
        move.w  (sp)+,d0
        TRB
        bra     .idx
.many:  bmi     .idx                        ; (sin grupos)
        move.w  (a4),d6                     ; ¿alguno de otro color?
        lea     4(a4),a0
        subq.w  #1,d6
.m1:    tst.l   4(a0)
        beq.s   .m2
        cmp.w   (a0),d3
        bne.s   .m3
.m2:    addq.l  #8,a0
        dbf     d6,.m1
        bra     .idx
.m3:    move.w  d2,d1
        bsr     g5l_mrowba
        move.l  d0,GV_SMW(a6)
.gen:   move.l  GV_SMW(a6),d0               ; el recorrido general
        move.l  a4,a0
        lea     GV_SE(a6),a4                ; entrada 0: el color de Mario
        move.w  d3,(a4)
        move.l  d0,4(a4)
        clr.l   8(a4)
        lea     12(a4),a4
        move.w  (a0)+,d6
        addq.l  #2,a0
        subq.w  #1,d6
.g:     move.l  4(a0),d1
        beq.s   .gn
        lea     GV_SE(a6),a2
        cmp.w   (a0),d3
        beq.s   .gadd                       ; del color de Mario: con sus filas
        move.l  a4,a2
        move.w  (a0),(a2)                   ; (colores distintos en un indice)
        clr.l   4(a2)
        clr.l   8(a2)
        lea     12(a4),a4
.gadd:  or.l    d1,4(a2)
        or.l    d1,8(a2)
.gn:    addq.l  #8,a0
        dbf     d6,.g
        moveq   #0,d5
        move.w  GV_SB(a6),d4
        bmi.s   .w0
        moveq   #1,d5
.w0:    moveq   #0,d6                       ; todas las filas
        lea     GV_SE(a6),a0
.u:     or.l    4(a0),d6
        lea     12(a0),a0
        cmp.l   a4,a0
        blo.s   .u
.walk:  move.l  d6,d0
        beq    .end
        move.w  d7,-(sp)
        LOWB                                ; la primera que queda
        move.w  d1,d7
        lea     GV_SE(a6),a0
.fe:    move.l  4(a0),d0
        btst    d7,d0
        bne.s   .fe1
        lea     12(a0),a0
        bra.s   .fe
.fe1:   cmp.w   (a0),d3
        beq.s   .same
        move.w  (a0),d3
        move.w  d7,d0
        add.w   a5,d0                       ; hasta
        TRB
.same:  move.w  (sp)+,d7
        move.l  4(a0),d0                    ; hasta la primera de otro color
        not.l   d0
        and.l   d6,d0
        beq.s   .tail
        LOWB                                ; d1 = esa fila
        moveq   #-1,d0
        lsl.l   d1,d0
        and.l   d0,d6
        not.l   d0
        and.l   4(a0),d0
        bra.s   .seg
.tail:  moveq   #0,d6
        move.l  4(a0),d0
.seg:   HIGHB                               ; d1 = la ultima de este color
        move.w  d1,d4
        add.w   a5,d4
        moveq   #0,d5
        move.l  GV_SMW(a6),d0
        btst    d1,d0
        beq.s   .o1
        moveq   #1,d5
.o1:    move.l  8(a0),d0
        btst    d1,d0
        beq    .walk
        addq.w  #2,d5
        bra    .walk
.end:   cmp.w   GV_SE(a6),d3
        beq     .idx
        move.w  GV_SA(a6),d0
        bmi     .idx
        move.w  GV_SE(a6),d3                ; vuelta al color de Mario
        TRB
        bra     .idx
.x:     rts

;----------------------------------------------------------------------
; --- g5l_patch --- con bandas: los flujos DMA de la variante limpia
; copiados al bufer de chip de esta lista (GV_RBUF, G5L_RSTR por flujo)
; y en las filas de cada banda los pixeles de ic pasados a f (XOR de
; ic ^ f en los planos, con las mascaras de pixeles de su grupo)
; entrada:  GV_VAR, GV_REM/NREM, GV_PBUF y su clave GV_RKP, a6 = g5l_v
; registros destruidos: d0-d7/a0-a5
;----------------------------------------------------------------------
g5l_patch:
        tst.w   GV_NREM(a6)
        beq     .x
        move.l  GV_VAR(a6),a3
        moveq   #0,d7
        move.b  5(a3),d7                    ; d7 = alto
        moveq   #0,d6
        move.b  6(a3),d6                    ; d6 = columnas
        lea     GV_REM(a6),a0               ; las mitades que cambian
        move.w  GV_NREM(a6),d1
        subq.w  #1,d1
        moveq   #0,d2
.hm:    move.b  (a0),d0
        move.b  1(a0),d3
        eor.b   d3,d0
        moveq   #3,d3
        and.b   d0,d3
        beq.s   .hm1
        bset    #0,d2
.hm1:   and.b   #12,d0
        beq.s   .hm2
        bset    #1,d2
.hm2:   addq.l  #8,a0
        dbf     d1,.hm
        move.w  d2,GV_RH(a6)
        move.l  GV_RKP(a6),a0               ; el bufer ya tiene este parche?
        move.l  a0,a1                       ; (variante y bandas; por lista y Rex)
        move.l  GV_VAR(a6),d0
        cmp.l   (a1)+,d0
        bne.s   .km
        move.w  GV_NREM(a6),d1
        cmp.w   (a1)+,d1
        bne.s   .km
        lea     GV_REM(a6),a4
        subq.w  #1,d1
.kc:    cmpm.l  (a4)+,(a1)+
        bne.s   .km
        cmpm.l  (a4)+,(a1)+
        bne.s   .km
        dbf     d1,.kc
        rts
.km:    move.l  GV_VAR(a6),(a0)+            ; la clave nueva
        move.w  GV_NREM(a6),d1
        move.w  d1,(a0)+
        lea     GV_REM(a6),a4
        subq.w  #1,d1
.ks:    move.l  (a4)+,(a0)+
        move.l  (a4)+,(a0)+
        dbf     d1,.ks
        ; La ultima lista parcheada es una fuente inmutable hasta el
        ; siguiente fallo. Copiar solo las mitades usadas evita repetir
        ; los XOR cuando el mismo parche pasa de A a B o C.
        lea     GV_RKS(a6),a0
        move.l  a0,a1
        move.l  GV_VAR(a6),d0
        cmp.l   (a1)+,d0
        bne     .sharedmiss
        move.w  GV_NREM(a6),d1
        cmp.w   (a1)+,d1
        bne     .sharedmiss
        lea     GV_REM(a6),a4
        subq.w  #1,d1
.sharedkey:
        cmpm.l  (a4)+,(a1)+
        bne     .sharedmiss
        cmpm.l  (a4)+,(a1)+
        bne     .sharedmiss
        dbf     d1,.sharedkey
        move.l  GV_RSBUF(a6),a0
        move.l  GV_PBUF(a6),a1
        move.w  d6,d5
        add.w   d5,d5
        subq.w  #1,d5
        moveq   #0,d3
.sharedcopy:
        btst    d3,d2
        beq.s   .sharednext
        move.l  a0,a2
        move.l  a1,a4
        move.w  d7,d1                       ; d7 + 2 .l (alto <= 32), desenrollado
        add.w   d1,d1                       ; (R1: 20 ciclos por .l, no 30)
        neg.w   d1
        jmp     .sharedend-4(pc,d1.w)       ; P40 ok: indice negativo a proposito
        rept    G5L_RSTR/4
        move.l  (a2)+,(a4)+
        endr
.sharedend:
.sharednext:
        lea     G5L_RSTR(a0),a0
        lea     G5L_RSTR(a1),a1
        eor.w   #1,d3
        dbf     d5,.sharedcopy
        rts
.sharedmiss:
        move.l  GV_VAR(a6),(a0)+
        move.w  GV_NREM(a6),d1
        move.w  d1,(a0)+
        lea     GV_REM(a6),a4
        subq.w  #1,d1
.sharedstore:
        move.l  (a4)+,(a0)+
        move.l  (a4)+,(a0)+
        dbf     d1,.sharedstore
        move.l  GV_PBUF(a6),GV_RSBUF(a6)
        move.l  GV_PBUF(a6),a1              ; copiar esos flujos de la limpia
        lea     12(a3),a2                   ; offsets (columna, mitad)
        move.w  d6,d5
        add.w   d5,d5
        subq.w  #1,d5
        moveq   #0,d3                       ; mitad
.cs:    move.l  (a2)+,d0
        btst    d3,d2
        beq.s   .cn
        bclr    #31,d0
        add.l   g5l_cdma(pc),d0
        move.l  d0,a0
        move.l  a1,a4
        move.w  d7,d1                       ; POS/CTL, alto filas, fin: d7 + 2 .l,
        add.w   d1,d1                       ; desenrollado (R1)
        neg.w   d1
        jmp     .cle-4(pc,d1.w)             ; P40 ok: indice negativo a proposito
.cl:    rept    G5L_RSTR/4
        move.l  (a0)+,(a4)+
        endr
.cle:
.cn:    lea     G5L_RSTR(a1),a1
        eor.w   #1,d3
        dbf     d5,.cs
        lea     GV_REM(a6),a5
        move.w  GV_NREM(a6),d5
        subq.w  #1,d5
.rm:    move.b  (a5),d4
        move.b  1(a5),d0
        eor.b   d0,d4                       ; d4 = los planos que cambian
        moveq   #0,d0                       ; G5L2: el bloque de la forma
        move.b  2(a5),d0                    ; su grupo de la tabla
        add.w   d6,d0
        lsl.w   #3,d0
        moveq   #0,d1
        move.b  13(a3,d0.w),d1              ; su mascara (el .b del grupo)
        mulu    d7,d1
        mulu    d6,d1
        add.l   d1,d1                       ; x alto x columnas .w
        moveq   #0,d0
        move.b  9(a3),d0
        add.w   d6,d0
        lsl.w   #3,d0
        add.l   12(a3,d0.w),d1              ; + el bloque (desde la tabla)
        add.l   GV_TAB(a6),d1
        move.l  d1,a0                       ; a0 = sus mascaras (filas x columnas .w)
        move.l  4(a5),d3                    ; la banda
        move.l  GV_PBUF(a6),a2
        addq.l  #4,a2                       ; a2 = fila 0 del primer flujo
.rr:    lsr.l   #1,d3
        bcc.s   .rn
        move.l  a0,a3
        move.l  a2,a1
        move.w  d6,d1
        subq.w  #1,d1
.rc:    move.w  (a3)+,d0
        btst    #0,d4
        beq.s   .q1
        eor.w   d0,(a1)
.q1:    btst    #1,d4
        beq.s   .q2
        eor.w   d0,2(a1)
.q2:    btst    #2,d4
        beq.s   .q3
        eor.w   d0,G5L_RSTR(a1)
.q3:    btst    #3,d4
        beq.s   .q4
        eor.w   d0,G5L_RSTR+2(a1)
.q4:    lea     2*G5L_RSTR(a1),a1
        dbf     d1,.rc
.rn:    add.w   d6,a0
        add.w   d6,a0
        addq.l  #4,a2
        tst.l   d3
        bne.s   .rr
        move.l  GV_VAR(a6),a3
        addq.l  #8,a5
        dbf     d5,.rm
.x:     rts

; ADV Dn: el x del MOVE siguiente (g2t_ref.advance, 256 px, P110)
ADV     macro
        cmp.w   #231,\1
        bne.s   .a\@
        move.w  #243,\1
        bra.s   .b\@
.a\@:   cmp.w   #239,\1
        blt.s   .c\@
        addq.w  #8,\1
        bra.s   .b\@
.c\@:   add.w   #16,\1
.b\@:
        endm

;----------------------------------------------------------------------
; --- g5l_place --- los MOVE de las transiciones: VBL, borrado a ciegas
; (pase 1, ventanas cortas primero: las cubetas de g5l_sweep) y plan
; exacto (pase 2)
; entrada:  cubetas GV_TRB/GV_BP, GV_VAR, a6 = g5l_v
; salida:   d0 = 0 (Z) y el pool / GV_VBL; 1 si no entra
; registros destruidos: d0-d7/a0-a5
;
; Por fila: GV_SEGIX = entrada del pool + 1 (0: sin abrir), GV_ROOM = lo
; que queda a ciegas en un segmento abierto (0: lleno o sin abrir) y
; GV_CAPNL = 12 - nb siguiente (0: el segmento nunca lleva MOVE a ciegas;
; con cargas caben 2 menos, siempre al menos 1). Un MOVE se guarda ya
; escrito (.w registro, .w color) con su need en ese segmento.
;----------------------------------------------------------------------
g5l_place:
        bsr     g5l_unpool
        move.l  GV_VAR(a6),a0               ; bordes por duenos
        moveq   #0,d0
        move.b  8(a0),d0
        add.w   GV_X0(a6),d0
        cmp.w   #255,d0
        ble.s   .e0
        move.w  #255,d0                     ; d0 = xr
.e0:    move.w  GV_XM(a6),d1
        clr.w   GV_E(a6)
        move.w  d1,d2
        addq.w  #1,d2
        move.w  d2,GV_E+2(a6)
        move.w  d0,d2
        addq.w  #1,d2
        move.w  d2,GV_E+4(a6)
        cmp.w   d1,d0
        bge.s   .e1
        move.w  d1,d0
.e1:    addq.w  #1,d0
        move.w  d0,GV_E+6(a6)
; g5l_place_e: con el pool vacio y GV_E ya puestos (G4-2: g5l_edges)
g5l_place_e:
        clr.w   GV_NV(a6)
        lea     GV_MISS(a6),a3              ; a3 = los que no entran a ciegas
        lea     GV_E(a6),a4                 ; a4 = bordes
        ; pase 1, cubeta por cubeta
        moveq   #0,d7                       ; cubeta x 4
.bk:    lea     GV_BP(a6),a0
        move.l  (a0,d7.w),a5                ; a5 = fin de la cubeta
        move.l  GV_BS-GV_BP(a0,d7.w),a1     ; a1 = su principio
        bra     .t9
.t:     move.w  4(a1),d3                    ; desde
        bpl.s   .g
        move.w  GV_NV(a6),d0                ; sin uso anterior: el bloque VBL
        cmp.w   #G5L_VBLN,d0
        bhs.s   .z
        addq.w  #1,GV_NV(a6)
        lsl.w   #2,d0
        lea     GV_VBL(a6),a0
        add.w   d0,a0
        moveq   #0,d0
        move.b  (a1),d0
        add.w   d0,d0
        add.w   #$01a0,d0
        move.w  d0,(a0)+
        move.w  2(a1),(a0)
        bra     .tn
.z:     moveq   #0,d3                       ; lo = 0
.g:     move.w  6(a1),d4
        subq.w  #1,d4                       ; hi
        move.w  d4,d2
        sub.w   d3,d2                       ; filas - 1
        bmi     .miss
        ; el segmento abierto con lugar mas tardio de [lo, hi]. R1: por
        ; las entradas del pool (GV_ROOM solo es <> 0 en sus filas, ver
        ; g5l_unpool) si son menos de la mitad de las filas (~40 ciclos
        ; por entrada contra ~20 por fila); si no, fila por fila
        move.w  GV_NP(a6),d1
        beq     .f2
        add.w   d1,d1
        cmp.w   d2,d1
        bhi.s   .fs
        move.w  GV_NP(a6),d2
        subq.w  #1,d2
        lea     GV_POOL+P_S(a6),a2
        lea     GV_ROOM(a6),a0
        moveq   #-1,d0                      ; d0 = s (ninguno)
.f1:    move.w  (a2),d1
        cmp.w   d3,d1
        blt.s   .f1n
        cmp.w   d4,d1
        bgt.s   .f1n
        cmp.w   d0,d1
        ble.s   .f1n
        tst.b   (a0,d1.w)                   ; P40 ok: 0 <= s < LINES
        beq.s   .f1n
        move.w  d1,d0
.f1n:   lea     PSZ(a2),a2
        dbf     d2,.f1
        tst.w   d0
        bmi.s   .f2
        bra.s   .fh
.fs:    lea     GV_ROOM+1(a6),a0            ; fila por fila (d2 = filas - 1)
        add.w   d4,a0
.fsl:   tst.b   -(a0)
        dbne    d2,.fsl
        beq.s   .f2
        move.l  a0,d0
        sub.l   a6,d0
        sub.w   #GV_ROOM,d0                 ; d0 = s
        lea     GV_ROOM(a6),a0
.fh:    subq.b  #1,(a0,d0.w)                ; P40 ok
        lea     GV_SEGIX(a6),a0
        moveq   #0,d1
        move.b  (a0,d0.w),d1
        subq.w  #1,d1
        lsl.w   #7,d1
        lea     GV_POOL(a6),a2
        add.w   d1,a2
        bsr     .add
        bra     .tn
        ; si no: abrir el mas tardio sin abrir que admita MOVE a ciegas
.f2:    lea     GV_SEGIX+1(a6),a0
        add.w   d4,a0
        lea     GV_CAPNL+1(a6),a2
        add.w   d4,a2
        move.w  d4,d2
        sub.w   d3,d2
.f3:    subq.l  #1,a2
        tst.b   -(a0)
        bne.s   .f4
        tst.b   (a2)
        bne.s   .open
.f4:    dbf     d2,.f3
.miss:  move.l  a1,(a3)+
        bra.s   .tn
.open:  move.l  a0,d0
        sub.l   a6,d0
        sub.w   #GV_SEGIX,d0                ; d0 = s
        moveq   #0,d5
        move.b  (a2),d5                     ; capacidad sin cargas
        move.w  GV_NP(a6),d1
        cmp.w   #G5L_NPOOL,d1
        bhs     .fail
        addq.w  #1,GV_NP(a6)
        move.b  GV_NP+1(a6),(a0)            ; SEGIX
        lsl.w   #7,d1
        lea     GV_POOL(a6),a2
        add.w   d1,a2
        move.w  d0,P_S(a2)
        clr.l   P_N(a2)                     ; P_N, P_WALK, P_MAXN
        moveq   #0,d1                       ; las cargas del segmento: 2 menos
        move.b  GV_NB(a6,d0.w),d1
        lsl.w   #2,d1
        move.l  GV_LIST(a6),a0
        add.w   d1,a0
        moveq   #0,d1
        move.w  d0,d1
        lsl.l   #8,d1
        add.l   d1,a0
        cmp.w   #$0084,CL_LINES+8(a0)
        beq.s   .o1
        subq.w  #2,d5
.o1:    subq.w  #1,d5                       ; el que entra ahora
        lea     GV_ROOM(a6),a0
        move.b  d5,(a0,d0.w)
        bsr     .add
.tn:    addq.l  #8,a1
.t9:    cmp.l   a5,a1
        blo     .t
        addq.w  #4,d7
        cmp.w   #5*4,d7
        blo     .bk
        ; pase 2: plan exacto en un segmento de la ventana
        move.l  a3,d6
        lea     GV_MISS(a6),a5
        sub.l   a5,d6
        lsr.w   #2,d6
        subq.w  #1,d6
        bmi     .p2done
.q1:    move.l  (a5)+,a1
        addq.w  #1,GV_DPASS2(a6)
        move.w  4(a1),d3
        bpl.s   .q2
        moveq   #0,d3
.q2:    move.w  6(a1),d7
        subq.w  #1,d7                       ; s = hi .. lo
.q3:    cmp.w   d3,d7
        blt     .fail
        cmp.w   #LINES-1,d7
        bhs     .q9
        move.w  d7,d0
        bsr     g5l_wcache                  ; d1 = last, d2 = free, a0 = J
        moveq   #0,d5                       ; need de la transicion aqui
        cmp.w   4(a1),d7
        bne.s   .q4
        move.b  1(a1),d5
        add.w   d5,d5
        move.w  (a4,d5.w),d5
.q4:    moveq   #1,d4                       ; k
        lea     GV_SEGIX(a6),a2
        moveq   #0,d0
        move.b  (a2,d7.w),d0
        beq.s   .q6
        subq.w  #1,d0                       ; abierto: sus MOVE tambien
        lsl.w   #7,d0
        lea     GV_POOL(a6),a2
        add.w   d0,a2
        tst.b   P_WALK(a2)                  ; recorrido: el plan exacto al emitir
        bne.s   .q5
        st      P_WALK(a2)
        move.w  d1,P_LAST(a2)
        move.w  d2,P_FREE(a2)
        move.l  a0,P_J(a2)
.q5:    add.b   P_N(a2),d4
        cmp.w   P_MAXN(a2),d5
        bge.s   .q7
        move.w  P_MAXN(a2),d5
        bra.s   .q7
.q6:    sub.l   a2,a2
.q7:    move.w  d7,d0
        moveq   #0,d3
        move.b  GV_NB+1(a6,d7.w),d3
        bsr     g5l_sched
        tst.w   d0
        bne.s   .q10
        move.w  4(a1),d3                    ; (restaurar lo)
        bpl.s   .q9
        moveq   #0,d3
.q9:    subq.w  #1,d7
        bra     .q3
.q10:   move.l  a2,d0
        bne.s   .q11
        move.w  GV_NP(a6),d1                ; abrir s (ya recorrido)
        cmp.w   #G5L_NPOOL,d1
        bhs.s   .fail
        addq.w  #1,GV_NP(a6)
        lea     GV_SEGIX(a6),a0
        move.b  GV_NP+1(a6),(a0,d7.w)
        lsl.w   #7,d1
        lea     GV_POOL(a6),a2
        add.w   d1,a2
        move.w  d7,P_S(a2)
        clr.l   P_N(a2)
        st      P_WALK(a2)
        move.w  d7,d0
        bsr     g5l_wcache
        move.w  d1,P_LAST(a2)
        move.w  d2,P_FREE(a2)
        move.l  a0,P_J(a2)
.q11:   move.w  d7,d0
        bsr     .add
        dbf     d6,.q1
.p2done:
        moveq   #0,d0
        rts
.fail:  moveq   #1,d0
        rts

; la transicion (a1) como MOVE de la entrada a2 (segmento d0): registro,
; color y need (el borde de sus duenos si empieza en esta fila).
; Destruye d0-d1/a0.
.add:   moveq   #0,d1
        cmp.w   4(a1),d0
        bne.s   .a1
        move.b  1(a1),d1
        add.w   d1,d1
        move.w  (a4,d1.w),d1
        cmp.w   P_MAXN(a2),d1
        ble.s   .a1
        move.w  d1,P_MAXN(a2)
.a1:    moveq   #0,d0
        move.b  P_N(a2),d0
        addq.b  #1,P_N(a2)
        lsl.w   #3,d0
        lea     P_MV(a2,d0.w),a0
        moveq   #0,d0
        move.b  (a1),d0
        add.w   d0,d0
        add.w   #$01a0,d0
        move.w  d0,(a0)+                    ; MOVE COLORxx
        move.w  2(a1),(a0)+
        move.w  d1,(a0)                     ; need
        rts

; --- g5l_unpool --- vaciar el pool. Destruye d0-d1/a0-a1.
g5l_unpool:
        move.w  GV_NP(a6),d1
        beq.s   .x
        move.l  a2,-(sp)
        lea     GV_POOL(a6),a0
        lea     GV_SEGIX(a6),a1
        lea     GV_ROOM(a6),a2
        subq.w  #1,d1
.l:     move.w  P_S(a0),d0
        clr.b   (a1,d0.w)
        clr.b   (a2,d0.w)
        lea     PSZ(a0),a0
        dbf     d1,.l
        clr.w   GV_NP(a6)
        move.l  (sp)+,a2
.x:     rts

; --- g5l_wcache --- g5l_walk del segmento d0 con una cache por frame
; (GV_WSTAMP: la lista no cambia hasta g5l_emit). salida: d1 = last,
; d2 = free, a0 = J. Destruye d0.
g5l_wcache:
        move.l  a1,-(sp)
        lea     GV_WK(a6),a1
        move.b  GV_WSTAMP(a6),d1
        cmp.b   (a1,d0.w),d1
        beq.s   .hit
        move.b  d1,(a1,d0.w)
        move.w  d0,-(sp)
        bsr     g5l_walk
        move.w  (sp)+,d0
        lea     GV_W(a6),a1
        lsl.w   #3,d0
        add.w   d0,a1
        move.w  d1,(a1)+
        move.w  d2,(a1)+
        move.l  a0,(a1)
        move.l  (sp)+,a1
        rts
.hit:   lea     GV_W(a6),a1
        lsl.w   #3,d0
        add.w   d0,a1
        move.w  (a1)+,d1
        move.w  (a1)+,d2
        move.l  (a1),a0
        move.l  (sp)+,a1
        rts

;----------------------------------------------------------------------
; --- g5l_walk --- el segmento d0 con el modelo de g2t_ref.segments
; salida: d1 = x de la ultima carga (G5L_NONE: ninguna), d2 = x libre
;         tras el borrado, a0 = el salto. Destruye d0.
;----------------------------------------------------------------------
g5l_walk:
        movem.l d3-d4,-(sp)
        addq.w  #1,GV_DWALK(a6)
        moveq   #0,d3
        move.b  GV_NB(a6,d0.w),d3
        move.l  GV_LIST(a6),a0
        moveq   #0,d4
        move.w  d0,d4
        lsl.l   #8,d4
        add.l   d4,a0
        move.w  d3,d4
        lsl.w   #2,d4
        add.w   d4,a0
        lea     CL_LINES+8(a0),a0
        move.w  #-56,d2                     ; T0 + max(0, 16 (nb - 9))
        sub.w   #9,d3
        ble.s   .t0
        lsl.w   #4,d3
        add.w   d3,d2
.t0:    move.w  d2,d4                       ; d4 = T
        move.w  #G5L_NONE,d1
.l:     move.w  (a0),d0
        cmp.w   #$0084,d0
        beq.s   .x
        btst    #0,d0
        beq.s   .mv
        and.w   #$fe,d0                     ; WAIT: T = max(T + 2 ranuras, x(h))
        bsr     g5l_xh
        ADV     d4
        ADV     d4
        cmp.w   d0,d4
        bge.s   .n
        move.w  d0,d4
        bra.s   .n
.mv:    move.w  d4,d1                       ; MOVE (o relleno): cae en T
        ADV     d4
.n:     addq.l  #4,a0
        bra.s   .l
.x:     movem.l (sp)+,d3-d4
        rts

; --- g5l_xh --- d0 = h (par) -> d0 = x del MOVE tras WAIT h (scrollsim.xh)
g5l_xh:
        cmp.w   #$C0,d0
        bhi.s   .t
        sub.w   #$48,d0
        asr.w   #2,d0
        lsl.w   #3,d0
        subq.w  #1,d0
        rts
.t:     cmp.w   #$C4,d0
        beq.s   .x243
        cmp.w   #$C6,d0
        beq.s   .x243
        cmp.w   #$C8,d0
        beq.s   .x247
        cmp.w   #$CA,d0
        beq.s   .x247
        cmp.w   #$CC,d0
        beq.s   .x251
        cmp.w   #$CE,d0
        bhi.s   .x999
        move.w  #255,d0
        rts
.x243:  move.w  #243,d0
        rts
.x247:  move.w  #247,d0
        rts
.x251:  move.w  #251,d0
        rts
.x999:  move.w  #999,d0
        rts

;----------------------------------------------------------------------
; --- g5l_sched --- g2t_ref.schedule para k MOVE del segmento
; entrada: d0 = s, d1 = last (G5L_NONE), d2 = free, d3 = nb siguiente,
;          d4 = k, d5 = need (el mayor)
; salida:  d0 = 0 no entra, 1 cadena (d1 = rellenos), 2 WAIT (d1 = h)
; registros destruidos: d0-d1
;----------------------------------------------------------------------
G5L_SLOTS equ   9
g5l_sched:
        movem.l d2-d7/a0-a1,-(sp)
        cmp.w   #G5L_WRAP,d0
        beq     .f
        subq.w  #7,d3
        cmp.w   #2,d3
        bhi     .f
        addq.w  #7,d3
        lsl.w   #3,d3
        move.w  #351,d6
        sub.w   d3,d6                       ; d6 = end
        move.w  d1,d7                       ; d7 = t
        cmp.w   #G5L_NONE,d7
        bne.s   .t1
        move.w  d2,d7
.t1:    moveq   #0,d0                       ; tipo
        sub.l   a1,a1                       ; parametro
        move.w  #$7fff,d3                   ; ultimo x del mejor
        cmp.w   #G5L_NONE,d1
        beq.s   .w
        ; cadena tras la ultima carga, con rellenos hasta need
        move.w  d7,d1
        ADV     d1
        sub.l   a0,a0                       ; a0 = rellenos
.cl:    cmp.w   d5,d1
        bge.s   .cd
        ADV     d1
        addq.w  #1,a0
        bra.s   .cl
.cd:    move.w  d4,d2
        subq.w  #1,d2
        bra.s   .ck2
.ck:    ADV     d1
.ck2:   dbf     d2,.ck                      ; d1 = x del ultimo MOVE
        move.w  a0,d2
        add.w   d4,d2
        cmp.w   #G5L_SLOTS,d2
        bhi.s   .w
        cmp.w   d6,d1
        bgt.s   .w
        moveq   #1,d0
        move.w  a0,a1
        move.w  d1,d3
.w:     cmp.w   #255,d5
        bgt.s   .wd
        ; WAIT con htab(need), si el copper esta libre 48 px antes
        move.w  d5,d1
        cmp.w   #239,d1
        bgt.s   .h1
        addq.w  #8,d1
        lsr.w   #3,d1
        lsl.w   #2,d1
        add.w   #$48,d1
        bra.s   .h3
.h1:    cmp.w   #252,d1
        blt.s   .h2
        move.w  #$ce,d1
        bra.s   .h3
.h2:    sub.w   #240,d1
        and.w   #$fffc,d1
        add.w   #$c4,d1
.h3:    move.w  d1,a0                       ; h
        move.w  d0,-(sp)
        move.w  d1,d0
        bsr     g5l_xh                      ; first
        move.w  d0,d1
        move.w  (sp)+,d0
        move.w  d1,d2
        sub.w   d7,d2
        cmp.w   #48,d2
        blt.s   .x
        move.w  d4,d2
        subq.w  #1,d2
        bra.s   .wk2
.wk:    ADV     d1
.wk2:   dbf     d2,.wk
        bra.s   .wc
.wd:    cmp.w   #255-48,d7
        bgt.s   .x
        move.w  #$d0,a0
        move.w  d4,d1
        subq.w  #1,d1
        lsl.w   #3,d1
        add.w   #263,d1
.wc:    move.w  d4,d2                       ; k + 1 <= 9, ultimo <= end, mejor
        addq.w  #1,d2
        cmp.w   #G5L_SLOTS,d2
        bhi.s   .x
        cmp.w   d6,d1
        bgt.s   .x
        cmp.w   d3,d1
        bge.s   .x
        moveq   #2,d0
        move.w  a0,a1
.x:     move.w  a1,d1
        movem.l (sp)+,d2-d7/a0-a1
        rts
.f:     moveq   #0,d0
        movem.l (sp)+,d2-d7/a0-a1
        rts

;----------------------------------------------------------------------
; --- g5l_emit --- bloque VBL (SPR4-7 y colores de partida) y sufijos
; entrada:  plan en GV_*, a6 = g5l_v
; registros destruidos: d0-d7/a0-a5
;----------------------------------------------------------------------
g5l_emit:
        move.l  GV_LIST(a6),a2
        move.l  GV_VAR(a6),a3
        lea     CL_VBL+4(a2),a4             ; a4 = SPR4PTH
        move.w  GV_R0(a6),d3
        moveq   #0,d4
        move.b  5(a3),d4                    ; H
        moveq   #0,d6                       ; clip = max(0, -r0)
        move.w  d3,d5                       ; vs = $2C + max(r0, 0)
        bpl.s   .v1
        move.w  d3,d6
        neg.w   d6
        moveq   #0,d5
.v1:    add.w   #$2c,d5
        move.w  d3,d7
        add.w   d4,d7
        add.w   #$2c,d7                     ; d7 = ve
        lsl.w   #2,d6                       ; 4 * clip
        moveq   #0,d2                       ; columna
.col:   moveq   #0,d0
        move.b  6(a3),d0
        cmp.w   d0,d2
        bhs     .null2
        move.w  d2,d1                       ; hx = x0 + 16c
        lsl.w   #4,d1
        add.w   GV_X0(a6),d1
        cmp.w   #-16,d1
        ble .null2
        cmp.w   #256,d1
        bge .null2
        move.w  d1,d4                       ; hp = $A0 + hx
        add.w   #$a0,d4
        move.w  d5,d0                       ; POS = vs << 8 | hp >> 1
        lsl.w   #8,d0
        move.w  d4,d3
        lsr.w   #1,d3
        and.w   #$ff,d3
        or.w    d3,d0
        move.w  d0,a0                       ; a0 = POS de los dos canales
        move.w  d7,d0                       ; CTL
        lsl.w   #8,d0
        move.w  d5,d3
        lsr.w   #8,d3
        lsl.w   #2,d3
        or.w    d3,d0
        move.w  d7,d3
        lsr.w   #8,d3
        add.w   d3,d3
        or.w    d3,d0
        and.w   #1,d4
        or.w    d4,d0
        move.w  d0,a1                       ; a1 = CTL (el impar, con ATTACH)
        moveq   #0,d3                       ; mitad
.half:  tst.w   GV_NREM(a6)
        beq.s   .h0
        move.w  GV_RH(a6),d0
        btst    d3,d0
        beq.s   .h0
        move.w  d2,d0                       ; con bandas: el bufer de la lista
        add.w   d0,d0
        add.w   d3,d0
        mulu    #G5L_RSTR,d0
        add.l   GV_PBUF(a6),d0
        bra.s   .bk2
.h0:    move.w  d2,d0                       ; pt = dma + off + 4 + 4 clip
        lsl.w   #3,d0
        add.w   d3,d0
        add.w   d3,d0
        add.w   d3,d0
        add.w   d3,d0
        move.l  12(a3,d0.w),d0
        bclr    #31,d0                      ; (G5L-R: solo variantes limpias,
        add.l   g5l_cdma(pc),d0             ; sin el banco G3)
.bk2:   addq.l  #4,d0
        moveq   #0,d4
        move.w  d6,d4
        add.l   d4,d0
        swap    d0
        move.w  d0,2(a4)
        swap    d0
        move.w  d0,6(a4)
        move.w  a0,10(a4)
        move.w  a1,d0
        tst.w   d3
        beq.s   .ev
        or.w    #$80,d0
.ev:    move.w  d0,14(a4)
        lea     16(a4),a4
        addq.w  #1,d3
        cmp.w   #2,d3
        blo     .half
        bra.s   .cn
.null2: bsr     g5l_nullch
        bsr     g5l_nullch
.cn:    addq.w  #1,d2
        cmp.w   #2,d2
        blo     .col
; g5l_emitc: colores de partida y sufijos (a2 = lista, a4 = tras SPR7)
g5l_emitc:
        ; colores de partida; despues, NOP solo donde esta lista tenia
        ; colores de antes (GV_PNVA/B: cuantos)
        lea     GV_VBL(a6),a0
        move.w  GV_NV(a6),d1
        move.w  d1,d2
        bra.s   .vc9
.vc:    move.l  (a0)+,(a4)+
.vc9:   dbf     d2,.vc
        lea     GV_PNVA(a6),a0
        lea     GV_RECA(a6),a1
        cmp.l   GV_REC(a6),a1
        beq.s   .pa
        addq.l  #1,a0
        ifd     CUSHION
        lea     GV_RECB(a6),a1
        cmp.l   GV_REC(a6),a1
        beq.s   .pa
        lea     GV_PNVC(a6),a0
        endc
.pa:    moveq   #0,d2
        move.b  (a0),d2
        move.b  d1,(a0)
        sub.w   d1,d2
        ble.s   .vnx
        subq.w  #1,d2
.vn:    move.l  #$01fe0000,(a4)+
        dbf     d2,.vn
.vnx:
        ; sufijos
        move.l  GV_REC(a6),a5
        move.w  GV_NP(a6),d7
        beq     .x
        lea     GV_POOL(a6),a3
        subq.w  #1,d7
.seg:   move.w  P_S(a3),d6                  ; d6 = s
        moveq   #0,d4
        move.b  P_N(a3),d4                  ; d4 = k
        tst.b   P_WALK(a3)
        beq.s   .blind
        move.w  d6,d0
        move.w  P_LAST(a3),d1
        move.w  P_FREE(a3),d2
        moveq   #0,d3
        move.b  GV_NB+1(a6,d6.w),d3
        move.w  P_MAXN(a3),d5
        bsr     g5l_sched
        tst.w   d0
        beq.s   .blind
        bsr     .sort                       ; los MOVE por need (estable)
        move.l  P_J(a3),a0
        cmp.w   #2,d0
        beq.s   .wt
        bra.s   .pad1                       ; cadena: d1 rellenos
.pad:   move.l  #$01a00000,(a0)+
.pad1:  dbf     d1,.pad
        bra.s   .mvs
.wt:    move.w  d6,d0
        add.w   #$2c,d0
        lsl.w   #8,d0
        or.w    d1,d0
        or.w    #1,d0
        move.w  d0,(a0)+
        move.w  #$fffe,(a0)+
        bra.s   .mvs
.blind: bsr     .jump                       ; a0 = J (el salto)
        move.l  a0,P_J(a3)
        move.w  d6,d0
        add.w   #$2c,d0
        lsl.w   #8,d0
        or.w    #$d1,d0
        move.w  d0,(a0)+
        move.w  #$fffe,(a0)+
.mvs:   lea     P_MV(a3),a1                 ; los MOVE, ya escritos
        move.w  d4,d2
        subq.w  #1,d2
.mv:    move.l  (a1),(a0)+
        addq.l  #8,a1
        dbf     d2,.mv
        move.w  d6,d0                       ; el salto al segmento siguiente
        addq.w  #1,d0
        and.l   #$ffff,d0
        lsl.l   #8,d0
        add.l   a2,d0
        add.l   #CL_LINES,d0
        move.w  #$0084,(a0)+
        swap    d0
        move.w  d0,(a0)+
        move.w  #$0086,(a0)+
        swap    d0
        move.w  d0,(a0)+
        move.l  #$008a0000,(a0)
        ; registro para la limpieza: J, w0, w1, s
        move.w  (a5),d0
        addq.w  #1,(a5)
        lsl.w   #4,d0
        lea     2(a5,d0.w),a0
        move.l  P_J(a3),a1
        move.l  a1,(a0)+
        move.l  (a1),(a0)+
        move.l  4(a1),(a0)+
        move.w  d6,(a0)
        lea     PSZ(a3),a3
        dbf     d7,.seg
.x:     move.w  GV_SLOT(a6),GV_DSLOT(a6)
        rts

; a0 = el salto del segmento d6 (buscado desde el inicio de las cargas)
.jump:  move.w  d6,d0
        moveq   #0,d1
        move.b  GV_NB(a6,d0.w),d1
        lsl.w   #2,d1
        and.l   #$ffff,d0
        lsl.l   #8,d0
        move.l  a2,a0
        add.l   d0,a0
        add.w   d1,a0
        lea     CL_LINES+8(a0),a0
.jl:    cmp.w   #$0084,(a0)
        beq.s   .jx
        addq.l  #4,a0
        bra.s   .jl
.jx:    rts

; ordenar los k (d4) MOVE de la entrada a3 por need, estable (insercion).
; Preserva todo.
.sort:  movem.l d0-d3/a0-a1,-(sp)
        moveq   #1,d2
.s1:    cmp.w   d4,d2
        bhs.s   .s9
        lea     P_MV(a3),a0
        move.w  d2,d0
        lsl.w   #3,d0
        lea     (a0,d0.w),a1                ; el que se inserta
        move.l  (a1),d1
        move.w  4(a1),d3                    ; su need
.s2:    cmp.l   a0,a1
        beq.s   .s3
        cmp.w   -4(a1),d3
        bhs.s   .s3                         ; need >= el de la izquierda: aqui
        move.l  -8(a1),(a1)
        move.l  -4(a1),4(a1)
        subq.l  #8,a1
        bra.s   .s2
.s3:    move.l  d1,(a1)
        move.w  d3,4(a1)
        addq.w  #1,d2
        bra.s   .s1
.s9:    movem.l (sp)+,d0-d3/a0-a1
        rts

;----------------------------------------------------------------------
; --- g5l_emitn --- G4-2: SPR4-7 de los GV_NPL Rex y despues g5l_emitc.
; El flujo s = 2c + mitad lleva la columna c de cada Rex que la tiene en
; pantalla: uno solo, desde su fuente (variante limpia o su bufer de
; bandas); dos, encadenados en el bufer de la lista (sus filas, POS/CTL del
; segundo, sus filas, fin), que el DMA lee tras el VSTOP del primero
; (tools/g5l.py channels_n)
; registros destruidos: d0-d7/a0-a5
;----------------------------------------------------------------------
g5l_emitn:
        lea     GV_EV(a6),a1                ; lo vertical de cada Rex, una vez
        lea     GV_RX(a6),a3
        move.w  GV_NPL(a6),d6
        subq.w  #1,d6
.v:     move.l  RX_VAR(a3),a0
        move.w  RX_R0(a3),d2
        moveq   #0,d3
        move.b  5(a0),d3                    ; alto
        moveq   #0,d0                       ; clip = max(0, -r0)
        move.w  d2,d4                       ; vs = $2C + max(r0, 0)
        bpl.s   .v1
        move.w  d2,d0
        neg.w   d0
        moveq   #0,d4
.v1:    add.w   #$2c,d4
        add.w   d3,d2
        add.w   #$2c,d2                     ; ve
        sub.w   d0,d3                       ; filas que lee el DMA
        move.w  d4,d1
        lsl.w   #8,d1
        move.w  d1,(a1)+                    ; POS sin la x
        move.w  d2,d1
        lsl.w   #8,d1
        lsr.w   #8,d4
        lsl.w   #2,d4
        or.w    d4,d1
        lsr.w   #8,d2
        add.w   d2,d2
        or.w    d2,d1
        move.w  d1,(a1)+                    ; CTL sin la x
        move.w  d3,(a1)+
        lsl.w   #2,d0
        addq.w  #4,d0
        move.w  d0,(a1)+                    ; 4 + 4 clip
        lea     RXSZ(a3),a3
        dbf     d6,.v
        move.l  GV_LIST(a6),a2
        lea     CL_VBL+4(a2),a4             ; a4 = SPR4PTH
        clr.w   GV_CI(a6)                   ; flujo s
.s:     lea     GV_EN(a6),a5
        moveq   #0,d7                       ; Rex con esta columna
        moveq   #0,d6                       ; Rex k
        lea     GV_RX(a6),a3
        lea     GV_EV(a6),a1
.k:     cmp.w   GV_NPL(a6),d6
        bhs     .kd
        move.l  RX_VAR(a3),a0
        move.w  GV_CI(a6),d5                ; d5 = s
        move.w  d5,d4
        lsr.w   #1,d4                       ; c
        moveq   #0,d0
        move.b  6(a0),d0
        cmp.w   d0,d4
        bhs     .kn                         ; sin esa columna
        lsl.w   #4,d4
        add.w   RX_X0(a3),d4                ; hx = x0 + 16c
        cmp.w   #-16,d4
        ble     .kn
        cmp.w   #256,d4
        bge     .kn
        add.w   #$a0,d4                     ; hp
        moveq   #1,d1
        and.w   d4,d1
        or.w    2(a1),d1
        btst    #0,d5
        beq.s   .o2
        or.w    #$80,d1                     ; el impar: ATTACH
.o2:    move.w  d1,6(a5)                    ; CTL
        lsr.w   #1,d4
        and.w   #$ff,d4
        or.w    (a1),d4
        move.w  d4,4(a5)                    ; POS
        move.w  4(a1),8(a5)                 ; filas
        moveq   #0,d0
        move.w  6(a1),d0                    ; 4 + 4 clip
        tst.w   RX_NREM(a3)
        beq.s   .o3
        move.w  RX_RH(a3),d1
        moveq   #1,d2
        and.w   d5,d2
        btst    d2,d1
        beq.s   .o3
        move.w  d6,d1                       ; con bandas: GV_RBUF + G5L_RSTR
        lsl.w   #2,d1                       ; x (4k + s)
        add.w   d5,d1
        mulu    #G5L_RSTR,d1
        add.l   GV_RBUF(a6),d1
        clr.w   10(a5)                      ; (de un bufer que cambia)
        bra.s   .o4
.o3:    move.w  d5,d1                       ; limpia: offs[c][mitad] = 12 + 4s
        lsl.w   #2,d1
        move.l  12(a0,d1.w),d1
        bclr    #31,d1
        add.l   g5l_cdma(pc),d1
        move.w  #1,10(a5)                   ; (del banco, que no cambia)
.o4:    add.l   d0,d1
        move.l  d1,(a5)
        lea     12(a5),a5
        addq.w  #1,d7
.kn:    addq.w  #1,d6
        lea     RXSZ(a3),a3
        addq.l  #8,a1
        bra     .k
.kd:    lea     GV_EN(a6),a5
        tst.w   d7
        beq     .null
        cmp.w   #1,d7
        beq     .one
        move.w  GV_CI(a6),d0                ; dos: la cadena del flujo s
        mulu    #12,d0
        move.l  GV_CKP(a6),a3
        add.w   d0,a3                       ; a3 = su clave
        move.w  GV_CI(a6),d0
        mulu    #G5L_CSTR,d0
        add.l   GV_RBUF(a6),d0
        add.l   #8*G5L_RSTR,d0
        move.l  d0,a1                       ; a1 = la cadena
        move.w  10(a5),d1                   ; las dos del banco: con clave
        and.w   12+10(a5),d1
        beq.s   .cn
        move.l  (a5),d1
        cmp.l   (a3),d1
        bne.s   .ck
        move.l  12(a5),d1
        cmp.l   4(a3),d1
        bne.s   .ck
        move.w  8(a5),d1
        cmp.w   8(a3),d1
        bne.s   .ck
        move.w  12+8(a5),d1
        cmp.w   10(a3),d1
        bne.s   .ck
        move.w  8(a5),d1                    ; la misma: solo POS y CTL del
        lsl.w   #2,d1                       ; segundo
        move.w  12+4(a5),(a1,d1.w)          ; P40 ok (0..128)
        move.w  12+6(a5),2(a1,d1.w)
        bra     .pt
.ck:    move.l  (a5),(a3)
        move.l  12(a5),4(a3)
        move.w  8(a5),8(a3)
        move.w  12+8(a5),10(a3)
        bra.s   .cc
.cn:    clr.l   (a3)                        ; con bandas: sin clave
.cc:    move.l  (a5),a0
        move.w  8(a5),d1
        add.w   d1,d1
        neg.w   d1
        jmp     .c1e(pc,d1.w)               ; P40 ok: indice negativo a proposito
        rept    32
        move.l  (a0)+,(a1)+
        endr
.c1e:   move.w  12+4(a5),(a1)+              ; POS y CTL del segundo
        move.w  12+6(a5),(a1)+
        move.l  12(a5),a0
        move.w  12+8(a5),d1
        add.w   d1,d1
        neg.w   d1
        jmp     .c2e(pc,d1.w)               ; P40 ok: indice negativo a proposito
        rept    32
        move.l  (a0)+,(a1)+
        endr
.c2e:   clr.l   (a1)                        ; fin
        bra.s   .pt
.one:   move.l  (a5),d0
.pt:    swap    d0
        move.w  d0,2(a4)
        swap    d0
        move.w  d0,6(a4)
        move.w  4(a5),10(a4)
        move.w  6(a5),14(a4)
        lea     16(a4),a4
        bra.s   .sn
.null:  bsr     g5l_nullch
.sn:    addq.w  #1,GV_CI(a6)
        cmp.w   #4,GV_CI(a6)
        blo     .s
        bra     g5l_emitc

; --- g5l_nullch --- canal nulo en a4 (PT = g_null, POS = CTL = 0); a4 += 16
; registros destruidos: d0/a0
g5l_nullch:
        GETBASE a0
        add.l   #g_null-binstart,a0
        move.l  (a0),d0
        swap    d0
        move.w  d0,2(a4)
        swap    d0
        move.w  d0,6(a4)
        clr.w   10(a4)
        clr.w   14(a4)
        lea     16(a4),a4
        rts

;----------------------------------------------------------------------
; --- g5l_vblnull --- sin Rex: SPR4-7 al nulo y colores de partida NOP
; registros destruidos: d0-d2/a0/a2/a4
;----------------------------------------------------------------------
g5l_vblnull:
        bsr     g5l_nullflag
        tst.b   (a0)
        bne.s   .x                          ; ya estaba nulo
        st      (a0)                        ; (TAS no: P29, bus compartido)
        move.l  GV_LIST(a6),a2
        lea     CL_VBL+4(a2),a4
        moveq   #4-1,d2
.l:     bsr     g5l_nullch
        dbf     d2,.l
        moveq   #G5L_VBLN-1,d2
.c:     move.l  #$01fe0000,(a4)+
        dbf     d2,.c
        lea     GV_PNVA(a6),a0              ; (sin colores en esta lista)
        lea     GV_RECA(a6),a2
        cmp.l   GV_REC(a6),a2
        beq.s   .pa
        addq.l  #1,a0
        ifd     CUSHION
        lea     GV_RECB(a6),a2
        cmp.l   GV_REC(a6),a2
        beq.s   .pa
        lea     GV_PNVC(a6),a0
        endc
.pa:    clr.b   (a0)
.x:     rts

; --- g5l_nullflag --- a0 = la bandera "VBL nulo" de la lista GV_LIST
; registros destruidos: a0
g5l_nullflag:
        move.l  a1,-(sp)
        lea     GV_RECA(a6),a1              ; GV_REC: A o B (g5l_render)
        lea     GV_NULLA(a6),a0
        cmp.l   GV_REC(a6),a1
        beq.s   .a
        addq.l  #1,a0
        ifd     CUSHION
        lea     GV_RECB(a6),a1
        cmp.l   GV_REC(a6),a1
        beq.s   .a
        lea     GV_NULLC(a6),a0
        endc
.a:     move.l  (sp)+,a1
        rts

        cnop    0,4
g5l_cdma:
        dc.l    0                           ; banco de las variantes limpias (chip)
g5l_rbuf:
        dc.l    0                           ; bufer de las bandas: 2 listas x 4 flujos (chip)
g5l_v:  ds.b    GV_SIZE
        even
        include "work/g5l.i"
