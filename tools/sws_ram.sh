#!/bin/sh
# SW-S:  volcado por frame de la RAM de los tres motores (snesorc --ram-out)
export SNESORC_ASSETS=${SNESORC_ASSETS:-C:/msys64/home/JC/.cache/snesrev-smw/smw_assets.dat}
R='0F34:0F3A,1697:1698,16E1:170B,17C0:17D0,17F0:185C,1863:1864,18E9:18F8'
mkdir -p work/sws/lf
for f in tools/snesorc/*.orc; do tr -d '\r' < $f > work/sws/lf/$(basename $f); done
tr -d '\r' < work/oracle_yi1.txt > work/sws/lf/replay.txt
work/snesorc --script work/sws/lf/boot_yi1.orc --replay work/sws/lf/replay.txt --replay-seg 2 \
    --ram $R --ram-out work/sws/ram_yi1.bin --out work/sws/chk_yi1.txt 2> work/sws/yi1.err; echo yi1=$?
for t in pw_bloques chuck_kill spin_kill stress_piranha pw_flor; do
  work/snesorc --script work/sws/lf/$t.orc --ram $R --ram-out work/sws/ram_$t.bin --out work/sws/chk_$t.txt 2> work/sws/$t.err; echo $t=$?
done
ls -la work/sws/*.bin
