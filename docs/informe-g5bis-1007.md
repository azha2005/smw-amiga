# G5a-bis — fase A parcial, puerta de plazos roja

2026-10-07. Rama `wt/g5bis-1007`, base `53c488b`. **No cumplida:** se
implementó el modelo offline A1-A7 y se detuvo antes de B/C por la parada
obligatoria de `docs/instrucciones-g5a-bis.md` §3. No hay render Amiga nuevo.

## Comandos y evidencia

Entorno Git Bash: `PATH="$TEMP/pyshim:/c/msys64/ucrt64/bin:$PATH"`,
`VBCC=/c/Users/JC/vbcc`, `PY=python`. Python identificado como WindowsApps;
`import machine68k, unicorn` imprimió `ok`.

```sh
python tools/g5ref.py --trace work/oam_yi1.trace=work/oracle_yi1_oam.bin \
  --trace work/oam_normal.trace=work/oracle_normal_oam.bin \
  --trace work/oam_spin_kill.trace=work/oracle_spin_kill_oam.bin \
  --bank work/g3/bank --out work/g5ref
```

Salida completa: `work/g5ref_a2.log`. Evidencia regenerable, sin versionar
(R9): `work/g5ref/resumen.json`, `plan_yi1.json`, `plan_normal.json`,
`plan_spin_kill.json`, `muestra.png`. Las listas de frames se conservan en
los JSON y, comprimidas sin pérdida en intervalos inclusivos, al final de
este informe.

```text
yi1: registros=3712 frames=3252 frames_con_rex=2288 diferencias_A2=0
normal: registros=1045 frames=825 frames_con_rex=661 diferencias_A2=0
spin_kill: registros=641 frames=566 frames_con_rex=455 diferencias_A2=0
PUERTA A2: OK
PUERTA A: FALLA. PARADA: no ejecutar B ni C.
```

| traza | sin destino | sin variante | sin plazo (MOVE) | errores color (píxeles) | prioridad distinta | máx. MOVE/línea | máx. escrituras/frame |
|---|---:|---:|---:|---:|---:|---:|---:|
| yi1 | 383 | 0 | 40524 | 136142 | 0 | 8 | 92 |
| normal | 220 | 0 | 11595 | 35522 | 0 | 8 | 95 |
| spin_kill | 75 | 0 | 7217 | 23983 | 0 | 8 | 96 |

El contador `sin_destino` cuenta los otros Rex de cada frame; nunca cambia
la elección del Rex superior. El de color cuenta cada píxel de Mario y
Rex por separado, incluidos los usos simultáneos, según A6. La primera
variante compatible del directorio se conserva aunque falle su plazo.

## Por qué falla

| traza | ventanas de color vacías | capacidad agotada | armado fuera de pantalla | frames sin plazo | frames con errores color |
|---|---:|---:|---:|---:|---:|
| yi1 | 40513 | 11 | 0 | 1506 | 1356 |
| normal | 11590 | 5 | 0 | 477 | 403 |
| spin_kill | 7215 | 2 | 0 | 292 | 260 |

Diagnóstico: `python work/g5diagnose.py`, salida en
`work/g5diagnostico.log` y `work/g5ref/diagnostico.json`. Es una extracción
de los planes ya generados; no selecciona otra variante ni vuelve a planear.
La clasificación puede reproducirse leyendo `sin_plazo_detalle`: color
con `lo > hi` es ventana vacía; armado con `hi < 0` es fuera de pantalla;
el resto es falta de capacidad en su ventana.

Primer testigo: yi1 frame **5811**, slot 7, variante **49**, sy=176,
origen_y=-8. El índice DMA 1 se usa con color `$000` en y=168 y con `$FFF`
en y=169. Su escritura es `{indice:1, valor:4095, lo:169, hi:168,
destino:169}`: la ventana `[169,168]` está vacía. El mismo testigo aparece
en normal frame 1991 y spin_kill frame 2005. Aunque esos primeros Rex
entran por fuera del borde horizontal, el bloqueo se repite con Rex
visible; las variantes y reservas se aplican por fila como exige A3-A5.
Una capacidad mayor no arregla una ventana vacía. Este resultado no
demuestra imposible otro diseño de recargas: documenta el fallo de este
modelo y su variante elegida por la tarjeta.

