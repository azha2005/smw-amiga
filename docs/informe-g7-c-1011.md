# G7-C — apoyo hardware exacto para el testigo de color

2026-10-11. Continuación de `f636329`, sin subagentes. **El testigo
k6047 está resuelto conservando D8.** Siete fotos, incluidas cuatro consecutivas, pasan
en WinUAE cycle-exact. La cobertura offline de las cinco trazas pasa;
el render G7-3 sigue pendiente. Esta entrega contiene herramientas y sondas, no efectos
activados en el juego.

## Destinos, DMA y colores

Se reprodujo la cota de k6047/fila161/x151..181: nueve colores,
siete registros PF1, 1.302 candidatos, ninguno factible bajo G2T-A.
No se amplió la rejilla ni se aproximó ningún color.

`g7_hw_support.py` decodifica los flujos chip efectivos de la foto,
incluidos POS/CTL, VSTART/VSTOP y cadenas. En esta tanda k6047 tiene
SPR0/1 de Mario en filas **130..161**, VSTOP exclusivo 162; SPR2/3
están detenidos. SPR4/5 contienen la piraña en filas 95..114;
SPR6/7 están detenidos. Esto se comprobó desde los controles, sin
inferir disponibilidad a partir de transparencia ni de la geometría
textual del informe anterior.

La ficha menor OAM 31, x169, filas158..165, pasa a SPR2/3 adosados.
Se arman en el bloque VBL con **PT apuntando a DATA y POS/CTL
explícitos**. No se reutiliza un canal ocupado durante el display.
Las fotos 6048/6049 de la sonda usan además SPR6/7 para OAM 30.
Se verifica BPLCON2 por píxel: la pareja elegida debe quedar delante
de PF1. Las cargas y cadenas de los enemigos permanecen intactas.

Los colores ya están en la paleta compartida de Mario:

| color OCS | índice de sprite |
|---|---:|
| FFF | 1 |
| 000 | 2 |
| 851 | 3 |
| DA3 | 4 |
| FD7 | 5 |

La selección comprueba el color vigente en cada píxel desde la
cabecera y todos los eventos del copper. Compartir un índice ocupado
es válido aquí porque el color requerido es el mismo. **El plan final
no agrega recargas de color.** Se conserva una alternativa acotada de
préstamo de índices libres y sufijo calibrado, con comprobación conjunta
de colores; no es un asignador general.

El primer experimento cargaba cinco colores en x263,271,279,287,295
de fila157: también dio 0 diferencias. La suite existente G2T-A `final0`
se repitió con seis planos, ocho canales sprite y cuatro canales de
audio DMA silencioso: **19 casos, puerta OK, 14.210 ticks PAL**. Incluye
cinco cargas tras c207/nb7 en el límite y el negativo con una más.
Evidencia: `work/g7c/cal.result.json`, `cal_compare.png`,
`work/g7c-cal-read.log`; imágenes inspeccionadas.

## Capturas del plan final

Cada control y candidato se compiló con BM1, REPLAY, G7_DOUBLE,
CUSHION, G5L y STOPF correspondiente. KS1.2, temporización exacta,
200 s de espera, copias independientes de shot.ps1 y candado compartido.
La comparación incluye toda la pantalla, con el control más los colores
OCS exactos de la OAM de la foto.

| foto | píxeles de efectos | DMA reservado para apoyo | diferencias ×2 |
|---|---:|---:|---:|
| 6046 | 212 | 80 B | **0** |
| 6047 | 212 | 80 B | **0** |
| 6048 | 212 | 160 B | **0** |
| 6049 | 212 | 160 B | **0** |
| 6064 | 106 | 80 B | **0** |
| 6065 | 106 | 80 B | **0** |
| 6066 | 120 | 160 B | **0** |

**1.180 píxeles de efectos, 0 diferencias dentro o fuera de ellos.**
Imágenes miradas: `work/g7c/<k>/probe/check.png`; resultados en
`check.json`. Las cuatro primeras son consecutivas con cambios de posición
y forma. Las otras tres verifican las recargas: cadena desde x239,
WAIT D0 al límite y cadena desde x231 → x243 (P110), compartida por
dos parejas. No equivalen a una prueba de la cola de bobs en movimiento.

El negativo deja PT y anula ambos POS/CTL: detecta **212 píxeles ×2
distintos, todos dentro del apoyo hardware; 0 fuera**. Un intento previo
anulaba solamente VSTOP y producía basura fuera del efecto: se corrigió
el arnés y se repitió, sin aflojar la comparación. Resultado final:
`work/g7c/6047/negative/check.json`.

## Referencia automática y límites

`g7_color_plan.py` ahora acepta índices distintos por X cuando la paleta
existente ya contiene el color exacto, sin cambiar ningún evento. También
usa la cota independiente en ventanas de 31 px antes del codo para
descartar casos demostrablemente imposibles antes de entrar en la DFS.
La cota sigue limitada a G2T-A; los rechazos por presupuesto de búsqueda
no se convierten en pruebas de imposibilidad.

`g7_hybrid_plan.py` conserva PF1 como primera opción y prueba apoyo
solo en parejas detenidas, con paleta existente exacta o un sufijo G2T-A.
Las recargas se validan juntas contra todos los flujos hardware originales
y todos los píxeles asignados. Dos parejas que necesitan el mismo sufijo
en la misma fila lo comparten; dos sufijos incompatibles se rechazan.
Barrida completa
**de las cuatro fotos 6046..6049**:

- 4 fotos, 848 píxeles; 1 foto solo PF1, 3 híbridas.
- 4 fichas hardware, 226 píxeles hardware; máximo 160 B DMA.
- 0 fotos sin resolver. `work/g7c/hybrid-four/report.json`.

