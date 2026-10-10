#!/bin/sh
# BM1: boot MFM, codigo fijo en C00000, arenas sin Exec. Desde 2026-10-09
# es el boot por defecto del vivo (tools/game_build.sh lo arma con -DBM_FIXED);
# este envoltorio sirve para el replay con BM (GDEFS por defecto -DREPLAY).
# XCDEFS agrega defines al C (p. ej. -DLSS_SNESORC para trazas de snesorc).
set -e
cd "$(dirname "$0")/.."
CDEFS="-DNOOAM -DSPR_OAM${XCDEFS:+ $XCDEFS}" GDEFS="${GDEFS--DREPLAY} -DG5L -DCUSHION -DBM_FIXED" SPR_BANK=work/g3/bank \
    OUT="${OUT:-work/bm1}" sh tools/game_build.sh
