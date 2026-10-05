; Macros PIC largas: ABI/coste documentados en player/pic68k.s (P102).
        ifnd    PIC68K_MACROS
PIC68K_MACROS equ 1
PICCALL macro
        lea     .pc\@(pc),a0
        adda.l  #\1-.pc\@,a0
        jsr     (a0)                       ; lint: targets \1
.pc\@:
        endm

PICJUMP macro
        lea     .pc\@(pc),a0
        adda.l  #\1-.pc\@,a0
        jmp     (a0)                       ; lint: targets \1
.pc\@:
        endm
        endc
