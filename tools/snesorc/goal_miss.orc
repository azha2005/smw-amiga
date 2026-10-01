# goal_miss.orc - pasar la meta ($7B, x = $12E0) de Yoshi's Island 1 SIN cortar la cinta
# (R_b, Etapa 8.1).  Variante de goal.orc.  -> work/oracle_goal_miss.txt
# Igual que goal_low.orc hasta frenar en x ~$12C5 despues del Chuck; luego espera a que la
# cinta pase por arriba (y < $100, $14D7 = 00) y 130 frames mas (la cinta llega abajo, y ~ $16C)
# y anda por el suelo: con la cinta tan abajo no la toca (barrido: a y <= $154 la corta).
# El nivel sigue ($100 = 14, la cinta en estado 8) con Mario en x >= $1310 (el borde derecho del nivel esta en $1315).
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
130 -                            # y baja al fondo (y ~ $16C)
until w$0094>=12D0 max 100 RIGHT
until w$0094>=12F0 max 200 RIGHT
assert $14CB==08                 # ya paso la cinta y esta viva (estado 8): no se corto
until w$0094>=1310 max 200 RIGHT # pasa por debajo de la cinta (a y $15C-$170 no la toca)
assert $0071==00
assert $0100==14
rec all
60 RIGHT
print
