# chuck_kill.orc - matar al Clappin' Chuck ($95, x = $12A0) con tres pisotones
# (R10, cobertura de chuck_die / _02C7B1).  -> work/oracle_chuck_kill.txt
#
# Es chuck.orc hasta el segundo pisoton (el 1.o y el 2.o ponen al Chuck en el
# estado 3, "golpeado"; solo cuentan los pisotones que le caen con el estado
# distinto de 3: SpriteMiscTbl4 llega a 3 en el tercero).  En chuck.orc el 3.o
# cae con el Chuck todavia en el estado 3 y no cuenta.  Aqui se espera a que
# el Chuck salga del estado 3 (slot 4, $00C6) y se salta encima: muere
# (estado 2) y se graba hasta que sale de pantalla.  La espera y el salto los
# encontro una busqueda; los 'assert' hacen fallar el guion si algo cambia.
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
until $00C6!=03 max 200 -        # el Chuck sale del estado "golpeado"
26 RIGHT+B                       # 3.er pisoton: muere (estado 2)
until $0072==00 max 80 -
assert $0071==00
120 -
assert $0071==00
