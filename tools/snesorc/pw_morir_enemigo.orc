# pw_morir_enemigo.orc - Mario chico muere al tocar un enemigo (R5, D12,
# Etapa 8.1).  -> work/oracle_pw_morir_enemigo.txt
#
# Arranque: boot_ruta_0CB2.orc (boot_ruta.orc hasta x = $0CB2, justo donde el
# camino salta y pisa el Rex de $0CDE).  Aqui Mario sigue corriendo sin
# saltar y el Rex lo toca: $71 pasa a 09 (animacion de muerte: sube, cae y
# sale del nivel) y el modo termina en $0B (tras la caida).  El oraculo
# graba solo el modo $14, asi que acaba en la animacion.
include boot_ruta_0CB2.orc
assert $0071==00
assert $0019==00
until $0071!=00 max 400 RIGHT+Y
assert $0071==09
assert $0100==14
200 -
assert $0071==09
print