El armado reserva los 16 MOVE exigidos por A5 (8 PT, 8 POS/CTL), con PT
antes de los controles. Las parejas sin columna de la pose se representan
inactivas. Se coloca el armado desde el último MOVE al primero conservando
su orden; después los colores van a la última línea disponible de su
ventana. Los 18 fallos de capacidad se distinguen de los 59318 de ventana
vacía; la parada ya está determinada por estos últimos.

`prioridad_distinta=0` fue comprobado con primera ficha opaca de OAM,
desempate por orden del tramo Rex frente a cada píxel dinámico de Mario.
Una prueba sintética del plan completo invierte ese orden: Rex primero
da 8 píxeles de prioridad distinta, Mario primero da 0.

## Evidencia visual

`work/g5ref/muestra.png` fue abierta e inspeccionada. Tiene 12 frames
repartidos entre las tres trazas, referencia arriba y registros simulados
abajo. Se ven errores de color en Mario y Rex; no se declara equivalencia.
El fondo negro corresponde al alcance del modelo (Mario/partículas
dinámicas y Rex elegido); no es una captura del nivel ni del emulador.
Los Rex adicionales que cuenta `sin_destino` quedan fuera de este par de
imágenes. No se hicieron capturas WinUAE ni medidas de tiempo: B/C no
empezaron.

## Verificaciones de integración

`python tools/test_g5ref.py`: **8 tests, OK**, sin ROM ni assets. Incluye
fila incompatible con Mario, orden del directorio, ventana vacía,
capacidad exacta 8, armado PT antes de controles, armado sin ventana,
máscaras con volteo vertical y prioridad OAM.

La regresión llama `test_g5ref.py` desde `g5ref_checks`; se comprobó su
ejecución: `rg -n 'test_g5ref.py|Ran 8 tests' work/regress.log` mostró
líneas 58 y 61 (`Ran 8 tests in 0.176s`, `OK`). Baselines intactas.

Red previa (`work/g5base.log`, `g5lint.log`, `g5regress.log`,
`g5oamgate.log`): lint **RESULTADO: OK**, regress con
`--baseline tools/baseline_pc.json --level` **RESULTADO: OK**,
`oam68k_gate.sh` **OAM68K: OK**. La misma red final terminó con
**RESULTADO: OK**, **RESULTADO: OK**, **OAM68K: OK**, en
`work/g5final.log`; el commit WIP conserva únicamente herramientas,
tests y este informe.

Hashes iniciales del bucle de §6.1:

| configuración | SHA256 |
|---|---|
| default | `c03b569643c7bf5ac62f55cdd2813951a6895a6d4801d1eef241e96cfa422769` |
| REPLAY | `9403f71c76bc2df9a92a3cc24d8db1e9e67c47e5e62a558e441c3994d0538109` |
| REPLAY+BENCH | `2bc486d77af939aedfb183457e33cc41eba172521959bb0192ddbe6f594363bb` |
| REPLAY+BENCH+SPR_OAM (build adicional explícito) | `b1736142e626e59c479c1a1134ebfab4e0d6511a663a781052f6391cd0231000` |

El bucle publicado usa `cut -d'|' -f3`, pero su cuarta entrada tiene un
solo separador: vuelve a compilar REPLAY+BENCH. Se ejecutó también el
build explícito `CDEFS='-DNOOAM -DSPR_OAM' GDEFS='-DREPLAY -DBENCH'`
para cubrir la variante verdadera. Ningún fichero del build del juego
fue modificado en esta rama. Los cuatro hashes del bucle publicado
coincidieron antes/después; la variante real adicional fue recompilada y
comparada con `cmp`, salida en `work/g5hashactual.log`. Comparación del
bucle con `Select-String`/`Compare-Object`: `work/g5hash_compare.log`,
`Cuatro hashes del bucle publicado: identicos`. Una primera extracción
Python de esos logs no obtuvo cuatro matches; fue reemplazada por la
lectura de PowerShell, sin alterar ni repetir los builds.

