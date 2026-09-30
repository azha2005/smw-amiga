# goal.orc - la meta ($7B, x = $12E0) de Yoshi's Island 1 (R4, Etapa 8.1):
# Mario pequeno salta por encima del Clappin' Chuck ($95) y corta la cinta
# en el aire (la cinta esta arriba, y = $11E); despues la secuencia de fin
# de nivel (Mario camina solo) hasta volver al mapa.  rec all: graba tambien
# la transicion.  -> work/oracle_goal.txt
include boot_ruta.orc
until w$0094>=121A max 500 RIGHT
4 RIGHT+B
until w$0094>=1230 max 500 RIGHT
until w$0094>=1265 max 200 RIGHT+Y
200 RIGHT+Y+B                    # salto largo por encima del Chuck
until w$0094>=12F0 max 300 RIGHT
assert $0071==00
rec all
until $0100==0E max 3000 RIGHT
60 -
