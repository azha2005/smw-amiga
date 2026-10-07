#!/bin/sh
# oam68k_gate.sh - la puerta de la OAM ampliada (SPR_OAM) en el 68000.
#
# tools/regress.py comprueba SPR_OAM solo en el C del PC; el binario de
# vbcc con -DNOOAM -DSPR_OAM no lo compila. Esta es la lista de
# docs/validacion-g8b.md ("Repetir trazas y puertas") en un solo script,
# para que no se salte ningun paso:
#
#   1. logicbench con CDEFS='-DNOOAM -DSPR_OAM' (copia en work/oamgate/)
#   2. marioverify y la biblioteca del PC con -DNOOAM -DSPR_OAM
#   3. por cada oraculo: traza OAM del PC y sprite_oam_verify del 68000
#   4. cruce de la RAM entera PC = 68000 (m68kverify --cross)
#   5. vuelve a armar el logicbench POR DEFECTO (lo usa regress.py)
#
#   sh tools/oam68k_gate.sh        # sale con 0 solo si TODO pasa
#
# Logs: work/oamgate/*.log. Ultima linea: "OAM68K: OK" o "OAM68K: FALLA (n)".
cd "$(dirname "$0")/.."
PY=${PY:-python}
CC=${CC:-gcc}
G=work/oamgate
mkdir -p "$G"
fails=0
fail() { echo "FALLA  $1"; fails=$((fails + 1)); }
ok() { echo "ok     $1"; }

SRC="player/mario.c player/mcoll.c player/manim.c player/mgfx.c player/mcam.c player/msprite.c player/mspr.c"

# 1. el 68000 con la OAM ampliada
if CDEFS='-DNOOAM -DSPR_OAM' sh tools/logicbench_build.sh > "$G/logicbench_build.log" 2>&1; then
    cp work/logicbench.bin "$G/logicbench.bin"
    cp work/logicbench.lst "$G/logicbench.lst"
    if grep -q "^[0-9A-F]* _rex_gfx$" "$G/logicbench.lst"; then
        ok "logicbench SPR_OAM ($(wc -c < "$G/logicbench.bin") B, con la OAM ampliada)"
    else
        fail "logicbench SPR_OAM: el listado no tiene _rex_gfx (CDEFS no llego)"
    fi
else
    fail "logicbench SPR_OAM (ver $G/logicbench_build.log)"
fi

# 2. el PC con la OAM ampliada
if $CC -O2 -DNOOAM -DSPR_OAM -Iplayer -o "$G/marioverify_oam" tools/marioverify.c $SRC \
        player/spr_*.c player/gen/smwrom00.c > "$G/gcc.log" 2>&1 &&
   $CC -shared -O2 -DNOOAM -DSPR_OAM -Iplayer -o "$G/libport_oam.so" $SRC \
        player/spr_*.c player/gen/smwrom00.c >> "$G/gcc.log" 2>&1; then
    ok "marioverify_oam y libport_oam"
else
    fail "gcc (ver $G/gcc.log)"
fi

# 3. la OAM de cada tipo, 68000 contra la grabada
if [ "$fails" = 0 ]; then
    for entry in yi1:AB chuck:95 goal:7B shells:05 banzai:9F stress_piranha:4F; do
        name=${entry%%:*}
        kind=${entry#*:}
        if [ ! -f "work/oracle_$name.bin" ]; then
            fail "OAM $name: falta work/oracle_$name.bin"
            continue
        fi
        GAME_OAM_TRACE="$G/$name.trace" "$G/marioverify_oam" "work/oracle_$name.bin" game \
            > "$G/${name}_pc.log" 2>&1
        if $PY tools/sprite_oam_verify.py --bin "$G/logicbench.bin" --lst "$G/logicbench.lst" \
                --trace "$G/$name.trace" --oracle "work/oracle_$name.bin" --require "$kind" \
                > "$G/${name}_68000.log" 2>&1; then
            ok "OAM $name ($kind): $(tail -n 1 "$G/${name}_68000.log")"
        else
            fail "OAM $name ($kind): $(tail -n 1 "$G/${name}_68000.log") (ver $G/${name}_68000.log)"
        fi
    done

    # 4. la RAM entera, PC = 68000, en lazo cerrado con sprites
    if $PY tools/m68kverify.py --engine musashi --mode loop --sprites \
            --bin "$G/logicbench.bin" --lst "$G/logicbench.lst" \
            --cross "$G/libport_oam.so" > "$G/cross.log" 2>&1; then
        ok "cruce RAM PC = 68000: $(grep -i 'diferen\|cruce' "$G/cross.log" | tail -n 1)"
    else
        fail "cruce RAM PC = 68000 (ver $G/cross.log)"
    fi
fi

# 5. dejar el logicbench por defecto, el que espera regress.py
if sh tools/logicbench_build.sh > "$G/logicbench_default.log" 2>&1; then
    ok "logicbench por defecto restaurado"
else
    fail "logicbench por defecto (ver $G/logicbench_default.log)"
fi

if [ "$fails" = 0 ]; then
    echo "OAM68K: OK"
    exit 0
fi
echo "OAM68K: FALLA ($fails)"
exit 1
