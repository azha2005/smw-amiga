# OAM + O5 y pico del scroll — medida local, 2026-10-05

**Resultado:** generar la OAM cabe en el objetivo de lógica ≤ 40 % del
frame en el replay probado. No aumenta las fotos omitidas por O5. El
cuello de botella medido sigue siendo `build_mid`, que alcanza el 89,2 %
del frame. Esto justifica ensayar el precálculo selectivo S5/E09/E10;
todavía no demuestra una ganancia de esa optimización.

## Banco y alcance

- Código: `4cec734213a8645292e1238d2f55561e2bf0cf97`, con P51 y O5.
- WinUAE **6.0.0.0**, A500 OCS, 68000, PAL, KS 1.2, 512 KB chip y
  512 KB slow. Perfil de `tools/shot.ps1 -Exact`, coincidente con la
  referencia `a500.uae`: `cpu_speed=real`, `cycle_exact=true`,
  `cpu_cycle_exact=true`, `cpu_memory_cycle_exact=true`,
  `blitter_cycle_exact=true`, `immediate_blits=false`, sin JIT.
- Mismo replay y datos en ambos builds; `GDEFS='-DREPLAY -DBENCH'`.
  Base: `CDEFS=-DNOOAM`. Candidato: `CDEFS='-DNOOAM -DSPR_OAM'`.
- Replay del oráculo 5145–11457: 6313 operaciones, de ellas 6181 RUN,
  129 SKIP, 2 SYNC y 1 LEVEL; el banco mide **6312 frames**.
- Temporización con CIA-B dentro de la Amiga. Un tick son 10 ciclos
  nominales de CPU; frame calibrado: 14211 ticks en base y 14210 en OAM.
  Porcentajes calculados con la calibración de cada build.
- Capturas y configuraciones privadas por banco. Se inspeccionaron las
  pantallas de resultados y se validaron las dos palabras de sincronía.

La OAM describe los objetos que debe dibujar el futuro renderer. Esta
prueba **no incorpora el DMA de enemigos, bobs, HUD ni audio**. Mario y
las capas actuales sí están presentes. No equivale al presupuesto del
demo final ni a un ensayo en hardware físico.

## Comparación integrada

| Métrica | Base + O5 | OAM + O5 |
|---|---:|---:|
| `level_frame`, máximo | 4190 ticks / 29,48 % | 5292 ticks / **37,24 %** |
| Interrupción lógica + foto, máximo | 5491 ticks / 38,64 % | 6593 ticks / **46,40 %** |
| `build_mid`, máximo | 12610 ticks / 88,73 % | 12670 ticks / **89,16 %** |
| Render total hasta blitter libre, máximo | 17017 ticks / 119,75 % | 17419 ticks / 122,58 % |
| Render total, media | 4449 ticks / 31,31 % | 5006 ticks / 35,23 % |
| Renderizaciones que exceden un frame | 11 | 13 |
| Frames lógicos / imágenes publicadas | 6312 / 6298 | 6312 / 6298 |
| Fotos omitidas / racha máxima | **14 / 1** | **14 / 1** |
| VBL sin imagen nueva | 15 | 15 |
| Incidencias COPER detectadas | **0** | **0** |
| Chip del banco / slow del banco | 390704 / 210112 B | 390704 / 212880 B |

Las 14 fotos son el **0,22 %** de los frames lógicos. O5 permite repetir
una imagen cuando el render no termina a tiempo: por eso el máximo del
render puede superar el 100 % mientras sigue avanzando la lógica. Las
fotos omitidas, los VBL sin imagen nueva y los renders largos son
contadores distintos; no deben sumarse.

El pico de `build_mid` y del render total coincide en ambos builds con el
frame de replay **5852**, cámara **1860**. Los máximos de `level_frame`
ocurren en frames distintos: 4570 en base y 2756 en OAM. No se deben sumar
los máximos de cada fase ni tratar su diferencia como coste de OAM en un
mismo frame. El aumento entre máximos de lógica es 26,3 %; el 19,7 %
anterior de Musashi pertenecía a otra medición.

La lógica con OAM conserva **2,76 puntos porcentuales** respecto de su
objetivo del 40 %. La interrupción completa ocupa unos 9,28 ms de los
20 ms PAL. Se completaron los 6312 ticks lógicos y no hubo incidencias
COPER detectadas en este recorrido. Quedan pendientes otros estados en
vivo y las cargas del renderer final. `SPR_OAM` conserva su carácter
opt-in; esta medición no cambia el modo por defecto.

## Barrido separado de scroll: ida y vuelta

