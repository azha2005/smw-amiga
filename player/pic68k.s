;----------------------------------------------------------------------
; pic68k.s - puente PIC junto al C para SPR_OAM; macros compartidas.
; Una rama de palabra alcanza +/-32 KB; vasm puede relajar jsr/jmp a una
; direccion absoluta del binario. El boot lo carga en otra base (P102).
;
; PICCALL/PICJUMP: entrada = argumentos de la funcion destino en la pila;
; salida: la del destino; registros destruidos: d0-d1/a0-a1 (ABI de vbcc).
; a0 se usa para calcular el destino. La diferencia de etiquetas es de 32
; bits; solo el lea a la etiqueta local usa desplazamiento corto.
; ciclos: PICCALL ~40 y PICJUMP ~32 (68000 sin DMA); el total se mide aparte.
;----------------------------------------------------------------------
        include "player/picmacros.i"

; Puente junto a mcoll.code.s: sus llamadas de palabra siguen cercanas.
; entrada: sin argumentos (f44d_asm lee ram[]).
; salida: d0 = resultado.
; registros destruidos: d0-d1/a0-a1 (ABI de vbcc).
        public  _f44d_asm_bridge
_f44d_asm_bridge:
        PICJUMP _f44d_asm
