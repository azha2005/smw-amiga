# G0: reuso de sprites medido a 256 px

2026-10-05. A500 PAL, OCS, 512 KB chip + A501, KS 1.2. WinUAE con
`cycle_exact=true`, `cpu_speed=real`, `immediate_blits=false` y los demas
valores de `tools/shot.ps1 -Exact`. No se midio en modo rapido.

**La recarga por copper funciona con poses compartidas**, si los punteros
se escriben en la linea anterior al VSTOP y POS/CTL despues de la lectura
DMA del control. El encadenado DMA tambien funciona con **gap 1**. El banco
comprueba los pixels de ambos objetos, no solo que una franja aparezca.

El plazo del modelo de `estudio-g1-g0.md` era demasiado optimista: escribir
los 16 MOVE de PT de ocho canales desde h=$00 de la linea VSTOP ya pierde
tres parejas, incluso sin cargas de color. Desde h=$D8 anterior tampoco
entra todo. G2 debe reservar una ventana anterior y comprobar su coste con
los colores reales; no puede dar por disponible todo el borrado.

## Banco y comprobacion

`player/bench_g0.s` ejecuta listas y flujos sinteticos generados por
`tools/g0bench.py`. No usa assets ni ROM de SMW. Seis planos DPF, DIW
`$2CA1`/`$0CA1`, fetch `$40`/`$C0`, modulo -34: los mismos fetch y ancho del
juego a 256 px. Todos los planos hacen DMA; PF1 muestra el indice 1 y los
otros planos estan a cero. BPLCON2=$24 pone los sprites delante.

Cada caso arma **las cuatro parejas adosadas, SPR0-7**, con dos objetos de
16x4. El primero esta en x=8,64,120,176; el segundo en x=24,80,136,192. Cada
fila tiene un patron distinto de cuatro bits: identifica tanto el puntero
como un desplazamiento, una primera fila perdida o un canal que dejo de
estar adosado. Se comprueban **512 pixels por caso** y se buscan pixels de
sprite sobrantes en toda la banda de 256 px. SPR7 aparece correctamente.

En la suite compartida todas las columnas reutilizan **el mismo flujo para
canales pares y el mismo para impares**. Sus encabezados originales llevan
una posicion falsa (y=250, x=0). El copper les pone X/Y distintos mediante
POS/CTL. Los patrones y posiciones correctos demuestran que el control DMA
no vuelve a sobrescribir esos registros antes del segundo objeto en la
secuencia medida.

La variante cargada pone, en cada linea, **8 MOVE de color desde h=$D8 de la
linea anterior + 6 MOVE desde h=$80**, con sus WAIT. Cambian registros que
no usa el fondo. Se conservan todos los fetch de planos y el DMA de los ocho
canales: no se libera ancho de banda al hacer invisible la carga de color.

El lector toma el centro del pixel x2 (P57), con origen (131,70), y valida
las barras binarias $A55A y ticks/frame PAL. Las puertas requieren los
controles positivos y que los controles negativos pierdan pixels **solo en
el segundo objeto**. Un PNG negro, mal alineado o anterior a publicar las
barras falla. `--expect-all` tambien falla ante cualquier caso tardio.

## Resultados de punteros con encabezado individual

PT completo = PTH+PTL en cada canal: **16 MOVE para las cuatro parejas**.
El segundo objeto empieza en VSTOP+1; VSTOP es la primera linea despues del
ultimo pixel del primero. El primer objeto tiene 0 errores en todos los
casos. Tabla: pixels erroneos del segundo, sobre 256.

| Inicio de PT | Sin carga | Cargado |
|---|---:|---:|
| Linea anterior, h=$80 | 0 | 0 |
| Linea anterior, h=$C0 | 0 | 0 |
| Linea anterior, h=$D8 | 64 | 256 |
| Linea VSTOP, h=$00 | 192 | 256 |
| Linea VSTOP, h=$10 | 256 | 256 |
| Linea VSTOP, h=$20 | 256 | 256 |

