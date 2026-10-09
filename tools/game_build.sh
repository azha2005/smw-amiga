#!/bin/sh
# game_build.sh - arma work/game.adf: el juego (player/game.s = el C de la
# logica + player/scroll.s), Etapas 6.3 y 6b.
#
#   sh tools/game_build.sh                       # replay entero (-DREPLAY)
#   GDEFS="-DREPLAY -DSTOPF=1200" OUT=work/g1200 sh tools/game_build.sh
#   ORACLE=work/oracle_stress_back.bin REPLAY=work/stress_back_replay.bin \
#     OUT=work/d1-back GDEFS="-DREPLAY -DBENCH" sh tools/game_build.sh
#
# 1. El C: lo compila tools/logicbench_build.sh (work/cc/*.s; arma tambien
#    logicbench, que no molesta).
# 2. Lo que se deriva del ROM y no esta en git (R9): work/yi1_s.dat
#    (mkscroll.py), work/yi1_replay.bin (m68kverify.py --replay, con el
#    binario de logicbench: el mismo C) y work/cc/spr.lv.
# 3. vasm (-Fbin) y mkadf.py con yi1_s.dat detras.
set -e
cd "$(dirname "$0")/.."
VBCC=${VBCC:-/c/Users/JC/vbcc}
X=; [ -f "$VBCC/bin/vasmm68k_mot.exe" ] && X=.exe
PY=${PY:-python}
GDEFS=${GDEFS--DREPLAY}
CDEFS=${CDEFS--DNOOAM}
export CDEFS
# Compartir el modo de OAM con logicbench; nunca activar solo una mitad.
case " $CDEFS " in
    *" -DSPR_OAM"*) GDEFS="$GDEFS -DSPR_OAM"; SPR_MODE=1 ;;
    *" -DNOOAM"*) SPR_MODE=0
        case " $GDEFS " in *" -DSPR_OAM"*) echo "ERROR: SPR_OAM en GDEFS requiere el mismo flag en CDEFS"; exit 1 ;; esac ;;
    *) GDEFS="$GDEFS -DSPR_OAM"; SPR_MODE=1 ;;
esac
# SPR_G5 (G2T, fase C1): el segmento de la lista del copper de 256 B y el
# bloque de armado de la linea 30; necesita su propio yi1_s_g5.dat
# (mkscroll.py --g5: los desplazamientos de CHG usan SEG = 256).
YDAT=work/yi1_s.dat
case " $CDEFS " in
    *" -DSPR_G5"*)
        [ "$SPR_MODE" = 1 ] || { echo "ERROR: SPR_G5 requiere SPR_OAM (CDEFS='-DNOOAM -DSPR_OAM -DSPR_G5')"; exit 1; }
        GDEFS="$GDEFS -DSPR_G5"; YDAT=work/yi1_s_g5.dat ;;
    *) case " $GDEFS " in *" -DSPR_G5"*) echo "ERROR: SPR_G5 en GDEFS requiere el mismo flag en CDEFS"; exit 1 ;; esac ;;
esac
# G5L (player/g5l.s): el Rex con el plan de color por filas. Layout de
# lista de SPR_G5, sin el C ni el asm de B2bis; la tabla la genera g5l.py.
case " $GDEFS " in
    *" -DG5L "*)
        [ "$SPR_MODE" = 1 ] || { echo "ERROR: G5L requiere SPR_OAM (CDEFS='-DNOOAM -DSPR_OAM')"; exit 1; }
        case " $CDEFS " in *" -DSPR_G5"*) echo "ERROR: G5L no usa el C de SPR_G5"; exit 1 ;; esac
        [ -n "$SPR_BANK" ] || { echo "ERROR: G5L requiere SPR_BANK"; exit 1; }
        YDAT=work/yi1_s_g5.dat
        $PY tools/g5l.py mk --bank "$SPR_BANK" ;;
esac
OUT=${OUT:-work}
if [ -n "$SPR_BANK" ]; then
    [ "$SPR_MODE" = 1 ] || { echo "ERROR: SPR_BANK requiere SPR_OAM"; exit 1; }
    GDEFS="$GDEFS -DSPR_BANK"
    $PY tools/sprgfx_load.py --bank "$SPR_BANK" --include work/sg3_bank.i
