# D1 — trazas WinUAE reales y coste de las sondas

2026-10-06. Base `44ba9dc`; integrado en master con `d30403a` (fusión `58784d9`, que también conectó `test_d1_trace.py` a `regress.py`). Cambios opt-in. **La compuerta de fluidez sigue roja.** Las trazas completas corresponden al build instrumentado; el control sin sondas también repite muchas imágenes. No se aprueba la fluidez ni se atribuyen tiempos Musashi al DMA.

## Resultado final instrumentado

| escenario | operaciones / ticks | VBL activos | omitidas | porcentaje | racha | peor ventana250 | edad lógica p99 / máx. |
|---|---:|---:|---:|---:|---:|---|---:|
| stress_back | 4127 / 4126 | 4126 | 753 | 18,2501 % | 57 | 241 desde el VBL 2563 | 77 / 106 |
| stress_sprites | 1915 / 1914 | 1914 | 205 | 10,7106 % | 93 | 188 desde el VBL 1636 | 96 / 108 |

Una operación LEVEL inicial prepara el estado fuera del denominador. Back conserva 4128 filas crudas: estado inicial, VBL1–4126 activos y VBL4127 de drenaje final. Sprites conserva 1915 filas: estado inicial y VBL1–1914 activos. Ambas últimas fotos y todos los ticks esperados terminaron.

| duración integrada, CIA-B | back media / p99 / máx. | sprites media / p99 / máx. |
|---|---:|---:|
| foto mostrada | 5947,63 / 47635 / 813708 | 4371,99 / 30602 / 1307666 |
| tick completo | 6870,08 / 12090 / 13615 | 6437,61 / 13427 / 13925 |

1 tick CIA-B = 1/709379 s. p99 usa rango más próximo. Foto = inicio de preparación antes de dc_capture hasta publicación DC_PEND: incluye captura, espera y render; excluye game_step y espera hasta presentación. Tick = antes de game_step hasta final de dc_capture. No son sumas de máximos. Se resta la calibración de lectura de timestamp (45 ticks en ambas corridas finales); el resto del coste de las sondas permanece.

Back tiene cero intervalos sin tick y cero con varios. Sprites tiene **30 intervalos sin tick y 30 con dos**, con 1914 eventos completos y saldo final cero. No se interpretan los primeros como ticks definitivamente perdidos: después se recuperan. La edad de la tabla es en ticks lógicos; los timestamps crudos permiten otro análisis temporal, pero aquí no se declara una distribución de edad física.

## Perturbación A/B, no corregirla a posteriori

A y B usan mismos CDEFS=-DNOOAM -DSPR_OAM, replay, datos y perfil cycle-exact. Ambos activan D1TIMER; B añade D1TRACE. Las columnas siguientes son **agregados BENCH** de cada captura, no un CSV del control:

| escenario | DC_REP A → B | total medio BENCH A → B, ticks | peor ISR A → B, ticks | DC_LATE A → B |
|---|---:|---:|---:|---:|
| back | 714 → 753 | 8005 → 8408 | 13225 → 13620 | 0 → 0 |
| sprites | 100 → 206 | 7247 → 7416 | 13527 → 13904 | 0 → 60 |

La sonda añade 403/169 ticks a esas medias (2,84/1,19 puntos del frame), cambia las decisiones de render y en sprites cruza el umbral que dispara el fallback. **205/1914 y su p99 describen B, no el juego sin sondas.** El control demuestra un problema real anterior a las sondas, pero sus agregados no demuestran ventana250, edad ni p99. DC_REP incluye límites inicial/final propios de dc_act; en sprites B da 206 frente a 205 repeticiones del tramo definido por el exportador. No se fuerza igualdad ni se cambia el denominador.

El alcance tiene O5 y OAM ampliada calculada, pero todavía no G5 definitivo, HUD ni audio. El diagnóstico sin SPR_OAM quedó **pendiente**: sus corridas se cerraron por el pedido de concluir la sesión. No se integran datos parciales.

## Exportación y memoria

