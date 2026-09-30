# boot_ruta.orc - camino "normal" de Mario pequeno por Yoshi's Island 1 desde
# el primer frame del nivel hasta x = $1200 (justo antes del Clappin' Chuck y
# de la meta), en la sesion de snesorc: corriendo, pisando los Rex del suelo y
# saltando los pozos (los saltos los encontro una busqueda: los 'assert'
# hacen fallar el guion si algo cambia la partida).  Los 'until' tienen la x
# del punto de control; cada tramo comprueba que Mario sigue vivo ($71 == 0),
# en el nivel ($100 == $14) y pequeno ($19 == 0).  Empieza con boot_yi1.orc y
# deja 'rec on'; lo incluyen chuck.orc, goal.orc, shells.orc...  No graba
# nada por si solo (make lo salta por el prefijo 'boot_').
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
until w$0094>=0EB0 max 500 RIGHT+Y
assert $0071==00
assert $0100==14
assert $0019==00
until w$0094>=0EB0 max 500 RIGHT+Y
8 RIGHT+Y+B
until w$0094>=0F10 max 500 RIGHT+Y
assert $0071==00
assert $0100==14
assert $0019==00
until w$0094>=0F40 max 500 RIGHT+Y
assert $0071==00
assert $0100==14
assert $0019==00
until w$0094>=0F70 max 500 RIGHT+Y
assert $0071==00
assert $0100==14
assert $0019==00
until w$0094>=0FA0 max 500 RIGHT+Y
assert $0071==00
assert $0100==14
assert $0019==00
until w$0094>=0FA0 max 500 RIGHT+Y
4 RIGHT+Y+B
until w$0094>=1000 max 500 RIGHT+Y
assert $0071==00
assert $0100==14
assert $0019==00
until w$0094>=100E max 500 RIGHT+Y
4 RIGHT+Y+B
until w$0094>=1060 max 500 RIGHT+Y
assert $0071==00
assert $0100==14
assert $0019==00
until w$0094>=1090 max 500 RIGHT+Y
assert $0071==00
assert $0100==14
assert $0019==00
until w$0094>=10C0 max 500 RIGHT+Y
assert $0071==00
assert $0100==14
assert $0019==00
until w$0094>=10F0 max 500 RIGHT+Y
assert $0071==00
assert $0100==14
assert $0019==00
until w$0094>=10F0 max 500 RIGHT+Y
4 RIGHT+Y+B
until w$0094>=1150 max 500 RIGHT+Y
assert $0071==00
assert $0100==14
assert $0019==00
until w$0094>=1180 max 500 RIGHT+Y
assert $0071==00
assert $0100==14
assert $0019==00
until w$0094>=118E max 500 RIGHT+Y
40 RIGHT+Y+B
until w$0094>=1200 max 500 RIGHT+Y
assert $0071==00
assert $0100==14
assert $0019==00
