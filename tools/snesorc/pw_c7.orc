# pw_c7.orc - el champinon invisible $C7 (x $0660, y $0170): Mario chico anda despacio, lo despierta a x ~$0653 (se vuelve $74), lo coge ($19 00 -> 01, f2706).
# -> work/oracle_pw_c7.txt
include boot_ruta_0200.orc
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
until w$0094>=0600 max 600 RIGHT
until w$0094>=0640 max 600 RIGHT
until w$0094>=0652 max 100 RIGHT
until $0019==01 max 200 RIGHT   # el 74 ($C7 despierto) sale a x $0653 y rebota hasta Mario
until $0071==00 max 100 -
assert $0019==01
30 -
print
