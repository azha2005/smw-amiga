# G7 — cobertura híbrida y paso al renderer

2026-10-11. G7-C tiene cobertura offline completa en las cinco trazas:
3.754 fotos, 250.347 píxeles, 0 sin resolver. Siete sondas físicas,
1.180 píxeles, 0 diferencias en pantalla completa. Leer
`informe-g7-c-1011.md`. La excepción está autorizada por el usuario;
no volver a pedir esa elección. Continuar por §4, G7-3; §1–3 conservan
la reproducción y las puertas para comprobar cambios del planificador.

## 1. Partida verde y reproducción acotada

```sh
export PATH="$TEMP/pyshim:/c/msys64/ucrt64/bin:$PATH" VBCC=/c/Users/JC/vbcc PY=python PYTHONIOENCODING=utf-8
python tools/lint_port.py
python tools/regress.py --baseline tools/baseline_pc.json --level --g5l --bm1
python tools/g7_sources.py
python tools/test_g7_color_plan.py
python tools/test_g7_hw_support.py
python tools/g7_hybrid_plan.py --bin work/rg_g7_double_replay/game.bin --lst work/rg_g7_double_replay/game.lst --from-k 6046 --to-k 6049 --out work/g7-hybrid-check
```

Esperado: lint/regress OK; fuentes 7.616 B; 8 y 14 tests OK;
`G7 HYBRID: OK`, 4 fotos, 848 píxeles, 1 foto PF1 y 3 híbridas.
El informe debe tener `complete=true`, 0 fotos sin resolver.
`complete=false` y `completed_until` son un checkpoint, no una puerta.

## 2. Cobertura y asignador de destinos

Puerta offline ya cumplida en `work/g7c/hybrid-<traza>-final/report.json`:
yi1 1.298 fotos/91.214 píxeles (21 híbridas), pw_bloques 510/39.735,
chuck_kill 669/53.932, spin_kill 358/28.598, stress_piranha 919/36.868.
Todas `complete=true`; 0 sin resolver. Repetir si se cambia la referencia
o los datos del juego; no sustituye las puertas del renderer.

1. Leer P108/P110/P111/P125/P132/P133 y G0. La reserva real de canal es
   VSTART/VSTOP/PT/POS/CTL; transparencia no libera DMA. Mantener la OAM
   de DC_REND y comprobar BPLCON2 y colores por píxel.
2. Extender la barrida **por tramos acotados**; registrar su último frame
   completado y sus rechazos. No repetir una búsqueda larga a ciegas:
   `g7_hybrid_plan.py` publica PHOTO/checkpoints cada 25 frames.
   Tramo acotado ya comprobado:
   ```sh
   python tools/g7_hybrid_plan.py --bin work/rg_g7_double_replay/game.bin --lst work/rg_g7_double_replay/game.lst --from-k 6015 --to-k 6060 --out work/g7-hybrid-6015
   ```
   Esperado en ese tramo: OK, 46 fotos, 8.929 píxeles, 40 fotos PF1 y
   seis híbridas. En otros tramos el resultado puede ser OK o PARCIAL.
   En PARCIAL, leer `failures`:
   distinguir cota negativa de PF1, presupuesto de búsqueda agotado,
   canal ocupado, prioridad o recarga compartida. Aislar cada caso con
   `--from-k K --to-k K`; ninguna de esas causas prueba imposibilidad
   universal de Amiga.
3. El modelo actual solo usa parejas 2/3 y 6/7 **detenidas durante toda
   la foto**, con paleta existente exacta o sufijo calibrado. La validación
   conjunta debe preservar cada píxel hardware original y los colores de
   todos los apoyos. Un sufijo idéntico compartido se emite una vez;
   cargas incompatibles en la misma fila requieren un plan conjunto.
   Extender destinos cuando un
   caso real lo exija: una sola pareja primero, después dos, y reuso
   vertical solo si se mide conforme a G0. Mantener la mayoría por PF1.
   No usar datos seleccionados por número de frame en el producto.
4. Comprobar todas las fotos visibles de yi1 y las cuatro trazas SW-S.
   Para generar los cinco binarios con OAM de foto:
   ```sh
   GDEFS="-DREPLAY -DG7_DOUBLE" sh tools/sws_gate.sh
   ```
   Esperado: SWS RAM/OAM/PHOTO OK en las cinco. Yi1 queda en
   `work/sws/b1/`, las otras en `work/sws/t_<traza>/`. Usar sus binarios
   y listados como entradas de `g7_hybrid_plan.py`, sin compilaciones
   concurrentes. Son pw_bloques, chuck_kill, spin_kill y stress_piranha.
5. Puerta: ningún píxel sin destino explícito, paleta/posición/orden
   reconstruidos exactos; ninguna foto sin resolver en los tramos que
   se declaren completados. Añadir pruebas de recorte, solape, estrella,
   Mario ancho y las dos direcciones de cámara. Medir los casos nuevos.

## 3. Repetir una sonda física

