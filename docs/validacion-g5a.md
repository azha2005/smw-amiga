# G5a — primer Rex exacto en WinUAE (2026-10-06)

**Prueba descartable, opt-in; puerta visual mínima aprobada.** No es el
asignador G4/G5 definitivo. El coste exclusivo de enemigos por A/B y la
comparación completa G8b/default quedan pendientes: cierre solicitado por
el usuario, sin otra ronda larga. No se activa SPR_OAM por defecto.

## Evidencia y alcance

Banco base SG3F/1: **48/48 poses, 10840 B chip, 5276 B metadata,
16431 píxeles exactos, cero fallos**. Se reconstruye con las trazas SOT1
yi1/normal/spin_kill y Rex legal; no depende del conversor G3 nuevo.

Caso fijo: oráculo **6277**, replay **1132**, cámara **288**, Rex ranura7,
pose20, x167/y160, recorte19×32, dos columnas attached SPR4–7. Las dos
entradas OAM ordenadas se cotejan con la grabación; la selección es offline
y explícita, no un lookup general por frame dentro del juego.

`tools/g5a.py read`: **0/57344 píxeles distintos** en toda la pantalla
256×224. Se compara la OAM exacta reconstruida desde el banco sobre la
captura control del mismo STOPF, incluyendo terreno y Mario.
Capturas cycle-exact: `work/g5a/visual_final.png`, `control_final.png`.
Referencia arriba/Amiga abajo: `work/g5a/compare.png`; diferencias:
`work/g5a/diff.png`. Lectura: `work/g5a_visual_read.log`.

El Rex permanece fijo durante la medida; solo el caso detenido corresponde
a su OAM real. No prueba animación, multiplexado/reuso entre enemigos,
selección de variantes Mario, bob/PF1, clipping ni todo YI1. Mario no tiene
píxeles opacos en las filas del Rex de este caso; el restore usa paleta0,
confirmada por la comparación completa, no generalizable a otros casos.

## Copper y DMA

El banco chip es inmutable. Cada render escribe PT alto/bajo completo al
DATA y POS/CTL en registros del copper; no parchea los controles DMA.
**Inicialización en línea local157, h=$40**, tres líneas antes del Rex160.
Los slots DMA de SPR4–7 ya pasaron; queda después de la recarga automática
del VBlank. Es el armado de un primer objeto detenido de G0, no su protocolo
de reuso PT→header/VSTOP. La inicialización temprana en la cabecera del
frame no mostró Rex: el control DMA podía sobrescribir POS/CTL.

Hay **16 MOVE de PT/POS/CTL + 136 MOVE de color por render**. Los mapas se
insertan después del borrado, junto a `build_mid`, sin modificar su modelo
P51. Segmentos de284B y cabecera+32B son exclusivos de fuentes generadas
en `work/g5a/`; se adaptan los offsets CHG al nuevo stride. La reserva
permite el restore de15 colores. No es una cuota universal para otros
objetos/filas. La pantalla completa exacta valida este caso y su terreno.

Primer bug del arnés corregido: `scroll_init` aún no fija V_BACK cuando
llama build_copper; elegir la tabla de slots por V_BACK dejaba una tabla
vacía. Se elige por el rango de dirección de la lista. Las capturas previas
fallidas se conservan; ninguna se aceptó como positiva.

ReadProcessMemory sobre PID propio confirmó banco chip idéntico al blob y
PT/POS/CTL de la lista; `tools/g5a_dump.py`, `work/g5a/runtime_header.json`.
NPUB>NLOG en un STOPF sin BENCH no era corrupción: el juego sigue
publicando fotos equivalentes después de terminar el replay.

## Medida PAL con DMA real

WinUAE OCS, KS1.2, chip512KB+A501, `cycle_exact=true`, `cpu_speed=real`,
`immediate_blits=false`, sin audio ni bobs. Captura y lectura:
`work/g5a/bench_final.png`, `work/g5a_bench_final_read.log`.
**Sync válida, 14210 ticks/frame, 31 ticks/sello, 1132 frames medidos**.