El planificador automático puede elegir menos apoyo que la sonda manual
(por ejemplo, una pareja distinta para resolver el caso 6049). Esta
barrida es offline, con cadencia ideal y sin renderer del juego.
El tramo 6015..6060 también se completó: **46 fotos, 8.929 píxeles,
40 fotos solo PF1 y seis híbridas, ocho fichas/414 píxeles hardware,
0 fotos sin resolver**, máximo 160 B DMA. Evidencia:
`work/g7c/hybrid-local/report.json`, `complete=true`.
Los primeros intentos de barrida larga se detuvieron para acotar los
casos y mejorar el buscador; los informes con `complete=false` no son
puertas cumplidas. Una sonda offline adicional k6015 pasó (85 píxeles
en el binario actual); no se mezcla con la captura histórica de G7-2.

**Las cinco trazas completas pasan**, con `complete=true` y cero fotos
sin resolver: 15.369 frames recorridos, 3.754 fotos con efectos visibles,
250.347 píxeles. Todos los destinos se reconstruyen desde la foto,
fuentes exactas, controles DMA y paleta del copper, sin tablas por frame.

| traza | último k | fotos con efectos visibles | píxeles | solo PF1 | híbridas |
|---|---:|---:|---:|---:|---:|
| yi1 | 6312 | 1.298 | 91.214 | 1.277 | 21 |
| pw_bloques | 2075 | 510 | 39.735 | 510 | 0 |
| chuck_kill | 2954 | 669 | 53.932 | 669 | 0 |
| spin_kill | 1006 | 358 | 28.598 | 358 | 0 |
| stress_piranha | 3017 | 919 | 36.868 | 919 | 0 |

El apoyo corresponde a 33 fichas/1.720 píxeles y nunca supera 160 B DMA
por foto. En 17 fotos usa paleta existente; las otras cuatro son
k6064/k6065/k6066/k6259 (cinco o cuatro recargas). No hay rearmado de
canales ocupados. Los rechazos PF1 del buscador no prueban que esas 21
fotos sean universalmente imposibles por PF1.

Informes finales: `work/g7c/hybrid-<traza>-final/report.json`; logs
`work/g7c-hybrid-<traza>-final.log`. Yi1 usa
`work/rg_g7_double_replay/`; las otras usan `work/sws/t_<traza>/`,
generados por la puerta RAM/OAM/PHOTO. Es cobertura offline a cadencia
ideal; no demuestra propiedad de una cola en movimiento ni coste real.

La primera barrida limitada a paleta existente encontró k6064..6066 y
k6259. No se interpretaron como falta de colores: se habilitó el sufijo
ya calibrado, sin mover cargas de terreno ni controles DMA ajenos.
k6064/k6065 pasan con una pareja y cinco recargas; k6066 usa dos
parejas y **un** sufijo compartido. Las tres sondas físicas pasan con
0 diferencias. El caso k6259 usa cuatro recargas WAIT D0, dentro del
contrato de cinco ya medido; su destino está verificado offline.
La referencia admite una foto resuelta completamente por hardware;
el generador omite el bucle CPU cuando no quedan píxeles PF1.

La extracción de transiciones usa operaciones sobre arrays en vez de
recorrer cada píxel en Python. Se cruzaron 2.000 casos contra el bucle
anterior, con destinos, colores y deadlines idénticos
(`work/g7c-transitions-check.log`). Esto agiliza la herramienta;
no es una medida del coste de G7-3 en la Amiga.

## Memoria y puertas

Los flujos se copian a la reserva existente, después de los 7.616 B de
fuentes: no se agrega arena chip. Para el producto habrá que darles
propiedad por lista; esta sonda congelada comparte almacenamiento.

| sonda | chip | slow |
|---|---:|---:|
| 6046 | 510.920 B | 514.824 B |
| 6047 | 510.920 B | 515.296 B |
| 6048 | 510.920 B | 514.312 B |
| 6049 | 510.920 B | 514.384 B |
| 6064 | 510.920 B | 514.072 B |
| 6065 | 510.920 B | 513.936 B |
| 6066 | 510.920 B | 512.752 B |

`memmap.py`: 0 violaciones en las siete. Logs `work/g7c-extend.log`
y `work/g7c-extra-build*.log` (las pruebas fallidas por elección inicial
de ficha quedan en el log, antes de los builds corregidos).
El vivo por defecto conserva SHA256
`33f2250a1b4231069ab975bfdc4f7d2336cd814a0e4e95d13bd862659c5b638b`.

Lint y regresión completa `--level --g5l --bm1`: verdes. La regresión
incluye ocho tests de color, catorce de apoyo DMA y generación offline
de los testigos hardware 6047 y 6066. SWS RAM/OAM/PHOTO: OK en las cinco trazas
con G7_DOUBLE; `g7_photo_verify.py`: OK en las cinco, incluidas diez
capturas CPU por traza con FRONT/PEND/REND ocupadas. OAM68K: OK.
Logs: `work/g7c-current-regress.log`, `work/g7c-final-sws-g7.log`,
`work/g7c-final-photos.log`, `work/g7c-final-oam.log`.

No hay BENCH nuevo del renderer: el arnés precalcula y escribe PF1 por
CPU, y su coste no representa G7-3. **D1 sigue roja.** Falta llevar
los destinos exactos al renderer, cargar las fuentes, restaurar regiones sucias,
implementar la cola y medir SW1/BENCH antes de activar los efectos.
El orden vigente está en `PROXIMO.md`.
