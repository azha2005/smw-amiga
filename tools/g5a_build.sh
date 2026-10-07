#!/bin/sh
# Prueba descartable G5a; no altera game_build.sh ni sus opciones normales.
set -eu
cd "$(dirname "$0")/.."
export VBCC=${VBCC:-/c/Users/JC/vbcc} PY=${PY:-python}
$PY tools/sprgfx_manifest.py --trace work/oam_yi1.trace=work/oracle_yi1_oam.bin \
    --trace work/oam_normal.trace=work/oracle_normal_oam.bin \
    --trace work/oam_spin_kill.trace=work/oracle_spin_kill_oam.bin --out work/g5a_manifest.json
$PY tools/mksprgfx.py --format-test --manifest work/g5a_manifest.json --out work/g5a_base
export CDEFS='-DNOOAM -DSPR_OAM'
OUT=work/g5a_cc GDEFS='-DREPLAY -DSTOPF=1132' sh tools/game_build.sh > work/g5a_cc.log 2>&1
$PY tools/g5a.py build > work/g5a_prepare.log
for kind in visual bench empty nodma; do
    extra=
    [ "$kind" = bench ] && extra=-DBENCH
    [ "$kind" = empty ] && extra='-DBENCH -DG5A_EMPTY'
    [ "$kind" = nodma ] && extra='-DBENCH -DG5A_NODMA'
    "$VBCC/bin/vasmm68k_mot.exe" -quiet -Fbin -m68000 -DREPLAY -DSPR_OAM -DSTOPF=1132 $extra \
        -I player -I . -L work/g5a/$kind.lst -o work/g5a/$kind.bin work/g5a/game.s
    $PY tools/piccheck.py --lst work/g5a/$kind.lst
    $PY tools/mkadf.py --boot work/boot.bin --stage2 work/g5a/$kind.bin \
        --data work/g5a/scroll.dat --out work/g5a/$kind.adf
done
# Mismo C/OAM y caso detenido, sin Rex ni cambios de stride/header.
NOCC=1 OUT=work/g5a_control GDEFS='-DREPLAY -DSTOPF=1132' sh tools/game_build.sh
NOCC=1 OUT=work/g5a_oam GDEFS='-DREPLAY -DBENCH' sh tools/game_build.sh
CDEFS=-DNOOAM OUT=work/g5a_default GDEFS='-DREPLAY -DBENCH' sh tools/game_build.sh
