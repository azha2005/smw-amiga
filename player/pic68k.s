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

        ifd SPR_OAM
; --- _powerup_from_block_bridge / _mario_E2BD_bridge ---
; entrada: argumentos vbcc intactos en la pila (retorno y ranuras long).
; salida: la del destino; el salto final conserva el retorno original.
; registros destruidos: a0 (caller saved); los del destino.
; ciclos: +32 por puente (68000 sin DMA); ver informe G8b.
        public  _powerup_from_block_bridge
_powerup_from_block_bridge:
        PICJUMP _powerup_from_block
        public  _mario_E2BD_bridge
_mario_E2BD_bridge:
        PICJUMP _mario_E2BD
        public  _sprite_run_bridge
_sprite_run_bridge:
        PICJUMP _sprite_run
        endif

; --- _mario_collide_bridge / D5F2 / D062 / D7E4 / CEB1 (G5L-R-L2) ---
; mario_player_c (el C raro de manim.c) llama a la logica que ahora es
; asm en logic68k.s, a mas de 32 KB en los dos builds (NOOAM y SPR_OAM).
; entrada: sin argumentos.
; salida: la del destino.
; registros destruidos: a0 (caller saved); los del destino.
        public  _mario_collide_bridge
_mario_collide_bridge:                      ; G5L-R-L2: mario_player_c -> logic68k.s
        PICJUMP _mario_collide
        public  _mario_D5F2_bridge
_mario_D5F2_bridge:
        PICJUMP _mario_D5F2
        public  _mario_D062_bridge
_mario_D062_bridge:
        PICJUMP _mario_D062
        public  _mario_D7E4_bridge
_mario_D7E4_bridge:
        PICJUMP _mario_D7E4
        public  _mario_CEB1_bridge
_mario_CEB1_bridge:
        PICJUMP _mario_CEB1
        public  _f7f4_bridge
_f7f4_bridge:                               ; camera_F6DB_c (mcam.c) -> f7f4 (asm)
        PICJUMP _f7f4
