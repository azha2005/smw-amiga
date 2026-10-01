# stress_sprites.orc - muchos sprites a la vez (R6, Etapa 8.1): el Banzai Bill
# ($9F) con 3 Rex ($AB) y Mario en pantalla.  -> work/oracle_stress_sprites.txt
#
# El Banzai sale cuando la camara llega a $0B92 (x = $0C9A, y = $0140) y avanza
# a la izquierda 1.5 px/frame.  Pasando de largo solo coincide con 1-2 Rex (los
# demas ya se fueron a la izquierda), asi que Mario cruza hasta x = $0BF0, deja
# que salga el Banzai y vuelve atras 24 frames: la camara retrocede a $0B57, el
# Banzai sigue vivo (solo se descarga si queda a mas de ~$40 px fuera) y los
# Rex que habian salido por la izquierda se recargan.  Mario espera quieto en
# x = $0BDB (sobre el suelo, y = $0160) y salta cuando el Banzai llega a x = $0C10
# (a 24 frames de salto lo pasa o lo pisa: sin saltar, el Banzai lo mata).
# Los tiempos los encontro una busqueda.
include boot_vert.orc
until w$0094>=0BF0 max 100 RIGHT
until $007B<=04 max 60 LEFT
until $009E==9F max 100 -        # sale el Banzai (ranura 0)
24 LEFT
until $007B==00 max 60 -
until $14E0==0C max 200 -
until $00E4<=10 max 80 -
24 B
until $0072==00 max 100 -
40 -
assert $0071==00
assert $0100==14
