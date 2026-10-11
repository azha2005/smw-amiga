# G7-C — resolver el testigo de color antes de la cola

2026-10-11. G7-2 capturó la OAM y generó fuentes exactas. Las sondas k409,
k5026 y k6015 pasan en WinUAE, pero k6047/fila161 tiene una cota negativa
independiente bajo el contrato G2T-A. Leer `informe-g7-2-1011.md` completo.
No repetir indefinidamente el buscador ni tratar un rechazo heurístico
como demostración: ahora existe un certificado local distinto.

## 1. Reproducir la partida

Git Bash, sin otras compilaciones en el mismo worktree:

```sh
export PATH="$TEMP/pyshim:/c/msys64/ucrt64/bin:$PATH" VBCC=/c/Users/JC/vbcc PY=python PYTHONIOENCODING=utf-8
python tools/lint_port.py
python tools/regress.py --baseline tools/baseline_pc.json --level --g5l --bm1
python tools/g7_sources.py
python tools/g7_photo_verify.py --bin work/rg_g7_double_replay/game.bin --lst work/rg_g7_double_replay/game.lst
python tools/g7_color_plan.py --bin work/rg_g7_double_replay/game.bin --lst work/rg_g7_double_replay/game.lst --from-k 409 --to-k 409 --out work/g7-check409
```

Esperado: lint/regress OK, fuentes 7.616 B, PHOTO OK y COLOR PLAN OK.
La regresión incluye esas herramientas y seis tests sintéticos. El banco
todavía no está cargado en el juego: la reserva de 12 KiB sí existe.

```sh
python tools/g7_color_plan.py --bin work/rg_g7_double_replay/game.bin --lst work/rg_g7_double_replay/game.lst --from-k 6047 --to-k 6047 --out work/g7-case6047
# Esperado: exit 1 / FALLA; filas 161 y 163 sin plan.
python tools/g7_color_bound.py --report work/g7-case6047/report.json
# Esperado: feasible=false, 9 colores, 7 registros, 1302 candidatos.
```

Mirar `work/g7-bound/window.png` y comprobar el certificado. No poner el
primer comando bajo `set -e` si se pretende ejecutar después la cota.
`--phase-max 7` es exploratorio, no el contrato físico G2T-A.

## 2. Decisión y evidencia que falta

1. **Decisión recibida el 2026-10-11:** «Apoyo puntual de sprites hardware
   para conservar los colores exactos». Investigar esta alternativa,
   autorizada como excepción puntual a efectos solo por bobs. No volver
   a consultar la elección. La viabilidad todavía debe demostrarse;
   conservar D8. El usuario pidió cerrar la sesión tras anotarla.
2. Auditar la cota: ventana x151..181 de fila161, nueve colores, registros
   libres al comienzo, dos MOVE como máximo; incluso permite remapear el
   terreno. El certificador ignora otras cargas para favorecer al candidato.
   Comprobar que la geometría usada para oclusión viene de esta foto, no de
   la RAM futura. `hardware_hidden` usa GV_NPL/RX_VAR y la prioridad real.
3. **Si se investiga temporización:** leer G2T-A/P110/P111 y las suites
   `g2t_cal.py`. Derivar primero una secuencia concreta que invalide alguna
   premisa de la cota manteniendo todos los píxeles y D8. Crear una sonda
   sintética con positivo en el límite y negativo un paso fuera. Medirla en
   WinUAE cycle-exact por el candado, con seis planos, sprites y audio DMA.
   Sin esa puerta, no ampliar las ranuras del modelo ni retocar deadlines.
4. **Apoyo hardware autorizado, siguiente trabajo:** demostrar el armado y los colores
   de un efecto concreto de k6047. No deducir disponibilidad a partir de
   píxeles transparentes: mirar VSTART/VSTOP, PT/POS/CTL y el rearmado G0.
   Mario opaco acaba en160, pero eso no prueba que su DMA esté libre en161.
   G5L tiene un objeto de dos columnas desde161. Medir la excepción y su
   coste, incluidas las recargas compartidas con los enemigos. Conservar
   la mayoría del render por bobs y hacer explícito el destino de cada
   píxel; ninguna ficha puede desaparecer por falta de canal.
