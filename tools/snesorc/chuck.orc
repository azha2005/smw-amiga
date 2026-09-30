# chuck.orc - el Clappin' Chuck ($95, x = $12A0) de Yoshi's Island 1 (R2,
# Etapa 8.1).  -> work/oracle_chuck.txt
#
# El camino hasta x = $1200 es boot_ruta.orc.  Despues: sube a la meseta de
# bloques ($11E0-$1230), salta el bloque suelto de $1230, llega hasta el Chuck
# y lo deja saltar y aplaudir (esta a $12A0, y = $143 arriba, $170 en el
# suelo), lo pisa varias veces (saltando en su sitio, sobre el y desde la
# izquierda) y, al final, se queda quieto: el Chuck lo alcanza y le hace dano
# (Mario pequeno: muere).  Las esperas y los saltos los encontro una busqueda
# (tools de la sesion): el 'orc_has.py --sprite 95' cuenta los pisotones.
include boot_ruta.orc
until w$0094>=121A max 500 RIGHT
4 RIGHT+B
until w$0094>=1230 max 500 RIGHT
assert $0071==00
assert $0100==14
assert $0019==00
until w$0094>=1240 max 500 RIGHT
assert $0071==00
assert $0100==14
assert $0019==00
until w$0094>=1250 max 500 RIGHT
assert $0071==00
assert $0100==14
assert $0019==00
until w$0094>=1260 max 500 RIGHT
assert $0071==00
assert $0100==14
assert $0019==00
until w$0094>=1270 max 200 RIGHT
until w$0094>=1274 max 80 RIGHT
14 B
until $0072==00 max 80 -
until w$0094<=1243 max 80 LEFT
65 -
24 RIGHT+B
until $0072==00 max 80 -
until w$0094<=1243 max 80 LEFT
24 RIGHT+B
until $0072==00 max 80 -

# --- el Chuck le hace dano a Mario (pequeno: muere) ---
until $0071!=00 max 400 -
150 -
