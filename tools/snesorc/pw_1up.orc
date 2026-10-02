# pw_1up.orc - el bloque giratorio de ($0D10,$00F0) de Yoshi's Island 1 (R_c, Etapa 8.1).
# -> work/oracle_pw_1up.txt
#
# Es el giratorio "estrella 2 / 1-UP": con Mario chico y en esta partida da un 1-UP (sprite $78), no la
# estrella.  Mario pisa al Rex $AB y salta (8 RIGHT+B) encima de la caja $B9 de ($0CF0,$0150); desde la
# caja salta con RIGHT+B 6 frames y B 18 (pico y $00EF) y le da con la cabeza al bloque (aire 36, f3284):
# sale el $78 de ($0D10,$00EE).  El $78 camina por encima de la fila de nubes ($0D30-$0E1F) y cae en x $0E20:
# Mario salta el pozo de $0D50, espera a que pase el Banzai $9F en la hondonada de $0DB0, sale por el
# escalon de $0DE0, sube a x $0E2C y salta justo cuando el $78 cae sobre el: lo coge (el $78 desaparece
# en f3636, ($0E35,$012E) con Mario en ($0E39,$0125)).  Los tiempos los encontro una busqueda.
include boot_ruta_0CB2.orc
until w$0094>=0CB2 max 100 RIGHT+Y
8 RIGHT+B
until $0072==00 max 120 RIGHT
6 RIGHT+B
18 B
until $0072==00 max 100 -
until w$0094>=0D30 max 200 RIGHT+Y
12 RIGHT+Y+B
until $0072==00 max 100 RIGHT+Y
60 -
until w$0094>=0DE0 max 200 RIGHT
12 RIGHT+B
until $0072==00 max 100 RIGHT
until w$0094>=0E2C max 100 RIGHT
94 -
24 B
40 -
print
