# turn_block.orc - bloques giratorios de YI1 (R10, cobertura de blocks_update:
# TurnBlockSpr y varios bloques rebotando a la vez).  -> work/oracle_turn_block.txt
#
# YI1 SI tiene bloques giratorios (Map16 $11E): el puente de $780-$79F (entre
# dos pilares de cemento, cerrado por abajo: no se puede golpear desde abajo) y
# tres sueltos al final: gx 239 / fila 20 (x $EF0), gx 243 / fila 21 ($F30, debajo
# del '?' de la flor) y gx 247 / fila 20 ($F70).  Es boot_ruta.orc hasta x = $0EB0
# (sin su saltito) y despues cuatro golpes desde abajo con la cabeza: $EF0, el
# '?' de la flor / $F30, y $F70 (los x y las duraciones de salto, de una busqueda
# que detecta el rebote de la cabeza, SpeedY de negativo a ~0 en el aire).
include boot_yi1.orc
rec on
8 -
until w$0094>=0058 max 200 RIGHT+Y
20 RIGHT+Y+B                     # sobre el Koopa que baja deslizandose
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
# --- el resto: correr y saltar (x de los saltos: busqueda) ---
until w$0094>=0140 max 600 RIGHT+Y
assert $0071==00
until w$0094>=0148 max 600 RIGHT+Y
32 RIGHT+Y+B
until w$0094>=0200 max 600 RIGHT+Y
assert $0071==00
until w$0094>=0280 max 600 RIGHT+Y
assert $0071==00
until w$0094>=0288 max 600 RIGHT+Y
4 RIGHT+Y+B
until w$0094>=0300 max 600 RIGHT+Y
assert $0071==00
until w$0094>=030A max 600 RIGHT+Y
10 RIGHT+Y+B
until w$0094>=0380 max 600 RIGHT+Y
assert $0071==00
until w$0094>=0400 max 600 RIGHT+Y
assert $0071==00
until w$0094>=0408 max 600 RIGHT+Y
10 RIGHT+Y+B
until w$0094>=0480 max 600 RIGHT+Y
assert $0071==00
until w$0094>=04B0 max 600 RIGHT+Y
4 RIGHT+Y+B
until w$0094>=0500 max 600 RIGHT+Y
assert $0071==00
until w$0094>=0580 max 600 RIGHT+Y
assert $0071==00
until w$0094>=0600 max 600 RIGHT+Y
assert $0071==00
until w$0094>=0680 max 600 RIGHT+Y
assert $0071==00
until w$0094>=06C0 max 600 RIGHT+Y
assert $0071==00
until w$0094>=06CA max 600 RIGHT+Y
4 RIGHT+Y+B
until w$0094>=0740 max 600 RIGHT+Y
assert $0071==00
until w$0094>=0750 max 600 RIGHT+Y
10 RIGHT+Y+B
until w$0094>=07A0 max 600 RIGHT+Y
assert $0071==00
until w$0094>=07D0 max 500 RIGHT+Y
assert $0071==00
assert $0100==14
assert $0019==00
until w$0094>=0800 max 500 RIGHT+Y
assert $0071==00
assert $0100==14
assert $0019==00
until w$0094>=0830 max 500 RIGHT+Y
assert $0071==00
assert $0100==14
assert $0019==00
until w$0094>=0860 max 500 RIGHT+Y
assert $0071==00
assert $0100==14
assert $0019==00
until w$0094>=0860 max 500 RIGHT+Y
6 RIGHT+Y+B
until w$0094>=0890 max 500 RIGHT+Y
assert $0071==00
assert $0100==14
assert $0019==00
until w$0094>=089A max 500 RIGHT+Y
10 RIGHT+Y+B
until w$0094>=08C0 max 500 RIGHT+Y
assert $0071==00
assert $0100==14
assert $0019==00
until w$0094>=08F0 max 500 RIGHT+Y
assert $0071==00
assert $0100==14
assert $0019==00
until w$0094>=0920 max 500 RIGHT+Y
assert $0071==00
assert $0100==14
assert $0019==00
until w$0094>=0950 max 500 RIGHT+Y
assert $0071==00
assert $0100==14
assert $0019==00
until w$0094>=0980 max 500 RIGHT+Y
assert $0071==00
assert $0100==14
assert $0019==00
until w$0094>=09B0 max 500 RIGHT+Y
assert $0071==00
assert $0100==14
assert $0019==00
until w$0094>=09E0 max 500 RIGHT+Y
assert $0071==00
assert $0100==14
assert $0019==00
until w$0094>=0A10 max 500 RIGHT+Y
assert $0071==00
assert $0100==14
assert $0019==00
until w$0094>=0A40 max 500 RIGHT+Y
assert $0071==00
assert $0100==14
assert $0019==00
until w$0094>=0A60 max 500 RIGHT+Y
assert $0071==00
assert $0100==14
assert $0019==00
until w$0094>=0A80 max 500 RIGHT+Y
assert $0071==00
assert $0100==14
assert $0019==00
until w$0094>=0A80 max 500 RIGHT+Y
4 RIGHT+Y+B
until w$0094>=0AA0 max 500 RIGHT+Y
assert $0071==00
assert $0100==14
assert $0019==00
until w$0094>=0AC0 max 500 RIGHT+Y
assert $0071==00
assert $0100==14
assert $0019==00
until w$0094>=0AE0 max 500 RIGHT+Y
assert $0071==00
assert $0100==14
assert $0019==00
until w$0094>=0B00 max 500 RIGHT+Y
assert $0071==00
assert $0100==14
assert $0019==00
until w$0094>=0B20 max 500 RIGHT+Y
assert $0071==00
assert $0100==14
assert $0019==00
until w$0094>=0B20 max 500 RIGHT+Y
4 RIGHT+Y+B
until w$0094>=0B40 max 500 RIGHT+Y
assert $0071==00
assert $0100==14
assert $0019==00
until w$0094>=0B60 max 500 RIGHT+Y
assert $0071==00
assert $0100==14
assert $0019==00
until w$0094>=0B80 max 500 RIGHT+Y
assert $0071==00
assert $0100==14
assert $0019==00
until w$0094>=0BA0 max 500 RIGHT+Y
assert $0071==00
assert $0100==14
assert $0019==00
until w$0094>=0BC0 max 500 RIGHT+Y
assert $0071==00
assert $0100==14
assert $0019==00
until w$0094>=0BE0 max 500 RIGHT+Y
assert $0071==00
assert $0100==14
assert $0019==00
until w$0094>=0C00 max 500 RIGHT+Y
12 RIGHT+Y+B
until w$0094>=0C90 max 500 RIGHT+Y
assert $0071==00
assert $0100==14
assert $0019==00
until w$0094>=0CB2 max 500 RIGHT+Y
4 RIGHT+Y+B
until w$0094>=0CF0 max 500 RIGHT+Y
assert $0071==00
assert $0100==14
assert $0019==00
until w$0094>=0D20 max 500 RIGHT+Y
assert $0071==00
assert $0100==14
assert $0019==00
until w$0094>=0D20 max 500 RIGHT+Y
4 RIGHT+Y+B
until w$0094>=0D80 max 500 RIGHT+Y
assert $0071==00
assert $0100==14
assert $0019==00
until w$0094>=0DB0 max 500 RIGHT+Y
assert $0071==00
assert $0100==14
assert $0019==00
until w$0094>=0DE0 max 500 RIGHT+Y
assert $0071==00
assert $0100==14
assert $0019==00
until w$0094>=0DE0 max 100 RIGHT+Y
70 -
16 RIGHT+Y+B
until w$0094>=0E20 max 100 RIGHT+Y
assert $0071==00
until w$0094>=0E20 max 500 RIGHT+Y
4 RIGHT+Y+B
until w$0094>=0E80 max 500 RIGHT+Y
assert $0071==00
assert $0100==14
assert $0019==00
until w$0094>=0EE0 max 300 RIGHT+Y
16 RIGHT+Y+B                     # cabeza contra el bloque giratorio de $EF0
until $0072==00 max 100 RIGHT+Y
until w$0094>=0F18 max 100 RIGHT+Y
8 RIGHT+Y+B                      # contra el '?' de la flor / el giratorio de $F30
until $0072==00 max 100 RIGHT+Y
until w$0094>=0F58 max 100 RIGHT+Y
16 RIGHT+Y+B                     # contra el giratorio de $F70
until $0072==00 max 100 RIGHT+Y
20 RIGHT
assert $0071==00
