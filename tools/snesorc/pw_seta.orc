# pw_seta.orc - la seta ($74) del bloque volador ($83) de Yoshi's Island 1
# (R5, D12, Etapa 8.1).  -> work/oracle_pw_seta.txt
#
# Arranque: boot_ruta_0200.orc (boot_ruta.orc hasta x = $0200).  El bloque
# volador va de derecha a izquierda ($250 -> $1F8, y $12E-$140); Mario, chico,
# aterriza y salta con LEFT+B para frenar la deriva y le da desde abajo (f2091:
# el bloque queda quieto en ($21F,$133) y sale un sprite $74).  La seta sube
# despacio, cae al suelo y camina hacia la derecha; Mario espera y la coge
# corriendo: $71 = 02 (crecer, 48 frames) y $19 pasa de 00 a 01.  Despues
# sigue corriendo y salta el Rex, ya grande.
include boot_ruta_0200.orc
until $0072==00 max 100 RIGHT+Y
16 LEFT+B                        # golpea el bloque volador desde abajo
until $0072==00 max 100 -
assert $0019==00
120 -                            # la seta sale, sube y cae al suelo
until $0019!=00 max 200 RIGHT+Y  # la coge
assert $0019==01
until $0071==00 max 200 -        # animacion de crecer ($71 = 02)
assert $0019==01
until w$0094>=0270 max 100 RIGHT+Y
8 RIGHT+Y+B
40 RIGHT+Y
assert $0071==00
assert $0100==14
assert $0019==01
print
