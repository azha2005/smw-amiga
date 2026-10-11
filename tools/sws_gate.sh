#!/bin/sh
# SW-S: la puerta de RAM de los motores de puntos, humo y sprites menores
# (tools/sws_cmp.py) contra los volcados de snesorc (tools/sws_ram.sh).
#   sh tools/sws_gate.sh                 # yi1 (replay normal) + 4 grabaciones
#   TRACES=" " sh tools/sws_gate.sh      # solo yi1
# pw_flor no entra en el arnes (replay de 79 KB: el binario pasa de DATA).
export PATH="$TEMP/pyshim:/c/msys64/ucrt64/bin:$PATH" VBCC=${VBCC:-/c/Users/JC/vbcc} PY=python PYTHONIOENCODING=utf-8
mkdir -p work/sws
OUT=work/sws/b1 sh tools/bm_build.sh > work/sws/b1.log 2>&1 || { echo "yi1: build fallo"; exit 1; }
echo "== yi1"
python tools/sws_cmp.py --bin work/sws/b1/game.bin --lst work/sws/b1/game.lst --ram work/sws/ram_yi1.bin --show ${SHOW:-3} 2>&1 | tail -${TAIL:-6}
for t in ${TRACES:-pw_bloques chuck_kill spin_kill stress_piranha}; do
  o=work/sws/t_$t
  XCDEFS=-DLSS_SNESORC ORACLE=work/oracle_$t.bin REPLAY=work/sws/${t}_replay.bin OUT=$o NOCC=1 sh tools/bm_build.sh > $o.build.log 2>&1 || { echo "$t: build fallo"; continue; }
  echo "== $t"
  python tools/sws_cmp.py --bin $o/game.bin --lst $o/game.lst --ram work/sws/ram_$t.bin --show ${SHOW:-3} 2>&1 | tail -${TAIL:-6}
done