La cadena DMA con gap 1, cargada, tiene **0 errores en ambos objetos y 0
pixels sobrantes**. Se mantuvo como control independiente en esta suite.
El banco incluye una suite exploratoria de gaps 0,2,4,8,17, pero **no se
capturo**: la evidencia de encadenado se limita a gap 1.

## Resultados de poses compartidas

Se escriben PT en la linea anterior; POS+CTL por canal en VSTOP, despues de
que el DMA pueda leer el encabezado. Son **32 MOVE en total**, 8 por pareja.
Tabla: errores del segundo objeto, sobre 256; el primero tiene siempre 0.

| Inicio de PT / inicio de POS+CTL | Sin carga | Cargado |
|---|---:|---:|
| Anterior $80 / VSTOP $38 | 0 | 0 |
| Anterior $C0 / VSTOP $38 | 0 | 0 |
| Anterior $D8 / VSTOP $38 | 57 | 252 |
| Anterior $80 / VSTOP $80 | 0 | 0 |
| Anterior $C0 / VSTOP $C0 | 0 | 0 |

El primer caso se repite al final de cada grupo y vuelve a tener 0 errores.
Son **10 casos exactos y 2 controles negativos**, incluyendo las repeticiones.
Los casos PT tardios dejan errores de bits/filas; no se los acepta por tener
la silueta cerca de donde corresponde.

El cambio de fondo azul indica el fin de PT; el verde, el de POS/CTL. Con
carga y POS/CTL desde VSTOP $38, el verde aparece por primera vez en x=0 de
la linea siguiente; el segundo objeto aun asi sale exacto. Esos marcadores
solo acotan el cambio **visible** del fondo: no son una lectura de hpos en
el borrado ni una garantia de plazo para otra distribucion de columnas.

## Coste CPU del encadenado

Se copia chip -> chip una carga de **1408 B** (1400 B del maximo de G1,
redondeado a 44 grupos de 32), con MOVEM d0-d7 desenrollado y avance de
destino por LEA. Se toman maximos de 32 repeticiones sincronizadas: linea 96
con los seis planos activos, linea 280 en el borrado vertical. La rutina
vacia mide el arnes en ambas condiciones. El reloj CIA-B corre durante el
DMA; no se usa un factor teorico uniforme (P96).

| Captura | Ticks/frame | Vacio / copia activa | Neto activo | Vacio / copia VBlank | Neto VBlank |
|---|---:|---:|---:|---:|---:|
| PT | 14210 | 55 / 1117 | 1062 = **7,47 %** (~1,50 ms) | 41 / 724 | 683 = **4,81 %** (~0,96 ms) |
| Compartido | 14211 | 56 / 1125 | 1069 = **7,52 %** (~1,50 ms) | 31 / 734 | 703 = **4,95 %** (~0,99 ms) |

Sin restar el arnes, el maximo activo es **7,92 %**. Este es el coste de la
copia, sin asignar columnas, parchear encabezados ni construir la lista.
La estimacion de G1 de 4,5 % no es valida como presupuesto del peor caso
durante la pantalla. Ejecutar la copia en VBlank mejora el coste pero
necesita un presupuesto y plazo propios. El copper sigue siendo la opcion
principal; copiar flujos de algunos objetos queda como alternativa acotada.

## Evidencia y comandos

Archivos regenerables, no versionados (R9), en `work/` de este worktree:

- `bench_g0_pt.png`, `bench_g0_pt_compare.png`, `bench_g0_pt.json`,
  `bench_g0_pt_meta.json`, `g0_pt_read.log`.
- `bench_g0_shared.png`, `bench_g0_shared_compare.png`,
  `bench_g0_shared.json`, `bench_g0_shared_meta.json`, `g0_shared_read.log`.

Los PNG `*_compare.png` apilan referencia sintetica arriba y WinUAE debajo;
el fondo de referencia es uniforme y las barras solo existen en la captura.
La puerta compara todos los pixels de los sprites y busca sobrantes.

Desde la raiz, bash MSYS2 **-c** (no -lc), entorno de la PC:

```bash
export PATH=/c/msys64/ucrt64/bin:/usr/bin:/c/Users/JC/AppData/Local/Temp/pyshim:$PATH
export PY=python VBCC=/c/Users/JC/vbcc
python tools/g0bench.py build --suite pt
cp work/bench_g0_data.json work/bench_g0_pt_meta.json
$VBCC/bin/vasmm68k_mot.exe -Fbin -m68000 -no-opt -I player -I work -o work/bench_g0_pt.bin player/bench_g0.s
$VBCC/bin/vasmm68k_mot.exe -Fbin -m68000 -no-opt -I player -o work/boot.bin player/boot.s
python tools/mkadf.py --boot work/boot.bin --stage2 work/bench_g0_pt.bin --out work/bench_g0_pt.adf
```

PowerShell, una instancia por vez:

```powershell
.\tools\g0shot.ps1 -Adf work\bench_g0_pt.adf -Out work\bench_g0_pt.png -Wait 25
```

Volver a bash:

```bash
python tools/g0bench.py read --shot work/bench_g0_pt.png --meta work/bench_g0_pt_meta.json
# PUERTA: OK (5 positivos, 8 negativos con primer objeto intacto)
python tools/g0bench.py build --suite shared
cp work/bench_g0_data.json work/bench_g0_shared_meta.json
$VBCC/bin/vasmm68k_mot.exe -Fbin -m68000 -no-opt -I player -I work -o work/bench_g0_shared.bin player/bench_g0.s
python tools/mkadf.py --boot work/boot.bin --stage2 work/bench_g0_shared.bin --out work/bench_g0_shared.adf
```

```powershell
.\tools\g0shot.ps1 -Adf work\bench_g0_shared.adf -Out work\bench_g0_shared.png -Wait 25
```

```bash
python tools/g0bench.py read --shot work/bench_g0_shared.png --meta work/bench_g0_shared_meta.json
# PUERTA: OK (10 positivos, 2 negativos con primer objeto intacto)
python tools/asmlint_port.py player/bench_g0.s
python tools/lint_port.py
python tools/regress.py --baseline tools/baseline_pc.json
```

`g0shot.ps1` conserva el perfil Exact del capturador del proyecto, inicia
Hidden, localiza el HWND por PID y habilita su dibujo sin foco al fondo de
las ventanas. PrintWindow de una ventana completamente oculta dio negro;
esa captura fue rechazada por el lector. Solo cierra su propio PID. Usa el
candado compartido si existe. En esta sesion se detuvieron capturas nuevas
al detectar SX la desaparicion de otras instancias: queda pendiente resolver
la convivencia de WinUAE, no se ejecuto la suite adicional de gaps.

## Alcance para G2 y limites

- **Medido:** cuatro columnas adosadas, ocho canales, posiciones distintas,
  4 filas identificables, gap 1, PT de dos palabras por canal y poses
  compartidas corregidas por POS/CTL. Carga de color sintetica de 8+6 MOVE.
- **No medido:** PT de una sola palabra en banco de 64 KB, limites finos de
  cada ranura DMA, POS/CTL escritos antes de su lectura DMA, otras fases de
  scroll, audio DMA, blitter concurrente, sprites de 32/64 filas, distribucion
  real de colores de todo YI1 y armado CPU del multiplexor. La medida de copia
  lee/escribe chip y el codigo del banco esta en chip.
- G2 puede partir de **PT temprano en la linea anterior y POS/CTL despues del
  control DMA**, con la cadena gap 1 como alternativa. Tiene que demostrar
  que encuentra esas ventanas en el copper real; este banco no da una cuota
  universal de MOVE libres ni completa G5/G7.
- Armar un canal detenido solo cambiando PT durante el display no mostro
  sprites en el primer arnes. La inicializacion ahora escribe POS/CTL y pone
  el puntero directamente al DATA; el reuso medido apunta al encabezado para
  que lo lea el DMA en VSTOP. No confundir esas dos operaciones.
- `DIWSTRT=$2CA1` usa **hx0=$A0** para sprites, como `mspr68k.s`; usar $A1
  desplazo todos los patrones un pixel y el comparador lo rechazo. No se
  corrige moviendo el recorte del lector.

El blob sintetico mayor medido tiene 15176 B de chip y la copia temporal
2816 B; el stage2 mayor medido ocupa 18752 B. No cambia el mapa del juego.