## Entrega y continuación

Commit local `WIP:` con fase A roja; hash verificable por
`git log -1 --format='%h %s'` y comunicado al coordinador al terminar.
G5a-bis sigue parcial. No corridos B1-B5, C1-C5, `--check` PC, Musashi
de g5_plan, scrollsim G5, comparaciones Amiga ni A/B integrado: parada
obligatoria de la fase A. El coordinador decide el siguiente trabajo de
diseño G2/G4 con esta evidencia; esta rama no intenta corregirlo.

Trampa nueva propuesta, **Pnn sin número:** una variante G3 compatible
con las reservas de Mario puede reutilizar un índice para colores
distintos en filas adyacentes del propio Rex. La puerta de compatibilidad
de color no garantiza una ventana de recarga libre entre esas filas.

## Frames exactos de las puertas rojas

Los intervalos siguientes son inclusivos; cada número aislado identifica
un frame de oráculo. `sin_variante`: lista vacía en las tres trazas.

yi1, frames_sin_plazo (1506):

5811-5857, 6137-6152, 6154-6160, 6169-6176, 6183-6273, 6281-6288, 6297-6304, 6313-6316, 6320-6387, 6389-6412, 6569-6570, 6572-6576, 6585-6592, 6601-6603, 6608-6643, 6649-6656, 6665-6672, 6701-6705, 6707, 6718, 6720-6721, 6723-6733, 6736, 6745-6746, 6748, 6750-6755, 6757-6760, 6766, 6768, 6770, 6772, 6778-6785, 6789, 6795, 6798, 6800-6801, 6803, 6805, 6808-6812, 6814-6815, 6817-6824, 6832, 6834, 6836, 6847-6880, 6893-6900, 7097-7122, 7129-7136, 7145-7152, 7161-7162, 7165-7172, 7177-7184, 7193-7200, 7209-7215, 7219-7258, 7263-7264, 7273-7280, 7289-7296, 7301-7320, 7347-7351, 7387-7394, 7403-7410, 7419-7426, 7435-7442, 7451-7458, 7464-7484, 7488-7490, 7499-7506, 7515-7608, 7610-7624, 7626-7636, 7641-7652, 7657-7666, 7669-7670, 7673-7682, 7685-7686, 7689-7697, 7699, 7701, 7703, 7705, 7707-7713, 7715, 7717, 7719, 7721, 7723-7832, 7837-7841, 7851-7857, 7867-7868, 7870, 7883-7884, 7886, 7888, 7890-7971, 7979-7986, 7995-7998, 8002-8005, 8016-8055, 8059-8066, 8075-8082, 8091-8098, 8107-8114, 8123-8130, 8139-8146, 8155-8162, 8171-8178, 8187-8194, 8203-8210, 8219-8226, 8235-8242, 8423-8430, 8439-8446, 8451-8509, 8519-8526, 8535-8542, 8546-8565, 8585-8596, 9661-9668, 9677-9684, 9693-9700, 9709-9716, 9725-9732, 9741-9748, 9757-9764, 9773-9780, 9789-9796, 9805-9826, 9846-9857, 10297-10304, 10313-10320, 10329-10336, 10345-10352, 10361-10368

yi1, frames_errores_color (1356):

