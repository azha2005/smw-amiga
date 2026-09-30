# boot_ruta_0200.orc - boot_ruta.orc cortado en el primer "until w$0094>=0200" (desde boot_yi1).
# Generado de boot_ruta.orc (no editar a mano): sirve de arranque a las grabaciones pw_*.orc.
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
until w$0094>=0140 max 600 RIGHT+Y
assert $0071==00
until w$0094>=0148 max 600 RIGHT+Y
32 RIGHT+Y+B
until w$0094>=0200 max 600 RIGHT+Y
