# goalhit.orc - la meta ($7B) CON contacto con la barra (P5, Etapa 9.1).
# Misma ruta que goal.orc (salto largo por encima del Clappin' Chuck hacia la
# cinta de Yoshi's Island 1, x = $12E0), pero en el frame en que Mario entra
# en la zona de contacto (x >= $12D4) se le sube con 'poke' a y = $0112 ($D3
# es la Y de verdad, $96 su copia) para que la barra lo toque: GoalTape toma
# la rama de MarioSprInteractRt con carry (MiscTbl8 = 1, MiscTbl7, DecTbl1 =
# $80, bonus de estrellas) y TriggerGoalTape deja la cinta en estado 8 (su
# Tweaker1686 conserva el bit $20) mientras el resto pasa a 6.  La cinta sigue
# en estado 8 hasta que DecTbl1 llega a 0 y desaparece.  -> work/oracle_goalhit.txt
# (en goal.orc la barra no se toca y la cinta pasa de 8 a 6).
include boot_ruta.orc
until w$0094>=121A max 500 RIGHT
4 RIGHT+B
until w$0094>=1230 max 500 RIGHT
until w$0094>=1265 max 200 RIGHT+Y
until w$0094>=12D4 max 300 RIGHT+Y+B
poke $00D3 12 01
poke $0096 12 01
until w$0094>=12F0 max 300 RIGHT
rec all
until $0100==0E max 3000 RIGHT
60 -
