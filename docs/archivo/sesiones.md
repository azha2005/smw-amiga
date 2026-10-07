# Registro de sesiones (archivo)

> Cada sesión, al cerrar, agrega aquí **el `PROXIMO.md` que tenía** y **qué
> se hizo** (regla: `ROADMAP.md` §7). Lo más nuevo va **arriba**. No se
> edita lo ya escrito. Antes del 2026-10-05 el día a día está en
> `docs/archivo/historia.md` y en el §1 de `docs/archivo/roadmap-2026-10-05.md`.

---

## 2026-10-05 (2) — Reorganización de los documentos

**Plan que tenía:** el de la sesión G3/Z1/H1 de abajo ("la siguiente sesión
debe comenzar por G2/G3"), ampliado durante esta sesión con G5a (entonces "V1"), la nota del
remapeo por copper y la compuerta D1 en fotos omitidas.

**Qué se hizo** (solo documentación; `lint_port.py` en verde en cada paso):

- Handoff G2/G3 con lote acotado y topes de chip/slow (`09902cd`); G5a (era "V1") y
  remapeo por copper (`aa58b0b`); **compuerta D1 redefinida en fotos
  omitidas** por el usuario (`c47baef`); plan de tarjetas paralelas
  (`3aa3698`); AGENTS §12 dejaba de contradecir R5 (`72ff088`).
- Reorganización: `PROXIMO.md` como único lugar de "qué sigue"; `ROADMAP.md`
  reducido a estado, presupuesto, decisiones, olas, riesgos, entornos,
  cierre de sesión y comprobaciones; §9-§11 a `docs/plan-tecnico.md`;
  `etapas.md`, `plan-original.md`, `historia.md` y el ROADMAP anterior a
  `docs/archivo/`; `docs/README.md` como índice; tabla de estado de
  tarjetas en `SUBAGENTES.md` §4; regla de cierre de sesión; comprobaciones
  de docs en `lint_port.py`.
- **Correcciones encontradas al revisar el estado:** la tabla de etapas
  decía que faltaban Chuck, caparazones y meta (hechos el 2026-10-01 en
  `spr_chuck.c`, `spr_shell.c`, `spr_goal.c`) y las grabaciones
  `stress_back`, `stress_sprites`, `pipe`, `goal_low`, `pw_medio`, etc.
  (hechas el 2026-10-01). El plan paralelo de `3aa3698` pedía grabarlas y
  portar esa lógica: se corrigió en `PROXIMO.md` a medir con ellas
  (D1-medida) y a escribir su OAM (G8b).

---

## 2026-10-05 (1) — Sesión G3, Z1 y H1


Autorizada por el usuario después de revisar el orden y los modelos.
Base `8102ffc`: lint y regresión completa PC con `--level` en verde antes
de lanzar. Coordinación con Sol high; Astra excluida por el usuario.

| tarjeta | modelo / esfuerzo | worktree | entrega y puerta |
|---|---|---|---|
| G3 final | GPT-6.1 Sol medium | `../wt-g3final` | formato DMA/bob y colores exactos según G2; autoprueba, cobertura y tamaño del banco; PNG comparado |
| Z1 | GPT-6.1 Sol medium | `../wt-z1` | fin de muerte y reinicio seguro con O5; binario real, replay, capturas cycle-exact y coste |
| H1 | GPT-6 Luna low | `../wt-h1` | banda real del HUD y cruces con capa 1, script reproducible, informe y PNG |

Resultados: G3 aporta conversor/formatos y pruebas exactas, **sin cerrar la
tarjeta final**; 48 poses compuestas (10840 B chip, 5276 B slow), 241 fichas
observadas y 12 rechazos negativos comprobados. G2 debe resolver banco y
diccionario de variantes antes de G4/G6 definitivos. Z1 pasa oráculos de
muerte 188/188 y 190/190, cinco vidas, mando sostenido, O5 y bucle antiguo
en modo usuario; carga real 300,19 ms y reaparición visible en 411. H1
deriva la máscara inicial (1342 píxeles opacos) y cuantifica los cruces;
no sustituye la referencia PPU pendiente. P103 documenta el fallo de `SR`
en modo usuario encontrado con WinUAE y corregido mediante `INTENA`.

El coordinador repitió las puertas en los worktrees y en el árbol integrado;
lint y regresión completa PC con `--level` pasan. Las baselines no se
modifican. `work/live/game.adf` está reconstruido; los informes, PNG y
manifiestos de la sesión se conservaron en `work/` (R9). La política queda
en `SUBAGENTES.md` §1. La siguiente sesión debe comenzar por **G2/G3:
reducir el banco y las tablas de variantes con píxeles exactos**, usando los
casos reproducibles del informe, antes de lanzar el asignador definitivo.

**Integrado en la continuación de la ola 3, mismo día (texto del ROADMAP de entonces):**


La ola 3 (`ab51d16`) está integrada. La continuación usa
`tools/baseline_pc.json` **sin modificarlo**. El plan del 2026-10-03 de
abajo queda como referencia histórica.

**Integrado y verificado:**

1. **G2:** [diseño e interfaces](docs/diseno-9.2.md), resumido en §10.6.
   OAM en la lógica original; foto O5 inmutable con propiedad de fichas;
   Mario reservado, Banzai bob y cola explícita para excedentes. El banco
   DMA propuesto, segundo PF1 y audio requieren liberar tablas CPU de chip
   (C2/C4); no caben todos en el mapa actual.
2. **G0 real a 256 px:** [banco y resultados](docs/medida-g0.md).
   Poses compartidas exactas en ocho canales con PT en la línea anterior
   y POS/CTL después del control DMA. PT desde h=$D8 llega tarde.
   Cadena gap 1 exacta; copia de 1408 B cuesta ~7,5 % activo, ~4,9 % VBlank.
   Carga sintética 8+6 MOVE: todavía falta demostrar ventanas con el copper
   real, audio y blitter concurrentes (G5/G7).
3. **OAM 68000:** `CDEFS='-DNOOAM -DSPR_OAM'`, opción coherente C/asm;
   [puertas y comandos](docs/oam-amiga.md). Rex YI1 2671/2671, RAM/mapa/ABI
   exactos; juego integrado 0 frames distintos. Máximo de lógica
   39 026 → 46 718 ciclos (+19,7 % relativo, sin DMA). Limpieza completa
   de fichas y marcas. Corregidas llamadas lejanas absolutas y añadido
   `piccheck.py` a ambos builds (P102). **Sigue apagado por defecto** hasta
   medir O5/DMA integrado; todavía no dibuja enemigos.
4. **Cobertura manual actualizada** con R10 y **G3a en `regress.py`**, también
   en `--quick`. Sin OAM grabada avisa y salta; datos presentes corruptos
   fallan. Autoprueba local: 227/227 poses, 512 fichas × cuatro flips.

5. **SX/SX2 cerrada** con P51 ([validación](docs/validacion-sx.md)):
   24 capturas cycle-exact, ida y vuelta en 6 posiciones contra el
   `scroll.s` anterior a SX. Ambas puertas OK; s=1700 pasa de 43/44 px a 0.
   **P51 arreglada** (`0361736`): tras DDFSTOP el copper encadena MOVE
   cada 8 px; `build_mid`/`bm_left` corrigen solo las cargas que cruzan
   el codo. Coste: `build_mid` máx. 75 816 → 80 868 (+6,7 %), total del
   juego 117 796 → 119 998 (+1,9 %).


---

## 2026-10-06 — Ronda experimental E11–E14

**Plan que tenía (textual):**

# PRÓXIMO — lo que sigue

> **Este es el único lugar que dice qué se hace a continuación.** Si otro
> documento dice otra cosa, manda este. Se **reescribe en el sitio** al
> cerrar cada sesión (regla de cierre: `ROADMAP.md` §7); lo que reemplaza
> se archiva en `docs/archivo/sesiones.md`. No se agregan secciones
> "próxima sesión" en ningún otro fichero.
>
> Estado de cada etapa: `ROADMAP.md` §1 · olas y sesiones: `ROADMAP.md` §4 ·
> tarjetas con su estado: `SUBAGENTES.md` §4 · índice de docs: `docs/README.md`.

**Escrito el 2026-10-05**, al cerrar la sesión de reorganización de docs
(base `master`). Última sesión de trabajo: G3, Z1 y H1 (resumen en
`docs/archivo/sesiones.md`).

---

## 1. La próxima sesión: banco de sprites (G2/G3) y primer enemigo visible

**Objetivo:** que el banco de gráficos de sprites y sus tablas entren en
memoria con reconstrucción exacta, ver el primer Rex en la Amiga y poder
medir la fluidez (compuerta D1) con los replays de estrés.

Modelos (`SUBAGENTES.md` §1): Opus → GPT-6.1 Sol high; Sonnet high →
GPT-6.1 Sol medium; Sonnet low → GPT-6 Luna medium. Astra queda fuera.

| tarjeta | modelo | toca | entrega y puerta |
|---|---|---|---|
| **G2** — revisar la representación del banco (la escribe el coordinador) | Sol high | `docs/diseno-9.2.md` | contrato con tamaños medidos, tope de slow en bytes y casos exactos que demuestren la reducción. **Evaluar primero el remapeo de color por copper** (nota abajo) |
| **G5a** — prueba mínima de Rex, descartable | Sol high | rama propia; `player/` mínimo | G4 + G5 mínimos sobre el banco base de 48 poses ya verificado (10840 B chip), solo Rex, `-DSPR_OAM`. Rex visible en WinUAE comparado con la OAM del oráculo; MOVE del copper por línea junto a `build_mid` (P51), CPU y DMA medidos en cycle-exact. Los números alimentan G2; el código no es el G4/G5 definitivo |
| **D1-medida** — fluidez con los replays de estrés | Sol medium (el coordinador fija el método; el recuento puede bajar a Luna medium) | `tools/game_build.sh` (variable de replay), `docs/` | replays de `oracle_stress_back` (vuelta de x `$1240` a `$0500`) y `oracle_stress_sprites` (Banzai + 3 Rex) armados como el de `oracle_yi1` (`m68kverify --oracle`); fotos omitidas, racha máxima y peor ventana de 250 frames en WinUAE cycle-exact. Es la primera medida de la compuerta D1 (`ROADMAP.md` §2) en estrés |
| **G8b** — OAM de Banzai `$9F`, piraña `$4F`, Chuck `$95`, meta `$7B`, caparazones | Sol medium | `player/spr_*.c` y `spr_gfx.c` de esos sprites | sus rutinas de gráficos escriben la OAM atribuida como G8 hizo con Rex: `oam_XX` exactas en `regress.py` contra `oracle_chuck`, `goal`, `shells`, `banzai`, `stress_piranha`. La lógica ya está; esto amplía la cobertura que G3 dejó fuera |
| **A1** — `tools/brr2pcm.py` | Sol medium | solo `tools/` | muestras BRR → PCM de 8 bits con signo (P7), ida y vuelta contra el decodificador de referencia; tamaño total frente a los 64 KB de D5 |

**De la investigación** (`docs/investigacion-ports.md`, una línea por tarjeta):

- **D1-medida:** usar §17.2 como protocolo (A/B iguales salvo el cambio;
  fotos omitidas, racha, edad de la foto, ticks perdidos, p99 y máximo; no
  sumar máximos de frames distintos).
- **G2/G3:** E05 (§16.4): recortar márgenes transparentes conservando el
  origen OAM y comparar máscara repetida contra única; la fórmula de
  palabras por fila sirve para el presupuesto de Banzai.
- **G5a:** E02 (§16.5): medir sobre Rex poses compartidas contra cadena DMA
  copiada, con su coste en MOVE, para darle el número a G2. E01 (§16.1,
  perfilador de Bartman) solo como diagnóstico si un pico no se explica;
  las medidas que valen siguen siendo las de `a500.uae`.

G2 y G3 van **en serie**: G3 (Sol medium, `tools/mksprgfx.py`) implementa
el contrato de G2 después de que el coordinador lo revise; si G3 encuentra
una decisión sin resolver, vuelve a G2 con evidencia. Si G2 cierra temprano,
G3 entra en esta misma sesión.

### Nota para G2: el remapeo por copper

La explosión de variantes (pose × reservas de Mario por fila × ocho
paletas) viene de hornear el color en el bitmap. D8 ya recarga los colores
17-31 por línea; si el remapeo pasa a esa recarga, cada pose se guarda
**una vez**. Medir esa opción (bytes de banco y tablas, MOVE extra por línea
con los datos de G5a) antes de optimizar la deduplicación actual. Si se
descarta, dejar en el contrato el número que la descarta.

### Lote y puerta de G2/G3

Hoy: 2593 variantes necesitan 145600 B de chip con la estrategia ensayada
(banco: 65536 B); el subconjunto emitido (1724) ocupa 693884 B de tablas
en slow. No son cotas mínimas. Casos y reproducción: `docs/informe-g3.md`.

**Lote de la puerta (acotado):** las variantes de las tres trazas actuales
(`yi1`, `normal`, `spin_kill`) con reservas reales de Mario y ocho paletas,
más las poses legales de Rex de `RexGfxRt`. **Fuera**: Banzai, piraña,
Chuck, meta, power-ups y partículas (esperan G8b) y el remapeo de bobs a
PF1 (G7). G2 diseña con margen para esa cobertura: estima cuánto crecen
banco y tablas al sumarla.

**Puerta de cierre:**

- **Chip:** banco ≤ 65536 B; `memmap` con cero violaciones sobre el juego
  actual + banco (≈ 456 KB), en replay **y en vivo**. Segundo PF1 y audio no
  cuentan aquí: necesitan C2/C4 (`docs/diseno-9.2.md` §5).
- **Slow:** las tablas entran en lo que queda después de C2/C4: 524288 −
  207296 (uso actual) − 135468 (tablas de CPU que C2/C4 mueven a slow) =
  **181524 B**, menos lo que sume el modo en vivo. G2 fija el tope concreto.
- **Exactitud:** todas las variantes del lote sin rechazos ocultos, píxeles
  y colores exactos, PNG referencia/decodificación comparado, regresión
  PC/68000 en verde. `--final` acepta el lote completo (no basta con las 48
  poses base ni con el subconjunto de 1724).
- **Coste:** si la representación agrega trabajo por frame, medirlo en
  WinUAE cycle-exact antes de cerrar.

### Antes de lanzar y al cerrar

- Antes: `python tools/lint_port.py` y
  `python tools/regress.py --baseline tools/baseline_pc.json --level` en
  verde; worktree por tarjeta (`sh tools/wt_new.sh <tarjeta>`); capturas con
  perfiles privados, máximo tres WinUAE a la vez, cada uno cierra solo su
  PID.
- Al cerrar: la regla de `ROADMAP.md` §7 (reescribir este fichero).

---

## 2. Sesión experimental: E11-E14 (de los juegos de referencia)

**Objetivo:** decidir con números si las técnicas de Lionheart, Elfmania,
Kid Chaos y Robocod (`docs/investigacion-ports.md` §19) le sirven a YI1,
**antes** de que S5 y G7 las necesiten. La primera mitad es solo offline,
sobre `tools/` y los oráculos, y no depende de G2-G5: puede ir en paralelo
con la sesión de §1 o en un hueco. Ninguna toca el juego hasta que su
recuento lo justifique.

| tarjeta | modelo | toca | entrega y puerta |
|---|---|---|---|
| **E11a** — recuento de líneas donde PF2 cabe en 2 planos | Sol medium | solo `tools/` (herramienta nueva, salida en `work/`) | para cada línea de pantalla y cada cámara del recorrido de los oráculos (ida, vuelta, cámara Y), el índice máximo de PF2 usado: líneas con ≤ 3 (DPF 3+2) y con 0 (PF2 vacío). Con el modelo de `copsim.py` (ranura cada 12 px con 5 planos, en vez de 16), cuántas cargas de `build_mid` dejan de retrasarse y cuánto baja el pico de vuelta. **Puerta:** un número por cámara y el total; si las líneas aptas no mueven el pico, E11 se cierra con ese número en §18.2 |
| **E11b** — franjas de 5 planos en la lista | Sol high | `tools/mkleveld.py`, `copsim.py`, `player/scroll.s` | **solo si E11a da.** `BPLCON0` por franja en el borrado, `BPL6PT` recargado al volver a 6 planos, franjas rehechas al mover la cámara en vertical. **Puerta:** píxeles iguales (capturas cycle-exact, `cmp_ref.py` sin cambios), ida/vuelta/cámara Y, pico de vuelta y fotos omitidas con el protocolo de §17.2 |
| **E12** — índices de PF1 sin conflicto por línea | Sol medium | solo `tools/` (plan offline) | los índices de PF1 cuyas variantes nunca comparten línea en YI1, **en todas las cámaras posibles** (no solo las grabadas), y cuántas cargas de `build_mid` pasarían al borrado. Es el recuento de E09; **comparte la herramienta con E11a**. **Puerta:** píxeles iguales; si son pocos índices, se cierra con el número |
| **E14a** — ¿cabe el Banzai en los 8 sprites? | Luna medium | solo `tools/`, sobre `work/oracle_*.txt` | en `oracle_stress_sprites` y `oracle_banzai`, cuántos frames tienen las 64 líneas del Banzai libres de otra OAM (Mario incluido). **Puerta:** si casi nunca están libres, E14 se descarta (el peor caso sigue siendo el bob de E04); si sí, queda como dato para G7 |

**E13** (prioridad por franja con `BPLCON2`) **no se abre**: no hay caso
en YI1. Se anota como recurso en `docs/plan-tecnico.md` hasta que una
comparación 1:1 lo pida.

Herramienta de apoyo, solo para diagnosticar: Engine9000 (§19.4) para ver
franjas y canales. Las medidas que cierran una puerta siguen siendo las
de WinUAE con `a500.uae`.

Al cerrar: el resultado de cada tarjeta (sirve, o se descarta con su
número) va a `docs/investigacion-ports.md` §19.5, y si E11b o E12 entran,
pasan a §3 junto a S5.

---

## 3. Después, en orden

Cada paso con su puerta; nada empieza con el anterior en rojo. Detalle de
cómo hacer cada cosa: `docs/plan-tecnico.md` §10; tarjetas: `SUBAGENTES.md`.

1. **G3** sobre el contrato de G2 (si no entró en la sesión de arriba).
2. **G4 + G6** (asignador de columnas y `sprcop_verify.py`), con el
   contrato cerrado.
3. **G5 + G9**: `SPRxPOS`/`SPRxPT` y colores por línea en la misma lista que
   `build_mid`; comparación automática contra la OAM. **Los enemigos se ven
   en la Amiga.**
4. **Medida de estrés + S5, inmediatamente después de G5**: render completo
   (scroll + sprites) en la vuelta (s ≈ 2832 y 4580), el Banzai y el tramo
   con más Rex; después S5 (repartir el trabajo de `build_mid` entre frames)
   con esos números. Compuerta D1 en fotos omitidas (`ROADMAP.md` §2).
   Para S5: E09 (reasignar colores a índices con la misma imagen y menos
   MOVE) y E10 (precalcular solo las zonas caras, p. ej. los postes; todas
   las listas serían 792 KB y no caben), `docs/investigacion-ports.md` §17.1.
5. **C2/C4** (vlink + loader) para liberar las ~135 KB de tablas de CPU que
   hoy viven en chip; después el segundo PF1 y **G7** (bobs).
   Para G7: E03 (lotes del blitter), E04 (interior opaco del Banzai) y E06
   (restauración: la copia espejo del buffer circular no es fondo limpio;
   una foto O5 retenida no se toca), `docs/investigacion-ports.md` §16.2-16.4, §17.1.
6. En paralelo según dependencias: S8 (cámara vertical de YI1), lógica que
   falta (P7 bolas de fuego, P9 monedas, P10 reserva), A0/A2 (audio), H2-H4
   (HUD), T1 (zona de la tubería).
   Audio (A3-A7): E08 desde el primer driver (tick separado de la
   reactivación de Paula; auditar qué timer de CIA usa cada cosa, O1 ya usa
   uno), §16.6. HUD (H2): trucos de módulo para líneas constantes, §16.9.
   Lógica (L5): E07 (GCC) solo si un perfil muestra que la lógica limita, §16.7.

## 4. Pendiente del usuario o de la PC

- **U1:** jugar `work/live/game.adf` en WinUAE con teclado (KS 1.2,
  512 KB chip + 512 KB slow). Los enemigos todavía no se dibujan; si se
  congela, captura de la página 2 del diagnóstico y
  `python tools/diag_read.py --shot X.png --repro --bin work/live/game.bin`.
- **U2:** Etapa 7 (`cmp_ref.py` de la capa 2 contra la referencia).
- **U3**, opcional: probar en una A500 real.


**Qué se hizo:**

Integradas E11a (a658b95), E12 (28b94c8) y E14a (3fa4241), en worktrees separados con Sol medium, Sol medium y Luna medium. E11: 15.755 frames, cero cargas PF1 en franjas aptas; E11b descartada para build_mid, sin inferir mejora global de DMA. E12: 0/7 indices, 1.016.785 camaras, 2.211.840 pixeles y cero diferencias. E14: estres 0/202 frames con 64 filas libres; Banzai solo 16/331. Atribucion y contadores cruzados independientemente, cero ambiguos. E13 no se abre. Herramientas y PNG offline reproducibles en docs/experimentos-e11-e14.md; sin cambios al juego ni medidas nuevas de WinUAE. Lint y regresion PC completa --level verdes en cada tarjeta. La sesion de banco G2/G3 y las estimaciones de ruta critica siguen pendientes; PROXIMO se reescribe con ese paso.


---

## 2026-10-06 — Revisión e integración de A1, G8b y preparación D1

**Plan de entrada (textual):**

# PRÓXIMO — lo que sigue

> **Este es el único lugar que dice qué se hace a continuación.** Si otro
> documento dice otra cosa, manda este. Se **reescribe en el sitio** al
> cerrar cada sesión (regla de cierre: `ROADMAP.md` §7); lo que reemplaza
> se archiva en `docs/archivo/sesiones.md`. No se agregan secciones
> "próxima sesión" en ningún otro fichero.
>
> Estado de cada etapa: `ROADMAP.md` §1 · olas y sesiones: `ROADMAP.md` §4 ·
> tarjetas con su estado: `SUBAGENTES.md` §4 · índice de docs: `docs/README.md`.

**Escrito el 2026-10-06**, al cerrar la ronda experimental E11–E14.
E11a y E12 integradas; E11b y E14 descartadas para sus objetivos
con la representación actual. E13 no se abrió. Resultados, límites
y comandos: `docs/experimentos-e11-e14.md`. La sesión de banco de
sprites de abajo sigue pendiente.

---

## 1. La próxima sesión: banco de sprites (G2/G3) y primer enemigo visible

**Objetivo:** que el banco de gráficos de sprites y sus tablas entren en
memoria con reconstrucción exacta, ver el primer Rex en la Amiga y poder
medir la fluidez (compuerta D1) con los replays de estrés.

Modelos (`SUBAGENTES.md` §1): Opus → GPT-6.1 Sol high; Sonnet high →
GPT-6.1 Sol medium; Sonnet low → GPT-6 Luna medium. Astra queda fuera.

| tarjeta | modelo | toca | entrega y puerta |
|---|---|---|---|
| **G2** — revisar la representación del banco (la escribe el coordinador) | Sol high | `docs/diseno-9.2.md` | contrato con tamaños medidos, tope de slow en bytes y casos exactos que demuestren la reducción. **Evaluar primero el remapeo de color por copper** (nota abajo) |
| **G5a** — prueba mínima de Rex, descartable | Sol high | rama propia; `player/` mínimo | G4 + G5 mínimos sobre el banco base de 48 poses ya verificado (10840 B chip), solo Rex, `-DSPR_OAM`. Rex visible en WinUAE comparado con la OAM del oráculo; MOVE del copper por línea junto a `build_mid` (P51), CPU y DMA medidos en cycle-exact. Los números alimentan G2; el código no es el G4/G5 definitivo |
| **D1-medida** — fluidez con los replays de estrés | Sol medium (el coordinador fija el método; el recuento puede bajar a Luna medium) | `tools/game_build.sh` (variable de replay), `docs/` | replays de `oracle_stress_back` (vuelta de x `$1240` a `$0500`) y `oracle_stress_sprites` (Banzai + 3 Rex) armados como el de `oracle_yi1` (`m68kverify --oracle`); fotos omitidas, racha máxima y peor ventana de 250 frames en WinUAE cycle-exact. Es la primera medida de la compuerta D1 (`ROADMAP.md` §2) en estrés |
| **G8b** — OAM de Banzai `$9F`, piraña `$4F`, Chuck `$95`, meta `$7B`, caparazones | Sol medium | `player/spr_*.c` y `spr_gfx.c` de esos sprites | sus rutinas de gráficos escriben la OAM atribuida como G8 hizo con Rex: `oam_XX` exactas en `regress.py` contra `oracle_chuck`, `goal`, `shells`, `banzai`, `stress_piranha`. La lógica ya está; esto amplía la cobertura que G3 dejó fuera |
| **A1** — `tools/brr2pcm.py` | Sol medium | solo `tools/` | muestras BRR → PCM de 8 bits con signo (P7), ida y vuelta contra el decodificador de referencia; tamaño total frente a los 64 KB de D5 |

**De la investigación** (`docs/investigacion-ports.md`, una línea por tarjeta):

- **D1-medida:** usar §17.2 como protocolo (A/B iguales salvo el cambio;
  fotos omitidas, racha, edad de la foto, ticks perdidos, p99 y máximo; no
  sumar máximos de frames distintos).
- **G2/G3:** E05 (§16.4): recortar márgenes transparentes conservando el
  origen OAM y comparar máscara repetida contra única; la fórmula de
  palabras por fila sirve para el presupuesto de Banzai.
- **G5a:** E02 (§16.5): medir sobre Rex poses compartidas contra cadena DMA
  copiada, con su coste en MOVE, para darle el número a G2. E01 (§16.1,
  perfilador de Bartman) solo como diagnóstico si un pico no se explica;
  las medidas que valen siguen siendo las de `a500.uae`.

G2 y G3 van **en serie**: G3 (Sol medium, `tools/mksprgfx.py`) implementa
el contrato de G2 después de que el coordinador lo revise; si G3 encuentra
una decisión sin resolver, vuelve a G2 con evidencia. Si G2 cierra temprano,
G3 entra en esta misma sesión.

### Nota para G2: el remapeo por copper

La explosión de variantes (pose × reservas de Mario por fila × ocho
paletas) viene de hornear el color en el bitmap. D8 ya recarga los colores
17-31 por línea; si el remapeo pasa a esa recarga, cada pose se guarda
**una vez**. Medir esa opción (bytes de banco y tablas, MOVE extra por línea
con los datos de G5a) antes de optimizar la deduplicación actual. Si se
descarta, dejar en el contrato el número que la descarta.

### Lote y puerta de G2/G3

Hoy: 2593 variantes necesitan 145600 B de chip con la estrategia ensayada
(banco: 65536 B); el subconjunto emitido (1724) ocupa 693884 B de tablas
en slow. No son cotas mínimas. Casos y reproducción: `docs/informe-g3.md`.

**Lote de la puerta (acotado):** las variantes de las tres trazas actuales
(`yi1`, `normal`, `spin_kill`) con reservas reales de Mario y ocho paletas,
más las poses legales de Rex de `RexGfxRt`. **Fuera**: Banzai, piraña,
Chuck, meta, power-ups y partículas (esperan G8b) y el remapeo de bobs a
PF1 (G7). G2 diseña con margen para esa cobertura: estima cuánto crecen
banco y tablas al sumarla.

**Puerta de cierre:**

- **Chip:** banco ≤ 65536 B; `memmap` con cero violaciones sobre el juego
  actual + banco (≈ 456 KB), en replay **y en vivo**. Segundo PF1 y audio no
  cuentan aquí: necesitan C2/C4 (`docs/diseno-9.2.md` §5).
- **Slow:** las tablas entran en lo que queda después de C2/C4: 524288 −
  207296 (uso actual) − 135468 (tablas de CPU que C2/C4 mueven a slow) =
  **181524 B**, menos lo que sume el modo en vivo. G2 fija el tope concreto.
- **Exactitud:** todas las variantes del lote sin rechazos ocultos, píxeles
  y colores exactos, PNG referencia/decodificación comparado, regresión
  PC/68000 en verde. `--final` acepta el lote completo (no basta con las 48
  poses base ni con el subconjunto de 1724).
- **Coste:** si la representación agrega trabajo por frame, medirlo en
  WinUAE cycle-exact antes de cerrar.

### Antes de lanzar y al cerrar

- Antes: `python tools/lint_port.py` y
  `python tools/regress.py --baseline tools/baseline_pc.json --level` en
  verde; worktree por tarjeta (`sh tools/wt_new.sh <tarjeta>`); capturas con
  perfiles privados, máximo tres WinUAE a la vez, cada uno cierra solo su
  PID.
- Al cerrar: la regla de `ROADMAP.md` §7 (reescribir este fichero).

---

## 2. Después, en orden

Cada paso con su puerta; nada empieza con el anterior en rojo. Detalle de
cómo hacer cada cosa: `docs/plan-tecnico.md` §10; tarjetas: `SUBAGENTES.md`.

1. **G3** sobre el contrato de G2 (si no entró en la sesión de arriba).
2. **G4 + G6** (asignador de columnas y `sprcop_verify.py`), con el
   contrato cerrado.
3. **G5 + G9**: `SPRxPOS`/`SPRxPT` y colores por línea en la misma lista que
   `build_mid`; comparación automática contra la OAM. **Los enemigos se ven
   en la Amiga.**
4. **Medida de estrés + S5, inmediatamente después de G5**: render completo
   (scroll + sprites) en la vuelta (s ≈ 2832 y 4580), el Banzai y el tramo
   con más Rex; después S5 (repartir el trabajo de `build_mid` entre frames)
   con esos números. Compuerta D1 en fotos omitidas (`ROADMAP.md` §2).
   Para S5: E09 (reasignar colores a índices con la misma imagen y menos
   MOVE) y E10 (precalcular solo las zonas caras, p. ej. los postes; todas
   las listas serían 792 KB y no caben), `docs/investigacion-ports.md` §17.1.
5. **C2/C4** (vlink + loader) para liberar las ~135 KB de tablas de CPU que
   hoy viven en chip; después el segundo PF1 y **G7** (bobs).
   Para G7: E03 (lotes del blitter), E04 (interior opaco del Banzai) y E06
   (restauración: la copia espejo del buffer circular no es fondo limpio;
   una foto O5 retenida no se toca), `docs/investigacion-ports.md` §16.2-16.4, §17.1.
6. En paralelo según dependencias: S8 (cámara vertical de YI1), lógica que
   falta (P7 bolas de fuego, P9 monedas, P10 reserva), A0/A2 (audio), H2-H4
   (HUD), T1 (zona de la tubería).
   Audio (A3-A7): E08 desde el primer driver (tick separado de la
   reactivación de Paula; auditar qué timer de CIA usa cada cosa, O1 ya usa
   uno), §16.6. HUD (H2): trucos de módulo para líneas constantes, §16.9.
   Lógica (L5): E07 (GCC) solo si un perfil muestra que la lógica limita, §16.7.

## 3. Pendiente del usuario o de la PC

- **U1:** jugar `work/live/game.adf` en WinUAE con teclado (KS 1.2,
  512 KB chip + 512 KB slow). Los enemigos todavía no se dibujan; si se
  congela, captura de la página 2 del diagnóstico y
  `python tools/diag_read.py --shot X.png --repro --bin work/live/game.bin`.
- **U2:** Etapa 7 (`cmp_ref.py` de la capa 2 contra la referencia).
- **U3**, opcional: probar en una A500 real.


**Qué se hizo:**

- A1 (`44b2f94`, merge `38a227e`): conversor BRR, 1024 bloques y
  20 muestras frente al DSP C, 0 diferencias PCM16; 50560 B PCM y
  14976 B de margen. CLI y regresión verificadas de nuevo al integrar.
  R8 WAV y reproducción exacta de loops quedan pendientes.
- D1 (`fa23784`, merge `e4dc05c`): selector ORACLE/REPLAY y contador CSV;
  replays de estrés 4127/1915 operaciones, 0 diferencias en gamecheck.
  Integración conjunta con G8b comprobada, incluidos los ADF BENCH.
  Faltan exportador por VBL y WinUAE; no se midió fluidez real.
- G8b (`0ef275b` y `756d184`): OAM PC/68000 de cinco tipos, 3150/3150
  casos exactos y 18076 despachos sin diferencias de RAM/mapa/marcas/ABI.
  Puentes PIC sin absolutas, cruce RAM 6549 llamadas / 0 diferencias y
  replay integrado 6313 operaciones / 0 diferencias. Se conserva opt-in:
  lógica máxima 62110 ciclos = 43,8 % PAL en Musashi sin DMA, por encima
  del objetivo de lógica antes incluso de añadir esperas DMA.
- El coordinador repitió las puertas y revisó los PNG OAM SNES/68000,
  añadió seis pruebas de límites D1 y 41 métricas nuevas de cobertura en
  cada baseline sin cambiar valores o tolerancias previos. Chip: 390704 B,
  cero violaciones; slow opt-in: 214880 B. Detalle de comandos y límites:
  `docs/integracion-a1-g8b-d1.md`.
- Se registran P104-P107 y se corrige el inventario histórico de audio.
  G2/G3 y el primer Rex visible siguen pendientes; PROXIMO se reescribe
  para el banco, la medida/optimización OAM, D1 y el registro DSP A0.


---

## 2026-10-06 — G2, revisión sin subagentes

**Plan que tenía (textual):**

# PRÓXIMO — lo que sigue

> **Este es el único lugar que dice qué se hace a continuación.** Si otro
> documento dice otra cosa, manda este. Se **reescribe en el sitio** al
> cerrar cada sesión (regla de cierre: `ROADMAP.md` §7); lo que reemplaza
> se archiva en `docs/archivo/sesiones.md`. No se agregan secciones
> "próxima sesión" en ningún otro fichero.
>
> Estado de cada etapa: `ROADMAP.md` §1 · olas y sesiones: `ROADMAP.md` §4 ·
> tarjetas con su estado: `SUBAGENTES.md` §4 · índice de docs: `docs/README.md`.

**Escrito el 2026-10-06**, tras revisar A1, G8b y la preparación D1.
A1 convierte las 20 muestras a 50560 B PCM y pasa la referencia DSP;
G8b amplía la OAM exacta en PC/68000, conservando el modo opt-in.
La OAM ampliada de G8b consume hasta 43,8 % PAL de lógica en Musashi
sin DMA: antes de activarla por defecto hay que optimizarla y medirla.
D1 tiene replays y contador preparados, pero faltan el exportador por VBL
y la medida real en WinUAE. Evidencia: `docs/informe-a1.md`,
`docs/validacion-g8b.md` y `docs/medida-d1-estres.md`. El banco G2/G3
y el primer Rex visible siguen pendientes.

---

## 1. La próxima sesión: banco de sprites (G2/G3) y primer enemigo visible

**Objetivo:** que el banco de gráficos de sprites y sus tablas entren en
memoria con reconstrucción exacta, ver el primer Rex en la Amiga y poder
medir la fluidez (compuerta D1) con los replays de estrés.

Modelos (`SUBAGENTES.md` §1): Opus → GPT-6.1 Sol high; Sonnet high →
GPT-6.1 Sol medium; Sonnet low → GPT-6 Luna medium. Astra queda fuera.

| tarjeta | modelo | toca | entrega y puerta |
|---|---|---|---|
| **G2** — revisar la representación del banco (la escribe el coordinador) | Sol high | `docs/diseno-9.2.md` | contrato con tamaños medidos, tope de slow en bytes y casos exactos que demuestren la reducción. **Evaluar primero el remapeo de color por copper** (nota abajo) |
| **G5a** — prueba mínima de Rex, descartable | Sol high | rama propia; `player/` mínimo | G4 + G5 mínimos sobre el banco base de 48 poses ya verificado (10840 B chip), solo Rex, `-DSPR_OAM`. Rex visible en WinUAE comparado con la OAM del oráculo; MOVE del copper por línea junto a `build_mid` (P51), CPU y DMA medidos en cycle-exact. Los números alimentan G2; medir también la lógica G8b (hoy máx. 43,8 % sin DMA) antes de activar la OAM ampliada. El código no es el G4/G5 definitivo |
| **D1-medida** — exportar y medir los replays de estrés | Sol medium (el coordinador fija la exportación; recuento ya disponible) | `tools/`, `docs/` | usar `ORACLE`/`REPLAY` de `game_build.sh` y `d1_count.py`; obtener una traza completa por VBL en WinUAE cycle-exact, con identidad de foto puesta y ticks terminados. `stress_back`: 4127 operaciones; `stress_sprites`: 1915. Medir omisiones, racha, ventana250, edad y p99; los agregados BENCH no bastan (`docs/medida-d1-estres.md`) |
| **A0** — registro del DSP | Sol medium | `tools/snesorc/orc.c`, `tools/dsplog.py` | escrituras DSP con frame/tick, notas por voz y efectos; oráculo idéntico con/sin registro. A1 ya da conversión exacta; A0 permite estudiar A2 y contrastar el audio (SUBAGENTES A0) |

**De la investigación** (`docs/investigacion-ports.md`, una línea por tarjeta):

- **D1-medida:** usar §17.2 como protocolo (A/B iguales salvo el cambio;
  fotos omitidas, racha, edad de la foto, ticks perdidos, p99 y máximo; no
  sumar máximos de frames distintos).
- **G2/G3:** E05 (§16.4): recortar márgenes transparentes conservando el
  origen OAM y comparar máscara repetida contra única; la fórmula de
  palabras por fila sirve para el presupuesto de Banzai.
- **G5a:** E02 (§16.5): medir sobre Rex poses compartidas contra cadena DMA
  copiada, con su coste en MOVE, para darle el número a G2. E01 (§16.1,
  perfilador de Bartman) solo como diagnóstico si un pico no se explica;
  las medidas que valen siguen siendo las de `a500.uae`.

G2 y G3 van **en serie**: G3 (Sol medium, `tools/mksprgfx.py`) implementa
el contrato de G2 después de que el coordinador lo revise; si G3 encuentra
una decisión sin resolver, vuelve a G2 con evidencia. Si G2 cierra temprano,
G3 entra en esta misma sesión.

### Nota para G2: el remapeo por copper

La explosión de variantes (pose × reservas de Mario por fila × ocho
paletas) viene de hornear el color en el bitmap. D8 ya recarga los colores
17-31 por línea; si el remapeo pasa a esa recarga, cada pose se guarda
**una vez**. Medir esa opción (bytes de banco y tablas, MOVE extra por línea
con los datos de G5a) antes de optimizar la deduplicación actual. Si se
descarta, dejar en el contrato el número que la descarta.

### Lote y puerta de G2/G3

Hoy: 2593 variantes necesitan 145600 B de chip con la estrategia ensayada
(banco: 65536 B); el subconjunto emitido (1724) ocupa 693884 B de tablas
en slow. No son cotas mínimas. Casos y reproducción: `docs/informe-g3.md`.

**Lote de la puerta (acotado):** las variantes de las tres trazas actuales
(`yi1`, `normal`, `spin_kill`) con reservas reales de Mario y ocho paletas,
más las poses legales de Rex de `RexGfxRt`. **Fuera de este lote**:
Banzai, piraña, Chuck, meta, power-ups y partículas, y el remapeo de bobs
a PF1 (G7). G8b ya proporciona OAM de los cinco tipos, pero G3 no amplía
su lote automáticamente: G2 estima cuánto crecen banco y tablas al
sumarlos y fija el contrato antes de ampliar la puerta.

**Puerta de cierre:**

- **Chip:** banco ≤ 65536 B; `memmap` con cero violaciones sobre el juego
  actual + banco (≈ 456 KB), en replay **y en vivo**. Segundo PF1 y audio no
  cuentan aquí: necesitan C2/C4 (`docs/diseno-9.2.md` §5).
- **Slow:** las tablas entran en lo que queda después de C2/C4: 524288 −
  207296 (uso actual) − 135468 (tablas de CPU que C2/C4 mueven a slow) =
  **181524 B**, menos lo que sume el modo en vivo. G2 fija el tope concreto.
- **Exactitud:** todas las variantes del lote sin rechazos ocultos, píxeles
  y colores exactos, PNG referencia/decodificación comparado, regresión
  PC/68000 en verde. `--final` acepta el lote completo (no basta con las 48
  poses base ni con el subconjunto de 1724).
- **Coste:** si la representación agrega trabajo por frame, medirlo en
  WinUAE cycle-exact antes de cerrar.

### Antes de lanzar y al cerrar

- Antes: `python tools/lint_port.py` y `python tools/regress.py --level`
  en verde (cloud: `tools/baseline.json`; PC: agregar
  `--baseline tools/baseline_pc.json`); worktree por tarjeta (`sh tools/wt_new.sh <tarjeta>`); capturas con
  perfiles privados, máximo tres WinUAE a la vez, cada uno cierra solo su
  PID.
- Al cerrar: la regla de `ROADMAP.md` §7 (reescribir este fichero).

---

## 2. Después, en orden

Cada paso con su puerta; nada empieza con el anterior en rojo. Detalle de
cómo hacer cada cosa: `docs/plan-tecnico.md` §10; tarjetas: `SUBAGENTES.md`.

1. **G3** sobre el contrato de G2 (si no entró en la sesión de arriba).
2. **G4 + G6** (asignador de columnas y `sprcop_verify.py`), con el
   contrato cerrado.
3. **G5 + G9**: `SPRxPOS`/`SPRxPT` y colores por línea en la misma lista que
   `build_mid`; comparación automática contra la OAM. **Los enemigos se ven
   en la Amiga.**
4. **Medida de estrés + S5, inmediatamente después de G5**: render completo
   (scroll + sprites) en la vuelta (s ≈ 2832 y 4580), el Banzai y el tramo
   con más Rex; después S5 (repartir el trabajo de `build_mid` entre frames)
   con esos números. Compuerta D1 en fotos omitidas (`ROADMAP.md` §2).
   Para S5: E09 (reasignar colores a índices con la misma imagen y menos
   MOVE) y E10 (precalcular solo las zonas caras, p. ej. los postes; todas
   las listas serían 792 KB y no caben), `docs/investigacion-ports.md` §17.1.
5. **C2/C4** (vlink + loader) para liberar las ~135 KB de tablas de CPU que
   hoy viven en chip; después el segundo PF1 y **G7** (bobs).
   Para G7: E03 (lotes del blitter), E04 (interior opaco del Banzai) y E06
   (restauración: la copia espejo del buffer circular no es fondo limpio;
   una foto O5 retenida no se toca), `docs/investigacion-ports.md` §16.2-16.4, §17.1.
6. En paralelo según dependencias: S8 (cámara vertical de YI1), lógica que
   falta (P7 bolas de fuego, P9 monedas, P10 reserva), A0/A2 (audio), H2-H4
   (HUD), T1 (zona de la tubería).
   Audio (A3-A7): E08 desde el primer driver (tick separado de la
   reactivación de Paula; auditar qué timer de CIA usa cada cosa, O1 ya usa
   uno), §16.6. HUD (H2): trucos de módulo para líneas constantes, §16.9.
   Lógica (L5): E07 (GCC) solo si un perfil muestra que la lógica limita, §16.7.

## 3. Pendiente del usuario o de la PC

- **U1:** jugar `work/live/game.adf` en WinUAE con teclado (KS 1.2,
  512 KB chip + 512 KB slow). Los enemigos todavía no se dibujan; si se
  congela, captura de la página 2 del diagnóstico y
  `python tools/diag_read.py --shot X.png --repro --bin work/live/game.bin`.
- **U2:** Etapa 7 (`cmp_ref.py` de la capa 2 contra la referencia).
- **U3**, opcional: probar en una A500 real.


**Qué se hizo:** G2 acotada auditada por el coordinador, sin agentes.
Contrato e informe `docs/diseno-9.2.md` / `docs/informe-g2.md`; herramienta
`tools/g2_bank_audit.py` y cinco tests. 64528 B chip, 72716 B tablas,
2593 peticiones + Rex legal exactos; matching descarta imagen única con
recargas por fila en 12/43 formas. G8b sin Banzai crece a 77152 B sin nuevas
reservas Mario; no ampliar silenciosamente. Memmap proyectado replay/vivo
sin violaciones, slow recalculada para vivo/G8b. PNG exacto, lint y regresión
antes/después en verde. Commit de cierre: «Etapa 9.2: auditar y cerrar el
contrato acotado G2». No se implementó G3 ni se midió WinUAE; esas puertas
siguen abiertas. Diseño anterior archivado completo.


## 2026-10-06 — G3, prueba G5a y medida D1 en la PC

# PRÓXIMO — lo que sigue

> **Este es el único lugar que dice qué se hace a continuación.** Si otro
> documento dice otra cosa, manda este. Se **reescribe en el sitio** al
> cerrar cada sesión (regla de cierre: `ROADMAP.md` §7); lo que reemplaza
> se archiva en `docs/archivo/sesiones.md`. No se agregan secciones
> "próxima sesión" en ningún otro fichero.
>
> Estado de cada etapa: `ROADMAP.md` §1 · olas y sesiones: `ROADMAP.md` §4 ·
> tarjetas con su estado: `SUBAGENTES.md` §4 · índice de docs: `docs/README.md`.

**Escrito el 2026-10-06**, tras G2 sin subagentes. El contrato acotado
está auditado: **64528 B DMA, 72716 B tablas**, 2593 peticiones y Rex legal
sin diferencias. Copper con una imagen por forma/recargas por fila falla
con Mario en 12/43 formas; la ampliación G8b tampoco cabe automáticamente.
Evidencia: `docs/informe-g2.md`, contrato `docs/diseno-9.2.md`.
G3 y su loader siguen pendientes; los enemigos todavía no se ven en Amiga.
A1/G8b/D1 mantienen sus resultados y límites de la sesión anterior:
`docs/informe-a1.md`, `docs/validacion-g8b.md`, `docs/medida-d1-estres.md`.
G8b sigue opt-in (máximo 43,8 % PAL sin DMA); D1 aún no tiene traza WinUAE.

---

## 1. La próxima sesión: implementar G3 y medir el primer Rex

**Objetivo:** que el banco de gráficos de sprites y sus tablas entren en
memoria con reconstrucción exacta, ver el primer Rex en la Amiga y poder
medir la fluidez (compuerta D1) con los replays de estrés.

Modelos (`SUBAGENTES.md` §1): Opus → GPT-6.1 Sol high; Sonnet high →
GPT-6.1 Sol medium; Sonnet low → GPT-6 Luna medium. Astra queda fuera.

| tarjeta | modelo | toca | entrega y puerta |
|---|---|---|---|
| **G3** — conversor y loader del banco acotado | Sol medium | `tools/mksprgfx.py`, `tools/sprgfx_final.py`, `player/` carga mínima | implementar el contrato G2: DMA inmutable solapado, catálogo enemigo deduplicado y directorio. Todas las 2593 peticiones y Rex legal, cero rechazos; tablas ≤98304 B. Formato versionado con bob ausente explícito; memmap real replay/vivo y pico del loader. `--final --scope g2-bounded` acepta solo el lote declarado; `--final` global no declara cubierto todo YI1 |
| **G5a** — prueba mínima de Rex, descartable | Sol high | rama propia; `player/` mínimo | G4 + G5 mínimos sobre el banco base de 48 poses ya verificado (10840 B chip), solo Rex, `-DSPR_OAM`. Rex visible en WinUAE comparado con la OAM del oráculo; MOVE del copper por línea junto a `build_mid` (P51), CPU y DMA medidos en cycle-exact. Los números validan G5/G6; medir también la lógica G8b (hoy máx. 43,8 % sin DMA) antes de activar la OAM ampliada. El código no es el G4/G5 definitivo |
| **D1-medida** — exportar y medir los replays de estrés | Sol medium (el coordinador fija la exportación; recuento ya disponible) | `tools/`, `docs/` | usar `ORACLE`/`REPLAY` de `game_build.sh` y `d1_count.py`; obtener una traza completa por VBL en WinUAE cycle-exact, con identidad de foto puesta y ticks terminados. `stress_back`: 4127 operaciones; `stress_sprites`: 1915. Medir omisiones, racha, ventana250, edad y p99; los agregados BENCH no bastan (`docs/medida-d1-estres.md`) |
| **A0** — registro del DSP | Sol medium | `tools/snesorc/orc.c`, `tools/dsplog.py` | escrituras DSP con frame/tick, notas por voz y efectos; oráculo idéntico con/sin registro. A1 ya da conversión exacta; A0 permite estudiar A2 y contrastar el audio (SUBAGENTES A0) |

**De la investigación** (`docs/investigacion-ports.md`, una línea por tarjeta):

- **D1-medida:** usar §17.2 como protocolo (A/B iguales salvo el cambio;
  fotos omitidas, racha, edad de la foto, ticks perdidos, p99 y máximo; no
  sumar máximos de frames distintos).
- **G2/G3:** E05 (§16.4): recortar márgenes transparentes conservando el
  origen OAM y comparar máscara repetida contra única; la fórmula de
  palabras por fila sirve para el presupuesto de Banzai.
- **G5a:** E02 (§16.5): medir sobre Rex poses compartidas contra cadena DMA
  copiada, con su coste en MOVE, para darle el número a G2. E01 (§16.1,
  perfilador de Bartman) solo como diagnóstico si un pico no se explica;
  las medidas que valen siguen siendo las de `a500.uae`.

G2 está cerrada como **diseño acotado**; G3 implementa su contrato.
`g2_bank_audit.py` emite evidencia SG2A descartable, no sustituye el
conversor/loader definitivo. Si G3 descubre un caso nuevo o un límite
incumplido, vuelve a G2 con evidencia. No ampliar el lote sin auditarlo.

### Decisión de color y DMA

La imagen única con recargas por fila falla con reservas reales de Mario;
se eligen variantes precalculadas con flujos **inmutables** compartidos.
G5 programa PT completo y POS/CTL por copper (G0); no parchea el banco ni
recodifica/copia imágenes por frame. Recargas por X siguen siendo una
alternativa pendiente de G5a/G6, no una medida ya realizada.

### Lote y puerta de G2/G3

G2 demuestra **64528 B chip + 72716 B tablas** para el lote. El diseño
anterior de 145600 B incluía fuentes bob de 15 índices que no completan
G7/PF1; G7 tiene presupuesto separado. Ampliar con las trazas G8b mide
77152 B DMA aun excluyendo Banzai y sin nuevas variantes Mario: no cabe.

**Lote de la puerta (acotado):** las variantes de las tres trazas actuales
(`yi1`, `normal`, `spin_kill`) con reservas reales de Mario y ocho paletas,
más las poses legales de Rex de `RexGfxRt`. **Fuera de este lote**:
Banzai, piraña, Chuck, meta, power-ups y partículas, y el remapeo de bobs
a PF1 (G7). G8b ya proporciona OAM de los cinco tipos, pero G3 no amplía
su lote automáticamente: G2 ya midió el crecimiento; antes de ampliar
la puerta se necesita otro presupuesto y auditoría (`docs/informe-g2.md`).

**Puerta de cierre:**

- **Chip:** banco ≤65536 B; `memmap` concreto con cero violaciones en
  replay y vivo con SPR_OAM. Proyección G2: 455232/466760 B chip. Auditar
  también el pico del loader y copias transitorias. PF1 doble/audio requieren C2/C4.
- **Slow:** tablas+índices ≤98304 B; trabajo G4/G6 ≤32768 B; fotos 2376 B.
  Vivo opt-in usa 251120 B; C2/C4 moverán 135472 B redondeados. Tope total
  nuevo 133448 B, margen 4248 B con el binario actual. Recalcular con
  crecimiento de código/loader; no usar el margen de replay para vivo.
- **Exactitud:** todas las variantes del lote sin rechazos ocultos, píxeles
  y colores exactos, PNG referencia/decodificación comparado, regresión
  PC/68000 en verde. `--final --scope g2-bounded` acepta el lote completo (no basta con las 48
  poses base ni con el subconjunto de 1724).
- **Coste:** si la representación agrega trabajo por frame, medirlo en
  WinUAE cycle-exact antes de cerrar.

### Antes de lanzar y al cerrar

- Antes: `python tools/lint_port.py` y `python tools/regress.py --level`
  en verde (cloud: `tools/baseline.json`; PC: agregar
  `--baseline tools/baseline_pc.json`); worktree por tarjeta (`sh tools/wt_new.sh <tarjeta>`); capturas con
  perfiles privados, máximo tres WinUAE a la vez, cada uno cierra solo su
  PID.
- Al cerrar: la regla de `ROADMAP.md` §7 (reescribir este fichero).

---

## 2. Después, en orden

Cada paso con su puerta; nada empieza con el anterior en rojo. Detalle de
cómo hacer cada cosa: `docs/plan-tecnico.md` §10; tarjetas: `SUBAGENTES.md`.

1. Terminar **G3** si la sesión de arriba no completa su puerta.
2. **G4 + G6** (asignador de columnas y `sprcop_verify.py`), con el
   contrato cerrado.
3. **G5 + G9**: `SPRxPOS`/`SPRxPT` y colores por línea en la misma lista que
   `build_mid`; comparación automática contra la OAM. **Los enemigos se ven
   en la Amiga.**
4. **Medida de estrés + S5, inmediatamente después de G5**: render completo
   (scroll + sprites) en la vuelta (s ≈ 2832 y 4580), el Banzai y el tramo
   con más Rex; después S5 (repartir el trabajo de `build_mid` entre frames)
   con esos números. Compuerta D1 en fotos omitidas (`ROADMAP.md` §2).
   Para S5: E09 (reasignar colores a índices con la misma imagen y menos
   MOVE) y E10 (precalcular solo las zonas caras, p. ej. los postes; todas
   las listas serían 792 KB y no caben), `docs/investigacion-ports.md` §17.1.
5. **C2/C4** (vlink + loader) para liberar las ~135 KB de tablas de CPU que
   hoy viven en chip; después el segundo PF1 y **G7** (bobs).
   Para G7: E03 (lotes del blitter), E04 (interior opaco del Banzai) y E06
   (restauración: la copia espejo del buffer circular no es fondo limpio;
   una foto O5 retenida no se toca), `docs/investigacion-ports.md` §16.2-16.4, §17.1.
6. En paralelo según dependencias: S8 (cámara vertical de YI1), lógica que
   falta (P7 bolas de fuego, P9 monedas, P10 reserva), A0/A2 (audio), H2-H4
   (HUD), T1 (zona de la tubería).
   Audio (A3-A7): E08 desde el primer driver (tick separado de la
   reactivación de Paula; auditar qué timer de CIA usa cada cosa, O1 ya usa
   uno), §16.6. HUD (H2): trucos de módulo para líneas constantes, §16.9.
   Lógica (L5): E07 (GCC) solo si un perfil muestra que la lógica limita, §16.7.

## 3. Pendiente del usuario o de la PC

- **U1:** jugar `work/live/game.adf` en WinUAE con teclado (KS 1.2,
  512 KB chip + 512 KB slow). Los enemigos todavía no se dibujan; si se
  congela, captura de la página 2 del diagnóstico y
  `python tools/diag_read.py --shot X.png --repro --bin work/live/game.bin`.
- **U2:** Etapa 7 (`cmp_ref.py` de la capa 2 contra la referencia).
- **U3**, opcional: probar en una A500 real.


### Qué se hizo (escrito en la revisión posterior, 2026-10-06)

El cierre original de esta sesión dejó los docs sin commitear, D1 sin
commitear en su worktree y G5a declarada como puerta aprobada. Se revisó
todo y quedó así:

- **G3** integrada en `3b42a2e`: SG3F/2, 2593 peticiones + Rex legal,
  64 528 B DMA / 72 724 B tablas, cero diferencias; loader opt-in replay y
  vivo, 7 casos negativos por modo en Unicorn, arranque WinUAE KS 1.2.
  Arreglos de la revisión: `525984a` (la CRC32 bit a bit costaba 46,9 M
  ciclos = 6,62 s de arranque en Musashi; por tabla, 12,6 M = 1,78 s) y,
  en la fusión `58784d9`, el loader pasa detrás de los datos: antes de
  `entry` rompía BENCH + D1TRACE (bsr a más de 32 KB, P102). Memmap
  replay/vivo: chip 455 728 / 467 256 B, slow 287 888 / 324 120 B.
- **D1**: el trabajo estaba sin commitear en `wt/d1-1006`. Commit
  `d30403a` + fusión `58784d9`. La revisión conectó `test_d1_trace.py` a
  `regress.py` (la función existía pero no se llamaba; el informe decía
  que sí), devolvió un comentario a su sitio y borró un directorio basura
  `%SystemDrive%`. Builds por defecto, replay, BENCH y SPR_OAM+BENCH
  idénticos byte a byte antes y después. Compuerta roja en estrés con
  `SPR_OAM`: 714/4126 y 100/1914 VBL repetidos sin traza
  (`docs/medida-d1-winuae.md`).
- **G5a no se cumplió.** La rama (`a2da1fd`; el `9d9e497` que citaba el
  handoff era un commit enmendado, fuera de toda rama) escribe la posición
  y los colores de **un solo frame** (oráculo 6277) en todas las listas:
  en el replay el Rex queda fijo en la pantalla mientras la cámara se
  mueve, y en las líneas 160-191 Mario toma los colores del Rex (los dos
  usan COLOR17-31 en modo attached); debajo se "restauraba" siempre la
  paleta 0. Lo vio el usuario. Se fusionó y se revirtió (`652b23c`).
  A/B medido en la revisión (WinUAE cycle-exact, 1132 frames, mismos
  binarios que la rama): bench 6435, sin DMA 6443, vacío 5245 ticks de
  media: el recorte cuesta +1190 ticks (+8,4 % del frame). `level_frame`
  con OAM ampliada: 49,4 % PAL.
- Lint y `regress.py --baseline tools/baseline_pc.json --level` en verde
  en cada commit. En la PC hay que poner `ucrt64` primero en el PATH y usar
  el `python` de WindowsApps (`docs/reglas-ola-pc.md`); si no, "FALLO build
  PC" sin mensaje y falta `machine68k`.


---

## 2026-10-07 — L-OAM asm / G5a-bis fase A

PROXIMO anterior, archivado textual al cerrar la sesión:

# PRÓXIMO — lo que sigue

> **Este es el único lugar que dice qué se hace a continuación.** Si otro
> documento dice otra cosa, manda este. Se **reescribe en el sitio** al
> cerrar cada sesión (regla de cierre: `ROADMAP.md` §7); lo que reemplaza
> se archiva en `docs/archivo/sesiones.md`. No se agregan secciones
> "próxima sesión" en ningún otro fichero.
>
> Estado de cada etapa: `ROADMAP.md` §1 · olas y sesiones: `ROADMAP.md` §4 ·
> tarjetas con su estado: `SUBAGENTES.md` §4 · índice de docs: `docs/README.md`.

**Escrito el 2026-10-06 y actualizado el 2026-10-07**, después de revisar
el cierre de la sesión G3/G5a/D1 (detalle en `docs/archivo/sesiones.md`,
al final) y del paso 1 de L-OAM.

- **G3 integrada** (`3b42a2e`, corregida en `525984a` y `58784d9`): banco
  acotado SG3F/2, 2593 peticiones + Rex legal, 64 528 B DMA / 72 724 B
  tablas, cero diferencias; loader opt-in (`SPR_BANK`) en replay y vivo.
  La revisión arregló dos cosas: la CRC32 bit a bit costaba **6,62 s de
  arranque** (ahora 1,78 s, por tabla) y el loader, incluido antes de
  `entry`, rompía el build BENCH + D1TRACE (P102); ahora va detrás de los
  datos. Memmap: chip 455 728 / 467 256 B, slow 287 888 / 324 120 B
  (replay/vivo), cero violaciones. `docs/informe-g3-final.md`.
- **D1 integrada como medida** (`d30403a`, fusión `58784d9`): traza v2
  opt-in (`D1TIMER`/`D1TRACE`), builds por defecto idénticos byte a byte.
  **La compuerta D1 está roja** en estrés (WinUAE, sin traza, fotos
  perdidas / racha):

  | replay | sin `SPR_OAM` | con `SPR_OAM` antes | con `SPR_OAM` tras L-OAM paso 1 |
  |---|---|---|---|
  | `stress_back` | 3,51 % / 3 | 17,28 % / 48 | 14,93 % / 38 |
  | `stress_sprites` | 0 % / 0 | 5,17 % / 10 | 2,93 % / 4 |
  | `yi1` (replay entero) | 0,22 % / 1 | — | 0,44 % / 1 |

  El banco G3 no agrega nada por frame. La traza D1 v2 suma 403/169 ticks
  de media: sus p99/edad/ventana250 describen el build instrumentado.
  `docs/medida-d1-winuae.md`, `docs/instrucciones-loam.md` §4.
- **G5a NO está hecha.** La rama `wt/g5a-1006` (`a2da1fd`) pega el Rex de
  **un solo frame** (oráculo 6277) en una posición fija de pantalla: en
  movimiento el Rex se queda quieto con la cámara, y en sus líneas
  (160-191) Mario, que también usa COLOR17-31, toma los colores del Rex.
  El "0/57344 píxeles" vale solo en ese frame. La fusión se revirtió
  (`652b23c`); la rama se conserva. Lo que sí sirve de ella: el armado
  PT/POS/CTL en la línea 157 h=$40 después del DMA de SPR7, y el A/B en
  WinUAE de esta revisión (1132 frames): escribir el recorte cuesta
  **+1190 ticks de media (+8,4 % del frame)**; el DMA de los cuatro
  sprites, casi nada (bench 6435 / sin DMA 6443 / vacío 5245 ticks).
- La lógica con la OAM ampliada (G8b), tras el paso 1 de L-OAM
  (`4b713c4`), llega a **43,1 %** del frame en el replay entero de YI1 y
  a 79,3 % en `stress_back` (WinUAE); sin ella, 29,5 % y 55,0 %. Objetivo
  ≤ 40 % en YI1: incumplido por ~3 puntos.

---

## 1. La próxima sesión: L-OAM y el primer Rex de verdad

**Objetivo:** que el Rex aparezca donde dice la OAM del juego **en cada
frame**, con la paleta de Mario intacta, comparado contra el oráculo en
muchos frames y no en uno; y antes, que la OAM ampliada deje de hundir la
lógica.

Modelos: los de `SUBAGENTES.md` §1 (el usuario decide cuál; la sesión
anterior entregó G5a como hecha sin serlo, así que **el coordinador
reproduce cada puerta antes de aceptarla**).

| tarjeta | nivel | toca | entrega y puerta |
|---|---|---|---|
| **L-OAM** — abaratar la OAM ampliada, **primero** | alto | `player/spr_gfx.c` (+ asm si hace falta), opt-in | **instrucciones paso a paso: `docs/instrucciones-loam.md`**. Paso 1 hecho (`4b713c4`, `finish_oam_write`): `stress_back` con OAM 17,28 % → 14,93 % de fotos perdidas, `level_frame` 83,1 % → 79,3 %; yi1 con OAM 43,1 %. Siguen `rex_gfx` y `finish_oam_write` en asm. Puerta: `level_frame` ≤ 40 % en YI1 con `SPR_OAM` y estrés con OAM no peor que sin ella; lint, regress y `tools/oam68k_gate.sh` en verde |
| **G5a-bis** — Rex desde la OAM, por frame | alto | rama propia; opt-in `SPR_G5` (`SPR_OAM` + `SPR_BANK`) | **instrucciones paso a paso: `docs/instrucciones-g5a-bis.md`**: fase A (modelo offline en todos los frames: variante compatible con la máscara de Mario por línea y plan de escrituras de color con ventana), fase B (el plan en C, PC = 68000), fase C (bloque después de las cargas de `build_mid`, `scrollsim --g5k`, ≥ 10 capturas WinUAE comparadas píxel a píxel). Ningún color ni posición fija |

Sin L-OAM, cualquier dibujo de enemigos se monta sobre una lógica que ya
no deja tiempo al render: G5a-bis puede desarrollarse en paralelo, pero no
se mide su coste hasta que L-OAM cierre.

G4 completo (asignador de columnas para varios enemigos) y G6
(`sprcop_verify.py`) siguen después: G5a-bis es un solo Rex y no los
sustituye.

### Decisión de color y DMA (de G2, sigue vigente)

La imagen única con recargas por fila falla con las reservas reales de
Mario (12/43 formas); se eligen **variantes precalculadas** con flujos DMA
**inmutables** compartidos, que es lo que trae el banco G3. G5 programa PT
completo y POS/CTL por copper (G0); no parchea el banco ni recodifica ni
copia imágenes por frame. Lo que G5a intentó (cargar los 15 colores del
Rex por fila y "restaurar" una paleta fija) es exactamente lo que G2
descartó.

### Lote y límites de memoria

El banco G3 cubre solo el lote acotado: variantes de `yi1`, `normal` y
`spin_kill` con reservas reales de Mario y ocho paletas, más las poses
legales de Rex de `RexGfxRt`. **Fuera**: Banzai, piraña, Chuck, meta,
power-ups, partículas y los bobs de PF1 (G7). Ampliar el lote necesita
otro presupuesto (`docs/informe-g2.md`: con G8b sin Banzai ya son 77 152 B
de DMA, no cabe). Topes: banco ≤ 65 536 B chip; tablas ≤ 98 304 B slow;
trabajo G4/G6 ≤ 32 768 B; fotos 2376 B (`docs/informe-g3-final.md`).

### Antes de lanzar y al cerrar

- Entorno de la PC (`docs/reglas-ola-pc.md`):
  `export PATH="$TEMP/pyshim:/c/msys64/ucrt64/bin:$PATH" VBCC=/c/Users/JC/vbcc PY=python`.
  Sin `ucrt64` primero, gcc falla sin mensaje y `regress.py` dice solo
  "FALLO build PC"; con el `python` de WorkBuddy falta `machine68k`.
- Antes: `python tools/lint_port.py` y
  `python tools/regress.py --baseline tools/baseline_pc.json --level` en
  verde; con `SPR_OAM`, también `sh tools/oam68k_gate.sh` (`regress.py`
  no prueba la OAM ampliada en el 68000); worktree por tarjeta; WinUAE por
  el candado, cada uno cierra solo su PID.
- Medidas de fluidez: `tools/stress_ab_build.sh` → `stress_ab_shots.ps1`
  → `stress_ab_read.sh`, siempre con el control (sin el cambio) en la
  misma tanda.
- Reglas para integrar: `docs/instrucciones-olas.md` §1.3 (obligatorias).
- Al cerrar: la regla de `ROADMAP.md` §7. **Nada sin commitear** en master
  ni en los worktrees.

---

## 2. Después, en orden

Cada paso con su puerta; nada empieza con el anterior en rojo. Guía de
ejecución de cada ola: `docs/instrucciones-olas.md`; detalle técnico:
`docs/plan-tecnico.md` §10; tarjetas: `SUBAGENTES.md`.

1. **G4 + G6** (asignador de columnas y `sprcop_verify.py`) sobre el
   contrato G3.
2. **G5 + G9**: todos los enemigos del lote, comparación automática contra
   la OAM. **Los enemigos se ven en la Amiga.**
3. **Medida de estrés + S5, inmediatamente después de G5**: render completo
   en la vuelta (s ≈ 2832 y 4580), el Banzai y el tramo con más Rex, con
   `tools/stress_ab_*` y la traza D1 ya integrada; sin OAM ampliada el pico
   es `build_mid` en la vuelta (165 % de un frame en s = 4606); después S5 (repartir el trabajo de `build_mid`
   entre frames). Compuerta D1 en fotos omitidas (`ROADMAP.md` §2).
   Para S5: E09 y E10, `docs/investigacion-ports.md` §17.1.
4. **C2/C4** (vlink + loader) para liberar las ~135 KB de tablas de CPU que
   hoy viven en chip; después el segundo PF1 y **G7** (bobs). Para G7:
   E03, E04 y E06, `docs/investigacion-ports.md` §16.2-16.4, §17.1.
5. En paralelo según dependencias: S8 (cámara vertical), P7 (bolas de
   fuego), P9 (monedas, puntos), P10 (reserva), A0/A2 (audio), H2-H4 (HUD),
   T1 (tubería).

## 3. Pendiente del usuario o de la PC

- **U1:** jugar `work/live/game.adf` en WinUAE con teclado (KS 1.2,
  512 KB chip + 512 KB slow). Los enemigos todavía no se dibujan; si se
  congela, captura de la página 2 del diagnóstico y
  `python tools/diag_read.py --shot X.png --repro --bin work/live/game.bin`.
- **U2:** Etapa 7 (`cmp_ref.py` de la capa 2 contra la referencia).
- **U3**, opcional: probar en una A500 real.
- Decidir qué modelo hace G5a-bis (ver arriba).
- `master` va por delante de `origin/master`: sin push hasta que el
  usuario lo diga.


### Qué se hizo

- L-OAM: `e8ec165`, `bbdf201`, `cd5001c`, informe `1fcb5a1`, fusión
  parcial `cb8ba8f`. Rex y Finish en asm; RAM entera PC=68000: 6549
  llamadas, 0 diferencias. Musashi frame 3097: 77756 -> 72900 ciclos.
- WinUAE cycle-exact l4: back OAM 295/4126 (7,15 %, racha 6) contra
  145 (3,51 %, racha 3); sprites OAM 32/1914 (1,67 %, racha 2) contra
  0; yi1 OAM level_frame 41,2 %, 27/6312 fotos (0,43 %, racha 1).
  Puerta L-OAM roja y parada §5 respetada. Tanda independiente coord4
  y revisión del código: docs/informe-coordinacion-1007.md.
- G5a-bis: WIP `8fe712d`, fase A en rama propia. Máscaras A2 y
  variantes exactas; 59318 ventanas vacías y 18 fallos de capacidad.
  El coordinador reproduce el mismo resumen SHA256 y mira las PNG.
  B/C detenidas, ninguna imagen nueva del juego. Informe copiado a
  master; herramientas conservadas en wt/g5bis-1007.
- Preflight y puertas semánticas repetidas por el coordinador, verdes;
  gamecheck integrado 6313 frames, 0 distintos; memmap replay/vivo
  0 violaciones. Sin baselines ni umbrales modificados. P109 agregada.
- PROXIMO reescrito, estados actualizados, no push. Nuevas instrucciones
  para resolver los bloqueos pendientes antes de continuar las olas.


### ROADMAP §4 anterior, superado el 2026-10-07

Se archiva textual porque las dos tarjetas llegaron a parada y se agregó una revisión de diseño al estimado.

## 4. Olas y sesiones (revisado el 2026-10-06)

Una **sesión** = un coordinador + 3-5 subagentes en worktrees, unas horas, e
integración al final. Una **ola** agrupa tarjetas que pueden ir a la vez.
Tarjetas y su estado: `SUBAGENTES.md` §4.

La ronda offline E11-E14 se ejecutó aparte el 2026-10-06. No completa
ninguna tarjeta de la ruta crítica del dibujo: quedan **9-11 sesiones**
(estimado sin cambios), comenzando por el banco de sprites. E11b y E12
no se suman a S5 con la representación actual; detalle y límites en
`docs/experimentos-e11-e14.md`. Se adelantaron A1 (conversor) y G8b (OAM opt-in), y se prepararon los dos replays D1 con contador CSV. La sesión del 2026-10-06 integró G3 y la traza D1 (compuerta roja en estrés: 714/4126 y 100/1914 VBL repetidos sin traza, `docs/medida-d1-winuae.md`). G5a no se cumplió: la rama pega el Rex de un solo frame en posición fija; se revirtió su fusión y queda G5a-bis en `PROXIMO.md`. La lógica con OAM ampliada llega a 49,4 % PAL con DMA. El banco sigue en la ruta crítica; el estimado 9-11 no se reduce por estos avances parciales.

**Hechas: ~5 sesiones** (2026-09-30 a 2026-10-05). Olas 1 y 2 cerradas; la 3
casi. La ola 3 se alargó porque el diseño del dibujo de sprites (G0, G2, G3)
resultó más grande de lo previsto; a cambio se adelantaron la lógica de casi
todos los sprites (P1-P6, P8), Z1 y las grabaciones de la ola 4.

| ola | contenido (lo que falta) | estado | sesiones que faltan |
|---|---|---|---|
| 1. Medir y preparar | — | **cerrada** | 0 |
| 2. 50 Hz (1) | — (S4 descartada, P89) | **cerrada** | 0 |
| 3. 50 Hz (2) + diseños | G2/G3 hechas (lote acotado), traza D1 integrada; G5a-bis (Rex por frame), perfil de la OAM ampliada, D1 sin `SPR_OAM`; A2 y R7. A1 y G8b adelantadas. S5 pasa a la ola 5, junto a G5 | **casi cerrada** | **1** (la de `PROXIMO.md`) |
| 4. Motores y estructura | G4 + G6, G5 + G9, C2 (vlink), S8 (cámara vertical), A0 + A2, P7/P9/P10, T1, I/E sueltas | pendiente | 2-3 |
| 5. Integraciones y 50 Hz con sprites | S5 (+ S3/S6) con G5 ya hecho, C3/C4/C5 (loader), segundo PF1 + G7 (bobs), H2-H4 (HUD), A3/A4 (música) | pendiente | 2-3 |
| 6. El juego completo | Z2-Z6 (punto medio, meta, tiempo, fundidos, poste), T2/T3 (tubería), A5-A8 (efectos, comparación), H5, R7 | pendiente | 2 |
| 7. Segunda ronda de 50 Hz | todo junto contra la compuerta D1 en estrés | pendiente | 1 |
| 8. Cierre | Z7, Z8, U1-U4, arreglos | pendiente | 1 |
| | **total que falta** | | **9-11** (13-16 si hay que serializar, sobre todo por el scroll y el copper) |

El proyecto completo queda en ~14-16 sesiones, contra las 12-15 estimadas el
2026-09-30. Lo que más puede mover la cuenta: el tamaño del banco de
sprites (G5a-bis y ampliación del banco; G3 acotada implementada) y el pico del scroll con G5 encima (S5). Si después de S5 la
compuerta D1 no pasa, se le llevan los números al usuario (§2).

En paralelo, del lado del usuario (PC): jugar cada ADF nuevo (U1), la
Etapa 7 (U2) y, si quiere, una A500 real (U3).

---
