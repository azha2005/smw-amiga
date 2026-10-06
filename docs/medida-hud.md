# H1 — Medida del HUD de Yoshi's Island 1

Herramienta reproducible: `python tools/hud_measure.py --selftest`. Lee
`work/yi1_d.dat` (PF1 planar), descomprime `gb-1/2` con el conversor existente
y lee las cámaras de todos los `work/oracle_*.txt`. `game.s` configura GFX
`$28..$2B` a VRAM `$4000`; GFX `$2C` no es `gb-5`. El PNG
`work/hud_medida.png` marca en rojo la banda candidata sobre el nivel a
`camY=192`; es evidencia geométrica, no una captura SNES.

## Fuente y huella gráfica

`game.s:1224` configura `BG3SC=$53`, cuyo tilemap empieza en `$5000`. La carga
inicial `GM04DoDMA` escribe en `$502E`, `$5042`, `$5063` y `$508E`, con tamaños
de 8, 56, 54 y 8 bytes: filas BG3 1, 2, 3 y 4, con 4, 28, 27 y 4 tiles.
Con scroll vertical cero ocupan coordenadas de tilemap **y=8..39**; son filas
de 8 píxeles, antes del desfase de raster SNES. `game.s:1457-1492` vuelve a
cargar las filas dinámicas `$5042/$5063` desde `STAT_BAR.L1/L2`. El NMI fuerza
`BG3HOFS/BG3VOFS` a cero; el IRQ se programa en `VTIMEL=$24` y cambia scroll y
modo de BG3. YI1 calcula `BG3VOFS=$D0`.

La banda de cambio PF1/PF2 se mide conservadoramente como pantalla **y=0..35**
(36 líneas), derivada del IRQ `$24`, el NMI y el código de scroll. El desfase
PPU y el corte efectivo dejan incierto si también entra la línea 36. La máscara
compuesta de las cuatro tablas DMA estáticas (`DATA_008C81`, `DATA_008C89`,
`DATA_008CC1`, `DATA_008CF7`), aplicando flips H/V, tiene **1342 píxeles
opacos de 10240** en un mapa de 32×5 tiles. Sus filas opacas son coordenadas
locales/tilemap **y=10..37**. Dentro de la banda conservadora, la parte de esa
huella estática queda en y=10..35 (26 líneas); la inclusión de y=36 solo
cambia el borde candidato, y en `camX=0` no cambia el solapamiento PF1 normal.

Los dígitos regulares `$00..$09` vienen de `gb-1`; se mide su unión de opacidad
por fila. Los bonus stars usan los 20 bytes de `DATA_008E06` (15 IDs únicos
`$B7..$C5` en `gb-2`); se mide la unión real de esos tiles, aparte de los
dígitos regulares. El borde de la caja de reserva usa `gb-1` tile `$3A`, con
`[0,0,1,3,4,5,5,6]` píxeles opacos por fila; `$3B` tiene
`[0,0,8,8,8,8,8,0]`. El decodificador cuenta índices de color no nulos y la
máscara PF1 sale de los bits de plano: no infiere transparencia desde el color
o el índice de paleta.

## Cruce medido con PF1

El blob D mide **5120×432**. A `camY=192`, la banda conservadora de pantalla
y=0..35 corresponde a nivel y=192..227. En la vista de 256 píxeles con
`camX=0`, PF1 tiene **0/9216** píxeles opacos. El barrido horizontal completo
`camX=0..4864` cada 4 px da mínimo **0/9216** en x=0 y máximo **6/9216
(0,065 %)** en x=2868. Si se incluye la línea candidata 36, el rango es
**0..16/9472**; el máximo está en x=2864. El terreno medido es la capa PF1
estática del blob, sin sprites.

`oracle_yi1` tiene 6229 frames, todos con `camY=192`, y máximo **0** píxeles
PF1 en sus vistas de 256 px. En las demás grabaciones, el script imprime el
conjunto exacto de `camY` y los mínimos/máximos de las ventanas de 256 px
realmente observadas. Las verticales varían de 129 a 192: `oracle_stress_vert`
y `oracle_stress_sprites` recorren 38 valores cada una; `oracle_spin_kill`
recorre 27 valores (132..192). La unión de cámaras observadas es
`129,132,135,136,138,140,141,144,145,147,148,149,150,152,153,154,156,158,159,160,162,164,165,166,167,168,170,171,172,173,174,175,176,177,178,179,180,181,182,183,184,185,186,187,188,189,190,191,192`.

El máximo observado entre las ventanas oracle es **6/9216 (0,065 %)**, en
`camY=192, camX=2619`. Aparece en `oracle_chuck`, `oracle_chuck_kill`,
`oracle_goal`, `oracle_goal_low`, `oracle_goal_miss`, `oracle_goalhit`,
`oracle_hills2`, los `oracle_pw_*` excepto `oracle_pw_c7` y `oracle_pw_seta`,
`oracle_shells`, `oracle_stress_back`, `oracle_stress_sprites`,
`oracle_stress_vert` y `oracle_turn_block`. El máximo es cero en
`oracle_banzai`, `oracle_diagpipe`, `oracle_hills`, `oracle_normal`,
`oracle_pipe`, `oracle_pw_c7`, `oracle_pw_seta`, `oracle_spin_kill`,
`oracle_stress_piranha` y `oracle_yi1`. Por ello, las cámaras verticales más
bajas no implican por sí solas terreno PF1 bajo el HUD.

La evidencia favorece componer la tinta del HUD sobre PF1 con una máscara del
blitter para preservar los píxeles de terreno; el copper mantiene el scroll de
PF2. H2/H3 aún deben estudiar la paleta de hasta 7 colores del HUD y los
cambios de contadores. Capturas O5 de la misma cámara permitirían medir el
terreno y los sprites en vivo.

## Límite de precisión

No hay captura local original de SNES con el HUD visible. El código, las
tablas, `memory.i`, `statusbar_tiles.txt`, `gb-1/2` y los oráculos permiten
derivar el mapa y las máscaras; los oráculos no registran `BG3VOFS`, el modo y
prioridad rasterizados ni el scanline efectivo del IRQ en cada frame. La banda
conservadora está medida y reproducible, pero la alineación final, incluido el
posible desfase de un píxel, requiere una captura PPU para cerrarse. El PNG
local del nivel no se presenta como referencia del HUD.