D1TR v2 reserva **147232 B de slow**: cabecera de 32 B, 4600 filas de 20 B y 4600 eventos de 12 B, sin wrap y con overflow explícito. Observa FRONT/R_FRAME después de dc_vb, y un contador terminado después de dc_capture; DC_NLOG previo a game_step no se usa como completado. Cada intervalo referencia todos sus eventos con ID, duración e instante final. El CSV singular de d1_count.py conserva el rechazo de varios ticks/VBL: back también produce vbl.csv; sprites usa trace.json + ticks.csv.

CIA-B timer B cuenta underflows de A (CRB=$51), con lectura TB/TA/TB coherente de 32 bits. No se añaden máscaras de IRQ ni escrituras SR. El timer B no tenía dueño en player/. Ambos A/B lo inicializan; no se cuantificó por separado una variante sin D1TIMER. Todo lo leído por el chipset conserva ubicación y configuración; la reserva experimental no es presupuesto de producción.

Memmap replay instrumentado: chip 390 704 B; slow back 349 872 B, sprites 336 600 B; cero violaciones. El loader transitorio carga stage2+datos antes de liberar la copia inicial: back 202 752 + 230 400 = 433 152 B chip, aparte del SO. La sonda no agrega un banco DMA ni una segunda copia de su reserva. Si AllocMem falla o sale del rango $C00000–$C80000, el build experimental se detiene con rojo; overflow o traza incompleta se rechazan.

