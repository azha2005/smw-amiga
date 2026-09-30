# shells.orc - el caparazon rojo ($DB, x = $D10) de Yoshi's Island 1 (R3,
# Etapa 8.1).  -> work/oracle_shells.txt
#
# El $DB se carga como caparazon quieto (estado 9) del sprite $05 (Koopa rojo),
# en el suelo de x = $D10, con un Rex ($AB) que viene andando hacia la
# izquierda.  Camino: el mismo que boot_ruta.orc hasta x = $C90.  Despues:
#   1. salta por encima del Rex y del caparazon y aterriza a su derecha;
#   2. lo patea hacia la izquierda (andando contra el, sin Y): el caparazon
#      (estado $A) mata al Rex y cae al pozo de $C10-$C5F;
#   3. baja al pozo y PISA el caparazon que rebota (queda quieto, estado 9);
#   4. lo AGARRA con Y (estado $B), lo lleva un poco y lo SUELTA (estado $A):
#      mata a otro Rex que cae al pozo; salta fuera del pozo.
# (No esta: pisar al Koopa $02; el guion banzai.orc ya lo hace.)  Los saltos
# del camino y las esperas los encontro una busqueda: los 'assert' hacen fallar
# el guion si algo cambia la partida.
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
# --- el resto: correr y saltar (x de los saltos: busqueda) ---
until w$0094>=0140 max 600 RIGHT+Y
assert $0071==00
until w$0094>=0148 max 600 RIGHT+Y
32 RIGHT+Y+B
until w$0094>=0200 max 600 RIGHT+Y
assert $0071==00
until w$0094>=0280 max 600 RIGHT+Y
assert $0071==00
until w$0094>=0288 max 600 RIGHT+Y
4 RIGHT+Y+B
until w$0094>=0300 max 600 RIGHT+Y
assert $0071==00
until w$0094>=030A max 600 RIGHT+Y
10 RIGHT+Y+B
until w$0094>=0380 max 600 RIGHT+Y
assert $0071==00
until w$0094>=0400 max 600 RIGHT+Y
assert $0071==00
until w$0094>=0408 max 600 RIGHT+Y
10 RIGHT+Y+B
until w$0094>=0480 max 600 RIGHT+Y
assert $0071==00
until w$0094>=04B0 max 600 RIGHT+Y
4 RIGHT+Y+B
until w$0094>=0500 max 600 RIGHT+Y
assert $0071==00
until w$0094>=0580 max 600 RIGHT+Y
assert $0071==00
until w$0094>=0600 max 600 RIGHT+Y
assert $0071==00
until w$0094>=0680 max 600 RIGHT+Y
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
until w$0094>=0800 max 500 RIGHT+Y
assert $0071==00
assert $0100==14
assert $0019==00
until w$0094>=0830 max 500 RIGHT+Y
assert $0071==00
assert $0100==14
assert $0019==00
until w$0094>=0860 max 500 RIGHT+Y
assert $0071==00
assert $0100==14
assert $0019==00
until w$0094>=0860 max 500 RIGHT+Y
6 RIGHT+Y+B
until w$0094>=0890 max 500 RIGHT+Y
assert $0071==00
assert $0100==14
assert $0019==00
until w$0094>=089A max 500 RIGHT+Y
10 RIGHT+Y+B
until w$0094>=08C0 max 500 RIGHT+Y
assert $0071==00
assert $0100==14
assert $0019==00
until w$0094>=08F0 max 500 RIGHT+Y
assert $0071==00
assert $0100==14
assert $0019==00
until w$0094>=0920 max 500 RIGHT+Y
assert $0071==00
assert $0100==14
assert $0019==00
until w$0094>=0950 max 500 RIGHT+Y
assert $0071==00
assert $0100==14
assert $0019==00
until w$0094>=0980 max 500 RIGHT+Y
assert $0071==00
assert $0100==14
assert $0019==00
until w$0094>=09B0 max 500 RIGHT+Y
assert $0071==00
assert $0100==14
assert $0019==00
until w$0094>=09E0 max 500 RIGHT+Y
assert $0071==00
assert $0100==14
assert $0019==00
until w$0094>=0A10 max 500 RIGHT+Y
assert $0071==00
assert $0100==14
assert $0019==00
until w$0094>=0A40 max 500 RIGHT+Y
assert $0071==00
assert $0100==14
assert $0019==00
until w$0094>=0A60 max 500 RIGHT+Y
assert $0071==00
assert $0100==14
assert $0019==00
until w$0094>=0A80 max 500 RIGHT+Y
assert $0071==00
assert $0100==14
assert $0019==00
until w$0094>=0A80 max 500 RIGHT+Y
4 RIGHT+Y+B
until w$0094>=0AA0 max 500 RIGHT+Y
assert $0071==00
assert $0100==14
assert $0019==00
until w$0094>=0AC0 max 500 RIGHT+Y
assert $0071==00
assert $0100==14
assert $0019==00
until w$0094>=0AE0 max 500 RIGHT+Y
assert $0071==00
assert $0100==14
assert $0019==00
until w$0094>=0B00 max 500 RIGHT+Y
assert $0071==00
assert $0100==14
assert $0019==00
until w$0094>=0B20 max 500 RIGHT+Y
assert $0071==00
assert $0100==14
assert $0019==00
until w$0094>=0B20 max 500 RIGHT+Y
4 RIGHT+Y+B
until w$0094>=0B40 max 500 RIGHT+Y
assert $0071==00
assert $0100==14
assert $0019==00
until w$0094>=0B60 max 500 RIGHT+Y
assert $0071==00
assert $0100==14
assert $0019==00
until w$0094>=0B80 max 500 RIGHT+Y
assert $0071==00
assert $0100==14
assert $0019==00
until w$0094>=0BA0 max 500 RIGHT+Y
assert $0071==00
assert $0100==14
assert $0019==00
until w$0094>=0BC0 max 500 RIGHT+Y
assert $0071==00
assert $0100==14
assert $0019==00
until w$0094>=0BE0 max 500 RIGHT+Y
assert $0071==00
assert $0100==14
assert $0019==00
until w$0094>=0C00 max 500 RIGHT+Y
12 RIGHT+Y+B
until w$0094>=0C90 max 500 RIGHT+Y
assert $0071==00
assert $0100==14
assert $0019==00
until w$0094>=0CB4 max 100 RIGHT+Y
24 RIGHT+Y+B                     # por encima del Rex y del caparazon
until $0072==00 max 80 RIGHT
8 LEFT
40 LEFT                          # patea el caparazon hacia la izquierda
until w$0094<=0C70 max 200 LEFT
12 LEFT                          # al pozo (1 bloque)
until $0072==00 max 40 -
24 -
8 B                              # pisa el caparazon que rebota
until $0072==00 max 60 -
10 -
until w$0094<=0C3E max 100 LEFT+Y   # lo agarra (Y)
3 LEFT+Y
4 -                              # lo suelta
1 RIGHT
28 RIGHT+B                       # y sale del pozo
until $0072==00 max 60 RIGHT
80 -
assert $0071==00