fi
# Cpre solo existe en el replay con banco y lista G5; nunca en el vivo.
case " $GDEFS " in
    *" -DG5_PRE "*)
        case " $GDEFS " in *" -DREPLAY "*) ;; *) echo "ERROR: G5_PRE requiere REPLAY"; exit 1 ;; esac
        case " $CDEFS " in *" -DSPR_G5 "*) ;; *) echo "ERROR: G5_PRE requiere SPR_G5"; exit 1 ;; esac
        [ -n "$SPR_BANK" ] || { echo "ERROR: G5_PRE requiere SPR_BANK"; exit 1; }
        case " $GDEFS " in *" -DG5_PRE_PROBE "*) ;; *) echo "ERROR: Cpre parcial requiere G5_PRE_PROBE; no hay emisor completo"; exit 1 ;; esac
        case " $GDEFS " in *" -DG5_EMPTY "*) echo "ERROR: G5_EMPTY pendiente del emisor C3"; exit 1 ;; esac
        case " $GDEFS " in
            *" -DG5_PRE_EXT "*) ;;
            *) [ -n "$G5_PRE_DATA" ] || { echo "ERROR: falta G5_PRE_DATA"; exit 1; }
               $PY tools/g2t_preplan.py include --table "$G5_PRE_DATA" ;;
        esac ;;
    *) case " $GDEFS " in
        *" -DG5_EMPTY "*|*" -DG5_PRE_EXT "*|*" -DG5_PRE_PROBE "*) echo "ERROR: flags Cpre requieren G5_PRE"; exit 1 ;;
       esac ;;
esac
REPLAY=${REPLAY:-work/yi1_replay.bin}
ORACLE=${ORACLE:-work/oracle_yi1.bin}
mkdir -p "$OUT"
[ -n "$NOCC" ] || sh tools/logicbench_build.sh
# NOCC tambien debe usar un C ya compilado con estas opciones (P36/P98).
if grep -q '^_rex_gfx' work/cc/msprite.code.s; then CC_SPR=1; else CC_SPR=0; fi
[ "$CC_SPR" = "$SPR_MODE" ] || { echo "ERROR: C y asm tienen distinto SPR_OAM; recompilar sin NOCC"; exit 1; }
[ -f work/cc/spr.lv ] || cp ../smw-src-master/project/mw_e10/levels/data/world_1/1/spr.lv work/cc/spr.lv
[ -f work/yi1_s.dat ] || $PY tools/mkscroll.py
[ "$YDAT" = work/yi1_s.dat ] || [ -f "$YDAT" ] || $PY tools/mkscroll.py --g5
[ -f work/cc/gfx32f.bin ] && [ -f work/cc/mario_pal.bin ] || $PY tools/mkmario.py
REPLAY_KEY=$($PY - "$ORACLE" work/logicbench.bin <<'PY'
import hashlib
import pathlib
import sys
print(" ".join(hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest() for p in sys.argv[1:]))
PY
)
if [ ! -f "$REPLAY" ] || [ ! -f "$REPLAY.oracle" ] || [ "$(cat "$REPLAY.oracle")" != "$REPLAY_KEY" ]; then
    mkdir -p "$(dirname "$REPLAY")"
    $PY tools/m68kverify.py --mode loop --sprites --oracle "$ORACLE" --replay "$REPLAY"
    printf '%s\n' "$REPLAY_KEY" > "$REPLAY.oracle"
fi
HARNESS=player/game.s
if [ "$REPLAY" != work/yi1_replay.bin ]; then
    # Fuente temporal, como logicbench PROF: no modificar el replay normal
    # ni player/game.s. Los otros includes conservan sus rutas originales.
    HARNESS="$OUT/game.replay.s"
    $PY - "$REPLAY" "$HARNESS" <<'PY'
import pathlib
import sys
replay = str(pathlib.Path(sys.argv[1]).resolve())
if any(c in replay for c in ('"', '\n', '\r')):
    raise SystemExit("ERROR: ruta del replay no representable en incbin")
source = pathlib.Path("player/game.s").read_text()
old = 'incbin  "work/yi1_replay.bin"'
if source.count(old) != 1:
    raise SystemExit("ERROR: cambió el incbin del replay en player/game.s")
pathlib.Path(sys.argv[2]).write_text(source.replace(old, 'incbin  "' + replay + '"'))
PY
fi
"$VBCC/bin/vasmm68k_mot$X" -quiet -Fbin -m68000 $GDEFS -I player -I . -L "$OUT/game.lst" \
    -o "$OUT/game.bin" "$HARNESS"
$PY tools/piccheck.py --lst "$OUT/game.lst"
$PY tools/mkadf.py --boot work/boot.bin --stage2 "$OUT/game.bin" --data "$YDAT" \
    --out "$OUT/game.adf"
if [ -n "$SPR_BANK" ]; then
    $PY tools/sprgfx_load.py --bank "$SPR_BANK" --adf "$OUT/game.adf"
fi
