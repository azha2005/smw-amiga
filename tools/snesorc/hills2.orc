# hills2.orc - la colina grande de x = $AE0 de Yoshi's Island 1 (cierra la 8c,
# Etapa 8.1).  -> work/oracle_hills2.txt
#
# La colina (screens 10-11): terraza baja de x = $AD6 a $B00 (y = $100), meseta
# de $B00 a $B60 (y = $E0) y una pendiente de 45 grados que baja hacia la
# DERECHA de $B60 (y $100) a $BD0 (y $140); cinco Rex por la zona ($AC0, $B60,
# $B80, $BA0 y el de la pendiente, $BD0) y el Banzai Bill $9F que cruza.
# Para subir hay que entrar por la derecha: desde el suelo interior (a la
# izquierda del pozo de $C10) se salta hacia la izquierda sobre la pendiente.
#
# Recorrido: (1) camino de normal.orc hasta $A40 y por encima de los Rex del
# suelo hasta el pie de la colina; (2) subir corriendo hacia la izquierda;
# parado (resbala), andando, agachado (se desliza); pisa al Banzai Bill;
# (3) meseta corriendo hasta la terraza, salto desde la terraza; (4) bajar
# corriendo, andando, con salto normal y con giro, agachado; (5) subir otra vez
# (salto en la pendiente) y salir por la izquierda.  Los saltos que esquivan a
# los Rex (que se pisan) los encontro una busqueda: los 'assert' hacen fallar
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
until w$0094>=0BE8 max 60 RIGHT+Y
30 LEFT
24 LEFT+B
until w$0094<=0BA8 max 100 LEFT+Y
until w$0094<=0BA8 max 100 LEFT+Y
30 -
until w$0094<=0BA0 max 100 LEFT
30 DOWN
until w$0094<=0B98 max 500 LEFT+Y
assert $0071==00
assert $0100==14
assert $0019==00
assert w$0096<=0140
until w$0094<=0B88 max 500 LEFT+Y
assert $0071==00
assert $0100==14
assert $0019==00
assert w$0096<=0140
until w$0094<=0B78 max 500 LEFT+Y
assert $0071==00
assert $0100==14
assert $0019==00
assert w$0096<=0140
until w$0094<=0B68 max 500 LEFT+Y
assert $0071==00
assert $0100==14
assert $0019==00
assert w$0096<=0140
until w$0094<=0B58 max 500 LEFT+Y
assert $0071==00
assert $0100==14
assert $0019==00
assert w$0096<=0140
until w$0094<=0B50 max 500 LEFT+Y
assert $0071==00
assert $0100==14
assert $0019==00
assert w$0096<=0140
10 -
until w$0094<=0B38 max 100 LEFT
until w$0094<=0B18 max 100 LEFT+Y
until w$0094<=0AF8 max 100 LEFT+Y
until $0072==00 max 60 LEFT
10 LEFT
20 RIGHT+Y
16 RIGHT+Y+B
until $0072==00 max 60 RIGHT+Y
until w$0094>=0B90 max 100 RIGHT+Y
until w$0094>=0BF0 max 100 RIGHT+Y
30 LEFT
24 LEFT+B
until w$0094<=0BA0 max 200 LEFT
until w$0094<=0B90 max 200 LEFT
12 LEFT+B
until $0072==00 max 100 LEFT
until w$0094<=0B70 max 200 LEFT
until $0072==00 max 100 LEFT
10 -
until w$0094>=0B78 max 200 RIGHT
12 RIGHT+A
until $0072==00 max 100 RIGHT
20 -
until w$0094>=0BC0 max 200 RIGHT
until w$0094<=0B90 max 200 LEFT+Y
until w$0094<=0B46 max 200 LEFT+Y
until w$0094>=0B68 max 200 RIGHT+Y
30 DOWN
until w$0094>=0BE0 max 200 RIGHT
until w$0094>=0BF0 max 60 RIGHT
30 LEFT
24 LEFT+B
until w$0094<=0B90 max 200 LEFT+Y
until w$0094<=0B80 max 500 LEFT+Y
assert $0071==00
assert $0100==14
assert $0019==00
assert w$0096<=0140
until w$0094<=0B70 max 500 LEFT+Y
assert $0071==00
assert $0100==14
assert $0019==00
assert w$0096<=0140
until w$0094<=0B60 max 500 LEFT+Y
assert $0071==00
assert $0100==14
assert $0019==00
assert w$0096<=0140
until w$0094<=0B60 max 500 LEFT+Y
4 LEFT+Y+B
until w$0094<=0B20 max 500 LEFT+Y
assert $0071==00
assert $0100==14
assert $0019==00
assert w$0096<=0140
until w$0094<=0B10 max 500 LEFT+Y
assert $0071==00
assert $0100==14
assert $0019==00
assert w$0096<=0140
until w$0094<=0B00 max 500 LEFT+Y
assert $0071==00
assert $0100==14
assert $0019==00
assert w$0096<=0140
until w$0094<=0AF0 max 500 LEFT+Y
assert $0071==00
assert $0100==14
assert $0019==00
assert w$0096<=0140
until w$0094<=0AE0 max 500 LEFT+Y
assert $0071==00
assert $0100==14
assert $0019==00
assert w$0096<=0140
until w$0094<=0AD0 max 500 LEFT+Y
assert $0071==00
assert $0100==14
assert $0019==00
assert w$0096<=0140
until w$0094<=0AC0 max 500 LEFT+Y
assert $0071==00
assert $0100==14
assert $0019==00
assert w$0096<=0140
until w$0094<=0AB0 max 500 LEFT+Y
assert $0071==00
assert $0100==14
assert $0019==00
assert w$0096<=0140
until $0072==00 max 100 LEFT
30 -
assert $0071==00
