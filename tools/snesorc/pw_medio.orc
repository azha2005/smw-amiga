# pw_medio.orc - el punto medio de Yoshi's Island 1 (R4, Etapa 8.1).
# -> work/oracle_pw_medio.txt
#
# Arranque: boot_ruta_0680.orc + el resto de boot_ruta.orc hasta x = $0950.
# Mario chico salta en x = $0958 y cruza la cinta del punto medio ($0970):
# $13CE pasa de 00 a 01 y, como es chico, el punto medio le da el champinon
# ($19 00 -> 01, f2944).  Sigue sin saltar: un Rex ($AB, x $0AA3) lo encoge
# (f3064, $71 = 01) y otro lo mata en x $0C52 ($71 = 09, f3568).  Despues del
# fundido vuelve al mapa ($100 = 0E, x $000D) y entra otra vez con B: reaparece
# en el punto medio, x = $0910, ($13CE se pone a 0 al cargar el nivel; el flag que sobrevive esta fuera del registro).
include boot_ruta_0680.orc
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
until w$0094>=0958 max 300 RIGHT+Y
4 RIGHT+Y+B                      # salta y toca la cinta del punto medio ($0970)
until $0072==00 max 100 RIGHT+Y
assert $0071==00
assert $13CE!=00
assert $0019==01                 # cruzar el punto medio da el champinon a Mario chico
until $0071==09 max 2500 RIGHT+Y   # sigue sin saltar: un Rex lo encoge y despues cae al pozo de $0C10
until $0100!=14 max 600 -        # animacion de muerte y fundido (el modo sale de $14)
until $0100==0E max 1500 -       # vuelve al mapa
60 -
until $0100==14 max 1500 B       # entra otra vez al nivel desde el mapa
assert $0071==00
assert w$0094>=0900              # reaparece en el punto medio (x = $0910), no en el principio
assert w$0094<=0960
60 RIGHT
print