5. **Parada:** si ninguna alternativa exacta medida funciona, mostrar la
   evidencia y pedir una decisión nueva antes de aproximar colores, omitir
   efectos, bajar a 25 Hz o cambiar D8. No presentar la cota actual como una
   prueba universal sobre toda implementación de Amiga.

## 3. Sondas comparables

```sh
python tools/g7_color_probe.py build --bin work/rg_g7_double_replay/game.bin --lst work/rg_g7_double_replay/game.lst --frame 409 --out work/g7-probe-new/409/probe
GDEFS="-DREPLAY -DG7_DOUBLE -DSTOPF=409" OUT=work/g7-probe-new/409/control sh tools/bm_build.sh
"$VBCC/bin/vasmm68k_mot.exe" -quiet -Fbin -m68000 -DREPLAY -DG7_DOUBLE -DG5L -DCUSHION -DBM_FIXED -DSPR_OAM -DSTOPF=409 -I player -I . -L work/g7-probe-new/409/probe/game.lst -o work/g7-probe-new/409/probe/game.bin work/g7-probe-new/409/probe/game.probe.s
python tools/mkadf.py --boot work/g7-probe-new/409/control/boot_bm.bin --stage2 work/g7-probe-new/409/probe/game.bin --data work/yi1_s_g5.dat --out work/g7-probe-new/409/probe/game.adf
python tools/memmap.py work/g7-probe-new/409/probe/game.lst --data work/yi1_s_g5.dat
```

Esperado: build y 0 violaciones. En PowerShell, capturar control y sonda
por `../winuae_lock.ps1`, `tools/shot.ps1 -Exact`, **90 s como mínimo** en
k409. Con copias de shot por slot, pasar ADF y Out **absolutos**. Con tres
emuladores dar margen adicional; k5026 y k6015 necesitaron 140/160 s.
No cerrar WinUAE ajenos ni comparar pantallas de carga.

```sh
python tools/g7_color_probe.py compare --meta work/g7-probe-new/409/probe/probe.json --control work/g7-probe-new/409/control/shot.png --shot work/g7-probe-new/409/probe/shot.png
```

Esperado: `G7 PROBE: OK`, 0 px distintos. Repetir k5026/k6015 y el testigo
que resuelva la alternativa; mirar las imágenes. El arnés es precalculado
y escribe por CPU: no usar sus tablas por frame en el producto ni su coste
como BENCH del render. No acepta una foto sin píxeles visibles.

## 4. G7-3, solo después de resolver color

1. Cargar las fuentes en la reserva existente, sin duplicarla; medir chip
   y slow en vivo y replay. Quedan 1.840 B de chip y unos 12 KiB de slow.
   Si el banco va embebido en slow antes de copiarlo, descontar también esa
   copia; preferir carga directa o reutilizar su almacenamiento.
2. Implementar las regiones sucias y la cola conforme a los pasos 5–6 de
   `instrucciones-g7-2.md`: restaurar BLK/D_MAP en las dos copias del anillo,
   alcanzar R_TSEQ, dibujar desde R_OAM válida, `bwait` antes de publicar.
3. Puertas CPU primero: ambas direcciones de cámara, cruce SLOTS, clipping,
   solapes, mapa mutado y FRONT/PEND/REND ocupadas. IRQ no usa el blitter.
   Con `NOSWS` no queda cola de efectos ni regiones mal restauradas.
4. SW1 completo a HOLDEVERY50 y las fotos señaladas en G7 original,
   controles y candidatos del mismo lote. 0 px distintos en efectos y sin
   diferencias nuevas fuera de ellos. Repetir con fotos omitidas.
5. BENCH A/B cycle-exact del prototipo actual y del candidato. Los 269 de
   G7-1 son históricos: la copia OAM nueva todavía no tiene A/B. Registrar
   omitidas, racha, ventana250 y espera de propiedad, sin ocultar costes.
   No activar por defecto sin esta evidencia y el estado D1 explícito.

Antes de cada commit: lint/regress completos, `sh tools/sws_gate.sh`
(RAM/OAM y PHOTO en los builds G7) y `sh tools/oam68k_gate.sh`, secuenciales.
Informe con comandos, límites, memoria, capturas y decisión real del usuario.
Cierre según ROADMAP §7; orden de trabajo únicamente en `PROXIMO.md`.
