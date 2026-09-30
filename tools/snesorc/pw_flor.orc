# pw_flor.orc - bloque ? de la flor de Yoshi's Island 1 (x $0F30, y $110) con
# Mario grande, coger la flor de fuego ($75) y disparar (R5, D12, Etapa 8.1).
# -> work/oracle_pw_flor.txt
#
# Arranque: boot_ruta_0EB0.orc (boot_ruta.orc hasta x = $0EB0).  Mario llega
# chico: la seta esta en pw_seta.orc y el camino a pie hasta aqui es de Mario
# chico, asi que aqui se le hace grande con 'poke $0019 01' (sin la animacion
# de crecer).  Salta el Rex del suelo, sube al bloque giratorio de $0F30
# ($0F30,$150), le da al bloque ? desde abajo (f3636: sale $75, pw grande) y
# salta al bloque de $0F70 y de vuelta sobre el bloque ?: al pasar por encima
# toca la flor ($19: 01 -> 03).  Despues dispara con Y y X (en la OAM
# aparecen los tiles $2C/$2D de la bola).  Los tiempos los encontro una
# busqueda.
include boot_ruta_0EB0.orc
poke $0019 01
8 RIGHT+Y+B                      # sobre el Rex y encima del bloque giratorio $0EF0
until $0072==00 max 100 RIGHT+Y
until w$0094>=0F10 max 300 RIGHT
8 RIGHT+B
until $0072==00 max 100 RIGHT    # sobre el bloque giratorio de $0F30
until $007B<=04 max 30 LEFT
until $007B==00 max 100 -
assert $0019==01
16 B                             # cabezazo al bloque ?: sale la flor
until $0072==00 max 100 -
assert $0019==01
10 RIGHT+Y+B
until $0072==00 max 100 RIGHT+Y  # encima del bloque giratorio de $0F70
10 LEFT+Y
20 LEFT+Y+B                      # de vuelta, por encima del bloque ?: coge la flor
until $0072==00 max 100 LEFT
assert $0019==03
assert $0071==00
10 -
pulse 1 Y                        # bola de fuego
30 -
pulse 1 Y
30 -
pulse 1 X
30 -
assert $0019==03
assert $0071==00
assert $0100==14
print
