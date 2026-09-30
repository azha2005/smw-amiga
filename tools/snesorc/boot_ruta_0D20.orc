# boot_ruta_0D20.orc - boot_ruta.orc cortado en el primer "until w$0094>=0D20" (incluye boot_ruta_0CB2).
# Generado de boot_ruta.orc (no editar a mano): sirve de arranque a las grabaciones pw_*.orc.
include boot_ruta_0CB2.orc
4 RIGHT+Y+B
until w$0094>=0CF0 max 500 RIGHT+Y
assert $0071==00
assert $0100==14
assert $0019==00
until w$0094>=0D20 max 500 RIGHT+Y
