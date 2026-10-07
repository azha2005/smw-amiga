# G2T-A — contrato candidato y puerta horizontal offline

2026-10-07. **Propuesta de tarjeta**, entregada por G2T. El contrato
temporal todavía no está aprobado ni implementado. Este documento define
lo que sustituiría A3/A5/C2 de G5a-bis; no modifica sus puertas actuales.
No iniciar el juego C/68000 ni G5 B/C hasta fijar este contrato y pasar la
nueva fase A. Modelo previsto: GPT-6.1 Sol high, worktree propio.

## 0. Motivo, alcance y parada

Leer `informe-g2t-1007.md`, `instrucciones-revision-1007.md` §2,
`diseno-9.2.md` §1-§3, `medida-g0.md`, y P35/P39/P42/P51/P59/P97/P108.

A5 genera 59318 ventanas vacías; cambiar solo la elección de variante
deja 1261 frames sin plan. Las recargas entre filas funcionan en el banco
sintético cycle-exact, pero faltan slots certificados para todas las
cargas reales y el protocolo completo PT/POS/CTL. Un plan lógico no
certifica hardware. Esta tarjeta implementa y calibra **solo el modelo
offline**; entrega instrucciones nuevas para B/C si pasa.

Se conserva un Rex elegido por menor `sy+origen_y`, empate slot; los
demás se cuentan como sin_destino. No ampliar a G4/G6, bobs u otro banco.
**Parar** si hace falta cambiar los flujos G3, exceder memoria, aproximar
color, saltarse una reserva o aflojar una puerta. Tras tres intentos
distintos sin cumplir una puerta, entregar el bloqueo con evidencias.

## 1. Contrato candidato (cambio explícito de A3/A5/C2)

1. **A3-T:** probar el directorio en su orden, preservando el filtro A3
   original por fila. Elegir la primera variante compatible **con plan
   temporal válido**. La variante inicial A3 se informa por separado.
   Sin candidato: contador sin_variante_temporal, no ocultar ni recolorear.
2. **A5-T:** cada índice COLOR17..31 tiene usos con color y envolvente
   inclusiva `[x_primero,x_último]` en cada fila. Conservar todos los usos
   de Mario y Rex, también los ocluidos; no usar prioridad para liberar
   colores. Una transición solo puede ejecutarse después del último
   píxel del color anterior y antes del primero del siguiente. Paleta
   inicial/restauraciones = `R_PAL` de la misma foto, nunca paleta0 fija.
3. Para esta primera puerta, no cambiar un índice a dos colores distintos
   dentro de la misma fila (lo excluye A3). Usar el hueco entre filas:
   un sufijo tardío después de la última carga real de `build_mid`.
   La ausencia de píxeles visibles no borra el filtro conservador A3;
   informar testigos fuera de pantalla por separado.
4. **C2-T:** presupuestar un WAIT + hasta ocho MOVE + el salto existente
   de tres MOVE. Esperas, punteros y salto cuentan en el timeline. No dar
   por disponible una línea por `h<=E2-8n`; esa regla antigua no modela
   este caso. La tabla de disponibilidad sale de la ejecución real y
   de las calibraciones. Nunca convertir h>$CE a x mediante una fórmula
   no medida. Tampoco escribir el sufijo inmediatamente si queda antes
   del último píxel de Mario/Rex.
5. En PAL255, **reemplazar** el WAIT tardío del sufijo por FFDF antes de
   cruzar a256, sin otro WAIT vertical255 detrás; el comienzo del segmento
   siguiente consume NOP en lugar de volver a esperar255. Es una parte
   nueva del contrato: exigir la calibración de §3 y después todas las
   listas reales. No mantener la barrera en dos lugares.
6. PT completo alto+bajo, POS/CTL completos y ATTACH; banco inmutable.
   Cada plazo de armado necesita un caso medido con cargas reales. G0
   mide reuso PT anterior $80/$C0 y POS/CTL desde $38 de VSTOP; no
   extrapolar ese plazo al primer armado ni convertir ocho recargas de
   color en una garantía para16 escrituras de control.
