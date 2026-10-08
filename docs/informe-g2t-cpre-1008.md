# G2T-Cpre — C2a exacta, prototipo C2b detenido por coste

2026-10-08. Worktree `wt-g2t-b2bis-1008`, rama `g2t-b2bis`, después de
la optimización B2bis `d3e431c`. Sin merge ni push. Entrega parcial:
**no hay emisor completo ni Rex visible en WinUAE**.

## C2a: tabla sobre las listas reales

`tools/g2t_preplan.py` recorre O5 en Musashi, con los segmentos de las
listas reales y el `g2t_ref.py` original. Recorre 6313 fotos desde el
frame lógico 5145; 0 fotos sin frame lógico del oráculo, 2288 con Rex.
En esas 2288 comprueba cámara, píxeles
de los cuatro flujos DMA de Mario y sus 32 bytes de paleta contra la
fuente gráfica. Resultado:

| contador del modelo | resultado |
|---|---:|
| sin_variante_temporal | 0 |
| sin_plazo | 0 |
| errores_color | 0 |
| errores_capa1 | 0 |
| prioridad_distinta | 0 |
| sin_destino (política de elegir un Rex) | 383 |

El índice G5PR usa el stamp lógico `R_FRAME`; el frame B1 conserva el
de la fuente gráfica. No son siempre el mismo reloj: 48 SKIP, f7552 a
f7599, conservan los gráficos de f7551 y cámara 1111. SYNC f7600 sigue
con esa pose, pero cámara 1113. Son 49 fotos retenidas. El mapeo gráfico
es la última llamada RUN/RUNSYNC a `level_frame`, comprobado contra los
píxeles DMA y colores de la foto; no se cambia el replay para ocultarlo.
No se ha demostrado aquí que toda la OAM viva de Rex coincida con la
SNES tras una resincronización: los Rex de esta prueba offline vienen
de la traza del oráculo de su fuente gráfica.

Tabla completa: 451172 B, 2288 entradas, máximo 28 filas con sufijo.
No se incluye en la A500: el arnés G5_PRE_EXT la inyecta en $180000 con
RAM virtual adicional. Esto no demuestra que quepa en 512 KB slow.
Las ventanas de C4 deben seguir limitadas a 16 KB; C4 no se ejecutó.

G5PR se valida antes de incluirlo o inyectarlo: cabecera, índice ordenado,
offsets alineados, longitudes B1, filas, colores, firmas y relleno. Siete
tests sintéticos sin ROM, incluidos firmas impares, truncaciones e índices
ambiguos; entran en `regress.py`. Los flags parciales fallan antes de
construir y G5_EMPTY se rechaza porque aún no está implementado.

## C2b: consulta y firmas, sin emitir

`player/g5.s` exige **G5_PRE_PROBE**. Busca el stamp en el índice y suma
los prefijos completos hasta COP2LCH, excluyendo el salto, como prescribe
la tarjeta. Lee valores B1/firma impares por bytes. No copia sufijos,
no arma sprites ni implementa limpieza del historial. La llamada está
tras `dc_hdr`, antes de publicar; es una sonda, no el último escritor
de un emisor terminado.

`tools/g2t_emitprobe.py` recorrió las 6313 fotos: 2288 planes verificados,
0 cambios en las listas completas, 0 errores ABI, `g5_miss=0`. Alterar
una firma produce `d0=1`, `g5_miss=1`, sin modificar la lista; después
se restaura la tabla y el contador para continuar la medición normal.

| Musashi, sin DMA | tabla completa | tabla vacía |
|---|---:|---:|
| ciclos medios de la sonda | 5295,57 | 468 |
| máximo / frame lógico | 28680 / 8508 | 468 / todos |
| CPU total máxima del recorrido | 154444 | 140040 |
| fotos > PAL en este recorrido | 2 | 0 |

La foto f9693 requiere leer 754 palabras de prefijos en 22 filas. El
máximo de coste de la sonda es otra foto, f8508. No son tiempos WinUAE
ni C5 de un emisor completo. La tabla vacía tampoco sustituye G5_EMPTY.

**Parada literal:** C2b de `instrucciones-g2t-cpre.md` exige «Objetivo
≤ 2500 ciclos máx.; parar si pasa de 4000». La sonda sale con código 1
y `Cpre: PARADA por coste >4000, antes de C3/C4`. Se pidió al usuario
elegir entre conservar el límite/rediseñar o permitir más coste solo
para la prueba offline; no se asume autorización por el tiempo transcurrido.

## Red y límites de la entrega

Memmap del prototipo externo: chip 472112 B, slow 317888 B, 0 violaciones;
la tabla virtual externa está expresamente fuera de esta contabilidad.
Lint, regress baseline_pc --level, OAM68K, G5ENV (incluidos reinicios del
vivo sin G5_PRE) y cinco hashes por defecto se repiten antes del commit.
Resultados: `work/g2tc/{lint_final,regress_final,oam_final,g5env_final,
hashes_final}.log`. La línea G5ENV: OK es la prueba del conjunto; no
basta con que un wrapper termine con cero.

Reproducción de C2a/C2b: `work/cpre_safety.sh` construye el prototipo,
valida memoria, genera la tabla y mide tabla vacía/completa. La salida
roja de coste es esperada; revisar `emit_probe_summary.json` y el texto
literal. Derivados en `work/g2tc/`: `summary.json`, `plans.json`,
`g2t_pre.bin`, `emit_probe_summary.json`, `empty_probe/` y logs. R9 intacta.

Pendientes: gamecheck C2b del emisor terminado, C3/listcheck y sus
negativos de sufijo, G5_EMPTY, limpieza de ambas listas, sprites/VBL,
12 casos C4 con comparación de 57344 píxeles y C5/C6 completos.
D1 sigue roja, B35 fuera del vivo. Ninguna de estas puertas se marca hecha.