| Parte | Máximo ticks | % PAL | Replay / oráculo / s |
|---|---:|---:|---|
| level_frame con SPR_OAM | **7024** | **49,4 %** | 996 / 6141 / 257 |
| mspr_draw | 1119 | 7,9 % | 670 / 5815 / 249 |
| columns | 1635 | 11,5 % | 603 / 5748 / 17 |
| build_mid + g5a_apply | 4766 | 33,5 % | 707 / 5852 / 214 |
| total integrado | **13195** | **92,9 %** | 710 / 5855 / 204 |

Total medio **6435 ticks, 45,3 %**. Los máximos pertenecen a frames
distintos; no se suman. Level_frame equivale a70240 ciclos de reloj con
las esperas reales DMA y **no cumple el objetivo≤40 %**. No habilitar G8b
por defecto con estos números. La comparación anterior Musashi43,8 % sin
DMA no es un control A/B de esta medida.

O5:1132 fotos publicadas, **0 omitidas, racha0**, 1VBL repetido,
0frames sin COPER; ISR máximo8291ticks58,3 %. Son agregados de este tramo
corto y Rex fijo, no la compuerta D1 de estrés ni una traza de edad/p99.

Se compilaron controles `empty` y `nodma` con **el mismo stride284 y
cabecera+32**. No se capturaron por el cierre: falta aislar CPU de
construcción y efecto DMA, validar≤8 %, y medir G8b/default completos.
`nodma` añade cuatro lecturas de g_null; contarlo al interpretar su delta.

Memmap concreto: **430280B chip, 228312B slow, cero violaciones**.
Stage2 transitorio228352B chip; se libera al copiarse a slow antes de
reservar scroll230400B y demás bloques. El banco fuente duplicado en
slow es intencional en esta prueba, no diseño del loader definitivo.
`work/g5a_memmap_final.log`; las fuentes normales siguen390704B chip.

## Reproducción y cierre

Desde este worktree con derivados/oráculos autorizados preparados:

~~~sh
export PATH="$TEMP/pyshim:/c/msys64/ucrt64/bin:$PATH" VBCC=/c/Users/JC/vbcc PY=python
sh tools/g5a_build.sh > work/g5a_build.log 2>&1
~~~

~~~powershell
.\tools\g5a_shot.ps1 -Adf work\g5a\visual.adf -Out work\g5a\visual_final.png -Wait 70 -Slot vis
.\tools\g5a_shot.ps1 -Adf work\g5a_control\game.adf -Out work\g5a\control_final.png -Wait 70 -Slot ctrl
.\tools\g5a_shot.ps1 -Adf work\g5a\bench.adf -Out work\g5a\bench_final.png -Wait 70 -Slot bench
~~~

Cada slot usa perfil privado, candado global y solo cierra su PID. Se fijaron las
tres opciones oficiales de pausa en false:
`win32.active_not_captured_pause`, `win32.inactive_pause`,
`win32.iconified_pause`; nombres verificados en
[fuente WinUAE](https://raw.githubusercontent.com/tonioni/WinUAE/master/od-win32/win32.cpp).
Perfil medido en `work/g5a-capture-bench/work/shot.uae`.

~~~sh
python tools/g5a.py read --shot work/g5a/visual_final.png --base-shot work/g5a/control_final.png
python tools/game_read.py --shot work/g5a/bench_final.png --auto
python tools/memmap.py work/g5a/visual.lst
python tools/lint_port.py
python tools/regress.py --baseline tools/baseline_pc.json --level
~~~

Lint y regresión PC final: **RESULTADO: OK**; sin cambiar baselines.
PIC de todos los binarios G5a: cero llamadas/saltos absolutos. Logs:
`work/g5a_lint_final.log`, `g5a_regress_final.log`, `g5a_build.log`.
No conflictos sobre game.s/scroll.s/game_build.sh: permanecen sin cambios;
no se editaron conversores G3, lógica ni documentos de estado.

**Al retomar:** capturar controles empty/nodma ya compilados con el perfil
privado, aislar coste exclusivo y comparar G8b/default. Después el
asignador/fotos reales y reuso G0; conservar la prueba descartable separada.
No integrar esta rama como renderer de juego por defecto.
