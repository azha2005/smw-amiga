# pipe.orc - la tuberia del frame 11425 de oracle_yi1 (x $0780-$079F, boca en
# y $0160, al fondo de la caja de cemento de $0770/$07A0 y con dos bloques
# giratorios encima) y su subnivel de 2 pantallas (R9, Etapa 8.1).
# -> work/oracle_pipe.txt
#
# Mario llega chico por boot_ruta.orc (los mismos saltos hasta x = $0750).  Alli
# se le hace grande con 'poke $0019 01' (como pw_flor.orc; oracle_yi1 tambien lo
# tiene grande aqui): un salto con giro (A) sobre un bloque giratorio lo rompe
# (chico no).  Con el bloque de la derecha roto, Mario cae a la boca de la
# tuberia (y = $0140) y baja con DOWN en x = $078D (oracle_yi1: $0787).  El
# subnivel (modo $0F -> $13 -> $14, x = $0018, camara 0; P68: _NoButtons borra
# $15-$18 durante la animacion $71 = 06) tiene 2 pantallas: corre a la derecha,
# salta para coger las 3 monedas de y $0150 (x $0070-$009F) y las 3 de y $0130
# (x $00D0-$00FF), pasa el escalon de $0135, cruza el puente de bloques
# giratorios de $0150-$017F y entra en la tuberia horizontal del extremo
# derecho (x $01B0-$01CF, $71 = 05) que lo dispara en diagonal (anim 07, modo
# $12/$13) de vuelta al nivel en x = $0818: la vuelta, con la camara en $078C.
# Los tiempos los encontro una busqueda.
include boot_ruta_0680.orc
until w$0094>=06C0 max 600 RIGHT+Y
assert $0071==00
until w$0094>=06CA max 600 RIGHT+Y
4 RIGHT+Y+B
until w$0094>=0740 max 600 RIGHT+Y
assert $0071==00
until w$0094>=0750 max 600 RIGHT+Y
10 RIGHT+Y+B
poke $0019 01
until w$0094>=0783 max 600 RIGHT
assert $0100==14
assert $0019==01
20 -
30 A                             # salto con giro sobre los bloques giratorios
until $0072==00 max 100 -
until w$0094<=078D max 30 LEFT
until $007B==00 max 60 -
60 DOWN                          # baja por la tuberia (modo $0F: cambio de subnivel)
until $0100==13 max 100 -
until $0100==14 max 400 -
until $0071==00 max 400 -
20 -
# --- subnivel: 2 pantallas ---
until w$0094>=0048 max 100 RIGHT+Y
12 RIGHT+Y+B                     # monedas de y $0150
until $0072==00 max 100 RIGHT+Y
assert $0DBF>=01
until w$0094>=00B0 max 100 RIGHT+Y
12 RIGHT+Y+B                     # monedas de y $0130
until $0072==00 max 100 RIGHT+Y
assert $0DBF>=03
until w$0094>=0128 max 300 RIGHT+Y
until $0072==00 max 50 RIGHT
40 RIGHT+B                       # el escalon del puente
until $0072==00 max 100 RIGHT
until w$0094>=0190 max 100 RIGHT+Y
until $0072==00 max 100 RIGHT
until w$0094>=01B2 max 200 RIGHT
assert $0100==14
# la tuberia horizontal: anim $71 = 05, luego modo $0F/$11/$12/$13 y la salida
until $0100!=14 max 200 RIGHT
until $0100==14 max 400 -
assert w$0094>=0800
until $0071==00 max 400 -
60 -