7. Datos = foto O5, incluido Mario ya dibujado en su buffer asociado,
   paleta y cámara; render sin RAM viva. Derivar las envolventes desde
   ese flujo y cotejarlas con SNES/VRAM dinámica. Las reservas de la nube
   del giro y partículas que comparten la paleta permanecen incluidas.
8. Selección por forma/pose/paleta/cámara/slots, nunca por frame o nombre
   de replay. Prioridad OAM, pertenencia y todos los píxeles se verifican
   independientemente; una variante viable no autoriza otra prioridad.

## 2. Entorno, evidencia de partida

Entorno de `reglas-ola-pc.md`; `tools/wt_new.sh <id>` desde el árbol
coordinador. Preparar/copiar los derivados G3 explícitamente, ya que
wt_new excluye `work/g3`.

```sh
export PATH="$TEMP/pyshim:/c/msys64/ucrt64/bin:$PATH" VBCC=/c/Users/JC/vbcc PY=python
python tools/lint_port.py
python tools/regress.py --baseline tools/baseline_pc.json --level
sh tools/oam68k_gate.sh
python tools/test_g2t.py
python tools/test_g5ref.py
```

Esperado: RESULTADO: OK, OAM68K: OK, diez/ocho tests OK. Si no, parar.
Derivados necesarios: `work/g3/bank.{idx,dma}`, trazas
`oam_{yi1,normal,spin_kill}.trace`, respectivos `oracle_*_oam.bin`,
`cc/{gfx32,mario_pal}.bin`, `yi1_s.dat`, ROM local. R9: todo lo generado
dentro de `work/`; no assets en git, no baselines cambiadas, no push.

Repetir §1/§2 del informe con los comandos exactos allí. G5 original debe
seguir fallando y su resumen conservar SHA256 `3d254a01…4722f8b7`.
G2T audit debe informar 3404 frames, 0 sin plan en su cota horizontal,
189 sin plan en la cota antigua C2; hardware_validado=False.
Si difiere, diagnosticar antes de cambiar el modelo.

## 3. Calibración de partida y ampliación obligatoria

Estos comandos ya se probaron (el arnés genera el fuente en work):

```sh
python tools/g2t_cal.py build --repair-wrap --out work/g2t_cal_wrap3.i
$VBCC/bin/vasmm68k_mot.exe -Fbin -m68000 -no-opt -I player -I work -o work/g2t_cal_wrap3.bin work/g2t_cal_wrap3.s
$VBCC/bin/vasmm68k_mot.exe -Fbin -m68000 -no-opt -I player -o work/boot.bin player/boot.s
python tools/mkadf.py --boot work/boot.bin --stage2 work/g2t_cal_wrap3.bin --out work/g2t_cal_wrap3.adf
```

```powershell
& C:\Users\JC\Downloads\sma\winuae_lock.ps1 .\tools\shot.ps1 -Exact -Adf work\g2t_cal_wrap3.adf -Out work\g2t_cal_wrap3.png -Wait 80
```

```sh
python tools/g2t_cal.py read --shot work/g2t_cal_wrap3.png --meta work/g2t_cal_wrap3.json --require-positive
```

Metadata `.json` y resultado `.result.json` separados; barras A55A y
ticks PAL entre14000 y14500. Control de ocho MOVE sin transición exacto,
negativo $C0 con27 errores de sprite y fondo intacto; colores normales y
cruce reparado deben tener0 errores. Comparación visual apilada y leída.

**Después**, extender este arnés con datos sintéticos que reproduzcan
las secuencias reales extremas: borrado14 MOVE, hasta12 cargas,
último WAIT y MOVE encadenados, salto3 MOVE, último píxel255/primero0,
cruce255/256 y primer armado/reuso de cada pareja. Los valores sintéticos
no necesitan assets. Cambiar X de Mario/Rex, incluir paleta de estrella,
índices distintos y más de un cambio; caso temprano/tardío negativo con
el objeto anterior intacto. No extrapolar los actuales tres MOVE desde
$C8 a cualquier secuencia. Registrar por caso el punto de escritura,
su ventana, píxeles y controles; medir con todos los DMA habilitados.

Puerta: cada combinación utilizada por el modelo tiene evidencia exacta
y un control negativo que confirme que el comparador detecta el plazo.
Caso no medido = slot no certificado. Si falla un positivo, **parar esa
configuración**, no introducirlo en la tabla como válido.

