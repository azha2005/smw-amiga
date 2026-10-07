#!/bin/sh
# stress_ab_build.sh - arma los ADF del A/B de estres con BENCH
# (docs/medida-d1-winuae.md, ultimo apartado).
#
#   sh tools/stress_ab_build.sh [prefijo]       # prefijo por defecto: st
#
# Arma work/<prefijo>_<escenario>_<variante>/game.adf para
#   escenario: back (oracle_stress_back, 4127 ops) y sprites (1915 ops)
#              y yi1 (el replay normal de YI1)
#   variante:  nooam (CDEFS=-DNOOAM), oam (-DNOOAM -DSPR_OAM)
# Con SPR_BANK=work/g3/bank agrega la variante g3 (SPR_OAM + banco G3).
# Despues: tools/stress_ab_shots.ps1 captura, tools/stress_ab_read.sh lee.
cd "$(dirname "$0")/.."
P=${1:-st}
VARS="nooam oam"
[ -n "$SPR_BANK" ] && VARS="$VARS g3"
BANK=$SPR_BANK
fails=0
for sc in back sprites yi1; do
    if [ "$sc" = yi1 ]; then
        oracle=work/oracle_yi1.bin; replay=work/yi1_replay.bin
    else
        oracle=work/oracle_stress_$sc.bin; replay=work/stress_${sc}_replay.bin
    fi
    for v in $VARS; do
        c='-DNOOAM -DSPR_OAM'
        b=
        [ "$v" = nooam ] && c='-DNOOAM'
        [ "$v" = g3 ] && b=$BANK
        out=work/${P}_${sc}_$v
        if env SPR_BANK="$b" CDEFS="$c" GDEFS='-DREPLAY -DBENCH' ORACLE="$oracle" REPLAY="$replay" \
               OUT="$out" sh tools/game_build.sh > "$out.log" 2>&1 \
           && ! grep -q 'ERROR PIC' "$out.log"; then
            echo "ok     $out/game.adf"
        else
            echo "FALLA  $out (ver $out.log)"
            fails=$((fails + 1))
        fi
    done
done
# el logicbench por defecto, que es el que espera regress.py
sh tools/logicbench_build.sh > "work/${P}_logicbench_default.log" 2>&1 || fails=$((fails + 1))
[ "$fails" = 0 ] && { echo "STRESS_AB_BUILD: OK"; exit 0; }
echo "STRESS_AB_BUILD: FALLA ($fails)"
exit 1
