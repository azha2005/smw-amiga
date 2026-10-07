# G2T — revisión temporal del banco G3

2026-10-07. Ejecutada por el coordinador, sin subagentes, en
`wt/g2t-1007`, partiendo de `70b25a8`. Revisión autorizada por el usuario
(«hace g2t vos»), según `instrucciones-revision-1007.md` §2.

**La vía recomendada es conservar el banco inmutable y modelar las
recargas entre píxeles de filas sucesivas, con selección de la primera
variante que tenga un plan temporal válido.** Hay evidencia cycle-exact
de un sufijo sintético de ocho recargas, y un fallo/reparación del cruce
255/256. No hay todavía una puerta G5 verde ni un dibujador de enemigos.
La entrega G2T es este diagnóstico, herramientas reproducibles y el
contrato candidato de `instrucciones-g2t-a.md`.

## 1. Referencia original preservada

Se importan de `8fe712d` únicamente `tools/g5ref.py` y sus ocho tests.
No se modifica A3 (primera compatible) ni A5 (líneas enteras libres).
Repetición en este worktree:

```sh
export PATH="$TEMP/pyshim:/c/msys64/ucrt64/bin:$PATH" VBCC=/c/Users/JC/vbcc PY=python
python tools/g5ref.py --trace work/oam_yi1.trace=work/oracle_yi1_oam.bin --trace work/oam_normal.trace=work/oracle_normal_oam.bin --trace work/oam_spin_kill.trace=work/oracle_spin_kill_oam.bin --bank work/g3/bank --out work/g5ref_repeat
sha256sum work/g5ref_repeat/resumen.json
```

Sale 1, como debe hacerlo ante la puerta roja. SHA256 del resumen:
`3d254a011312cfa88f6eb6e4ae2d4519c427a251469b0cdd16a5362f4722f8b7`,
idéntico al de G5a-bis y su repetición anterior. A2=0 diferencias;
sin_variante=0; ventanas vacías=59318. Log: `work/g5ref_repeat.log`.

El testigo f5811 sigue siendo variante 49, slot 7, sy176, origen Y=-8:
COLOR17 negro en y168 y blanco en y169, ventana A5 `[169,168]`.
**En ese frame el Rex está fuera del recorte horizontal**, sx283. La
reserva conservadora por fila le genera plazos, pero no tiene píxeles
visibles que prueben ese cambio. Esto no invalida el fallo A5; exige
también un testigo visible. La auditoría encuentra f6150, variante 59:
índice 3 usado por Mario hasta `(119,169)` y por Rex desde `(254,170)`.
Su intervalo temporal no está vacío aunque no haya una línea entera libre.

## 2. Tres alternativas, sin sustituir silenciosamente A3/A5

`tools/g2t_audit.py` recorre las tres trazas y todas las variantes A3
compatibles de cada Rex elegido. No cambia pertenencia, selección del
objeto ni reservas de Mario. Salidas en `work/g2t/`, log
`work/g2t_audit.log`:

```sh
python tools/g2t_audit.py --trace work/oam_yi1.trace=work/oracle_yi1_oam.bin --trace work/oam_normal.trace=work/oracle_normal_oam.bin --trace work/oam_spin_kill.trace=work/oracle_spin_kill_oam.bin --bank work/g3/bank --out work/g2t
```

| traza | frames con Rex | primera variante con ventana vacía | otra sin vacías | ningún plan A5 | sin plan en cota horizontal de 8 MOVE | sin plan con búsqueda y cota C2 antigua |
|---|---:|---:|---:|---:|---:|---:|
| yi1 | 2288 | 1505 | 644 | 861 | 0 | 131 |
| normal | 661 | 477 | 222 | 255 | 0 | 44 |
| spin_kill | 455 | 292 | 147 | 145 | 0 | 14 |

**Selección con plazos A5:** rescata los 1013 frames conocidos, pero
1261 siguen sin plan. No es solución suficiente por sí sola.

**Remapeo estable:** ensayo deliberadamente fuerte: un índice distinto
por color en toda la pose, evitando además reservas diferentes de Mario
en las filas anterior/siguiente. Hay asignación en 2409 frames y no la
hay en 995 (751/169/75); ningún límite de búsqueda se alcanzó. No prueba
imposible cualquier remapeo temporalmente estable: descarta esta
restricción suficiente como solución completa. Serializar sus éxitos da
255 descriptores, 22 formas, 56864 B DMA y 69218 B tablas. Es un banco
**incompleto de ensayo**, no las 48 formas/2593 peticiones/ocho paletas
del contrato G3. Su tamaño dentro del presupuesto no autoriza reemplazar
el banco. Sus flujos se decodifican y verifican contra la fuente SNES;
138631 píxeles verificados; PNG inspeccionado: `work/g2t/estable.png`.

