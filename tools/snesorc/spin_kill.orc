# spin_kill.orc - salto con giro (A) sobre enemigos (R10, cobertura de
# spr_spin_kill / _01A924).  -> work/oracle_spin_kill.txt
#
# Es el camino de boot_ruta.orc hasta el Rex de x ~ $0500 con tres saltos distintos:
#   1. el primer salto (el del Koopa $BD que baja deslizandose) es un salto
#      con giro (A) desde x = $3C: el Koopa $BD se deshace en humo (estado 4);
#   2. los saltos sobre dos Rex (frames 2164 y 2347 del oraculo; B en
#      boot_ruta) son con giro (A): los Rex se deshacen en humo (estado 4) en
#      vez de aplastarse.
#   3. al final, parado, mira arriba (UP, mario_CEB1 pose 3).
# El resto es boot_ruta tal cual.  Los saltos de A se encontraron con una
# busqueda (cambiar un B por un A y ver si el sprite pasa a estado 4 con
# Mario vivo); los 'assert' hacen fallar el guion si algo cambia la partida.
include boot_yi1.orc
rec on
8 -
until w$0094>=003C max 200 RIGHT+Y
14 RIGHT+A
until $0072==00 max 100 RIGHT
until w$0094>=00E4 max 200 RIGHT # cruza la colina 1 andando
until $0072==00 max 100 RIGHT
until w$0094>=0118 max 200 RIGHT
20 -                             # para
24 LEFT
16 RIGHT+Y                       # derrapa
20 -
24 DOWN                          # agachado
12 B                             # salto en el sitio
30 -
16 A                             # salto con giro
40 -
20 LEFT
12 LEFT+B                        # salto hacia la izquierda
30 LEFT
20 RIGHT+Y
until w$0094>=0140 max 600 RIGHT+Y
assert $0071==00
until w$0094>=0148 max 600 RIGHT+Y
32 RIGHT+Y+B
until w$0094>=0200 max 600 RIGHT+Y
assert $0071==00
until w$0094>=0280 max 600 RIGHT+Y
assert $0071==00
until w$0094>=0288 max 600 RIGHT+Y
4 RIGHT+Y+A
until w$0094>=0300 max 600 RIGHT+Y
assert $0071==00
until w$0094>=030A max 600 RIGHT+Y
10 RIGHT+Y+B
until w$0094>=0380 max 600 RIGHT+Y
assert $0071==00
until w$0094>=0400 max 600 RIGHT+Y
assert $0071==00
until w$0094>=0408 max 600 RIGHT+Y
10 RIGHT+Y+A
# --- ya sin enemigos cerca: parado, mira arriba (UP, mario_CEB1 pose 3) ---
until $0072==00 max 100 RIGHT
30 -
40 UP
20 -
assert $0071==00