ReadProcessMemory se aplica únicamente al PID propio, después de done=1. Dos lecturas deben ser iguales. El exportador cruza firma del binario, offset d1_ptr del listado del mismo build, puntero runtime y rango slow: no elige una copia antigua de stage2. No hay pausas ni sondeo del host por frame. El formato de memwatch logonly oficial no proporciona los timestamps necesarios: [fuente WinUAE](https://github.com/tonioni/WinUAE/blob/master/debug.cpp).

## Configuración y evidencia

WinUAE **6.0.0.0**, KS 1.2; OCS PAL/68000; chip 512 KiB, slow 512 KiB, fast 0; cycle_exact, cpu_cycle_exact, cpu_memory_cycle_exact y blitter_cycle_exact=true; cpu_speed=real; immediate_blits=false; cachesize=0; floppy_speed=100. Se carga run.uae privado, cuya identidad aparece en las capturas. Host: gfx_framerate=1 y win32.active_not_captured_pause/inactive_pause/iconified_pause=false. Candado compartido, máximo 3 procesos; solo se cierran PID propios.

Todos los artefactos quedan en work/, no en git:

- work/d1-back-final/ y work/d1-sprites-final/: raw.bin, raw.export.json, trace.json, ticks.csv, final.png, read.txt, manifest.json, memmap.log; back añade vbl.csv.
- work/d1-back-a/ y work/d1-sprites-a/: final.png, read.txt y manifest.json del control.
- work/d1-lint-final.log y work/d1-regress-final.log: RESULTADO OK; regresión PC --baseline tools/baseline_pc.json --level, sin cambiar bases.
- Los manifiestos contienen hashes completos de WinUAE, ROM, perfil, binario, ADF, datos, oráculo, replay, listado y fuentes. Ejecutable d365aa5a45476a400a0d4ec85332efe500a5ad11c1b418af9f5877d3ee477c13; ROM 87cddb1f499e32758de20145e73031a84bab299e3f6e5c8487e76d02b2ee9d16.

| archivo en work/ | SHA256 |
|---|---|
| d1-back-final/game.bin | 5cb7464d2a22df5ed05215b369c15af2251e9bb3182609b259000649111413ba |
| d1-back-final/game.adf | 81ae1427bf9714089d64deea6f3583af74e25b7f1898349d092fee67fc772954 |
| d1-back-final/run.uae | b86adc1c4890b9c27ce47e608e017a56570b32a8fe2e4173cf59c811a0d281bb |
| d1-back-final/raw.bin | 6928f0fa20599d48be80c0ab27b301ad756ebbe2cd4453eff8b2420564d66098 |
| d1-sprites-final/game.bin | 7748330014f8984f329ba4bb8527ef0a25028655f56ee4082e7af415777f94fc |
| d1-sprites-final/game.adf | 988e8192a50ae0d5237846b13fd38e12a9f2b553ff7bb83a1e7f9e10ea1c2520 |
| d1-sprites-final/run.uae | 3dc8bd2e88a4898e9f928c4f838633da9e188c12bd43d5dea210ab04a3595d89 |
| d1-sprites-final/raw.bin | f0bc4fad86aa62b475dad639842f8e306f4b751f58ea42e8404ded5db819f12e |

Reproducir después de game_build.sh con los flags indicados:

```sh
python tools/d1_capture.py work/d1-back-final --ops 4127 \
  --oracle work/oracle_stress_back.bin --replay work/stress_back_replay.bin \
  --flags 'CDEFS=-DNOOAM -DSPR_OAM; GDEFS=-DREPLAY -DBENCH -DD1TIMER -DD1TRACE'
python tools/d1_count_v2.py work/d1-back-final/raw.bin --expected-ops 4127 --out work/d1-back-final/trace.json
```

Para sprites cambiar escenario y --ops 1915. El capturador usa el ejecutable Python que lo invoca; en la PC evitar el stub python3 de WindowsApps. Las cinco pruebas de tools/test_d1_trace.py entran en regress.py: continuidad, múltiples eventos, overflow, evento fuera de intervalo y conservación del rechazo singular. Los datos anteriores v1/v2 preliminares se conservan en work/ pero no sustituyen la tabla final. No hubo A/B que compare optimizaciones del juego; esta entrega mide y deja la puerta roja.

## A/B sin traza: sin OAM ampliada, con `SPR_OAM` y con el banco G3 (2026-10-06, revisión)

Mismos replays de estrés, `GDEFS=-DREPLAY -DBENCH`, sin `D1TIMER`/`D1TRACE`;
WinUAE cycle-exact (KS 1.2, OCS PAL, `tools/shot.ps1 -Exact` con copias
privadas por slot), lectura `tools/game_read.py --auto`. Capturas en
`work/st_{back,sprites}_{nooam,oam,g3}/bench.png`.

| escenario | build | fotos perdidas | racha máx. | `level_frame` máx. | total medio |
|---|---|---:|---:|---:|---:|
| stress_back | `-DNOOAM` | 145 / 4126 = 3,51 % | 3 | 55,1 % | 46,2 % |
| stress_back | `SPR_OAM` | 713 = 17,28 % | 48 | 83,1 % | 56,3 % |
| stress_back | `SPR_OAM` + `SPR_BANK` (G3) | 712 = 17,26 % | 48 | 83,1 % | 56,3 % |
| stress_sprites | `-DNOOAM` | 0 / 1914 | 0 | 53,5 % | 40,9 % |
| stress_sprites | `SPR_OAM` | 99 = 5,17 % | 10 | 86,6 % | 51,0 % |
| stress_sprites | `SPR_OAM` + `SPR_BANK` (G3) | 99 = 5,17 % | 10 | 86,9 % | 51,0 % |

- **El banco G3 no cuesta nada por frame** (solo carga al arrancar);
  todavía no dibuja nada, así que esto no mide G5.
- **El derrumbe lo pone la OAM ampliada de G8b**: la lógica pasa de 55 % a
  83-87 % del frame en el peor caso y, con O5, al render no le queda tiempo.
  Perfil en Musashi (`tools/m68kprof.py --oracle work/oracle_stress_back.bin
  --sprites`, sin DMA): media 35 000 → 47 000 ciclos; peor frame 58 000 →
  81 700. En ese peor frame (Banzai en pantalla) `finish_oam_write` se lleva
  21 000 ciclos (25,7 %): transcripción literal que lee y escribe `$00-$0B`
  en la RAM emulada en cada ficha.
- **Sin OAM ampliada, `stress_back` tampoco pasa la compuerta** (3,51 %,
  racha 3; objetivo ≤ 0,1 %, racha 1): el pico es `build_mid` en la vuelta
  (165 % en s = 4606), que es lo que tiene que resolver S5.
