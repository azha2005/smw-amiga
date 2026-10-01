# boot_vert.orc - arranque de stress_sprites.orc: boot_ruta.orc hasta x = $0A60 y despues
# los dos saltos a plena carrera de stress_vert.orc sobre la colina de $0AE0-$0B60
# (el segundo desde x = $0B30), siguiendo hasta x = $0BC0 (assert incluido).  Deja 'rec on'.  No graba
# nada por si solo (make lo salta por el prefijo 'boot_').
include boot_ruta_0680.orc
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
22 RIGHT+Y+B                     # salto a plena carrera: $149F ~ 80, $13F1 != 0 (P84)
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
until w$0094>=0B30 max 500 RIGHT+Y
22 RIGHT+Y+B                     # otro salto a plena carrera sobre la colina
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