Para k6047, una pareja. Para k6048/6049, la sonda medida usa dos:

```sh
python tools/g7_color_probe.py build --bin work/rg_g7_double_replay/game.bin --lst work/rg_g7_double_replay/game.lst --frame 6047 --hardware-entry 31 --out work/g7-hw-check/probe
GDEFS="-DREPLAY -DG7_DOUBLE -DSTOPF=6047" OUT=work/g7-hw-check/control sh tools/bm_build.sh
"$VBCC/bin/vasmm68k_mot.exe" -quiet -Fbin -m68000 -DREPLAY -DG7_DOUBLE -DG5L -DCUSHION -DBM_FIXED -DSPR_OAM -DSTOPF=6047 -I player -I . -L work/g7-hw-check/probe/game.lst -o work/g7-hw-check/probe/game.bin work/g7-hw-check/probe/game.probe.s
python tools/mkadf.py --boot work/g7-hw-check/control/boot_bm.bin --stage2 work/g7-hw-check/probe/game.bin --data work/yi1_s_g5.dat --out work/g7-hw-check/probe/game.adf
python tools/memmap.py work/g7-hw-check/probe/game.lst --data work/yi1_s_g5.dat
```

Esperado: build y 0 violaciones. Para dos fichas, repetir
`--hardware-entry 31 --hardware-entry 30`; cambiar frame/STOPF y carpetas.
Las sondas con recargas usan OAM 29 en k6064/k6065, y
`--hardware-entry 28 --hardware-entry 29` en k6066. Este último caso
no tiene escrituras PF1: ambas fichas usan un solo sufijo compartido
en fila180, x243/251/259/267/275. No generar un `DBF` con cuenta −1.
Capturar control y candidato por el candado y `shot.ps1 -Exact`, 200 s;
workers con copias de shot y rutas ADF/Out absolutas. Después:

```sh
python tools/g7_color_probe.py compare --meta work/g7-hw-check/probe/probe.json --control work/g7-hw-check/control/shot.png --shot work/g7-hw-check/probe/shot.png
```

Esperado: G7 PROBE OK, 0 diferencias en pantalla completa. Mirar
`check.png`. El negativo se genera con `--hardware-late`, se compila y
captura igual, y se compara con `--expect-negative`: debe detectar
errores dentro del apoyo y cero fuera. No comparar pantallas de carga.

## 4. G7-3 y coste, después de la cobertura

1. Producir un descriptor de destino desde R_OAM/R_S/R_TSEQ y el copper
   de DC_REND: píxeles PF1, índices por X, eventos de color y apoyo
   hardware, sin escoger tablas por número de frame. Usar la referencia
   para comparar cada descriptor antes de escribir el PF1. La DFS offline
   no tiene presupuesto de CPU demostrado: medir y diseñar la ruta del
   juego antes de trasladarla al 68000; un cache hit no prueba el coste
   de la primera foto ni de un mapa mutado.
2. Cargar fuentes dentro de los 12 KiB existentes. Medir el almacenamiento
   del payload en el ADF y en vivo, además de su destino chip: copiarlo a
   la reserva no descuenta por sí solo la copia que sigue en el binario.
   Mantener `memmap.py` con 0 violaciones en replay y vivo.
3. Seguir paso 5 de `instrucciones-g7-2.md`: regiones sucias por PF1,
   restauración desde BLK/mapa, columnas y diario hasta R_TSEQ, las dos
   copias del anillo, clipping y vuelta. Dibujar únicamente R_OAM válida;
   esperar `bwait` antes de publicar. Probar primero restauración sin
   efectos, después cola de bobs y solapes.
4. Dar almacenamiento **por lista** a los flujos hardware y conservar su
   propiedad hasta que VERTB libere la lista; la reserva compartida de una
   sonda congelada no sirve como producto. No modificar FRONT ni PEND.
   Validar los controles DMA y la paleta de cada píxel tras emitir el plan.
5. Seguir paso 6 de `instrucciones-g7-2.md`: activar opt-in, repetir puertas
   de foto/propiedad, SW1 y A/B BENCH del árbol actual. Registrar todos los
   frames sin destino y el coste de fallos de caché; ninguno se oculta.

Puertas CPU: clipping, vuelta, SLOTS, solapes, mapa mutado, FRONT/PEND/
REND ocupadas y NOSWS sin residuos. Después SW1 HOLDEVERY50 y A/B BENCH
del árbol actual, no contra los 269 históricos. Registrar omitidas,
racha y ventana250. No activar por defecto antes de esas puertas.

## 5. Parada y cierre

No aproximar colores, omitir efectos, bajar a 25 Hz ni cambiar D8.
Si una alternativa exacta medida exige una decisión nueva, mostrar la
evidencia; un buscador lento o acotado no basta para esa conclusión.

Antes de cada commit: lint/regress completos, SWS RAM/OAM/PHOTO y
OAM68K verdes. Informe con cobertura **completada**, rechazos concretos,
memoria, negativos, imágenes miradas y coste real. Cierre ROADMAP §7.
