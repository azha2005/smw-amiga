#!/bin/sh
# BM1 opt-in: boot MFM, codigo fijo en C00000, arenas sin Exec.
set -e
cd "$(dirname "$0")/.."
VBCC=${VBCC:-/c/Users/JC/vbcc}
PY=${PY:-python}
OUT=${OUT:-work/bm1}
mkdir -p "$OUT"
"$VBCC/bin/vasmm68k_mot.exe" -quiet -Fbin -m68000 -no-opt -I player -L "$OUT/boot_bm.lst" -o "$OUT/boot_bm.bin" player/boot_bm.s
$PY - "$OUT/boot_bm.lst" <<'PY'
import sys
from pathlib import Path
sys.path.insert(0, 'tools')
from m68kverify import symbols
s = symbols(sys.argv[1])
Path('work/bm_boot.i').write_text('BM_READ_ADDR equ $%x\nBM_MOTOR_ADDR equ $%x\n' % (
    s['BM_CODE'] + s['bm_read'], s['BM_CODE'] + s['bm_motoroff']))
PY
CDEFS='-DNOOAM -DSPR_OAM' GDEFS="${GDEFS--DREPLAY} -DG5L -DCUSHION -DBM_FIXED" SPR_BANK=work/g3/bank OUT="$OUT" sh tools/game_build.sh
$PY tools/mkadf.py --boot "$OUT/boot_bm.bin" --stage2 "$OUT/game.bin" --data work/yi1_s_g5.dat --out "$OUT/game.adf"
