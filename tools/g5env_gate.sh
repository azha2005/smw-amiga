#!/bin/sh
# B2bis: puertas reproducibles, derivados y logs exclusivamente en work/.
set -eu
trap 'echo "G5ENV: FALLO"' 0
PY=${PY:-python}
mkdir -p work/b2b
CDEFS='-DNOOAM -DSPR_OAM -DSPR_G5' GDEFS='-DREPLAY' OUT=work/b2b_r \
    sh tools/game_build.sh > work/b2b/game_build.log 2>&1
"$PY" tools/g5env_verify.py key --bin work/b2b_r/game.bin --lst work/b2b_r/game.lst
"$PY" tools/g5env_verify.py decode
"$PY" tools/g5env_verify.py cache
CDEFS='-DNOOAM -DSPR_OAM -DSPR_G5' sh tools/logicbench_build.sh > work/b2b/front_build.log 2>&1
cp work/logicbench.bin work/logicbench.lst work/b2b/
"$PY" tools/g5env_verify.py front
"$PY" tools/g5env_verify.py project
"$PY" tools/g5env_edges.py
"$PY" tools/g5env_verify.py game
"$PY" tools/gamecheck.py --bin work/b2b_r/game.bin --lst work/b2b_r/game.lst --engine musashi --spr
for bank in plain g3; do
    for mode in replay live; do
        g=''; [ "$mode" = replay ] && g='-DREPLAY'
        b=''; [ "$bank" = g3 ] && b='work/g3/bank'
        out="work/b2b_${mode}_${bank}"
        CDEFS='-DNOOAM -DSPR_OAM -DSPR_G5' GDEFS="$g" SPR_BANK="$b" OUT="$out" \
            sh tools/game_build.sh > "work/b2b/build_${mode}_${bank}.log" 2>&1
        "$PY" tools/memmap.py "$out/game.lst" --data work/yi1_s_g5.dat > "$out/memmap.log"
        [ "$mode" = replay ] || "$PY" tools/restart_verify.py --dir "$out"
    done
done
"$PY" tools/g5env_memory.py
trap - 0
echo 'G5ENV: OK'