## 4. Modelo horizontal nuevo, separado de la referencia original

Ficheros acotados: nuevo `tools/g2t_ref.py`, `tools/test_g2t_ref.py`,
soporte de timeline en `tools/scrollsim.py` y calibraciones en
`tools/g2t_cal.py`; conservar `g5ref.py` sin cambios de A3/A5.

1. Leer las tres trazas mediante `g5ref.read_trace`. Ejecutar A2 original.
2. Implementar y comprobar envolventes de Mario desde los flujos de su
   foto contra `mario_pixels`/VRAM dinámica: **0 diferencias** en los
   registros de las tres trazas. Respetar clipping, flips y partículas.
3. Ejecutar `build_mid` real para las cámaras de cada foto y ambas listas;
   conservar cargas y offsets. Publicar el timeline completo de WAIT,
   MOVE, PT/POS/CTL, salto y borrado siguiente usando solo slots medidos.
4. Enumerar variantes A3 compatibles en orden; construir ventanas de usos
   exactos y plan con capacidad física. Una búsqueda voraz fallida no
   demuestra imposibilidad: conservar el testigo y probar su ventana
   completa antes de proponer otro banco. Sin plan sigue siendo rojo.
5. Validar colores por píxel desde la fuente SNES, índice DMA, control
   sprite y timeline; validar además **toda la capa1** contra el control
   sin sufijo. No sustituirlo por conjuntos de colores reservados.
6. Tests sin assets: transición negro/blanco contigua, Mario vecino y
   restaura paleta real, sprite fuera de pantalla, orden de directorio,
   sin slot/sin ventana, capacidad tras última carga y barrera255 única.
   Engancharlos en regress y comprobar que aparecen en su log.

El nuevo CLI a implementar debe aceptar los mismos `--trace`, `--bank`
y `--out` del audit. Su invocación final será:

```sh
python tools/g2t_ref.py --trace work/oam_yi1.trace=work/oracle_yi1_oam.bin --trace work/oam_normal.trace=work/oracle_normal_oam.bin --trace work/oam_spin_kill.trace=work/oracle_spin_kill_oam.bin --bank work/g3/bank --out work/g2t_ref
```

**Puerta nueva A-T:** los3404 frames con Rex procesados, 0 A2/envolventes
distintas, 0 sin_variante_temporal, 0 sin_plazo, 0 errores_color, 0 errores
de capa1, 0 prioridad_distinta; sin_destino informativo y listado. Casos
fuera de alcance/no calibrados hacen fallar la puerta, no se omiten.
F6150 es testigo visible adicional; f5811 conserva su diagnóstico A5.
≥12 PNG repartidos por las tres trazas, con fuente arriba/simulación
abajo, incluyendo reservas compartidas, sentidos, clips y barrera255.
El coordinador repite esta puerta y mira todas las imágenes.

## 5. Presupuestos, cierre y condición para B/C

Banco≤65536 chip, tablas≤98304 slow, trabajo≤32768 slow; fotos de
enemigos≤2376 slow. Propuesta de reserva24 KiB para23648 B de trabajo,
detallada en el informe. No implementar ninguna tabla que supere estos
límites ni copiar intervalos grandes a cada una de las tres fotos.
Un WAIT+8 MOVE =36 B de extensión por segmento, +16128 B chip en dos
listas, en lugar de14336; comprobar al implementar replay/vivo con
memmap (estimación actual471856/483384 B chip). La barrera sustituye el
WAIT, no añade uno. No ampliar silenciosamente el máximo de recargas.

Entregar informe con logs, metadatos de calibración, tiempos/píxeles,
listas completas de casos y presupuestos medidos. Red de seguridad
antes del commit, archivo textual del PROXIMO y estados actualizados
según ROADMAP§7. Un paso por commit; lo que no pase se entrega WIP.

**B/C necesitan instrucciones nuevas**, escritas después de pasar A-T:
equivalencia PC/68000 del plan, coste capture≤~3000 ciclos, render G4/G5
≤8%, comparación de pantalla entera0/57344 en cada captura y A/B D1 con
control. L-OAM≤40%/estrés y fidelidad50Hz conservan sus puertas.
