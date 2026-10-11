#!/bin/sh
# ARQ-0 P1-V: builds BENCH con 5 planos + la sonda de DMA de los cortes de PF2
# (K MOVE nulos por linea). Uso: K=8 sh tools/arq0/build_cut.sh -> work/arq0/c<K>_*
# Bandas (P1-V2): BANDS=48,192 sh tools/arq0/build_cut.sh -> work/arq0/bd48_192_*
# (5 planos fuera de [48, 192), sin MOVE nulos)
cd "$(dirname "$0")/../.."
K=${K:-8}
if [ -n "$BANDS" ]; then
  P=bd$(echo $BANDS | tr , _); D="-DARQ_BANDS -DARQ_B1=${BANDS%,*} -DARQ_B2=${BANDS#*,}"
else
  P=c$K; D="-DARQ_5PL -DARQ_CUTN=$K"
fi
b() {  # nombre oraculo replay
  OUT=work/arq0/${P}_$1 ORACLE=$2 REPLAY=$3 GDEFS="-DREPLAY -DBENCH $D" sh work/buildlock.sh sh tools/bm_build.sh > work/arq0/${P}_$1.log 2>&1
  echo "${P}_$1 rc=$?"
}
b yi1 work/oracle_yi1.bin work/yi1_replay.bin
b back work/oracle_stress_back.bin work/stress_back_replay.bin
b sprites work/oracle_stress_sprites.bin work/stress_sprites_replay.bin
b hills2 work/oracle_hills2.bin work/arq0/hills2_replay.bin
b goal work/arq0/oracle_goal_cut.bin work/arq0/goal_replay.bin