**Ventanas horizontales:** incluir la línea del último uso, escribiendo
después de sus píxeles, elimina las ventanas vacías en la cota lógica y
permite planes de hasta ocho MOVE por línea en los 3404 frames. La
simulación comprueba colores en todos los usos reservados de los planes
que pasan la cota C2 (3215 frames, 0 usos de color distintos). Esos ceros
**no son sin_plazo/errores_color del
hardware**. Las listas reales de `build_mid` se ejecutan en Musashi con
`VIS=256, SPRITES`; se leen sus últimos WAIT, MOVE restantes y salto.
La capacidad C2 `h <= E2-8n` sigue dejando 189 frames sin plan del
algoritmo probado. No es prueba de imposibilidad: C2 es una cota antigua,
la colocación es voraz, omite el WAIT añadido y no mide todos los slots.

En f5811/y168 la última carga real usa WAIT h=$B0, queda un MOVE y el
modelo medido de `scrollsim` sitúa la instrucción siguiente en x223.
El modelo no extrapola h>$CE. En f6150/y169 no hay cargas intermedias;
el sufijo queda libre antes de x0. Estos casos requieren un WAIT tardío,
no escribir inmediatamente tras la carga: se corrompería Mario/Rex.

15 frames de normal y 145 de spin_kill tienen cámara Y distinta de 192.
Los sprites/reservas se calculan con su cámara real; la capacidad leída
corresponde al scroll actual, cuyo fondo todavía fija Y=192. Antes de
integrar S8 hay que repetir esa parte del modelo y la puerta visual.

## 3. Calibración propia, WinUAE cycle-exact

`tools/g2t_cal.py` genera datos sintéticos y reutiliza el arnés
`player/bench_g0.s` en un fuente generado dentro de `work/`. No toca el
juego ni usa ROM/assets. DIW=$2CA1/$0CA1, DDF=$40/$C0, seis planos DPF,
los ocho canales DMA activos. Cuatro parejas attached en x=0/64/128/240;
sus cuatro filas usan el mismo índice 1, alternando rojo/blanco. Así se
prueban tanto el último píxel x255 como el primero x0 de la fila siguiente.

Cada segmento contiene dos WAIT de borrado + siete MOVE PF1, una carga
desde h=$B0 (un MOVE) o $C8 (tres MOVE), el WAIT y las recargas del
sufijo, más los tres MOVE reales COP2LC/COPJMP2. Se reponen registros en
la línea siguiente. Esto mide **ese sufijo**, no todas las distribuciones
de 12 cargas ni borrados de 14 MOVE, ni los plazos de armar otro sprite.

```sh
python tools/g2t_cal.py build
$VBCC/bin/vasmm68k_mot.exe -Fbin -m68000 -no-opt -I player -I work -o work/g2t_cal.bin work/g2t_cal.s
python tools/mkadf.py --boot work/boot.bin --stage2 work/g2t_cal.bin --out work/g2t_cal.adf
```

```powershell
& C:\Users\JC\Downloads\sma\winuae_lock.ps1 .\tools\shot.ps1 -Exact -Adf work\g2t_cal.adf -Out work\g2t_cal.png -Wait 80
```

```sh
python tools/g2t_cal.py read --shot work/g2t_cal.png
```

| caso | errores de sprites en las 4 filas (256 píxeles) | errores de fondo |
|---|---|---:|
| control, ocho MOVE sin transición | 0/0/0/0 | 0 |
| negativo: recarga temprana h=$C0 | 9/9/9/0 | 0 |
| h=$D0, un MOVE tras carga $B0 | 0/0/0/0 | 0 |
| h=$D0, ocho MOVE tras tres cargas $C8, color primero | 0/0/0/0 | 0 |
| igual, color último | 0/0/0/0 | 0 |
| h=$DE, ocho MOVE, color último | 0/0/0/0 | 0 |
| h=$D0, cruce PAL255 sin cambio de barrera | 0/0/0/64 | 0 |

El caso cargado de ocho MOVE pasa donde la cota C2 anterior permitiría
solo tres, aun sin contar los tres MOVE posteriores a su WAIT $C8.
Por eso C2 no debe convertirse en una sentencia de imposibilidad física.

**Cruce PAL255:** el sufijo puede atravesar h=$DE antes de saltar al
segmento siguiente. Si allí se espera FFDF como antes, la barrera llega
tarde y falla. Ensayo nuevo, separado: consumir FFDF antes del sufijo en
la propia línea255 **sustituyendo** el WAIT tardío, y sustituir las dos
esperas de su segmento siguiente por NOP. Un ensayo intermedio que
conservaba otro WAIT vertical255 después de FFDF falló en la fila256
(64 píxeles). Se descartó; la variante final usa una única barrera.
`--repair-wrap` genera la alternativa final, sin cambiar el juego:

