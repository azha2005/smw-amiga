#!/bin/sh
# stress_ab_read.sh - lee las capturas de tools/stress_ab_shots.ps1 y
# escribe una fila por build: fotos perdidas, racha, level_frame max.,
# total medio. Una captura sin sincronia es un FALLO, no un cero.
#
#   sh tools/stress_ab_read.sh [prefijo]
cd "$(dirname "$0")/.."
P=${1:-st}
PY=${PY:-python}
fails=0
printf '%-22s %-16s %6s %-16s %-14s\n' build "fotos perdidas" racha "level_frame max" "total medio"
for d in work/${P}_*_*/; do
    d=${d%/}
    [ -f "$d/bench.png" ] || continue
    out=$($PY tools/game_read.py --shot "$d/bench.png" --auto 2>&1)
    if ! printf '%s\n' "$out" | grep -q '^sincronia *: OK'; then
        echo "FALLA  $d: sin sincronia (captura mala o el juego no termino)"
        fails=$((fails + 1))
        continue
    fi
    lost=$(printf '%s\n' "$out" | sed -n 's/.*fotos perdidas *: \([0-9]*\) (\([0-9.]*\) %.*/\1 (\2 %)/p')
    streak=$(printf '%s\n' "$out" | sed -n 's/.*racha mas larga *: \([0-9]*\).*/\1/p')
    lf=$(printf '%s\n' "$out" | sed -n 's/^level_frame *[0-9]* *[0-9]* *\([0-9.]*%\).*/\1/p')
    mean=$(printf '%s\n' "$out" | sed -n 's/^total medio *: [0-9]* ticks = \([0-9.]*%\).*/\1/p')
    printf '%-22s %-16s %6s %-16s %-14s\n' "${d#work/}" "$lost" "$streak" "$lf" "$mean"
    printf '%s\n' "$out" > "$d/read.txt"
done
n=$(ls -d work/${P}_*_*/bench.png 2>/dev/null | wc -l)
[ "$n" -gt 0 ] || { echo "STRESS_AB_READ: FALLA (no hay work/${P}_*/bench.png)"; exit 1; }
[ "$fails" = 0 ] || { echo "STRESS_AB_READ: FALLA ($fails)"; exit 1; }
echo "STRESS_AB_READ: OK"