Se ensambló el `player/scroll.s` actual con
`-DBENCH -DSPEED=2 -DRETURN=4864 -DSTOPX=0`. No incluye la lógica del juego
ni el dibujador de enemigos. Mide el barrido en ambos sentidos, con los
6 planos actuales; no es el mismo escenario que el replay integrado.

| Grupo de frames | Cantidad | Media | Máximo | Posición del máximo |
|---|---:|---:|---:|---:|
| Con columna nueva | 2404 | 1625 ticks / 11,4 % | **12387 ticks / 87,2 % / 17,46 ms** | s=4576 |
| Sin columna nueva | 2452 | 1227 ticks / 8,6 % | 10704 ticks / 75,3 % / 15,09 ms | s=2152 |

Calibración: 14210 ticks/frame. Los 4856 frames excluyen ocho de
inicialización. El banco agrupa ambos sentidos; el dato decodificado no
identifica el sentido del máximo. La proximidad a s=4580 confirma la zona
costosa conocida, pero no permite atribuirle una dirección por sí sola.

## Verificación y evidencia

Se construyeron también las dos variantes sin `BENCH` para
`tools/gamecheck.py --engine unicorn --spr`:

- **0 frames distintos del oráculo** en ambas variantes.
- Gráfico de Mario C y dos buffers alternos del asm:
  **6184/6184** coincidencias en cada variante.
- Guard de llamadas PIC: correcto en los builds.
- `tools/memmap.py`: **0 violaciones** en ambos bancos.
- `tools/lint_port.py`: OK, con avisos existentes C4/P40/V3.

Antes del commit se ejecutó también
`tools/regress.py --baseline tools/baseline_pc.json --level`: las
comprobaciones de PC, assets y nivel pasaron, pero el resultado global
fue **FALLA (1)** por la dependencia `machine68k` ausente. La parte de
Musashi no quedó verificada en esta corrida; no se cambió la baseline
para ocultar esa limitación.

Unicorn se usó para comparar estados; **los tiempos de esta página son
de WinUAE cycle-exact**, no de Unicorn. Se restauró el build C por defecto
al terminar. No se modificaron la baseline ni las rutinas del juego.

Artefactos locales regenerables, ignorados por git:

- `work/research_oam/{base,oam}/game.{bin,lst,adf}`.
- `work/research_oam/{base,oam}/capture_220s.png` y los perfiles privados
  `capture/work/shot.uae` de cada variante.
- `work/research_oam/scroll/capture_180s.png`.
- `work/research_oam/results.json`: palabras crudas, contadores y hashes.
- Scripts locales `work/research_oam_build.sh`,
  `work/research_oam_verify.sh` y `work/research_scroll_build.sh`.
- Logs `work/research_oam_build.*.log`,
  `work/research_oam_verify.*.log` y `work/research_oam_capture*.log`.

Hashes SHA-256 para identificar los inputs y binarios medidos:

| Archivo | SHA-256 |
|---|---|
| Base `game.bin` | `2bc486d77af939aedfb183457e33cc41eba172521959bb0192ddbe6f594363bb` |
| OAM `game.bin` | `3f0c6a64facb0af17205e65ac3df09bba06a87f46cfbada9ead8b266af04331f` |
| `yi1_s.dat` | `d9274027530ba5664dc928cf468299890ddb8850cab2ababa1835d1c9c8088e0` |
| `yi1_replay.bin` | `9bbc93d3b77e0bf6829491646c306751e4d853550a3ebb4eae4b106fb1e15fbc` |

Para repetir, construir secuencialmente las dos variantes con las opciones
anteriores y un `OUT` distinto; no reutilizar el C compilado entre ellas.
Capturar cada ADF con `tools/shot.ps1 -Exact -Wait 220` y un perfil privado.
Decodificación con las herramientas existentes:

```sh
python tools/game_read.py --shot work/research_oam/base/capture_220s.png --auto
python tools/game_read.py --shot work/research_oam/oam/capture_220s.png --auto
python tools/scroll_read.py --shot work/research_oam/scroll/capture_180s.png
```

En la captura del scroll se usa el origen fijo por defecto: `--auto`
confunde la barra blanca del título de WinUAE con la del banco.

## Decisión que habilita

La generación OAM pasa la puerta de lógica en este replay; se puede
continuar G3–G6 sin descartarla por su coste medido. La mayor oportunidad
actual de rendimiento sigue siendo evitar reconstruir la parte costosa
del copper en cada foto. El ensayo S5/E09/E10 deberá comparar contra estos
bancos con píxeles idénticos, memoria acotada y cámaras de ida/vuelta,
incluida Y. El trabajo del renderer final conserva el orden del ROADMAP.