5811-5836, 5843-5850, 5855-5857, 6137-6148, 6150-6152, 6154-6160, 6169-6176, 6183-6273, 6281-6288, 6297-6304, 6313-6316, 6320-6380, 6409-6412, 6585-6592, 6601-6603, 6608-6643, 6649-6656, 6665-6672, 6720-6721, 6723-6733, 6736, 6745-6746, 6748, 6750-6755, 6757-6760, 6766, 6768, 6770, 6772, 6778-6785, 6789, 6795, 6798, 6800-6801, 6803, 6805, 6808-6812, 6814-6815, 6817-6824, 6832, 6834, 6836, 6847-6880, 6893-6900, 7097-7098, 7104-7122, 7129-7136, 7145-7152, 7161-7162, 7165-7172, 7177-7184, 7193-7200, 7209-7215, 7219-7258, 7263-7264, 7273-7280, 7289-7296, 7301-7320, 7347-7351, 7404-7410, 7419-7426, 7435-7442, 7451-7458, 7464-7484, 7488-7490, 7499-7506, 7515-7608, 7610-7624, 7626-7636, 7641-7652, 7657-7660, 7665-7666, 7669, 7677-7678, 7681-7682, 7693-7694, 7697, 7707-7713, 7715, 7717, 7719, 7721, 7723-7832, 7837-7841, 7851-7857, 7867-7868, 7870, 7883-7884, 7886, 7888, 7890-7954, 7956-7970, 8002-8005, 8019-8034, 8038-8052, 8054-8055, 8066, 8075-8082, 8091-8098, 8107-8114, 8123-8130, 8139-8146, 8155-8162, 8171-8178, 8187-8194, 8203-8210, 8219-8226, 8235-8242, 8439-8446, 8451-8509, 8519-8526, 8535-8542, 8546-8565, 8585-8596, 9677-9684, 9693-9700, 9709-9716, 9725-9732, 9741-9748, 9757-9764, 9773-9780, 9789-9796, 9805-9826, 9846-9857, 10314-10320, 10329-10336, 10345-10352

normal, frames_sin_plazo (477):

1991-1998, 2007-2014, 2023-2030, 2039-2046, 2051, 2053-2070, 2072-2126, 2130, 2139-2151, 2153, 2164, 2166, 2168, 2170, 2180, 2182, 2184, 2186, 2192-2201, 2203-2213, 2216-2217, 2222-2273, 2275-2304, 2308-2314, 2323-2330, 2339-2402, 2413-2418, 2429-2434, 2445-2450, 2461-2466, 2477-2482, 2485-2532, 2567-2610, 2612, 2615-2622, 2631-2638, 2647, 2650, 2652-2656, 2658-2659, 2663-2670, 2679-2686

normal, frames_errores_color (403):

2007-2014, 2023-2030, 2039-2046, 2051, 2053-2070, 2072-2098, 2101-2126, 2130, 2139-2146, 2164, 2166, 2168, 2170, 2180, 2182, 2184, 2186, 2192-2201, 2203-2213, 2216-2217, 2222-2257, 2275-2282, 2285-2304, 2308-2314, 2323-2330, 2339-2378, 2389-2393, 2395-2398, 2413-2418, 2429-2434, 2445-2450, 2461-2466, 2477-2482, 2485-2516, 2520-2522, 2525-2532, 2567-2610, 2612, 2615-2622, 2631-2638, 2647, 2650, 2653-2654, 2656

spin_kill, frames_sin_plazo (292):

2005-2012, 2021-2028, 2037-2044, 2053-2060, 2065, 2067-2084, 2086-2142, 2153-2165, 2167, 2178, 2180, 2182, 2184, 2194, 2196, 2198, 2200, 2206-2215, 2217-2224, 2226-2228, 2230-2231, 2236-2316, 2318, 2320-2326, 2335-2342, 2378-2380, 2389-2396, 2405-2412, 2421-2428, 2437-2444, 2453-2459

spin_kill, frames_errores_color (260):

2021-2028, 2037-2044, 2053-2060, 2065, 2067-2084, 2086-2112, 2115-2142, 2153-2160, 2178, 2180, 2182, 2184, 2194, 2196, 2198, 2200, 2206-2215, 2217-2224, 2226-2228, 2230-2231, 2236-2271, 2287-2294, 2296-2316, 2318, 2320-2326, 2335-2342, 2378-2380, 2389-2396, 2405-2412, 2421-2428, 2437-2444, 2453-2459
