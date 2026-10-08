# G2T-B2bis rendimiento — segunda iteración local

2026-10-08. Rama `g2t-b2bis`, sin merge ni push. Control de partida:
`2785b74`; G5ENV se repitió antes de editar y dio OK. Esta entrega no
activa B35 ni cambia modelo, banco, scroll o los cinco builds por defecto.

## Cambios y perfil

La primera proyección de YI1, medida sobre las fotos B2, promediaba
29922 ciclos; reutilizar una entrada compactada promediaba 6595.
`g5env_verify.py cache` ahora guarda ambas medidas por clase de consulta,
incluidos alias y casos sin clave. El modo game guarda el perfil de las
6313 fotos, además de las 2288 con Rex: las primeras también afectan al
historial de la caché y no se pueden omitir del análisis.

Se conserva el formato 4 y la vista propia portable B2. El camino warm
evita borrar el índice que reemplaza por completo y, cuando todas las
filas son visibles, evita comprobar el recorte en cada fila. El camino
frío totalmente visible omite tests ya garantizados por su condición de
entrada y lee el byte alto original en vez de desplazarlo. El camino
conservador conserva el recorte antes de calcular los extremos.
La copia del payload se comparte; no se añade ninguna tabla.

La palabra n=1..4 de la clave marca ahora la validez de cada entrada;
cero significa vacía. Se conservan los 40 bytes completos y la prueba
de igualdad de DATA para los alias. Sus ocho bytes de punteros usados
se comparan con dos grupos alineados enmascarados y dos bytes. Una
entrada pasa de 1246 a 1244 B; N sigue siendo 8, cache total 12436 B.

| medida Musashi sin DMA | antes | después |
|---|---:|---:|
| primera proyección YI1, media | 29922 | 28606 |
| proyección hit YI1, media | 6595 | 5501 |
| proyección máxima, fotos B2 YI1 | 34476 | 33004 |
| lookup hit máximo | 558 | 554 |
| lookup miss máximo, tres trazas | 11904 | 11910 |
| captura máxima | 270 | 270 |
| render real máximo | 46940 | 45456 |
| CPU total máxima, juego completo | 140932 | 139482 |
| fotos por encima de PAL, sin DMA | 0 | 0 |
| margen slow vivo G3, con reservas | 264 B | 272 B |

El miss crece 6 ciclos en su peor caso; sigue bajo 12000. El caso sin
clave vacío crece por el bucle compacto de borrado. No se confunde la
mejora del camino warm con una mejora de todas las consultas.

## Opciones descartadas y canarios

N=4 con el hash anterior alcanzó 12060 ciclos en un miss. Otro hash
pasó las tres trazas aisladas, pero el juego completo dio 4 fotos por
encima de PAL y máximo 173482: se descartó. Buscar candidatos con las
fotos con Rex solamente no modela el historial real. Se mantiene N=8
y el hash original, sin fingir que la reducción de memoria de N=4 pasó.

El arnés todavía reservaba 1326 B por entrada, mientras el binario usaba
1246. El canario quedaba 640 B demasiado lejos con N=8. Ahora deriva la
reserva de G5ENV_ENTRY del listado y comprueba N. Una prueba nueva llena
los 1204 B de la última entrada con una pose densa y corrompe su canario:
la siguiente consulta debe detectarlo. Las pruebas de recorte, pack
denso, overflow, ABI, dos bases y foto retenida continúan intactas.

## Verificación y evidencia

G5ENV actual: 3404 frames, 762496 filas y 258 bordes exactos; 6313
renders con RAM/OAM/fichas vivas envenenadas; foto anterior y DATA
intactos mientras COPER usa el buffer 2. Cuatro memmap y reinicios
verdes. Reservas completas 169760 B, sin reducir fotos, salida o pila.

Los logs y JSON reproducibles están en `work/b2b/`: `gate_final.log`,
`cache/cache_summary.json`, `game/game_profile.json`,
`game/game_summary.json`, `memory_summary.json` y los logs de la red.
Lint, regress con baseline_pc --level, OAM68K entero, G5ENV y cinco
hashes por defecto: OK. `work/b2b_final.sh` repite la red y compara los
hashes con la partida; no se modificó la base. El plan B35 sigue exacto
y fuera del juego: máximo 2423094 ciclos.

WinUAE PAL OCS, 512+512 KB, KS1.2, CPU/blitter reales, por candado;
tres workers con sus propios shot.ps1, pausas desactivadas. BENCH: 190 s;
vista STOPF=1800: 95 s en control y candidato. Comparador intacto.

| build | lógica | publicadas | perdidas | racha | total CIA medio | máximo / frame | >PAL |
|---|---:|---:|---:|---:|---:|---|---:|
| control C1 a52e2ba, mismo C | 6312 | 6285 | 27 | 1 | 5414 | 18376 / 10997 | 24 |
| B2bis actual | 6312 | 6220 | 92 | 2 | 6735 | 27144 / 9363 | 61 |
| G5BENCHSCREEN | 6312 | 6220 | 92 | 2 | 6735 | 27145 / 9363 | 60 |

Captura: máximo 63 ticks CIA, frame 8215. Render B2bis: máximo 7285
ticks, frame 7256. Son medidas reales, distintas de los ciclos Musashi.
La iteración anterior daba 98 pérdidas, media 6876 y máximo 28655;
esta da 92 (1,46 %), sin cerrar D1 ni igualar al control (0,43 %).

Vista: 0/327680 píxeles distintos, oráculo 6945. Se inspeccionó
`work/b2b/view_control_ab.png`: Mario salta sobre el arbusto junto a la
tubería inclinada; terreno, fondo, tubería y Mario coinciden en ambos
paneles. Todas las instancias WinUAE propias terminaron.

D1 sigue siendo una puerta global independiente: el control anterior
perdía 27 fotos y tampoco cumplía su mínimo. No declarar 50 Hz por una
cota sin DMA ni por acercarse al control. Cpre es una prueba offline
del emisor, independiente de B35 y de la puerta global D1.