```sh
python tools/g2t_cal.py build --repair-wrap --out work/g2t_cal_wrap3.i
$VBCC/bin/vasmm68k_mot.exe -Fbin -m68000 -no-opt -I player -I work -o work/g2t_cal_wrap3.bin work/g2t_cal_wrap3.s
python tools/mkadf.py --boot work/boot.bin --stage2 work/g2t_cal_wrap3.bin --out work/g2t_cal_wrap3.adf
```

Captura por el mismo candado con `-Exact`, ADF/PNG `g2t_cal_wrap3`;
lectura con `--meta work/g2t_cal_wrap3.json --require-positive`.
**Resultado final: 0/0/0/0 errores en el cruce y en los otros cinco casos
positivos; negativo temprano9/9/9/0; fondo0 en todos.** A55A correcto,
14210 ticks/frame PAL (primera tanda14209). Son dos capturas con fallo
del cruce y una final exacta; los controles se repiten en cada tanda.
Los PNG `*_compare.png` apilan esperado arriba / captura abajo y se
inspeccionaron visualmente. Logs: `work/g2t_cal_read.log`,
`work/g2t_cal_wrap_read.log` (ensayo descartado) y
`work/g2t_cal_wrap3_read.log`; metadata sintética `.json` y resultados de
captura `.result.json`, separados para permitir repetir la lectura.

## 4. Presupuesto y contrato candidato

Banco G3 original intacto: DMA64528 / tablas72724 B. SHA256 DMA
`4dd51fcc9bd03edd9afaad0b0a2459af7113259f43caa8c0789ff457a839f4fc`,
tablas `8589b85a0e7368333b91b26d42a4f5cec7febbecc918bbebfb0743ce6f689cd2`.

Un sufijo con **un WAIT + ocho MOVE** necesita 36 B, no los 32 B de la
tarjeta anterior. Dos listas ×224: +16128 B chip (**estimado**, sin
implementar). Sobre los mapas actuales: replay471856 B, vivo483384 B,
margen vivo40904 B; repetir memmap al implementarlo. No cabe presupuestar
segundo PF1/audio antes de C2/C4.

Tablas de máscara opcionales11904 B: total84628 ≤98304. Los intervalos
por índice/fila se calculan desde los sprites de Mario **de la foto O5**,
ya inmutables, y desde los flujos G3; no consultar RAM viva ni almacenar
una tabla por replay. Propuesta de trabajo slow: envolventes/color
13440 B + máscaras de presencia448 + plan224×36=8064 + cantidades224 +
capacidades448 + scratch1024 = **23648 B estimados**, reserva24 KiB
≤32768. Las fotos de enemigos conservan su presupuesto2376 B separado.
La equivalencia de Mario SNES/flujo de la foto es una puerta nueva, no
una propiedad que se dé por hecha con estas cifras.

El contrato candidato está detallado en `instrucciones-g2t-a.md`:
primera variante A3 compatible con plan válido en un timeline calibrado;
intervalos X/Y conservadores, COLOR inicial de la paleta de esa foto;
PT/POS/CTL y prioridad explícitos; un WAIT tardío máximo por sufijo;
barrera 255 consumida antes de cruzarla; cargas de `build_mid` intactas;
sin slot probado = no validado. No se propone recolorear el banco ni
aproximar colores. El plazo de controles debe medir también el primer
armado y el reuso: la medida de colores no sustituye G0.

## 5. Puertas y límites del cierre

Diez tests G2T y ocho de la referencia original pasan sin ROM; se llaman
desde `regress.py`, con evidencia en su log. La auditoría completa y la
calibración son comandos separados: jamás se declara G5 verde por pasar
estos tests sintéticos. Baselines intactas. Preflight: lint, regress
`--baseline tools/baseline_pc.json --level`, OAM68K verdes; 6549 llamadas
PC=68000, cero RAM distinta. **Cierre repetido en verde:**
`work/session1007_lint.log`, `work/session1007_regress.log` y
`work/session1007_oam.log`. En `work/regress.log` constan las llamadas a
`test_g5ref.py` (8 tests) y `test_g2t.py` (10 tests). `git diff -- player
tools/baseline.json tools/baseline_pc.json` vacío.

**No ejecutado:** un plan horizontal completo calibrado en las tres
trazas, port C/68000, emisor del juego, comparación de pantalla entera,
coste de render/fotos omitidas. G5 A/B/C y L-OAM siguen sin cerrar. No
se hace push. Trampa de revisión: un hueco lógico de color, la capacidad
C2 y un slot real de copper son tres comprobaciones distintas.
