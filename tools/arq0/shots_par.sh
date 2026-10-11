#!/bin/sh
# capturas BENCH en paralelo, una copia de shot.ps1 por slot (P135: cada copia
# escribe su propio <slot>/work/shot.uae), sin pausa por foco
cd "$(dirname "$0")/../.."
LOCK=$(cygpath -w ../winuae_lock.ps1)
s() {  # slot dir espera
  sd=work/arq0/slot/$1
  mkdir -p "$sd/tools" "$sd/work"
  sed "s/'use_gui=no'/'win32.active_not_captured_pause=false'\n    'win32.inactive_pause=false'\n    'win32.iconified_pause=false'\n    'use_gui=no'/" tools/shot.ps1 > "$sd/tools/shot.ps1"
  d=work/arq0/$2
  rm -f "$d/bench.png" "$d/read.txt"
  powershell.exe -NoProfile -ExecutionPolicy Bypass -File "$LOCK" "$(cygpath -w "$sd/tools/shot.ps1")" -Exact -Adf "$(cygpath -w "$PWD/$d/game.adf")" -Out "$(cygpath -w "$PWD/$d")\bench.png" -Wait $3 > "$d.shot.log" 2>&1
  python tools/game_read.py --shot "$d/bench.png" --auto > "$d/read.txt" 2>&1
  echo "$2 rc=$? $(grep 'frames medidos' "$d/read.txt")"
}
# uso: sh tools/arq0/shots_par.sh b_yi1:260 b_back:200 p5_goal:170 ...  (de a 3)
i=0
for arg in "$@"; do
  slot=$(echo a b c | cut -d' ' -f$((i % 3 + 1)))
  s $slot ${arg%%:*} ${arg#*:} &
  i=$((i + 1))
  [ $((i % 3)) = 0 ] && wait
done
wait
