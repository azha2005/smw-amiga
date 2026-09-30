# stress_piranha.orc - la Jumping Piranha Plant ($4F) con Mario corriendo (R6,
# Etapa 8.1).  -> work/oracle_stress_piranha.txt
#
# OJO: en el frame 9714 de oracle_yi1 hay UNA sola piranha en pantalla (ranura
# 4, x = $8B8); las de $710 y $8B8 estan a 416 px una de otra y la pantalla
# mide 256, asi que nunca se ven dos a la vez.  Este guion hace 4 idas y
# vueltas corriendo (Y) ante la tuberia de $710 (x = $688-$6C0) y 8 ante la de
# $8B8 (x = $7E0-$838; mas alla hay un pozo en $850), con las dos piranhas
# saliendo y entrando: ~800 frames con la piranha levantada (y < $130).
include boot_ruta_0680.orc
until w$0094>=06C0 max 200 RIGHT+Y
assert $0071==00
until w$0094<=0688 max 200 LEFT+Y
assert $0071==00
until w$0094>=06C0 max 200 RIGHT+Y
assert $0071==00
until w$0094<=0688 max 200 LEFT+Y
assert $0071==00
until w$0094>=06C0 max 200 RIGHT+Y
assert $0071==00
until w$0094<=0688 max 200 LEFT+Y
assert $0071==00
until w$0094>=06C0 max 200 RIGHT+Y
assert $0071==00
until w$0094<=0688 max 200 LEFT+Y
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
until w$0094>=0838 max 200 RIGHT+Y
assert $0071==00
until w$0094<=07E0 max 200 LEFT+Y
assert $0071==00
until w$0094>=0838 max 200 RIGHT+Y
assert $0071==00
until w$0094<=07E0 max 200 LEFT+Y
assert $0071==00
until w$0094>=0838 max 200 RIGHT+Y
assert $0071==00
until w$0094<=07E0 max 200 LEFT+Y
assert $0071==00
until w$0094>=0838 max 200 RIGHT+Y
assert $0071==00
until w$0094<=07E0 max 200 LEFT+Y
assert $0071==00
until w$0094>=0838 max 200 RIGHT+Y
assert $0071==00
until w$0094<=07E0 max 200 LEFT+Y
assert $0071==00
until w$0094>=0838 max 200 RIGHT+Y
assert $0071==00
until w$0094<=07E0 max 200 LEFT+Y
assert $0071==00
until w$0094>=0838 max 200 RIGHT+Y
assert $0071==00
until w$0094<=07E0 max 200 LEFT+Y
assert $0071==00
until w$0094>=0838 max 200 RIGHT+Y
assert $0071==00
until w$0094<=07E0 max 200 LEFT+Y
assert $0071==00
assert $0100==14
assert $0019==00
30 -
