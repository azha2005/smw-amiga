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
#   4b. G2T-B2 (-DSPR_G5): el bloque de la foto (g5_capture) en el PC
#      contra g2t_ref.mario_amiga y en el 68000 contra el PC, con ciclos
#      (tools/g5plan_verify.py; logs en work/g5gate/)
#   4c. G2T-B4/B5: segmentos del PC = referencia y plan PC = 68000 =
#      g2t_ref en las tres trazas (logs en work/g2tb35/)
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

# 4b. G2T-B2: g5_capture (SPR_G5), PC = g2t_ref y 68000 = PC
G5G=work/g5gate
mkdir -p "$G5G"
if [ "$fails" = 0 ]; then
    if CDEFS='-DNOOAM -DSPR_OAM -DSPR_G5' sh tools/logicbench_build.sh > "$G5G/logicbench_build.log" 2>&1 &&
       cp work/logicbench.bin work/logicbench.lst "$G5G/" &&
       $CC -O2 -DNOOAM -DSPR_OAM -DSPR_G5 -Iplayer -o "$G5G/marioverify_g5" tools/marioverify.c $SRC             player/g5plan.c player/spr_*.c player/gen/smwrom00.c > "$G5G/gcc.log" 2>&1; then
        ok "logicbench y marioverify SPR_G5 ($(wc -c < "$G5G/logicbench.bin") B)"
        for name in yi1 normal spin_kill; do
            if [ ! -f "work/oam_$name.trace" ] || [ ! -f "work/oracle_${name}_oam.bin" ]; then
                fail "G2T-B2 $name: falta work/oam_$name.trace o work/oracle_${name}_oam.bin"
                continue
            fi
            GAME_G2T_CAP="$G5G/cap_$name.bin" "$G5G/marioverify_g5" "work/oracle_$name.bin" game                 > "$G5G/${name}_pc.log" 2>&1
            if $PY tools/g5plan_verify.py env --name "$name" --cap "$G5G/cap_$name.bin"                     --trace "work/oam_$name.trace=work/oracle_${name}_oam.bin" > "$G5G/${name}_env.log" 2>&1; then
                ok "G2T-B2 envolventes $name: $(grep '^B2 ' "$G5G/${name}_env.log")"
            else
                fail "G2T-B2 envolventes $name: $(tail -n 2 "$G5G/${name}_env.log" | head -n 1) (ver $G5G/${name}_env.log)"
            fi
            if $PY tools/g5plan_verify.py m68k --name "$name" --cap "$G5G/cap_$name.bin"                     --bin "$G5G/logicbench.bin" --lst "$G5G/logicbench.lst" > "$G5G/${name}_68000.log" 2>&1; then
                ok "G2T-B2 68000 $name: $(grep '^g5_capture' "$G5G/${name}_68000.log")"
            else
                fail "G2T-B2 68000 $name: $(tail -n 1 "$G5G/${name}_68000.log") (ver $G5G/${name}_68000.log)"
            fi
        done
    else
        fail "build SPR_G5 (ver $G5G/logicbench_build.log, $G5G/gcc.log)"
    fi
fi

# 4c. Plan del Rex: regenerar los insumos desde el banco y el modelo.
# No aceptar derivados viejos como una comprobacion hecha del codigo actual.
B35G=work/g2tb35
mkdir -p "$B35G"
if [ "$fails" = 0 ]; then
    if $PY tools/g5bank_env.py --bank work/g3/bank --out work/g3/bank.g5env \
         --trace work/oam_yi1.trace=work/oracle_yi1_oam.bin \
         --trace work/oam_normal.trace=work/oracle_normal_oam.bin \
         --trace work/oam_spin_kill.trace=work/oracle_spin_kill_oam.bin > "$B35G/env.log" 2>&1 &&
       $PY tools/g2t_ref.py --dump --bank work/g3/bank --out work/g2t_ref \
         --trace work/oam_yi1.trace=work/oracle_yi1_oam.bin \
         --trace work/oam_normal.trace=work/oracle_normal_oam.bin \
         --trace work/oam_spin_kill.trace=work/oracle_spin_kill_oam.bin > "$B35G/ref.log" 2>&1 &&
       $PY tools/g2t_segdump.py --out "$B35G" \
         --trace work/oam_yi1.trace=work/oracle_yi1_oam.bin \
         --trace work/oam_normal.trace=work/oracle_normal_oam.bin \
         --trace work/oam_spin_kill.trace=work/oracle_spin_kill_oam.bin > "$B35G/segdump.log" 2>&1 &&
       $CC -O2 -DNOOAM -DSPR_OAM -DSPR_G5 -Iplayer -o "$B35G/g5plan_test" \
         tools/g5plan_test.c player/g5plan.c > "$B35G/gcc.log" 2>&1; then
        for name in yi1 normal spin_kill; do
            if "$B35G/g5plan_test" "$G5G/cap_$name.bin" "$B35G/segw_$name.bin" \
                    "$B35G/segs_$name.bin" work/g3/bank.idx work/g3/bank.g5env \
                    work/cc/mario_pal.bin "$B35G/plan_$name.bin" > "$B35G/${name}_pc.log" 2>&1 &&
               cmp "$B35G/plan_$name.bin" "work/g2t_ref/plan_$name.bin" >> "$B35G/${name}_pc.log" 2>&1; then
                ok "G2T-B5 PC $name: $(tail -n 1 "$B35G/${name}_pc.log"); plan identico a g2t_ref"
            else
                fail "G2T-B5 PC $name (ver $B35G/${name}_pc.log)"
            fi
            if $PY tools/g5plan_verify.py plan --name "$name" --cap "$G5G/cap_$name.bin" \
                    --segw "$B35G/segw_$name.bin" --ref "work/g2t_ref/plan_$name.bin" \
                    --bin "$G5G/logicbench.bin" --lst "$G5G/logicbench.lst" \
                    > "$B35G/${name}_68000.log" 2>&1; then
                ok "G2T-B5 68000 $name: $(grep '^g5_plan ' "$B35G/${name}_68000.log")"
            else
                fail "G2T-B5 68000 $name (ver $B35G/${name}_68000.log)"
            fi
        done
    else
        fail "insumos del plan G2T (ver $B35G/env.log, ref.log, segdump.log, gcc.log)"
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
