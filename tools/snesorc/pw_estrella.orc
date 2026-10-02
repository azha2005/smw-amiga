# pw_estrella.orc - Mario con la estrella ($1490 = $FF, puesta con poke) corre
# contra el Rex de $0CDE (P8, Etapa 9.1).  -> work/oracle_pw_estrella.txt
#
# Arranque: boot_ruta_0CB2.orc (el mismo punto que pw_morir_enemigo, donde un
# Mario chico muere al tocar el Rex).  Con la estrella el Rex muere (RexStarKill,
# estado 2) y Mario no se hace dano: $71 sigue en 00.  La estrella baja de a 1
# cada 4 frames: dura de sobra los 60 frames del guion.
include boot_ruta_0CB2.orc
assert $0071==00
assert $0019==00
poke $1490 FF
60 RIGHT+Y
assert $0071==00
assert $0100==14
print
