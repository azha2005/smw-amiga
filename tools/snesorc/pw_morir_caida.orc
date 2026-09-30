# pw_morir_caida.orc - Mario chico muere cayendo a un pozo (R5, D12,
# Etapa 8.1).  -> work/oracle_pw_morir_caida.txt
#
# Arranque: boot_ruta_0D20.orc (boot_ruta.orc hasta x = $0D20, donde el
# camino salta el pozo de $0D30-$0D6F sobre las plataformas de bloques '!').
# Aqui Mario sigue corriendo sin saltar, cae por el hueco (y > $1B0) y
# $71 pasa a 09 con Mario ya fuera de pantalla (y $1C7 -> $44F).
include boot_ruta_0D20.orc
assert $0071==00
assert $0019==00
until $0071!=00 max 400 RIGHT+Y
assert $0071==09
assert $0100==14
200 -
assert $0071==09
print
