#!/bin/sh
# ARQ-0 paso 1: builds BENCH de partida (replay BM1, G5L+CUSHION)
cd "$(dirname "$0")/../.."
b() {  # nombre oraculo replay
  OUT=work/arq0/b_$1 ORACLE=$2 REPLAY=$3 GDEFS="-DREPLAY -DBENCH" sh work/buildlock.sh sh tools/bm_build.sh > work/arq0/b_$1.log 2>&1
  echo "$1 rc=$?"
}
b yi1 work/oracle_yi1.bin work/yi1_replay.bin
b back work/oracle_stress_back.bin work/stress_back_replay.bin
b sprites work/oracle_stress_sprites.bin work/stress_sprites_replay.bin
b hills2 work/oracle_hills2.bin work/arq0/hills2_replay.bin
b goal work/arq0/oracle_goal_cut.bin work/arq0/goal_replay.bin
