# G7-3 — retoma del renderer parcial

2026-10-11. Leer `informe-g7-3-1011.md`, `instrucciones-g7-hibrido.md`
§4 y `instrucciones-g7-2.md` pasos 5–6. Apoyo hardware autorizado.

1. Partir de lint/regress completos y SWS/OAM68K verdes. En Git Bash:
   `export PATH="$TEMP/pyshim:/c/msys64/ucrt64/bin:$PATH" VBCC=/c/Users/JC/vbcc PY=python PYTHONIOENCODING=utf-8`.
   Usar el `G7_OPT=1` por defecto; 991 fue exploratorio, no aprobado.
2. Recompilar secuencialmente `GDEFS="-DREPLAY -DG7_BOBS" sh tools/sws_gate.sh`.
   Ejecutar `python tools/g7_bobs_verify.py --bin work/sws/b1/game.bin --lst work/sws/b1/game.lst --to-k 99999 --out work/g73-yi1-final.json`.
   Repetir para t_pw_bloques, t_chuck_kill, t_spin_kill y t_stress_piranha.
   Los informes anteriores no prueban las últimas correcciones.
3. Aislar chuck con `--from-k 2500 --to-k 2830`. Quedan 13 rechazos:
   2681,2682,2684,2685,2686,2687,2688,2814,2815,2816,2817,2820,2821.
   Comparar `g7_color_plan.py --from-k 2681 --to-k 2681` contra C,
   por fila y por evento. La referencia resuelve las 12 filas de k2681.
   Auditar prefijo, borrow, WAIT/NOP, presupuesto compartido y asignación
   por agrupaciones; ampliar estados no resolvió todos. No usar tablas por frame.
4. Repetir k409 físico: candidato `-DREPLAY -DG7_BOBS -DSTOPF=409`;
   control igual con `-DNOSWS`. `OUT=work/g73/shot409` y control409,
   `sh tools/bm_build.sh`. Generar meta con `g7_color_probe.py build`
   desde el control G7_DOUBLE de `work/rg_g7_double_replay`, frame409.
   Capturar por `../winuae_lock.ps1`, `shot.ps1 -Exact`, 240 s,
   con copias privadas de shot para no compartir UAE/log.
   Comparar `g7_color_probe.py compare --meta work/g73/meta409/probe.json
   --control work/g73/control409/shot.png --shot work/g73/shot409/shot.png`.
   Antes del cambio a lectura del PF1 hubo 1.484 píxeles diferentes.
   Medir R_FRAME/R_S, PF1, segmentos originales y emitidos y fuentes de
   cola en la instancia propia; verificar la foto que realmente está FRONT.
   La hipótesis mapa/materialización aún no está confirmada en WinUAE.
5. Puerta CPU: core cola/IRQ/minterm/anillo/diario, ida/vuelta, mapa
   mutado, clipping y solapes; FRONT/PEND inmutables; R_OAM inválida y
   NOSWS sin residuos. Añadir casos a `g7_bobs_verify.py`; conservar
   validación de hardware original y contar capacidad máxima del diario.
6. Recompilar vivo y BENCH, ejecutar memmap en ambos: límites 524.288 B
   chip/slow. BENCH tiene poco margen; no confiar en el tamaño del vivo.
   Auditar carga ADF, KS1.2/1.3 y reinicio del banco/IRQ. Fuentes 7.616 B,
   payload 2.330 B en cinco sectores; CDMA 34.760 B en 68 sectores.
7. Solo con fidelidad verde, SW1 HOLDEVERY50 y fotos exigidas por G7-2;
   después A/B BENCH candidato y NOSWS del mismo árbol, cycle-exact.
   No aceptar una captura anterior al fin ni un HOLD que terminó antes
   de publicar la foto. Registrar omitidas, racha y ventana250, y coste
   de primera foto (el productor no tiene caché).
8. Antes de commit repetir lint/regress, SWS RAM/OAM/PHOTO y OAM68K.
   Mantener el hash default 33f2250a1b4231069ab975bfdc4f7d2336cd814a0e4e95d13bd862659c5b638b.
   Cerrar ROADMAP §7 con cobertura completada, fotos miradas y límites;
   no marcar G7-3 hecha hasta completar las puertas.
