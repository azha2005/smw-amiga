# goal_low.orc - la meta ($7B, x = $12E0) de Yoshi's Island 1 cortada con la cinta
# ABAJO (R_b, Etapa 8.1).  Variante de goal.orc.  -> work/oracle_goal_low.txt
# La cinta sube y baja entre y $0F8 y $170 con periodo ~240 frames; goal.orc la corta en
# el aire con la cinta a y $11F.  Aqui Mario salta el Chuck con un salto corto, aterriza
# en x $12C5 (el Chuck mata a Mario si se queda en x < $12B8), frena y espera a que la
# cinta baje ($14D7 = 00 -> 01, despues $00DB >= $50: slot 3) y la corta andando por el
# suelo con la cinta en y $153.
include boot_ruta.orc
until w$0094>=121A max 500 RIGHT
4 RIGHT+B
until w$0094>=1230 max 500 RIGHT
until w$0094>=1265 max 200 RIGHT+Y
10 RIGHT+Y+B                     # salto corto por encima del Chuck
until $0072==00 max 150 -
until $007B<=03 max 60 LEFT
assert $0071==00
until $14D7==00 max 400 -        # la cinta pasa por arriba (y < $100)
until $14D7==01 max 400 -        # y baja
until $00DB>=50 max 400 -        # hasta y >= $150
until $14CB!=08 max 120 RIGHT    # la corta andando por el suelo
assert $0071==00
rec all
until $0100==0E max 3000 RIGHT
60 -
