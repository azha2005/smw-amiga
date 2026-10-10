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


---

## 2026-10-07 — G2T, revisión propia del coordinador

**PROXIMO textual que tenía:**

# PRÓXIMO — lo que sigue

> **Este es el único lugar que dice qué se hace a continuación.**
> Se reescribe al cerrar cada sesión (`ROADMAP.md` §7); el texto anterior
> está en `docs/archivo/sesiones.md`. Estados: `ROADMAP.md` §1/§4 y
> `SUBAGENTES.md` §4. Ejecución: `docs/instrucciones-olas.md`.

**Escrito el 2026-10-07**, al cerrar L-OAM asm / G5a-bis fase A.
Revisión independiente: `docs/informe-coordinacion-1007.md`.

- **L-OAM mejora parcial integrada**, `e8ec165` + `bbdf201` + `cd5001c`,
  fusión `cb8ba8f`. `finish_oam_write` y `rex_gfx` en asm para la Amiga,
  C como referencia del PC. RAM PC=68000: 6549 llamadas, 0 distintas.
  Frame 3097 Musashi: 77756 -> 72900 ciclos. Default idéntico.
  **Puerta todavía roja** en WinUAE cycle-exact, tanda l4:

  | replay | sin OAM: fotos / racha | con OAM: fotos / racha | level_frame con OAM |
  |---|---|---|---|
  | stress_back | 145 (3,51 %) / 3 | 295 (7,15 %) / 6 | 73,9 % |
  | stress_sprites | 0 / 0 | 32 (1,67 %) / 2 | 70,7 % |
  | yi1 entero | 14 (0,22 %) / 1 | 27 (0,43 %) / 1 | 41,2 % |

  Se cumplió la parada de `docs/instrucciones-loam.md` §5 tras ambas
  rutinas en asm. No seguir optimizando funciones a ciegas.
  Informe: `docs/informe-loam-1007.md`; segunda tanda independiente
  coord4 y sus números: `docs/informe-coordinacion-1007.md`.
- **G5a-bis detenida en la fase A**, WIP `8fe712d`, rama
  `wt/g5bis-1007` (`../wt-g5bis-1007`). Herramientas/tests en esa rama;
  informe en `docs/informe-g5bis-1007.md`. A2=0 diferencias y
  sin_variante=0 en las tres trazas, pero **59318 ventanas de color
  vacías**, 18 fallos de capacidad. Primer testigo yi1 f5811: COLOR17
  negro en y168 y blanco en y169, ventana `[169,168]`. El coordinador
  reprodujo el resumen idéntico y miró las 12 imágenes.
  **B/C no iniciadas**, por la parada de
  `docs/instrucciones-g5a-bis.md` §3. Escribir CPU asm no resuelve
  ventanas vacías del copper.
- G3 permanece acotada e inmutable: 64528 B DMA / 72724 B tablas;
  banco replay/vivo con último código: chip 455728/467256 B, slow
  287712/323944 B (`memmap.py`, 0 violaciones). No dibuja enemigos.

---

## 1. La próxima sesión: revisar los dos bloqueos antes de implementar

**Recomendación del coordinador; las nuevas tarjetas necesitan fijar sus
instrucciones antes de ejecutar.** Las dos tarjetas originales llegaron
a su condición explícita de parada. No se declara cerrada ninguna ni se
habilitan las fases u olas dependientes con estas puertas en rojo.

| revisión propuesta | modelo | toca | entrega y puerta |
|---|---|---|---|
| **L-OAM: revisar el margen restante y fijar nueva tarjeta** | GPT-6.1 Sol high | informes y perfiles, inicialmente lectura | `docs/instrucciones-revision-1007.md` §1: explicar 41,2 % YI1 y exceso en estrés; propuesta acotada con presupuesto y verificador RAM. Umbrales conservados; no ampliar funciones sin nueva instrucción |
| **G2T: contrato temporal de variantes y recargas** | GPT-6.1 Sol high | modelo offline en rama propia, sobre G5a-bis | `docs/instrucciones-revision-1007.md` §2: determinar si variantes con plazos viables o ventanas horizontales permiten color exacto. Propuesta con testigos, slots reales y presupuesto; nuevo contrato decidido antes de B/C |

Para G2T, empezar por el testigo f5811 y separar compatibilidad por fila
de viabilidad temporal. Dato de partida (sonda `tools/g2t_probe.py` en
`wt/g5bis-1007`, `9d865e2`): el 87 % de las 59318 ventanas vacías son del
propio Rex en filas contiguas, y 1013 de los 2274 frames afectados tienen
otra variante compatible sin ninguna (`docs/instrucciones-revision-1007.md`
§2). La regla A5 de `instrucciones-g5a-bis.md` no modelaba el hueco
horizontal entre filas: era demasiado estricta. La regla vigente elige la primera variante
compatible; **no cambiarla para esconder la puerta roja**. Evaluar
alternativas explícitamente, con capacidad real después de `build_mid`,
reservas de Mario en X/Y y flujos DMA inmutables (P108). Aumentar MOVE
por línea no soluciona una ventana vacía. Cualquier cambio del contrato
se documenta y se vuelve a comprobar en las tres trazas completas.

Antes de lanzar: entorno de `docs/reglas-ola-pc.md`, lint,
`regress.py --baseline tools/baseline_pc.json --level` y
`sh tools/oam68k_gate.sh` verdes; worktree por tarjeta. WinUAE siempre
por el candado, controles en la misma tanda y solo PIDs propios.
Coordinador repite puertas y mira imágenes (`instrucciones-olas.md` §1.3).
Al cerrar: `ROADMAP.md` §7; nada sin commitear.

---

## 2. Después, en orden

Dependencias originales conservadas; no avanzar mientras sus puertas
anteriores estén rojas (`docs/instrucciones-olas.md`, `SUBAGENTES.md`).

1. Cerrar L-OAM y G5a-bis con instrucciones de revisión resueltas.
2. G4 + G6, luego G5 + G9, con todos los enemigos del lote G3.
3. Medida de estrés con G5 y S5 inmediatamente después (picos de
   `build_mid`, compuerta D1 en fotos omitidas).
4. C2/C4 para liberar tablas CPU de chip; segundo PF1 y G7.
5. Según dependencias: S8, P7/P9/P10, A0/A2, H2-H4 y T1.

## 3. Pendiente del usuario o de la PC

- Fijar las nuevas instrucciones de revisión tras las dos paradas.
  Recomendación: contrato temporal G2T y revisión acotada del coste OAM,
  con Sol high; mantener fidelidad, 50 Hz y umbrales actuales.
- U1: jugar `work/live/game.adf` con teclado, KS1.2, 512 KB chip +
  512 KB slow. Los enemigos aún no se dibujan; diagnóstico si congela.
- U2: comparación de capa 2 contra la referencia (`cmp_ref.py`).
- U3 opcional: A500 real.
- No push hasta indicación explícita del usuario.


**Qué se hizo:** G2T revisada sin subagentes: referencia G5 original reproducida (mismo SHA256), auditoría de3404 frames y tres alternativas; ocho recargas entre filas medidas en WinUAE cycle-exact, con control temprano negativo. Cruce PAL255: dos ensayos fallidos y barrera única final con0 errores; seis positivos exactos y negativo27 px. Herramientas/tests de revisión y contrato candidato en docs/informe-g2t-1007.md y docs/instrucciones-g2t-a.md. Banco y juego originales intactos. G5 A-T completa y B/C pendientes; L-OAM no cambia. Esta entrega no autoriza fases dependientes. Red de seguridad y commits se registran en el informe.


**Estimado ROADMAP§4 anterior, textual (sustituido tras G2T):**

## 4. Olas y sesiones (revisado el 2026-10-07)

Una sesión agrupa coordinación, agentes en worktrees, revisión e integración.
Tarjetas y estados: `SUBAGENTES.md` §4. La sesión L-OAM/G5a-bis del
2026-10-07 integra una mejora de lógica, pero **no cierra tarjetas**:
L-OAM queda en 41,2 % de lógica YI1 y estrés peor que su control;
G5a-bis se detiene en A por ventanas de color vacías. Los dos bloqueos
se reproducen y se detallan en `docs/informe-coordinacion-1007.md`.
Las olas 1 y 2 siguen cerradas. La 3 necesita revisar las instrucciones
antes de continuar implementación, sin cambiar sus umbrales.

| ola | contenido (lo que falta) | estado | sesiones que faltan |
|---|---|---|---|
| 1. Medir y preparar | — | **cerrada** | 0 |
| 2. 50 Hz (1) | — (S4 descartada, P89) | **cerrada** | 0 |
| 3. 50 Hz (2) + diseños | G2/G3 acotadas y traza D1 integradas; L-OAM asm parcial (41,2 % YI1, estrés rojo), G5a-bis detenida fase A (ventanas vacías). Revisión temporal y nueva tarjeta de coste antes de retomar; A2 y R7. A1/G8b adelantadas | **pendiente de revisión de las dos puertas rojas** | **2 estimadas** (revisión + implementación, sin garantizar cierre) |
| 4. Motores y estructura | G4 + G6, G5 + G9, C2 (vlink), S8 (cámara vertical), A0 + A2, P7/P9/P10, T1, I/E sueltas | pendiente | 2-3 |
| 5. Integraciones y 50 Hz con sprites | S5 (+ S3/S6) con G5 ya hecho, C3/C4/C5 (loader), segundo PF1 + G7 (bobs), H2-H4 (HUD), A3/A4 (música) | pendiente | 2-3 |
| 6. El juego completo | Z2-Z6 (punto medio, meta, tiempo, fundidos, poste), T2/T3 (tubería), A5-A8 (efectos, comparación), H5, R7 | pendiente | 2 |
| 7. Segunda ronda de 50 Hz | todo junto contra la compuerta D1 en estrés | pendiente | 1 |
| 8. Cierre | Z7, Z8, U1-U4, arreglos | pendiente | 1 |
| | **total que falta** | | **10-12 estimadas**, incluyendo una revisión adicional de los bloqueos; 14-17 si hay que serializar |

Estimado actualizado: 10-12 sesiones restantes, una más que las 9-11
anteriores para revisar los bloqueos; no garantiza que una sola revisión
los resuelva. Proyecto completo ~15-17 sesiones estimadas (14-17 restantes
si hay que serializar). El estimado anterior se archiva textual en
`docs/archivo/sesiones.md`. E11-E14, A1 y G8b son avances previos parciales
que no cierran las tarjetas de dibujo ni reducen por sí solos la ruta crítica.

Lo que más mueve el estimado: viabilidad temporal del banco G3, alcance
de la siguiente optimización OAM, G5 integrado y el pico del scroll con
enemigos (S5). Las decisiones de 50 Hz y fidelidad permanecen vigentes.
El trabajo del usuario en la PC (U1-U3) sigue registrado en `PROXIMO.md`.

---


## 2026-10-07 (noche) — G2T-A: contrato fijado y puerta A-T verde

PRÓXIMO que regía (escrito el 2026-10-07 al cerrar la revisión G2T), textual:

> > **Este es el único lugar que dice qué se hace a continuación.**
> > Se reescribe al cerrar cada sesión (`ROADMAP.md` §7); el texto anterior
> > está en `docs/archivo/sesiones.md`. Estados: `ROADMAP.md` §1/§4 y
> > `SUBAGENTES.md` §4. Ejecución: `docs/instrucciones-olas.md`.
>
> **Escrito el 2026-10-07**, al cerrar la revisión G2T del coordinador.
>
> - **G2T revisión entregada**, sin subagentes: `docs/informe-g2t-1007.md`.
>   Tres trazas,3404 frames con Rex. Cambiar solo la selección A5 deja1261
>   frames sin plan; ensayo estable incompleto (995 frames sin asignación).
>   Cota horizontal8 MOVE:0 sin plan lógico; cota antigua C2:189 sin plan.
>   **WinUAE cycle-exact:** ocho recargas desde h=$D0 exactas en el banco
>   sintético; control temprano $C0 detecta27 píxeles erróneos. Cruce
>   PAL255 con barrera única antes del sufijo:64 ->0 errores. No equivale
>   a tener un plan calibrado completo ni un dibujador de enemigos.
> - **Contrato candidato A3-T/A5-T/C2-T** en `docs/instrucciones-g2t-a.md`:
>   primera variante compatible con plan temporal válido, intervalos X/Y,
>   banco inmutable, WAIT+8 MOVE, barrera255 única. **Propuesta pendiente
>   de fijar**, antes de implementarla. Segmento +36 B, dos listas +16128 B
>   chip estimados (incluye WAIT). No se cambia la puerta roja anterior.
> - **G5a-bis sigue detenida en A**, WIP `8fe712d`. Su referencia original
>   y tests se incorporan como evidencia, sin modificar A3/A5: resumen
>   SHA256 `3d254a01…4722f8b7` reproducido, A2=0, sin_variante=0,
>  59318 ventanas vacías. **B/C no iniciadas**.
> - **L-OAM mejora parcial integrada**, fusión `cb8ba8f`: Finish y Rex asm,
>  6549 llamadas PC=68000, RAM idéntica. WinUAE l4/coord4: YI1 con OAM
>  41,2% >40%; back295 fotos contra145 del control, sprites32 contra0.
>   Parada original respetada. Revisión de coste aún pendiente;
>   `docs/informe-loam-1007.md`, `docs/informe-coordinacion-1007.md`.
> - G3 acotada:64528 B DMA/72724 B tablas, banco intacto; chip replay/vivo
>  455728/467256 B, slow287712/323944 B. Los enemigos no se dibujan.
>
> ---
>
> ## 1. La próxima sesión: fijar el contrato y probar toda la fase A-T
>
> **Recomendación; fijar el contrato candidato antes de ejecutar la nueva
> tarjeta.** La revisión G2T está entregada; las puertas G5 y L-OAM siguen
> rojas. No implementar B/C ni olas dependientes con este estado.
>
> | tarjeta propuesta | modelo | toca | entrega y puerta |
> |---|---|---|---|
> | **G2T-A: timeline calibrado y puerta horizontal offline** | GPT-6.1 Sol high | `tools/g2t_ref.py` nuevo, tests, `scrollsim.py`, banco sintético | `docs/instrucciones-g2t-a.md`: calibrar slots reales, controles y todas las cargas;3404 frames,0 sin_variante_temporal/sin_plazo/errores_color/capa1/prioridad. Banco≤65536, tablas≤98304, trabajo≤32768. Repetición e imágenes del coordinador antes de B/C |
> | **L-OAM: revisar margen y nueva tarjeta acotada** | GPT-6.1 Sol high | informes/perfiles, inicialmente lectura | `docs/instrucciones-revision-1007.md` §1: diagnóstico de41,2%/estrés y propuesta acotada; conservar≤40% y estrés no peor que control; no ampliar funciones sin instrucciones nuevas |
>
> Preflight: entorno PC, lint, regress `--baseline tools/baseline_pc.json
> --level`, OAM68K verdes; worktree por tarjeta. WinUAE cycle-exact por
> candado, controles en la misma tanda y solo PIDs propios. Cada commit
> pasa red de seguridad; cierre ROADMAP§7, nada sin commitear.
>
> ## 2. Después, en orden
>
> 1. Nueva A-T verde y L-OAM resuelta; escribir las instrucciones B/C
>    con el contrato temporal medido y cerrar G5a-bis.
> 2. G4+G6, luego G5+G9, con todos los enemigos del lote G3.
> 3. Estrés con G5 y S5 inmediatamente después; compuerta D1 sin rebajas.
> 4. C2/C4 para liberar tablas CPU de chip; segundo PF1 y G7.
> 5. Según dependencias: S8, P7/P9/P10, A0/A2, H2-H4 y T1.
>
> ## 3. Pendiente del usuario o de la PC
>
> - Fijar el contrato candidato temporal G2T-A; el informe ya contiene
>   alternativas, evidencia y límites. Mantener fidelidad y50Hz.
> - U1: jugar `work/live/game.adf` con teclado, KS1.2,512KB chip+512KB slow.
>   Enemigos aún no dibujados; diagnósticos si congela.
> - U2: comparación de capa2 contra la referencia (`cmp_ref.py`).
> - U3 opcional: A500 real.
> - No push hasta indicación explícita del usuario.

**Qué se hizo** (coordinador sin subagentes, delegación del usuario:
«hacelo, te doy libertad creativa»; rama `wt/g2ta-1007`):

- Partida repetida en verde; G5 original con el mismo SHA256 del resumen
  y auditoría G2T igual (3404 frames, 0/189).
- **El contrato candidato no era físicamente válido.** La suite `main`
  de `tools/g2t_cal.py` (borrado con COLOR01 al final y carga en x = 7)
  mostró que WAIT + 8 MOVE tras x = 255 lleva la carga de la línea
  siguiente a x = 47..119 (P111). Suite `cap`: caben 12 − nb MOVE.
- Sonda `knee`: el modelo de copper es exacto salvo el paso 231 → 243
  (P110); efecto en el scroll actual: 5119 → 5110 px de capa 1 mal.
- **Contrato fijado** (`docs/instrucciones-g2t-a.md` §1-bis): sufijo tras
  la última carga con cadena o WAIT con copper libre, último MOVE en
  x ≤ 351 − 8·nb, sin sufijo en la línea 255, armado en un bloque VBL.
- Suite `final` (83 casos: 56 positivos exactos, 27 negativos
  detectados, WinUAE cycle-exact, 14202-14211 ticks).
- `tools/g2t_ref.py`: **puerta A-T verde** en las tres trazas (0 sin
  plazo/variante, 0 errores de color/capa 1/prioridad, Mario Amiga = SNES
  en 5398 registros; 69 293 transiciones; siempre la primera variante A3).
  `tools/test_g2t_ref.py` (10) en regress. Commit `70a0c0d`.
- Pendiente: G2T-B/C, revisión L-OAM (41,2 %). Informe:
  `docs/informe-g2t-a-1007.md`.

---

# Sesión 2026-10-08 — continuación de B35 en g2t-b35

# PRÓXIMO — lo que sigue

> **Este es el único lugar que dice qué se hace a continuación.**
> Se reescribe al cerrar cada sesión (`ROADMAP.md` §7); el texto anterior
> está en `docs/archivo/sesiones.md`. Estados: `ROADMAP.md` §1/§4 y
> `SUBAGENTES.md` §4. Ejecución: `docs/instrucciones-olas.md`.

**Escrito el 2026-10-07 (noche)**, al cerrar G2T-A.

> **Actualización 2026-10-08 (ola en curso, antes del cierre).**
> Integrado en master: C1 (`7df7ebe`, `ab50698`), la revisión L-OAM
> (`bf950d4`, `docs/informe-revision-loam-1007.md`) y el WIP de B2
> (`876d28d`: envolvente exacta, pero 231 612 ciclos contra 3000).
> Siguiente: tres tarjetas en paralelo, con instrucciones detalladas:
> `docs/instrucciones-g2t-b2bis.md`, `docs/instrucciones-g2t-b35.md` y
> `docs/instrucciones-g2t-cpre.md` (la única con WinUAE). Después, la
> ruta de la piraña en asm (tarjeta propuesta por la revisión L-OAM; la
> puerta de estrés de L-OAM se redefine como «no peor que la medida
> `l4`», 295/32 fotos omitidas, salvo otra decisión del usuario).

- **G2T-A hecha, contrato fijado** (delegación del usuario):
  `docs/instrucciones-g2t-a.md` §1-bis, informe
  `docs/informe-g2t-a-1007.md`, código `70a0c0d`. El candidato de G2T era
  inviable: tras x = 255 caben solo 12 − nb MOVE antes de retrasar la
  línea siguiente (P111). Codo del copper: 231 → 243 (P110).
- **Puerta A-T verde** en las tres trazas (3404 frames con Rex): 0 sin
  plazo, 0 sin variante, 0 errores de color, capa 1 y prioridad; Mario
  desde sus flujos = SNES en 5398 registros. 56 casos exactos y 27
  negativos detectados en WinUAE cycle-exact (`tools/g2t_cal.py` suites
  main/cap/final/knee). Presupuesto **estimado** +16 384 B chip.
- **L-OAM sigue roja** (41,2 % > 40 %; estrés peor que el control).
- Los enemigos todavía no se ven en la Amiga.

---

## 1. La próxima sesión: G2T-B (plan en C/68000) y revisión L-OAM

**Recomendación:** dos tarjetas en paralelo, worktree cada una. La fase C
de G2T (copper del juego, WinUAE) se ejecuta en la misma tarjeta solo si
B queda verde; su compuerta D1 se informa contra control pero no se
declara cerrada con L-OAM roja.

| tarjeta propuesta | modelo | toca | entrega y puerta |
|---|---|---|---|
| **G2T-B/C: el plan del Rex en el juego** | GPT-6.1 Sol high | `player/g5plan.c` y `g5.s` nuevos, `game.s`/`scroll.s` bajo `SPR_G5`, `marioverify.c`, `mkscroll.py --g5`, herramientas nuevas | `docs/instrucciones-g2t-bc.md`: B2 envolventes de la foto = modelo, ≤ 3000 ciclos; B4/B5 plan PC = 68000 = `g2t_ref.py` byte a byte; C3 listas reales en regla; C4 0/57344 px en ≥ 12 frames; builds por defecto idénticos |
| **L-OAM: revisar margen y nueva tarjeta acotada** | GPT-6.1 Sol high | informes/perfiles, inicialmente lectura | `docs/instrucciones-revision-1007.md` §1: diagnóstico del 41,2 %/estrés y una propuesta acotada; conservar ≤ 40 % y estrés no peor que el control |

Preflight: entorno PC, lint, regress `--baseline tools/baseline_pc.json
--level`, OAM68K y la puerta A-T (`g2t_ref.py`) verdes; WinUAE
cycle-exact por candado, controles en la misma tanda, solo PIDs propios.
Cada commit pasa la red de seguridad; cierre según ROADMAP §7.

## 2. Después, en orden

1. G2T-C completa y L-OAM verde; cerrar G5a-bis como G2T.
2. G4+G6, luego G5+G9, con todos los enemigos del lote G3 (reuso de
   canales a mitad de pantalla con el protocolo G0 y la regla P111).
3. Estrés con G5 y S5 inmediatamente después; compuerta D1 sin rebajas.
   Revisar P110 en el scroll (5110 px con el paso medido).
4. C2/C4 para liberar tablas CPU de chip; segundo PF1 y G7.
5. Según dependencias: S8, P7/P9/P10, A0/A2, H2-H4 y T1.

## 3. Pendiente del usuario o de la PC

- Revisar el contrato fijado (`docs/instrucciones-g2t-a.md` §1-bis) si
  querés otra decisión; lo fijé con tu delegación y con las medidas.
- U1: jugar `work/live/game.adf` con teclado, KS 1.2, 512 KB chip + 512 KB
  slow. Enemigos aún no dibujados; diagnósticos si congela.
- U2: comparación de capa 2 contra la referencia (`cmp_ref.py`).
- U3 opcional: A500 real.
- No push hasta indicación explícita del usuario.

## Resultado de esta sesión

- Se continuó el handoff `307394a`/`dac4244` sobre `g2t-b35`; commits `213ba3c` y `06e777f`, sin merge a master ni push.
- Único intento en C: filas activas, Mario una vez y validez por bits. B4/B5 exactas en 3404 frames; 762 496 filas de segmentos exactas, ABI distinta 0.
- Media 0,96–1,03 M y máximo 2 405 022 ciclos sin DMA (Musashi), frente a 8000. B35 queda parcial por coste; no se implementó asm ni integración en vivo.
- Paso 4c OAM68K (seis ok), ocho tests G5EV en regress, 68 480 casos de recorte exactos, negativos, lint, regress --level y cinco hashes por defecto verdes.
- G5EV 133 040 B; área de trabajo 29 952 B. Memmap replay/vivo: 0 violaciones; vivo slow libre 191 016 B, con esas dos reservas quedarían 28 024 B estimados.
- Perfil y evidencia: `docs/informe-g2t-b35-1008.md`; instrucciones de viabilidad `docs/instrucciones-g2t-b35-asm.md`. B2bis y Cpre no se hicieron en esta continuación.

## Estimado sustituido del ROADMAP

Estimado actualizado tras G2T-A: 9-12 sesiones restantes (una menos: la
puerta offline calibrada quedó hecha en la misma sesión que fijó el
contrato). No garantiza que B/C cierren en una sesión. Proyecto completo
~15-17 sesiones estimadas (13-17 restantes si hay que serializar).


## 2026-10-08 — fase de medida B35-asm

Archivado textual al entregar `a9b44fe`: transiciones asm exactas en 3404 frames, pero máximo 18 794 ciclos solo en ese núcleo. Integración detenida según §4.5; B2bis/Cpre revisadas, sin entregas locales. Informe: `docs/informe-g2t-b35-asm-1008.md`.

# PRÓXIMO — lo que sigue

> **Este es el único lugar que dice qué se hace a continuación.**
> Se reescribe al cerrar cada sesión (`ROADMAP.md` §7); el texto anterior
> está en `docs/archivo/sesiones.md`. Estados: `ROADMAP.md` §1/§4 y
> `SUBAGENTES.md` §4. Ejecución: `docs/instrucciones-olas.md`.

**Escrito el 2026-10-08**, al cerrar la continuación de B35 en
**`g2t-b35`**. No está integrado en master y no se hizo push.

- B35: `307394a` + `dac4244` + `213ba3c` + `06e777f`. B4/B5 exactas en **3404 frames**,
  ABI intacta, segmentos exactos en **762 496 filas**. Paso 4c de OAM68K,
  ocho tests G5EV en regress, negativos y cinco hashes por defecto verdes.
- **Único intento en C agotado**: media 0,96–1,03 millones, máximo
  **2 405 022 ciclos sin DMA frente a 8000**. Sigue inviable en vivo.
  Perfil, comandos y memoria: `docs/informe-g2t-b35-1008.md`.
- Vivo `SPR_G5` + banco G3: slow libre 191 016 B. Tras reservar G5EV
  (133 040) y `g5_work` (29 952), quedarían **28 024 B estimados**, antes
  de caché B2bis, fotos, salidas y pila. Auditar todas las reservas juntas.
- En master siguen C1 (`7df7ebe`, `ab50698`), revisión L-OAM (`bf950d4`)
  y B2 (`876d28d`, exacta pero máximo 231 612 ciclos). G2T-A y su
  contrato siguen verdes. L-OAM/D1 siguen rojas; enemigos aún no visibles
  mediante el plan B35 en el juego.

## 1. La próxima sesión: viabilidad de B35, B2bis y Cpre

**Recomendación:** comenzar por la fase de medida de B35-asm; una
traducción directa no garantiza el presupuesto. Continuar o revisar las
entregas existentes de B2bis/Cpre en sus ramas antes de relanzarlas.
Cpre puede probar el emisor con datos offline; el plan en vivo espera
las puertas de rendimiento y memoria de B.

| tarjeta propuesta | modelo | toca | entrega y puerta |
|---|---|---|---|
| **G2T-B35-asm: viabilidad del plan exacto** | Codex | núcleo del planificador y arneses opt-in; inicialmente sin juego ni scroll | `docs/instrucciones-g2t-b35-asm.md`: perfil, representación dispersa y microbenchmarks; B1 idéntico, ABI/PIC correctos, plan completo ≤ 8000 ciclos máximo; parar la integración si no hay ruta medida |
| **G2T-B2bis: envolvente barata de Mario** | según tarjeta | foto, clave MA1, caché/decodificación en slow y frontera B2/B3 | `docs/instrucciones-g2t-b2bis.md`: envolventes exactas; captura de clave ≤ 300 ciclos, acierto ≤ 600, fallo ≤ 12 000; sumar su memoria a la reserva de B35 |
| **G2T-Cpre: emisor con plan precalculado** | según tarjeta | `g5_emit`, listas del replay bajo `SPR_G5`, verificador y capturas WinUAE | `docs/instrucciones-g2t-cpre.md`: listas en regla y 0/57 344 px en ≥ 12 frames; coste contra control, sin declarar D1 cerrada |

Preflight: lint, regress `--baseline tools/baseline_pc.json --level`,
OAM68K completo (seis líneas `ok G2T-B5`) y A-T verdes. Repetir hashes
por defecto antes de cada commit opt-in. WinUAE cycle-exact por candado,
controles en la misma tanda, solo PIDs propios. Cierre según ROADMAP §7.

## 2. Después, en orden

1. Revisar e integrar las ramas solo después de repetir sus puertas.
   B35 sigue como control exacto WIP; integración en vivo únicamente con
   rendimiento y reservas completos. Completar G2T-C y cerrar G5a-bis
   como G2T cuando también se cumplan sus puertas visuales.
2. Ruta de la piraña en asm propuesta por la revisión L-OAM, con tarjeta
   detallada antes de implementarla. Conservar la puerta de lógica ≤ 40 %;
   el control de estrés acordado es l4 (295/32 fotos), sin rebajar D1.
3. G4+G6 y G5+G9 con todos los enemigos del lote G3; luego estrés con G5
   y S5 contra D1 (fotos omitidas ≤ 0,1 %, racha 1). P110 en el scroll:
   todavía 5110 px con el paso medido.
4. C2/C4 para liberar tablas CPU de chip y revisar slow; segundo PF1/G7.
5. Según dependencias: S8, P7/P9/P10, A0/A2, H2-H4 y T1.

## 3. Pendiente del usuario o de la PC

- U1: jugar `work/live/game.adf` con teclado, KS 1.2, 512 KB chip +
  512 KB slow; enemigos aún no dibujados, diagnósticos si congela.
- U2: comparación de capa 2 contra la referencia (`cmp_ref.py`).
- U3 opcional: A500 real.
- Mantener la rama B35 separada de master mientras siga inviable para
  el juego en vivo. No push sin instrucción explícita.


---

# Archivo del PROXIMO anterior a B2bis (2026-10-08)

# PRÓXIMO — lo que sigue

> **Este es el único lugar que dice qué se hace a continuación.**
> Se reescribe al cerrar cada sesión (`ROADMAP.md` §7); el texto anterior
> está en `docs/archivo/sesiones.md`. Estados: `ROADMAP.md` §1/§4 y
> `SUBAGENTES.md` §4. Ejecución: `docs/instrucciones-olas.md`.

**Escrito el 2026-10-08**, al cerrar la fase de medida B35-asm en
**`g2t-b35`** (`a9b44fe`). Sin merge a master ni push.

- B35: `307394a` + `dac4244` + `213ba3c` + `06e777f`. B4/B5 exactas en **3404 frames**,
  ABI intacta, segmentos exactos en **762 496 filas**. Paso 4c de OAM68K,
  ocho tests G5EV en regress, negativos y cinco hashes por defecto verdes.
- **Único intento en C agotado**: media 0,96–1,03 millones, máximo
  **2 405 022 ciclos sin DMA frente a 8000**. Sigue inviable en vivo.
  Perfil, comandos y memoria: `docs/informe-g2t-b35-1008.md`.
- **Primer prototipo asm disperso medido**: transiciones exactas en los
  3404 frames, ABI/PIC correctos, pero **18 794 ciclos solo en ese núcleo**.
  No hay ruta medida a 8000 para el plan entero; integración detenida
  según B35-asm §4.5. No traducir el resto sin un nuevo diseño viable.
  Trabajo real, costes y reproducción: `docs/informe-g2t-b35-asm-1008.md`.
- Vivo `SPR_G5` + banco G3: slow libre 191 016 B. Tras reservar G5EV
  (133 040) y `g5_work` (29 952), quedarían **28 024 B estimados**, antes
  de caché B2bis, fotos, salidas y pila. Auditar todas las reservas juntas.
- En master siguen C1 (`7df7ebe`, `ab50698`), revisión L-OAM (`bf950d4`)
  y B2 (`876d28d`, exacta pero máximo 231 612 ciclos). G2T-A y su
  contrato siguen verdes. L-OAM/D1 siguen rojas; enemigos aún no visibles
  mediante el plan B35 en el juego.

## 1. La próxima sesión: B2bis y Cpre independientes del plan en vivo

**Recomendación:** comenzar por B2bis B2b-1/B2b-2 (clave y decoder
aislados), y Cpre C2a (planes sobre listas reales). Se revisaron todas
las ramas locales: **no hay entregas B2bis/Cpre para integrar**. Ambas
pueden avanzar con el C de B35 como control; el plan en vivo sigue
detenido. Antes de reservar caché: N=16/32 con máscaras no entra junto
a G5EV y el work actual; sumar fotos, salidas y pila incluso con N=8.

| tarjeta propuesta | modelo | toca | entrega y puerta |
|---|---|---|---|
| **G2T-B2bis: envolvente barata de Mario** | según tarjeta | foto, clave MA1, caché/decodificación en slow y frontera B2/B3 | `docs/instrucciones-g2t-b2bis.md`: envolventes exactas; captura de clave ≤ 300 ciclos, acierto ≤ 600, fallo ≤ 12 000; sumar su memoria a la reserva de B35 |
| **G2T-Cpre: emisor con plan precalculado** | según tarjeta | `g5_emit`, listas del replay bajo `SPR_G5`, verificador y capturas WinUAE | `docs/instrucciones-g2t-cpre.md`: listas en regla y 0/57 344 px en ≥ 12 frames; coste contra control, sin declarar D1 cerrada |

Preflight: lint, regress `--baseline tools/baseline_pc.json --level`,
OAM68K completo (seis líneas `ok G2T-B5`) y A-T verdes. Repetir hashes
por defecto antes de cada commit opt-in. WinUAE cycle-exact por candado,
controles en la misma tanda, solo PIDs propios. Cierre según ROADMAP §7.

B35 queda en investigación de otro algoritmo exacto. La medición no
demuestra imposibilidad general, pero sí rechaza integrar esta propuesta.
Reabrir únicamente con presupuesto completo medido hacia 8000 y memoria
para todas las reservas; no ampliar el objetivo ni cambiar el contrato.

## 2. Después, en orden

1. Revisar e integrar las ramas solo después de repetir sus puertas.
   B35 sigue como control exacto WIP; integración en vivo únicamente con
   rendimiento y reservas completos. Completar G2T-C y cerrar G5a-bis
   como G2T cuando también se cumplan sus puertas visuales.
2. Ruta de la piraña en asm propuesta por la revisión L-OAM, con tarjeta
   detallada antes de implementarla. Conservar la puerta de lógica ≤ 40 %;
   el control de estrés acordado es l4 (295/32 fotos), sin rebajar D1.
3. G4+G6 y G5+G9 con todos los enemigos del lote G3; luego estrés con G5
   y S5 contra D1 (fotos omitidas ≤ 0,1 %, racha 1). P110 en el scroll:
   todavía 5110 px con el paso medido.
4. C2/C4 para liberar tablas CPU de chip y revisar slow; segundo PF1/G7.
5. Según dependencias: S8, P7/P9/P10, A0/A2, H2-H4 y T1.

## 3. Pendiente del usuario o de la PC

- U1: jugar `work/live/game.adf` con teclado, KS 1.2, 512 KB chip +
  512 KB slow; enemigos aún no dibujados, diagnósticos si congela.
- U2: comparación de capa 2 contra la referencia (`cmp_ref.py`).
- U3 opcional: A500 real.
- Mantener la rama B35 separada de master mientras siga inviable para
  el juego en vivo. No push sin instrucción explícita.


## 2026-10-08 — B2bis: cierre de puertas locales y rendimiento pendiente

Se completaron los pendientes del handoff: ec320ab, G5ENV/lint/regress/OAM68K/hashes verdes. WinUAE exacto: 98 fotos perdidas contra 27 del control; D1 no cerrada. Informe en docs/informe-g2t-b2bis-1008.md. PROXIMO cumplido y handoff anterior, textuales:

# PRÓXIMO — lo que sigue

Escrito el 2026-10-08 al guardar el handoff por límite de uso del usuario.
**B2bis sigue parcial; sin merge a master ni push.**

Worktree activo: `C:/Users/JC/Downloads/sma/wt-g2t-b2bis-1008`, rama
`g2t-b2bis`. Commits `8a4a43d` y `a401723`; integración y optimizaciones
posteriores **sin commit**. Handoff exacto:
`docs/handoff-g2t-b2bis-1008.md`.

Últimas medidas Musashi: cache hit 558 / miss 11904 ciclos, captura 270;
3404 envolventes exactas; O5 real 6313 renders, 2288 fotos Rex exactas,
0 frames > PAL (máximo total 140916). La limpieza final ya se recompiló: game/decode verdes, decoder máximo
10906. **Lint rojo: 12 errores V3 en dc_capture**, resolver antes de commit.
Front/project del nuevo soporte C todavía sin repetir. Memoria, casos de borde,
WinUAE, puerta global y red de seguridad final todavía pendientes.
No declarar 50 Hz ni enemigos visibles: `g5_plan` no está en el render.

## 1. La próxima sesión: completar las puertas de B2bis

| tarjeta | toca | instrucciones y entrega |
|---|---|---|
| **G2T-B2bis cierre** | worktree existente; verificación de cache/foto, memoria y BENCH; gates y documentos | `docs/instrucciones-g2t-b2bis-cierre.md`: retomar sin rehacer pasos verdes, completar todos los pendientes del handoff y red final antes de commit |
| **G2T-Cpre** | emisor con plan precalculado, después del cierre anterior | `docs/instrucciones-g2t-cpre.md`: listas exactas y prueba visual cycle-exact; aún no iniciado |

Leer primero el handoff y la tarjeta de cierre. La autorización del usuario
es seguir iterando hasta cumplir requisitos, sin rebajar exactitud ni coste.
No activar B35 en vivo: el C sigue costando 2405022 ciclos contra 8000.

## 2. Después

Revisar B2bis solo tras repetir sus puertas; completar Cpre/C. Reabrir B35
con otro algoritmo y presupuesto completo medido, incluyendo memoria.
L-OAM/D1 y la ruta OAM de piraña siguen pendientes. Conservar los cinco
hashes por defecto; no tocar `g2t_ref.py`, contrato ni `scroll.s`.

## 3. Pendiente del usuario o la PC

U1: jugar el ADF vivo con teclado/KS1.2/A501. U2: comparación de capa 2.
U3 opcional: A500 real. No hace falta autorización adicional para seguir
las pruebas y correcciones de la tarjeta.


# Handoff G2T-B2bis — 2026-10-08

Cierre solicitado por el usuario al quedar 7 % de uso. **Trabajo parcial, sin integración ni push.**
El usuario autorizó seguir iterando hasta cumplir los requisitos; las paradas por número de intentos de la tarjeta no revocan esa autorización. No declarar B2bis cerrada todavía.

## Ubicación y commits

- Worktree: `C:/Users/JC/Downloads/sma/wt-g2t-b2bis-1008`.
- Rama: `g2t-b2bis`, creada desde `a52e2ba` de `g2t-b35`. La carpeta principal `port-amiga` y master no se tocaron.
- `8a4a43d`: B2b-1, clave MA1 real sin colisiones.
- `a401723`: B2b-2, decoder asm exacto; entonces máximo 11 268 ciclos.
- **Todo lo posterior está sin commit**, incluidos los documentos de este cierre. No hacer commit sin lint, regress con `--level`, OAM68K completo y hashes verdes.
- `player/g5plan.c` aparece modificado por finales de línea, pero `git diff -- player/g5plan.c` no muestra cambios de contenido. Evitar un commit de ruido.

## Resultados medidos y límites

B2b-1: 2288 + 661 + 455 frames. Claves por traza 245/155/139, global 465; 0 colisiones. Hay 32 imágenes visibles y una vacía. Muchísimas claves difieren solamente en punteros de tiles no utilizados.

Última prueba de caché **incluyendo el projector real y la mutación a formato disperso**, `work/b2b/cache_packed.log` y `work/b2b/cache/cache_summary.json`:

| N | traza | hit completo | miss (incluye alias) | alias de imagen | sin clave | máximo hit | máximo miss |
|---|---|---:|---:|---:|---:|---:|---:|
| 8/16/32 | yi1 | 1878 | 410 | 234 | 63 | 558 | 11904 |
| 8/16/32 | normal | 477 | 184 | 158 | 0 | 558 | 11904 |
| 8/16/32 | spin_kill | 279 | 176 | 139 | 0 | 558 | 11904 |

Todas exactas, ABI intacta, canarios de salida/cache/entrada/pila intactos. Estos hashes solo ocupan ocho candidatos en las trazas aunque N sea mayor: N16/32 no aportaron beneficio. **N8** por defecto, 12 452 B incluyendo scratch 2484 + 8 × 1246.

Último O5 completo medido **tras recompilar la limpieza final**: `work/b2b/game_handoff.log`:

- 6313 renders con RAM/OAM/fichas MA1 vivas envenenadas; 2288 fotos con Rex exactas contra `g2t_ref` aplicado a los datos capturados.
- 63 fotos Rex sin clave.
- Captura nueva: **270 ciclos máximo**, cota conservadora incluyendo exposición de fuentes y diferencia de MULU por tamaño DC_REC.
- Render B2bis máximo **46 924 ciclos**, frame 6936.
- Total CPU O5 máximo **140 916 ciclos**, frame 11301; **0 frames > PAL**. Musashi, sin DMA; margen pequeño. **No es prueba de 50 Hz en WinUAE**.
- Foto 5219 → frame del oráculo 10364; el replay empieza en 5145.

**Fixture conocido:** 47 SKIP + 1 SYNC (7600) no coinciden con los volcados PC provisionales de B2. `marioverify` captura antes de deshacer SKIP, pero el replay Amiga conserva gráficos previos; SYNC carga física sin recalcular mgfx. Todas las fotos RUN coinciden también con esos volcados; las 2288 coinciden con el modelo del estado real capturado. No cambiar `g2t_ref.py`, replay, scroll ni hashes para ocultarlo. Documentar explícitamente esta limitación; no afirmar igualdad SNES en esos 48 fixtures. El verificador actual separa SKIP/SYNC en el informe.

Al cerrar se recompiló el build replay final (243428 B) y se repitieron **game y decode**, ambos verdes. El decoder final da **10906 ciclos máximo**, 3404 frames exactos, ABI 0; sinteticos y negativa verdes (`work/b2b/decode_handoff.log`). El soporte C recién añadido para formato 4 todavía no pasó front/project de nuevo. Cache completa se probó antes de esa limpieza, con el mismo ASM. La puerta `game` ahora falla si hay un frame > PAL; antes solo informaba el número.

**BLOQUEO descubierto en el cierre: lint rojo.** `work/b2b/lint_handoff.log`: 12 errores V3 en dc_capture (registros y stack). Los marcadores globales `dc_g5copy_start/end` probablemente hacen que asmlint corte el cuerpo y no vea el MOVEM de retorno. Verificar esta causa, corregir etiquetas/aliases manteniendo los símbolos de medición y demostrar la ABI; **no desactivar lint ni cambiar las declaraciones para silenciarlo**. `git diff --check` pasa. No se hizo commit del trabajo posterior.

## Diseño actual

### Decoder y caché (`tools/g5env_asm.py` → `player/g5env.s`)

Regenerar con `python tools/g5env_asm.py`; no editar el ensamblador generado a mano. Los datos matemáticos son código, no assets ROM.

- `_g5env_decode(spr, out)`: ABI vbcc completa, preserva D2–D7/A2–A6, incluido A4. Máximo salida 2484 B.
- Cabecera: alto.w, formato.w. Formato 1: quince máscaras.w por fila (30 B), todas escritas. Formato 2: presencia.w y quince máscaras.l (62 B), solo significativos los índices presentes. Formato 0: vacío.
- Mono procesa dos filas por vuelta; alto impar entra por la segunda mitad. Se eliminó el EOR de transparencia innecesario. Prueba de decoder actual debe repetirse: el JSON existente puede ser de un intento anterior; no citarlo como versión final.
- `_g5env_lookup(cache, key nullable, spr)`: tabla directa, siempre igualdad completa de 40 B para un hit. Primero compara el interior con punteros que suelen cambiar, luego el prefijo. D1=1 hit completo, D1=0 decoder, D1=2 **miss de clave cuya igualdad de imagen se demuestra**. El coste de alias se cuenta entre los misses, no como hit ≤600.
- Hash: `((key[5] >> 6) ^ (key[21] >> 5) ^ (key[18] >> 6)) & (N-1)`. No determina igualdad, solo candidato.
- Alias conservador: n≤2, tiles de ambas entradas≤2, prefijo de 18 B igual y punteros 0/1/5/6 iguales byte a byte. Esos tiles 16×16 no utilizan otros punteros. Cualquier otro caso decodifica. La prueba inicial compara algunos largos adicionales: puede rechazar un alias válido, nunca aceptarlo sin comprobar los punteros usados.
- No hay filtro horizontal en lookup; si se devolvieron límites compactados y luego la caja cruza el borde, **project** vuelve a decodificar el buffer de la foto en scratch antes del recorte. Probar bien este caso sintético: las trazas tienen 0 recortes horizontales.

### Proyección

- `_g5env_project(blk, spr, data)` materializa la representación B2 original en un bloque de 1292 B. Mantiene las funciones originales `g5_mario_mask/span` y sus firmas; `g5_plan` no se cambia. Se abandonó leer máscaras perezosamente desde esas funciones porque repetía demasiado trabajo. Informar esta elección frente al texto de la tarjeta, no fingir que se reimplementaron ambas.
- Primera proyección completamente dentro de pantalla: empaqueta **formato 4** en el mismo payload máximo de 1204 B. Por fila: presencia.w, (npares−1).w, pares `(offset ENV.w, extremos relativos.w)`. Solo índices utilizados.
- Construye el pack en **1204 B temporales de pila**, copia con MOVEM y conserva las máscaras originales si el pack no cabe. Las filas densas excepcionales continúan por el camino conservador. Primera proyección más cara, warm mucho más barata.
- Camino totalmente visible duplicado por el generador: evita AND y tests de flags por celda; camino recortado conserva las máscaras. El bucle warm tiene BRA explícito a `.return`: sin él caería en la copia del bucle rápido (error ya arreglado).
- Alto/posición salen siempre del sprite de la foto. Recorte antes de hallar extremos. Campos Rex intactos.
- `player/g5env.c/h`: projector **de control**, no el habitual de producción. Tabla matemática `g5env_bounds[256]`. Soporte recién añadido para formato 4 y recorte desde DATA, pendiente repetir PC/vbcc. Formato 2 raro usa este C en producción; ninguna de las tres trazas entra por ese camino. No afirmar coste ≤12000 para dibujos sintéticos arbitrarios de dos columnas.

### Juego opt-in

- `mspr68k.s`, bajo SPR_G5, expone al retornar A0=n/entradas, A1=punteros, D0=validez. L1 apunta a la ficha real; camino fast/free-buffer apunta a mspr_n y RAM de punteros; oculto/C devuelve flag 0.
- `DC_REC`: 8 B por defecto, 50 B con SPR_G5. R_G5HAS=8.w, R_G5KEY=10 (40 B). Copia MOVEM alineada; fuente de punteros está impar.
- Permutación de clave: `natural[:19] + natural[39:40] + natural[19:39]`; mantiene los 40 bytes. `cache_key` reproduce esa permutación.
- Marcadores `dc_g5copy_start/end` para medir captura mediante trampas Musashi. A0/A1/D0 de mspr_draw se preservan hasta dc_recp, 12 ciclos.
- `dc_g5render`: después de build_mid, consulta cache y proyecta **solo la foto DC_REND**. Cache y view en slow, al final del binario para evitar P102/distancias PC. No se llama `g5_plan` en vivo.
- `logicbench_build.sh`: compila `g5plan` + `g5env` bajo SPR_G5; datos de bounds quedan dentro del alcance A4. Cambios auxiliares en `g5plan_work.py` y `oam68k_gate.sh` enlazan g5env.c.
- `gamecheck.py` y `restart_verify.py`: base del arnés 0x8000 si el binario grande no cabe en 0x10000 antes de DATA=0x48000. No aumenta la memoria simulada ni modifica el binario.

## Herramientas y reproducción

PowerShell nativo funciona. Git Bash:

```
export PATH="$TEMP/pyshim:/c/msys64/ucrt64/bin:$PATH" VBCC=/c/Users/JC/vbcc PY=python
```

Invocar un wrapper con `& 'C:/Program Files/Git/bin/bash.exe' work/b2b_gamebuild.sh` desde ESTE worktree. No mezclar escrituras/builds concurrentes: comparten work/cc y logicbench.

Wrappers ignorados disponibles:

- `work/b2b_gamebuild.sh`: build replay SPR_G5 a `work/b2b_r`, log `work/b2b/game_build.log`.
- `work/b2b_front.sh`: recompila logicbench SPR_G5, copia bin/lst a work/b2b y ejecuta front.
- `work/b2b_checks.sh`: lint y regress `--baseline tools/baseline_pc.json --level`, logs en work/b2b.
- `work/b35_memory_hashes.sh`: memoria con banco G3 replay/vivo, cuatro hashes game + logicbench, comparación con work/b35_before/hashes.log. Guarda logs en work/b35_mem_* y work/b35_after.

Comandos verificador:

```
python tools/g5env_verify.py decode
python tools/g5env_verify.py cache
python tools/g5env_verify.py front
python tools/g5env_verify.py project --bin work/b2b_r/game.bin --lst work/b2b_r/game.lst
python tools/g5env_verify.py game --bin work/b2b_r/game.bin --lst work/b2b_r/game.lst
```

`key` genera copia instrumentada del arnés PC en work/b2b/key. Ahora mismo su default bin/lst son work/b35_mem_replay antiguos: para probar la exposición nueva, pasar explícitamente el bin/lst de work/b2b_r.

Fixtures `work/g5gate/cap_{yi1,normal,spin_kill}.bin`, keys `work/b2b/key/key_*.bin`, banco work/g3/bank. Los ignorados ya se copiaron al worktree. **No regenerar/subir ROM ni assets.**

**Pitfall del arnés:** machine68k comparte un núcleo global. No alternar dos Machine vivas en el mismo proceso. En front/project primero predecodificar todas las entradas con EnvCPU, eliminarlo y crear M68k. EnvCPU sí alterna dos bases de código dentro de UNA Machine.

`cache` actualmente monta un fixture pequeño con el asm de producción, tabla matemática, scratch y un `_g5env_bind` inválido intencionado: solo cubre mono. `project_call` controla ABI/canarios/pila y alterna bases. Caso raro ancho doble debe comprobarse con el binario real que contiene el C.

## Pendiente antes de cerrar B2bis

1. Resolver primero los 12 errores de lint; después repetir decode/cache/front/project/game y recompilar lo que cambie. Corregir cualquier rojo; no rebajar umbrales.
2. Ampliar pruebas de **cache compactada → recorte con huecos**, vertical, SPR2 aislado/no-key y formato denso que no cabe en pack; comparar también con projector C y frontera PC. `decode_env` tiene fallback por píxel para packed recortado, pero eso por sí solo NO prueba que ASM lo hizo: comparar view de `project_call`.
3. Repetir source de clave real en L1 con `mspr_n` envenenado, free buffer 2 y hidden/C. run_key actual solo comprueba la ficha de dibujo inicial; faltan esos caminos expuestos.
4. Probar render tardío reteniendo DC_REND, avanzar un dc_cop que obligue a buffer 2, comprobar que foto vieja y DATA no cambiaron, y renderizarla contra referencia anterior. Envenenar RAM ya está probado, pero no sustituye esa prueba.
5. Añadir marcas BENCH de copia de clave y render (GBS/GBR, crecer gb_t solo bajo SPR_G5). Aún no implementadas.
6. `tools/g5env_gate.sh` **todavía no existe**. Debe ejecutar pasos de la tarjeta en las tres trazas y fallar con `G5ENV: FALLO`; terminar `G5ENV: OK` solo si todas pasan. Integrar tests significativos en `tools/test_g5env.py` (ya entra en regress).
7. Gamecheck indicado en tarjeta, build vivo + restart, memmap de **cuatro builds** con/sin banco G3. Auditar reservas conjuntas: G5EV 133040, g5_work 29952, fotos, cache, view, salidas y pila. Último tamaño replay sin banco: 243428 B; memoria final **sin auditar**. No citar números de B35 como actuales. Pila IRQ existente dc_stk=8192, ya forma parte del binario; el pack usa la pila del render, por tanto justificar reserva propia además de IRQ.
8. **WinUAE cycle-exact y evidencia visual pendientes**. Por candado `C:/Users/JC/Downloads/sma/winuae_lock.ps1`, tools/shot.ps1 -Exact; comparar control en la misma tanda, solo PIDs propios. No declarar D1 cerrada con Musashi.
9. Lint, regress --level, **OAM68K entero** (B35 PC+68000 en tres trazas incluidos), cinco hashes por defecto antes de cada commit. Última red completa fue antes de a401723, NO cubre integración actual. No está autorizado merge ni push.
10. Informe final, commits por pasos cerrados, actualizar handoff/PROXIMO/estados. B35 plan sigue inviable (2.405 M vs8000); Cpre todavía sin iniciar. Cumplir B2bis no significa que enemigos ya se dibujen.

Hashes esperados: live c03b569643c7bf5ac62f55cdd2813951a6895a6d4801d1eef241e96cfa422769; replay 9403f71c76bc2df9a92a3cc24d8db1e9e67c47e5e62a558e441c3994d0538109; replay BENCH 2bc486d77af939aedfb183457e33cc41eba172521959bb0192ddbe6f594363bb; replay BENCH SPR_OAM 71071566e75a0c1a9dd5391d8398fc44f69ace2e1a4dd489e936c5f7c8bbfad4; logicbench ec8147ac1989ab7e7714f1db3f3cebbc723730a980aa33158a6a41173e4dc37e.


## Vista solicitada por el usuario (2026-10-08)

Se recompiló `work/b2b_r/game.adf` y se abrió para el usuario en WinUAE
PID 30888 (helper PowerShell 8104). Replay automático, KS1.2, A500 PAL,
512 KB chip + 512 KB slow, config cycle-exact de `a500.uae` en
`work/b2b_r/view.uae`. El helper `work/b2b_r/view-open.ps1` se ejecuta
por `winuae_lock.ps1`, espera el cierre del emulador y entonces libera
el candado. No cerrar esa ventana del usuario como si fuera una prueba
propia abandonada. Sin cambios al código ni commit. No se tomó una
captura ni se midió rendimiento dentro de WinUAE; abrirlo no cierra
la puerta visual/de rendimiento. Enemigos todavía no dibujados.


## 2026-10-08 — segunda iteración B2bis y Cpre parcial

PROXIMO y handoff anteriores, archivados textualmente:

# PRÓXIMO — lo que sigue

2026-10-08. Worktree `C:/Users/JC/Downloads/sma/wt-g2t-b2bis-1008`, rama
`g2t-b2bis`. **Sin merge ni push.** Código de B2b3-5 guardado en `ec320ab`;
clave/decoder en `8a4a43d` y `a401723`.

Se cerraron las puertas locales de B2bis: 3404 frames y 762496 filas
exactos, 258 casos de borde, captura 270 ciclos, cache 558/11904,
reinicios y cuatro memmap verdes. G5ENV, lint, regress con --level,
OAM68K entero y cinco hashes por defecto verdes. Vista WinUAE:
0/327680 píxeles diferentes del control.

**El rendimiento real sigue pendiente:** WinUAE cycle-exact pierde
98 fotos (1,55 %, racha 2) contra 27 del control (0,43 %, racha 1).
La vista compacta bajó de 100 a 98; no alcanza D1. La cota Musashi
0 > PAL no reemplaza esta medida. Vivo G3 deja solo 264 B tras reservas
completas: recuperar margen antes de activar B35 o añadir datos.
Informe: `docs/informe-g2t-b2bis-1008.md`; handoff actualizado:
`docs/handoff-g2t-b2bis-1008.md`.

## 1. La próxima sesión

| tarjeta | toca | instrucciones y entrega |
|---|---|---|
| **G2T-B2bis rendimiento** | perfil frío/cache/vista y memoria; bajar fotos perdidas antes de integrar | `docs/instrucciones-g2t-b2bis-rendimiento.md`: red exacta intacta, control de la misma tanda, no rebajar umbrales ni reservas |
| **G2T-Cpre** | después, emisor con plan precalculado independiente de B35 | `docs/instrucciones-g2t-cpre.md`: C2a control vacío, listas reales exactas y capturas cycle-exact; sin iniciar |

La autorización del usuario es seguir iterando hasta cumplir requisitos.
No tocar modelo, contrato, scroll.s ni banco en B2bis; si el rendimiento
requiere S5/L-OAM, abrir esa tarjeta y leer sus instrucciones primero.
No activar el plan B35 en vivo: la repetición actual cuesta hasta 2423094
ciclos contra 8000. Mantener R9: derivados únicamente en work/.

## 2. Después

Revisar la rama tras cerrar rendimiento y memoria; Cpre/C, rediseño viable
de B35, L-OAM/D1 y OAM de piraña siguen pendientes. Los enemigos todavía
no se ven. El resto del alcance y las estimaciones siguen en ROADMAP.md.

## 3. Pendiente del usuario o la PC

U1: jugar el ADF vivo con teclado/KS1.2/A501. U2: capa 2 contra referencia.
U3 opcional: A500 real. No hace falta autorización adicional para repetir
las puertas ni corregir dentro del alcance de la tarjeta.


# Handoff G2T-B2bis — 2026-10-08, actualizado

Worktree `C:/Users/JC/Downloads/sma/wt-g2t-b2bis-1008`, rama `g2t-b2bis`.
Commits reales: `8a4a43d` clave; `a401723` decoder; `ec320ab` integración
cache/frontera/foto y herramientas. Sin merge ni push.

Las puertas locales están verdes. Todos los pendientes del handoff viejo
se ejecutaron, incluidos bordes, L1/free-buffer/raros C, foto retenida,
BENCH, cuatro memmap, reinicios, WinUAE y red completa. El informe con
números, límites, formatos y hashes es `informe-g2t-b2bis-1008.md`.
El texto anterior está archivado en `archivo/sesiones.md`.

**Pendiente real:** WinUAE pierde 98 fotos (1,55 %, racha 2), control 27.
Antes de vista compacta eran 100. No declarar D1 cerrada ni integrar como
50 Hz cumplidos. Vivo G3 deja 264 B tras G5EV/work/fotos/salida/pila:
revisar memoria antes de añadir código. B35 no se ejecuta en vivo; Cpre
no se inició. El usuario autorizó continuar iterando sin rebajar puertas.

## Retomar

1. Leer PROXIMO y `instrucciones-g2t-b2bis-rendimiento.md`.
2. Git Bash: PATH="$TEMP/pyshim:/c/msys64/ucrt64/bin:$PATH",
   VBCC=/c/Users/JC/vbcc, PY=python. `sh tools/g5env_gate.sh`.
3. Perfilar primero el miss/proyecto frío; conservar el formato warm
   portable con copia propia. No dejar punteros a cache mutable en vista.
4. Regenerar ASM con tools/g5env_asm.py. Repetir los 258 sintéticos,
   callbacks reales del juego y los controles ABI/canarios. Leer P112.
5. Para evidencia: work/b2b_shotbuild.sh y work/b2b_shots.ps1; el control
   sale de a52e2ba con el mismo C. BENCH 190 s, visual STOPF=1800 95 s;
   copias de shot.ps1 y candado. `python tools/g5env_shot.py`.
6. Red antes de commit: lint, regress baseline_pc --level, OAM68K, G5ENV,
   hashes. work/b2b_final.sh lo reproduce secuencialmente; no ejecutar
   builds concurrentes porque comparten work/cc y logicbench.

Logs/JSON final: work/b2b/{gate_final,lint_final,regress_final,oam_final,
hashes_final,shot_final}.log, memory_summary.json, shot_summary.json;
cache/decode/game/edges tienen su JSON. Vista control arriba/B2bis abajo:
work/b2b/view_control_ab.png, 0 píxeles distintos, inspeccionada.
No hay WinUAE de prueba pendiente; no cerrar procesos ajenos.

47 SKIP + 1 SYNC difieren del fixture PC provisional por la captura
antes del rollback/gráficos congelados. Todas las fotos son exactas contra
el modelo del estado capturado. No modificar g2t_ref ni replay para
ocultar esta limitación. Decodificación de imágenes arbitrarias de dos
columnas exacta, sin promesa de 12000 ciclos para esos dibujos raros.


Entrega: d3e431c baja B2bis de 98 a 92 fotos perdidas; control 27, D1 roja. Cache 554/11910, captura 270, margen vivo G3 reservado 272 B. Cpre C2a exacta en 2288 fotos; sonda C2b sin emitir, máximo 28680 ciclos contra parada 4000. C3/C4 no ejecutadas. Informes de rendimiento y Cpre del 1008; sin merge/push.


---

## Sesión 2026-10-08/09 — G5L-R y colchón (PROXIMO cumplido en parte)

PROXIMO.md vigente al empezar, textual:

# PRÓXIMO — lo que sigue

2026-10-08. Worktree `C:/Users/JC/Downloads/sma/wt-g2t-b2bis-1008`, rama
`g2t-b2bis`. **Sin merge ni push.** B2bis: `ec320ab`, optimización y
canarios reales `d3e431c`; esta sesión deja además Cpre parcial en WIP.

**B2bis rendimiento mejoró pero no cerró D1:** WinUAE cycle-exact baja
de 98 a 92 fotos perdidas (1,46 %, racha 2), control 27 (0,43 %, racha 1).
Las puertas exactas siguen verdes: 3404 frames, 762496 filas, 258 bordes;
lookup 554/11910, captura 270. Vivo G3 con reservas deja 272 B.
Informe: `docs/informe-g2t-b2bis-rendimiento-1008.md`.

**Cpre C2a exacta, C2b detenida por coste:** 2288 planes sobre 6313 fotos
reales, cinco contadores cero. Consulta y firmas sin emitir: máximo
28680 ciclos frente a la parada de 4000; ABI/listas intactas y firma
negativa detectada. No hay emisor completo, C3/C4 ni Rex visible.
Informe: `docs/informe-g2t-cpre-1008.md`. Handoff actualizado:
`docs/handoff-g2t-b2bis-1008.md`. B35 sigue fuera del vivo.

## 1. La próxima sesión

| tarjeta | toca | instrucciones y entrega |
|---|---|---|
| **G2T-B2bis rendimiento** | continuar perfil y memoria hasta una mejora que cumpla D1 global; el control tampoco la cumple | `docs/instrucciones-g2t-b2bis-rendimiento.md`: mismos umbrales, reservas, control de la tanda y red exacta |
| **G2T-Cpre coste** | resolver la parada C2b antes del emisor completo y C3/C4 | `docs/instrucciones-g2t-cpre-coste.md`: repetir sonda, medir componentes, conservar firmas; decisión de presupuesto pendiente del usuario |

El usuario pidió B2bis y después Cpre; se trabajó en ese orden. Continuar
sin rebajar exactitud. No tocar modelo, contrato, scroll.s o banco dentro
de estas tarjetas. Si hace falta S5/L-OAM, abrir y leer su tarjeta antes
de tocar otra área. No activar B35: máximo 2423094 ciclos frente a 8000.
R9: derivados exclusivamente en work/. No compilar en paralelo.

## 2. Después

Con presupuesto Cpre resuelto: emisor completo, C3 sobre ambas listas,
12 capturas C4 exactas, C5/C6. Sigue pendiente D1 global, recuperar
memoria y rediseñar B35; después revisión/integración de rama y OAM de
piraña. Los enemigos todavía no se ven. Alcance restante en ROADMAP.md.

## 3. Pendiente del usuario o la PC

Consulta enviada: conservar el límite Cpre de 4000 y rediseñar, o
permitir mayor coste solo para la prueba offline. Sin respuesta sigue
vigente 4000; no se interpreta el silencio como aprobación.
U1: jugar ADF vivo con teclado/KS1.2/A501. U2: capa 2 contra referencia.
U3 opcional: A500 real. Las puertas y correcciones autorizadas continúan
sin pedir permiso de nuevo.


**Qué se hizo.** El usuario cambió el objetivo de la sesión: "encontrá una
manera de que se dibujen los enemigos y quepan en el presupuesto; libertad
creativa". B2bis/Cpre quedaron como estaban. Nuevo enfoque **G5L-R**: el
Rex por los sprites 4-7 con 4 mapas limpios y camino rápido (`9c84534`,
263 fotos perdidas en WinUAE, control 27). Muestra a 25 Hz (`-DHZ25`) que
el usuario descartó por fluidez; colchón de tercera lista (`-DCUSHION`,
`c90e961`, 88 fotos) **aceptado por el usuario el 2026-10-09** con +20 ms
de latencia; tirones del Rex diagnosticados con la traza por VBL
(`-DVBTRACE`, `tools/vbtrace.py`) como pares repetir/saltear (P115);
caché del plan y clave de Mario (P116) en `052dac2`: **67 fotos, racha 1**.
G5L GAME OK, lint/regress verdes, 5 hashes por defecto iguales. Quedó a
medias: el colchón en vivo y bajar los ~40 tirones restantes. Informe:
`docs/informe-g5l-r-1009.md`. Rama `g2t-b2bis` integrada a `master` por
fast-forward a pedido del usuario (sin push).


## 2026-10-09 — T medida; V/BM1 parciales verificadas

PROXIMO anterior del worktree, archivado textual. T llegó a su parada; V y BM1 quedan WIP por puertas externas.

# PRÓXIMO — lo que sigue

2026-10-09. Rama `master` (integrada desde `g2t-b2bis` por fast-forward,
**sin push**). Worktree de trabajo: `C:/Users/JC/Downloads/sma/wt-g2t-b2bis-1008`.

**Los enemigos se ven.** G5L-R dibuja al Rex por los sprites 4-7 (opt-in
`-DG5L`); con el colchón de tercera lista (`-DCUSHION`, solo replay) el
replay de YI1 pierde **67 fotos** en WinUAE cycle-exact (1,06 %, racha 1;
control sin enemigos 27). El usuario aceptó el colchón (+20 ms) el
2026-10-09 y pidió revisar los tirones del Rex: son pares repetir/saltear
(P115), no errores del render. Informe: `docs/informe-g5l-r-1009.md`.

## 1. La próxima sesión

| tarjeta | toca | instrucciones y entrega |
|---|---|---|
| **G5L-R-T tirones** | bajar las fotos perdidas por el Rex (67 → hacia 27): patch compartido, camino rápido fallido, sweep con Mario en movimiento | `docs/instrucciones-g5l-r-tirones.md`: G5L GAME OK, WinUAE, vbtrace, parada si dos candidatos no bajan de ~55 |
| **G5L-R-V vivo** | el colchón fuera del replay (reinicio, diagnóstico, carga) y `-DG5L -DCUSHION` por defecto al final | `docs/instrucciones-g5l-r-vivo.md`: ADF jugable, Z1, memmap, latencia medida, hashes nuevos en commit propio |

Recomendado: primero T (lo que pidió el usuario), después V. No compilar
en paralelo; una sola WinUAE midiendo. R9: derivados solo en work/.

## 2. Después

Los otros enemigos de YI1 con el mismo mecanismo (Banzai Bill por bob en
PF1, piraña, Chuck), cobertura de dos Rex a la vez, D1 global (el control
tampoco la cumple: build_mid/S5), HUD, audio. B2bis/Cpre/B35 quedan como
estaban (`docs/informe-g2t-b2bis-rendimiento-1008.md`,
`docs/informe-g2t-cpre-1008.md`): G5L-R los reemplaza como ruta de dibujo;
no se retoman salvo decisión del usuario. Alcance en ROADMAP.md.

## 3. Pendiente del usuario o la PC

Decisiones tomadas por el agente con libertad creativa, para revisar:
4 mapas limpios (`CLEAN_PERMS`), quitar el banco G3 del juego con G5L
(65 KB de chip), caché del plan de 4 entradas, y dejar B2bis/Cpre/B35
aparcadas en favor de G5L-R. Consulta Cpre de presupuesto (4000) sigue
sin respuesta y queda sin efecto mientras Cpre esté aparcada.
Worktrees viejos: todos integrados o equivalentes en master salvo
`tools/g2t_probe.py` (`wt/g5bis-1007`, sonda de un enfoque superado);
borrarlos es decisión del usuario.
U1: jugar ADF vivo con teclado/KS1.2/A501. U2: capa 2 contra referencia.
U3 opcional: A500 real.


PROXIMO de master f24cee7, que añadió BM1 y confirmó el foco del usuario, archivado textual:

# PRÓXIMO — lo que sigue

2026-10-09. Rama `master` (integrada desde `g2t-b2bis` por fast-forward,
**sin push**). Worktree de trabajo: `C:/Users/JC/Downloads/sma/wt-g2t-b2bis-1008`.

**Los enemigos se ven.** G5L-R dibuja al Rex por los sprites 4-7 (opt-in
`-DG5L`); con el colchón de tercera lista (`-DCUSHION`, solo replay) el
replay de YI1 pierde **67 fotos** en WinUAE cycle-exact (1,06 %, racha 1;
control sin enemigos 27). El usuario aceptó el colchón (+20 ms) el
2026-10-09 y pidió revisar los tirones del Rex: son pares repetir/saltear
(P115), no errores del render. Informe: `docs/informe-g5l-r-1009.md`.

## 1. La próxima sesión

| tarjeta | toca | instrucciones y entrega |
|---|---|---|
| **G5L-R-T tirones** | bajar las fotos perdidas por el Rex (67 → hacia 27): patch compartido, camino rápido fallido, sweep con Mario en movimiento | `docs/instrucciones-g5l-r-tirones.md`: G5L GAME OK, WinUAE, vbtrace, parada si dos candidatos no bajan de ~55 |
| **BM1 bare metal** | sin el SO también al arrancar: medir la chip que retiene, supervisor, trackloader MFM propio, mapa fijo (pedido del usuario 2026-10-09) | `docs/instrucciones-bm1.md`: fase 1 medida con parada si < 16 KB; KS 1.2/1.3; después de T, antes de V si falta chip |
| **G5L-R-V vivo** | el colchón fuera del replay (reinicio, diagnóstico, carga) y `-DG5L -DCUSHION` por defecto al final | `docs/instrucciones-g5l-r-vivo.md`: ADF jugable, Z1, memmap, latencia medida, hashes nuevos en commit propio |

Recomendado: primero T (lo que pidió el usuario), después V; BM1 entre las dos si la chip aprieta, si no al final. No compilar
en paralelo; una sola WinUAE midiendo. R9: derivados solo en work/.

## 2. Después

Los otros enemigos de YI1 con el mismo mecanismo (Banzai Bill por bob en
PF1, piraña, Chuck), cobertura de dos Rex a la vez, D1 global (el control
tampoco la cumple: build_mid/S5), HUD, audio. B2bis/Cpre/B35 quedan como
estaban (`docs/informe-g2t-b2bis-rendimiento-1008.md`,
`docs/informe-g2t-cpre-1008.md`): G5L-R los reemplaza como ruta de dibujo;
no se retoman salvo decisión del usuario. Alcance en ROADMAP.md.

## 3. Pendiente del usuario o la PC

**[usuario, 2026-10-09]: el foco es G5L-R**; B2bis/Cpre/B35 quedan
aparcadas. Decisiones del agente con libertad creativa, para revisar:
4 mapas limpios (`CLEAN_PERMS`), quitar el banco G3 del juego con G5L
(65 KB de chip) y caché del plan de 4 entradas. Consulta Cpre de presupuesto (4000) sigue
sin respuesta y queda sin efecto mientras Cpre esté aparcada.
Worktrees viejos: todos integrados o equivalentes en master salvo
`tools/g2t_probe.py` (`wt/g5bis-1007`, sonda de un enfoque superado);
borrarlos es decisión del usuario.
U1: jugar ADF vivo con teclado/KS1.2/A501. U2: capa 2 contra referencia.
U3 opcional: A500 real.


Entrega en g2t-b2bis, sin merge/push: 5461b8a (T, 66 fotos BENCH frente a 67; segundo candidato 65/racha2 retirado), a728ddc (V, tres listas/Z1/latencia), a41da43 (BM1, MFM/fijo KS1.2, 18920 B recuperados). Red final lint/regress --level --g5l --bm1/OAM68K/hashes verdes. Faltan teclado real y defecto V, KS1.3 y control de carga trackdisk; informes de esta fecha.

Revisión final BM1 `c30ff27`: sincronías corruptas acotadas al DMA, 84 casos MFM exactos, boot988 B; nueva captura Z1 final vuelve en411/$71=00. Informe `docs/informe-bm1-limites-1009.md`.

---

## Archivado 2026-10-09 (noche): PROXIMO de la sesión T/V/BM1, cumplido

# PRÓXIMO — lo que sigue

2026-10-09. **Código en `g2t-b2bis`, sin merge ni push**; worktree:
`C:/Users/JC/Downloads/sma/wt-g2t-b2bis-1008`. Master conserva el código
anterior; los documentos indican el avance de la rama.

Se iteraron las tres tarjetas. **T llegó a su parada**: 67→66 fotos BENCH;
el segundo intento dio 65 pero racha2 y se retiró. Control con tres listas
9; VBTRACE sin BENCH 25 saltos (instrumentaciones distintas). D1 roja.
**V implementada opt-in**: tres listas en vivo, muerte/reinicio/diagnóstico
y latencia de dos ticks verdes; falta teclado real antes del defecto.
**BM1 opt-in funciona en KS1.2/A501**: MFM y arenas fijas, datos/imagen
exactos, reinicio, 18920 B recuperados y carga 32,24 s. Falta KS1.3.

Commits de código: `5461b8a`, `a728ddc`, `a41da43`, `c30ff27`. Informes:
`docs/informe-g5l-r-tirones-1009.md`, `docs/informe-g5l-r-vivo-1009.md`,
`docs/informe-bm1-1009.md`, `docs/informe-bm1-limites-1009.md`. Lint, regress `--level --g5l --bm1`, OAM68K
y cinco MD5 normales verdes. **Los defectos siguen iguales**.

## 0. Sesión interrumpida 2026-10-09 (tarde) — retomar desde aquí

El usuario pidió la PC; quedó a medias. **Decisiones del usuario:**
KS 1.3 = `C:\Users\JC\Desktop\Escritorio 26\Escritorio 25\jueguitos p amiga\Kickstart v1.3 r34.005 (1987-12)(Commodore)(A500-A1000-A2000-CDTV)[!].rom`;
**sin A501 el juego no carga** (el rojo estable del boot fijo es la
política; se cierra la exclusión). El usuario jugó el vivo: "anda y se
mueve" (U1 a mano). Worktrees redundantes borrados (9, ya en master);
quedan los que tienen commits fuera de master: agent-ab11…, agent-af1f…,
wt-g5bis-1007, wt-review-1007.

Hecho: partida verde (lint, regress `--level --g5l --bm1`), builds
`work/g5l/liveclose` (188/190 verdes) y `work/bm1/compare` (MFM y
memmap verdes). `tools/shot.ps1 -Keys "seg:down|up|tap:TECLA;..."`
manda scancodes con SendInput; **hace falta `-norawinput_keyboard`**
(lo agrega solo) o WinUAE no las ve.

**Abierto con teclas inyectadas** (`work/g5l/liveclose/d_*.png`, no
reproducido a mano por el usuario): mantener RIGHT mata a Mario al
instante (diag: motivo 11 muerte, frame 07EE, X0010 Y0336, $71=09, PIE
FFFF, HIST 0002); reaparece, camina y vuelve a morir. Sin teclas no
muere. Sospecha: artefacto de la inyección (el ALT que `Front()` manda
cada segundo, o el scancode extendido) — **leer la página 2 con
`diag_read.py --shot d_105s.png --bin work/g5l/liveclose/game.bin
--repro`** para ver los bits que vio el juego antes de tocar código.
Espacio → página 2 y RETURN → juego de nuevo funcionaron (d_111s+);
d_117s salió negra (sin explicar).

Faltan: esa lectura, KS 1.3 (BM1 pasos 1-3), control trackdisk (paso
4), defectos G5L+CUSHION y BM_FIXED (ahora sin bloqueo A501), MD5,
informes y cierre §7.

## 1. La próxima sesión

| tarjeta | toca | instrucciones y entrega |
|---|---|---|
| **G5L-R-V cierre** | teclado real/RETURN en WinUAE; después, G5L+CUSHION por defecto en commit propio | `docs/instrucciones-g5l-r-cierre.md`: arranque/interacción, Z1, historial, memoria y cinco hashes nuevos |
| **BM1 cierre** | KS1.3, política sin A501 y tiempo comparable contra trackdisk; conservar boot opt-in mientras falten puertas | `docs/instrucciones-bm1-cierre.md`: MFM/mapa/Z1 verdes, bytes y píxeles exactos en ambas ROMs, tiempo con mismos extremos |

No repetir implementaciones que ya pasan. Si falta el helper o ROM,
continuar solo puertas independientes. Builds seriales, una WinUAE midiendo,
R9. T no recibe otro candidato antes de revisar los números de su parada.

## 2. Después

Revisión de T: fast fallido/sweep durante daño y presupuesto global de
build_mid/S5; 66 BENCH y 25 VBTRACE aún no cumplen D1. Luego otros enemigos,
dos Rex, bobs/Banzai, HUD y audio. BM1 deja solo 24856 B de chip en vivo:
las tablas CPU en chip (135468 B) todavía necesitan C2/C4 y espacio slow.
**[usuario, 2026-10-09]: el foco es G5L-R**; B2bis/Cpre/B35 aparcadas.

## 3. Pendiente del usuario o la PC

- Ruta local de **Kickstart 1.3**: solo se encontró `amivideo/kick12.rom`.
- Helper Computer Use: error de conexión nativa (`os error 2`) tras dos
  intentos y reinicio; impide enviar teclado real. U1 también puede
  validarse jugando el ADF normal G5L vivo de la rama.
- Antes de sustituir el boot normal, cerrar soporte sin A501: el fijo
  muestra rojo estable, el normal conserva su comportamiento anterior.
- U2 capa 2 contra referencia; U3 opcional A500 real. Borrar worktrees
  viejos sigue siendo decisión del usuario.

ADF vivo normal con Rex/colchón: `work/session/live/game.adf` en el
worktree. ADF vivo bare metal final: `work/rg_bm1/game.adf`.

### Qué se hizo (sesión de cierre V/BM1, 2026-10-09 noche)

G5L-R-V y BM1 **cerradas** en g2t-b2bis, sin merge/push. Teclado real por
`shot.ps1 -Keys` (SendInput + `-norawinput_keyboard`, P117): corre, salta,
diagnóstico, historial reproducido por la PC, RETURN a juego nuevo, en KS 1.2
(trackdisk) y KS 1.3 (BM). Las muertes al inicio son fieles (Koopa `$BD`,
snesorc). Defectos en commit propio `53e6453`: G5L+CUSHION+SPR_OAM, vivo con
boot BM1 (sin A501 no carga, decisión del usuario); `PROFILE=legacy` da los
cinco MD5 del informe T. BM1 KS 1.3: datos exactos, 0/327680 px, Z1 411,
rojo sin A501. Control trackdisk `-DLOADTIME` (`143c9ea`): 33,02 s contra
31,96-31,98 s de BM1 (−3 %). lint y regress `--level --g5l --bm1` verdes.
9 worktrees redundantes borrados. Informe: `docs/informe-cierre-v-bm1-1009.md`.

---

## Archivado 2026-10-09 (noche, 2): PROXIMO de la sesión G5L-R-T2, cumplido

# PRÓXIMO — lo que sigue

2026-10-09 (noche). **Código en `g2t-b2bis`, sin merge ni push**; worktree:
`C:/Users/JC/Downloads/sma/wt-g2t-b2bis-1008`. Master conserva el código
anterior; los documentos indican el avance de la rama.

**G5L-R-V y BM1 cerradas** (`docs/informe-cierre-v-bm1-1009.md`). Teclado
real verificado en WinUAE (`shot.ps1 -Keys`, P117) en KS 1.2 y 1.3, y el
usuario jugó el vivo a mano. **Defectos nuevos** (`53e6453`, commit propio):
G5L+CUSHION+SPR_OAM; el vivo arranca con el boot BM1 (sin A501 no carga,
decisión del usuario); `PROFILE=legacy` es el control y da los cinco MD5
del informe T. BM1: KS 1.3 con datos y píxeles exactos, Z1, rojo sin A501;
carga 31,96 s contra 33,02 s de trackdisk (−3 %, `-DLOADTIME`). lint y
regress `--level --g5l --bm1` verdes. BENCH del defecto: 66 fotos, racha 1.
**D1 sigue roja.** 9 worktrees redundantes borrados.

ADF vivo por defecto: `GDEFS=" " OUT=work/live sh tools/game_build.sh`
→ `work/live/game.adf` (BM1, exige A501).

## 1. La próxima sesión

| tarjeta | toca | instrucciones y entrega |
|---|---|---|
| **G5L-R-T2** | solo medida: atribuir los 25 saltos de VBTRACE (y las 66 fotos BENCH) a las partes de G5L y a `build_mid` por frame; propuesta de candidato con coste estimado, **sin implementarla** | `docs/instrucciones-g5l-r-t2.md`: 66/25 reproducidos, CSV por frame que cuadra con G5L GAME, tabla de los 25 saltos, patrón ≥ 20/25 o su ausencia |

Builds seriales, una WinUAE midiendo, R9. Un candidato nuevo para los
tirones necesita autorización del usuario después del informe T2.

## 2. Después

Con el informe T2: el candidato que el usuario autorice y la compuerta D1.
Luego otros enemigos (dos Rex, Banzai/bobs), HUD y audio. BM1 deja 24856 B
de chip en el vivo: las tablas de CPU en chip (135468 B) todavía necesitan
C2/C4 y espacio slow. **[usuario, 2026-10-09]: el foco es G5L-R**;
B2bis/Cpre/B35 aparcadas.

## 3. Pendiente del usuario o la PC

- U2 capa 2 contra referencia; U3 opcional, A500 real (con A501).
- Worktrees con commits fuera de master, conservados: `agent-ab11…`
  (G2T-B2 parada), `agent-af1f…` (revisión L-OAM), `wt-g5bis-1007`,
  `wt-review-1007`. Borrarlos o integrarlos es decisión del usuario.
- Integrar `g2t-b2bis` a master (sin push) cuando el usuario lo pida.

### Qué se hizo (sesión G5L-R-T2, 2026-10-09 noche)

T2 **hecha** en g2t-b2bis, solo medida, sin merge/push; no cambió código
del juego. Paso 1 reproducido con el defecto nuevo (WinUAE cycle-exact,
KS 1.2 + A501): BENCH 66 fotos (1,05 %), racha 1, 68 VBL; VBTRACE 25
omitidas, los mismos frames del informe T (`vbtrace.py` necesitaba
`use_gui=no`, P120). `g5l.py game` guarda por foto lógica, captura,
`build_mid` y demás, partes G5L y la clave del plan; puerta del paso 2 OK
(media 10 477,6, máx. 93 752). `t2_attrib.py`, `t2_model.py` y
`t2_keys.py` nuevos. Patrón: atraso acumulado, 21/25 en un modelo de cola
(B = 102 000, S = 65 000). Dos fuentes: el camino lento de G5L (145
fotos; el Rex cambia de forma mientras se solapa con Mario y la altura
relativa cambia; caché mayor no sirve) y los picos de `build_mid`. Estimado:
camino lento gratis 8-12 saltos, S5 al 50 % 13-18, las dos 0-4. Propuesta
G5L-R-P (P-a medida offline de planes corridos, P-b S5) sin implementar,
pendiente de autorización. Informe: `docs/informe-g5l-r-t2-1009.md`.

---

## Archivado 2026-10-09 (noche, 3): PROXIMO de la sesión G5L-R-Pa, cumplido

# PRÓXIMO — lo que sigue

2026-10-09 (noche). **Código en `g2t-b2bis`, sin merge ni push**; worktree:
`C:/Users/JC/Downloads/sma/wt-g2t-b2bis-1008`. Master conserva el código
anterior; los documentos indican el avance de la rama.

**G5L-R-T2 hecha** (`docs/informe-g5l-r-t2-1009.md`), solo medida. Con el
defecto nuevo: BENCH 66 fotos, racha 1; VBTRACE 25 omitidas, los frames
del informe T. Los saltos son **atraso acumulado** por rachas de 3-6 fotos
caras (modelo de cola: 21 de 25). Dos fuentes independientes:

- **camino lento de G5L**: 145 fotos con sweep/plan, `g5l_render` 66 k
  ciclos contra 9 k. El Rex cambia de forma mientras se solapa con Mario y
  la altura relativa cambia; agrandar la caché no sirve (26/145 sin límite);
- **picos de `build_mid`** (S5).

Estimado: el camino lento gratis deja 8-12 saltos, S5 al 50 % 13-18, las
dos juntas 0-4. **D1 sigue roja.**

## 1. La próxima sesión — decide el usuario

La parada de T sigue: **un candidato nuevo necesita autorización.**
Recomendación: empezar por la fase de medida de P-a, que no toca el juego.

| tarjeta | toca | instrucciones y entrega |
|---|---|---|
| **G5L-R-Pa** (recomendada; **pendiente de autorización**) | solo medida, offline: ¿el plan de G5L de un fallo es el de un fallo anterior corrido en Δr0? Si sí en ≥ 80 % de los aciertos, la caché con clave sin la altura vale | `docs/instrucciones-g5l-r-pa.md`: planes por foto, comparación con corrimiento, puerta ≥ 80 %, informe con contrafáctico |

Las otras opciones del informe T2 §5, para que el usuario elija:

- **P-b, S5 en `build_mid`** (cola por plazo, `docs/plan-tecnico.md`
  §9.2): necesaria igual, pero sola deja 13-18 saltos (estimado).
- **Recorte uniforme del 20-30 % de `g5l_render`** más S5: sin diseño
  todavía.

Builds seriales, una WinUAE midiendo, R9.

## 2. Después

Con P-a: la implementación (clave reducida o sweep/plan en asm) y S5, con
la puerta BENCH ≤ 9 fotos (control sin G5L), VBTRACE ≤ 5, `G5L GAME: OK`,
0 píxeles distintos en el frame 1700 y la compuerta D1. Luego otros
enemigos (dos Rex, Banzai/bobs), HUD y audio. BM1 deja 24856 B de chip en
el vivo: las tablas de CPU en chip (135468 B) todavía necesitan C2/C4 y
espacio slow. **[usuario, 2026-10-09]: el foco es G5L-R**; B2bis/Cpre/B35
aparcadas.

## 3. Pendiente del usuario o la PC

- **Autorizar (o no) G5L-R-Pa**, o elegir otra opción de §1.
- U2 capa 2 contra referencia; U3 opcional, A500 real (con A501).
- Worktrees con commits fuera de master, conservados: `agent-ab11…`
  (G2T-B2 parada), `agent-af1f…` (revisión L-OAM), `wt-g5bis-1007`,
  `wt-review-1007`. Borrarlos o integrarlos es decisión del usuario.
- Integrar `g2t-b2bis` a master (sin push) cuando el usuario lo pida.

### Qué se hizo (sesión G5L-R-Pa, 2026-10-09 noche)

El usuario autorizó Pa. Hecha en g2t-b2bis, solo medida, sin merge/push;
el juego no cambió. `g5l.py game` guarda el plan de Python y la s por
foto. `pa_shift.py`: sin `R0` en la clave, el plan corrido es igual al
100 %, pero acierta 0 con N = 4 (13 con N = 16); sin `R0`/`MSH`, 8 % de
iguales en 36 aciertos. **Puerta (≥ 80 %) no cumplida**: la vía de la
caché queda descartada. `pa_levers.py`: un fallo cuesta 66 k contra 27,5 k
(sweep + plan 19 k, exceso de patch 8 k); `build_mid` > 40 000 en 60
fotos de la vuelta y 11 de la ida, pero el 56 % del exceso es de la ida.
Para ≤ 5 saltos (modelo, ESTIMADO): S5 + camino lento −50 % (2-6), S5 +
`g5l_render` −20 % (1-2), o `g5l_render` −30 % (4-5). Siguiente
recomendada: G5L-R-Q, perfil por PC y recortes posibles, pendiente de
autorización. Informe: `docs/informe-g5l-r-pa-1009.md`.

---

## Archivado 2026-10-09 (noche, 4): PROXIMO de la sesión G5L-R-Q, cumplido

# PRÓXIMO — lo que sigue

2026-10-09 (noche). **Código en `g2t-b2bis`, sin merge ni push**; worktree:
`C:/Users/JC/Downloads/sma/wt-g2t-b2bis-1008`. Master conserva el código
anterior; los documentos indican el avance de la rama.

**G5L-R-T2 y G5L-R-Pa hechas**, solo medida (`docs/informe-g5l-r-t2-1009.md`,
`docs/informe-g5l-r-pa-1009.md`). Los 25 saltos de VBTRACE (66 fotos
BENCH) son atraso acumulado por rachas de fotos caras. **Reutilizar el
plan de G5L no sirve**: sin la altura absoluta el plan corrido es igual,
pero casi nunca acierta (0 con N = 4); sin la relativa acierta, pero el
plan es otro en el 92 %. El exceso está repartido entre el render de G5L
y `build_mid` en los dos sentidos. Para ≤ 5 saltos (modelo, ESTIMADO):

- S5 (`build_mid` −50 % del exceso) + camino lento −50 %: 2-6;
- S5 + `g5l_render` −20 %: 1-2;
- `g5l_render` −30 % sin S5: 4-5.

**D1 sigue roja.**

## 1. La próxima sesión — decide el usuario

| tarjeta | toca | instrucciones y entrega |
|---|---|---|
| **G5L-R-Q** (recomendada; **pendiente de autorización**) | solo medida: histograma por PC de `g5l_render` (ventanas de salto y fallos) y de `build_mid` (picos), una reescritura concreta por bucle caliente con su recorte estimado, y el modelo con esos recortes | `docs/instrucciones-g5l-r-q.md`: puerta del histograma = ciclos de `game_frames.json`; informe con qué meta es alcanzable |

Sin Q, cualquier candidato sería elegir un porcentaje sin saber si se
puede. Si Q dice que ninguna meta es alcanzable, D1 vuelve al usuario con
números (colchón aceptado; 25 Hz solo con la optimización agotada).

Builds seriales, una WinUAE midiendo, R9.

## 2. Después

El candidato que Q haga posible (S5 + recortes de asm en G5L), con la
puerta BENCH ≤ 9 fotos (control sin G5L), VBTRACE ≤ 5, `G5L GAME: OK`,
0 píxeles distintos en el frame 1700 y la compuerta D1. Luego otros
enemigos (dos Rex, Banzai/bobs), HUD y audio. BM1 deja 24856 B de chip en
el vivo: las tablas de CPU en chip (135468 B) todavía necesitan C2/C4 y
espacio slow. **[usuario, 2026-10-09]: el foco es G5L-R**; B2bis/Cpre/B35
aparcadas.

## 3. Pendiente del usuario o la PC

- **Autorizar (o no) G5L-R-Q.**
- U2 capa 2 contra referencia; U3 opcional, A500 real (con A501).
- Worktrees con commits fuera de master, conservados: `agent-ab11…`
  (G2T-B2 parada), `agent-af1f…` (revisión L-OAM), `wt-g5bis-1007`,
  `wt-review-1007`. Borrarlos o integrarlos es decisión del usuario.
- Integrar `g2t-b2bis` a master (sin push) cuando el usuario lo pida.

### Qué se hizo (sesión G5L-R-Q, 2026-10-09 noche)

El usuario autorizó Q. Hecha en g2t-b2bis, solo medida, sin merge/push;
el juego no cambió. `g5l.py game --pcprof`: histograma por PC de
`g5l_render` y `build_mid` instrucción por instrucción; puerta OK (6313
fotos, totales idénticos, histogramas exactos). `q_report.py`: el perfil
del render es plano (máx. bucle 5,1 % en las ventanas); `g5l_pcget`
acierta 159/1980 y compara 6,7 .l por entrada; `build_mid` en las ventanas
es 84 % `bm_left`. `q_levers.py`: reescrituras concretas −8 % del render y
de `build_mid` (ESTIMADO) → modelo 14-16 saltos, 10-11 con S5; ≤ 5 pide
además −10 % general sin bucle identificado. Recomendada G5L-R-R1
(reescrituras + primera medida en WinUAE), pendiente de autorización.
Informe: `docs/informe-g5l-r-q-1009.md`.

## Archivado 2026-10-10: PROXIMO de la sesión G5L-R-R1/S9, cumplido

# PRÓXIMO — lo que sigue

2026-10-09 (noche). **Código en `g2t-b2bis`, sin merge ni push**; worktree:
`C:/Users/JC/Downloads/sma/wt-g2t-b2bis-1008`. Master conserva el código
anterior; los documentos indican el avance de la rama.

**G5L-R-T2, Pa y Q hechas**, solo medida (`docs/informe-g5l-r-t2-1009.md`,
`docs/informe-g5l-r-pa-1009.md`, `docs/informe-g5l-r-q-1009.md`). Los 25
saltos de VBTRACE (66 fotos BENCH) son atraso acumulado; reutilizar el plan
de G5L no sirve. El perfil por PC es **plano**: las reescrituras concretas
y exactas ahorran ~8 % del render G5L y ~8 % de `build_mid` en las
ventanas de salto. Modelo (ESTIMADO): 25 → 14-16 saltos, 10-11 con S5;
≤ 5 pide además −10 % general sin bucle identificado (2-4 con S5), o el
patch por blitter (sin medir). **D1 sigue roja.**

## 1. La próxima sesión — decide el usuario

| tarjeta | toca | instrucciones y entrega |
|---|---|---|
| **G5L-R-R1** (recomendada; **pendiente de autorización**: es un candidato) | `player/g5l.s`: clave del plan con lo que cambia primero, copias con `movem`, `emit.mv` desenrollado, mapa de bits en `place.f1`; cada una con `G5L GAME: OK`; después **la primera medida en WinUAE** (BENCH, VBTRACE) de cuánto valen los ciclos de Musashi en fotos omitidas | `docs/instrucciones-g5l-r-r1.md`: ahorro medido por reescritura contra el estimado de Q, BENCH/VBTRACE antes/después, modelo recalibrado |

Con ese número el usuario elige entre S5, el patch por blitter o revisar
D1 (colchón aceptado; 25 Hz solo con la optimización agotada).

Builds seriales, una WinUAE midiendo, R9.

## 2. Después

Según R1: S5 (`build_mid`, sobre todo `bm_left` a la vuelta), el patch de
G5L por blitter, o D1 al usuario. Luego otros enemigos (dos Rex,
Banzai/bobs), HUD y audio. BM1 deja 24856 B de chip en el vivo: las tablas
de CPU en chip (135468 B) todavía necesitan C2/C4 y espacio slow.
**[usuario, 2026-10-09]: el foco es G5L-R**; B2bis/Cpre/B35 aparcadas.

## 3. Pendiente del usuario o la PC

- **Autorizar (o no) G5L-R-R1.**
- U2 capa 2 contra referencia; U3 opcional, A500 real (con A501).
- Worktrees con commits fuera de master, conservados: `agent-ab11…`
  (G2T-B2 parada), `agent-af1f…` (revisión L-OAM), `wt-g5bis-1007`,
  `wt-review-1007`. Borrarlos o integrarlos es decisión del usuario.
- Integrar `g2t-b2bis` a master (sin push) cuando el usuario lo pida.

---

## PROXIMO.md archivado el 2026-10-10 (cierre G5L-R-L2, lote 1)

# PRÓXIMO — lo que sigue

2026-10-10. **Código en `g2t-b2bis`, sin merge ni push**; worktree:
`C:/Users/JC/Downloads/sma/wt-g2t-b2bis-1008`. Master conserva el código
anterior; los documentos indican el avance de la rama.

**G5L-R-R1 y S9 hechas** (autorizadas: "hacé lo que puedas, ojalá llegar
al máximo nivel de optimización", 2026-10-09). R1: reescrituras del render
G5L, −5,6 % (`docs/informe-g5l-r-r1-1009.md`). S9: `build_mid` copia la
línea de la lista anterior cuando vale; S5 (repartir) se probó y se
descartó (`docs/informe-g5l-r-s9-1010.md`, P121). WinUAE cycle-exact:

| | T2 | R1 | S9 |
|---|---:|---:|---:|
| BENCH, fotos perdidas | 66 | 53 | **36** (0,57 %) |
| VBTRACE, omitidas | 25 | 17 | **12** |

**D1 sigue roja** (objetivo ≤ 5 omitidas).

## 1. La próxima sesión — decide el usuario

G5L-R-L paso 1 (`docs/informe-g5l-r-l1-1010.md`): la lógica también es
**plana** (la función más cara 6,5 %, casi todo asm ya escrito); el racimo
3305-3364 sube por tener más sprites vivos. Según el modelo de cola, ≤ 5
omitidas pide **−20 % de toda la lógica** o **una cuarta lista**.

| opción | qué | costo |
|---|---|---|
| **A. Lógica a asm, por partes** (recomendada si se sigue a 50 Hz sin más latencia) | `_level_frame`, `mcoll.c`, `_banzai_gfx`, `_sprites_all` y el resto del C de sprites, cada uno con el cruce PC = 68000 (V1); `docs/instrucciones-g5l-r-l2.md` | varias sesiones; −6-9 k por foto ESTIMADO pasando casi todo el C |
| B. Cuarta lista del copper | otra foto de holgura: modelo 1-8 saltos | **+20 ms de latencia** (decisión del usuario); 57 692 B de chip (`CL_SIZE`) que hoy no hay (24 856 B libres en el vivo): antes C2/C4 |
| C. G5L (camino lento) y el primer pico de `bm_left` | `instrucciones-g5l-r-l.md` pasos 2-3 | 1-3 saltos según el modelo |

Builds seriales, una WinUAE midiendo, R9.

## 2. Después

Si G5L-R-L no deja una palanca concreta para llegar a ≤ 5, D1 vuelve al
usuario con los números (colchón aceptado; 25 Hz solo con la optimización
agotada). Luego otros enemigos (dos Rex, Banzai/bobs), HUD y audio. BM1
deja 24856 B de chip en el vivo: las tablas de CPU en chip (135468 B)
todavía necesitan C2/C4 y espacio slow. **[usuario, 2026-10-09]: el foco
es G5L-R**; B2bis/Cpre/B35 aparcadas.

## 3. Pendiente del usuario o la PC

- **Elegir A, B o C** (o D1: dejarlo así, 12 omitidas en el replay).
- Probar el vivo con S9 (`work/s9/vivo`, MD5 `510e1ee3…`) a mano: el
  scroll a la izquierda es lo que cambió.
- U2 capa 2 contra referencia; U3 opcional, A500 real (con A501).
- Worktrees con commits fuera de master, conservados: `agent-ab11…`
  (G2T-B2 parada), `agent-af1f…` (revisión L-OAM), `wt-g5bis-1007`,
  `wt-review-1007`. Borrarlos o integrarlos es decisión del usuario.
- Integrar `g2t-b2bis` a master (sin push) cuando el usuario lo pida.


---

## 2026-10-10 — P123 y perfil del estrés (cierre)

PROXIMO anterior, textual; archivado tras corregir P123 y llegar a la parada del candidato de optimización.

# PRÓXIMO — lo que sigue

2026-10-10. **Código en `g2t-b2bis`, sin merge ni push**; worktree:
`C:/Users/JC/Downloads/sma/wt-g2t-b2bis-1008`. Master conserva el código
anterior.

**G5L-R-L2 lote 1 hecho** (directiva del usuario: "todo asm y bare metal,
lo más optimizado posible"): la lógica caliente está en asm
(`docs/informe-g5l-r-l2-1010.md`). Replay normal de YI1, WinUAE
cycle-exact: **VBTRACE 0 fotos omitidas** (S9: 12), BENCH 10 perdidas
(0,16 %, S9: 36). **El objetivo D1 del replay normal se cumple.**

**Estrés sigue rojo:** `stress_back` 341/4126 (8,26 %, racha 4),
`stress_sprites` 92/1914 (4,81 %, racha 3). Ahí domina el scroll/render
(`build_mid` hasta 171 % del frame en la vuelta), no la lógica.

## 1. La próxima sesión, en orden

1. **El Guru 3 latente (P123, informe §4).** Con `e7234ab` +
   `stress_back`, `g5l_render` lee `GV_TAB` pisado (`$31FA0031`).
   Encontrar quién lo escribe (candidato `g5l_wcache` con segmento ≥ 224)
   antes de seguir optimizando: el render es el mismo en la rama.
   Herramientas: `-DADRTRAP` + `tools/adrtrap.py`, `tools/g5l.py game`.
   Para reconstruir el build viejo: `git stash; git checkout e7234ab;
   git apply` del parche de ADRTRAP (`git diff 222fb64 HEAD --
   player/game.s`), compilar, volver a la rama.
2. **Estrés: el render en la vuelta.** Perfil por PC de `build_mid` y
   `scroll_frame` sobre `stress_back` (`g5l.py game --pcprof`, P121) y
   bajar los picos de columnas al volver. Medir con BENCH en los dos
   replays de estrés (comandos en el informe §3). El perfil decide la
   técnica (`docs/investigacion-demoscene-1010.md` §11): si dominan las
   decisiones, speedcode por línea generado por `mkscroll.py` + corte con
   `RTS` parcheado; si domina la copia, escribir menos palabras; si
   dominan las esperas del blitter, copper → blitter o cambiar cómo se
   termina la columna al dar la vuelta. Puerta: lista del copper idéntica
   byte a byte en Musashi en los tres replays.
3. **Seguir la directiva asm** sobre lo caliente que queda
   (`finish_oam` costo fijo, `mario_E2BD`, `spr_tile`, `mc_pxy`,
   cámara, `mspr_draw`), cada cambio con `fuzzcall.py` + lint + regress.

Antes de cada commit: `python tools/lint_port.py && python tools/regress.py
--baseline tools/baseline_pc.json --level --g5l --bm1`.

## 2. Pendiente del usuario

Probar el vivo a mano en esta rama; decidir cuándo integrar a master.

### Resultado de esta sesión

P123 corregida: columns destruía a2 antes de leer DC_REND; watchpoint atrapó al escritor en g5l_choose. Nuevo verificador del bucle real, integrado en regress. Perfil de diez picos: domina bm_left. Los recortes bm_share/FinishOAM fueron exactos y más baratos en CPU, pero se retiraron por BENCH: back 387 → 389, sprites 98 → 104. Código final back idéntico al control corregido. Speedcode y más recortes asm pendientes; parada de L2 respetada. Informe: docs/informe-p123-scroll-1010.md.

### Estado anterior de ROADMAP §1, textual

**G5L-R-R1 y S9 (2026-10-09/10, rama g2t-b2bis, autorizadas):** R1
reescribe el render G5L (clave del plan, copias desenrolladas, búsqueda
del segmento): −5,6 % en Musashi. S9: `build_mid`/`bm_left` copian la
línea de la lista anterior si vale en s (los picos venían de a tres, uno
por lista, P121); S5 se probó y se descartó. WinUAE: BENCH 66 → 53 → **36**
fotos, VBTRACE 25 → 17 → **12** omitidas. Siguen: el racimo 3305-3364
(camino lento de G5L y la lógica). `docs/informe-g5l-r-r1-1009.md`,
`docs/informe-g5l-r-s9-1010.md`. G5L-R-L paso 1: la lógica es plana; ≤ 5
pide −20 % de la lógica o una cuarta lista (decide el usuario,
`docs/informe-g5l-r-l1-1010.md`).

**G5L-R-Q (2026-10-09 noche, rama g2t-b2bis, solo medida):** histograma
por PC en Musashi (`g5l.py game --pcprof`, totales idénticos en 6313
fotos). Render G5L plano (máx. bucle 5,1 % en las ventanas); `build_mid` en
las ventanas 84 % `bm_left`. Reescrituras concretas: −8 % render, −8 %
`build_mid` (ESTIMADO) → modelo 14-16 saltos (10-11 con S5). ≤ 5 pide −10 %
general más S5, o el patch por blitter. `docs/informe-g5l-r-q-1009.md`.

**G5L-R-Pa (2026-10-09 noche, rama g2t-b2bis, solo medida):** reutilizar
el plan de G5L corrido no sirve: sin `R0` es igual al 100 % pero acierta 0
con N = 4; sin `R0`/`MSH`, 8 % de iguales (`pa_shift.py`). Un fallo cuesta
66 056 contra 27 562 ciclos (sweep + plan 19 k, exceso de patch 8 k).
`build_mid` > 40 000: 60 fotos a la izquierda, 11 a la derecha; el 56 % del
exceso es de la ida. ≤ 5 saltos pide dos palancas (S5 + recortes de G5L)
o `g5l_render` −30 % (ESTIMADO, `pa_levers.py`).
`docs/informe-g5l-r-pa-1009.md`.

**G5L-R-T2 (2026-10-09 noche, rama g2t-b2bis, solo medida):** BENCH del
defecto 66 fotos/racha 1 y VBTRACE 25 omitidas reproducidas (WinUAE
cycle-exact). Coste por foto en Musashi: total mediana 52 521, p99
122 544, máx. 156 864 ciclos sin DMA. Saltos = atraso acumulado por rachas
de fotos caras (modelo de cola 21/25). Fuentes: camino lento de G5L (145
fotos, 66 k contra 9 k; el Rex cambia de forma solapado con Mario) y picos
de `build_mid`. Estimado: 8-12 / 13-18 saltos atacando cada una, 0-4 las
dos. Propuesta G5L-R-P sin implementar (`docs/informe-g5l-r-t2-1009.md`).
D1 roja.

**Cierre V/BM1 (2026-10-09 noche, rama g2t-b2bis, sin integrar):**
G5L-R-V y BM1 cerradas (`docs/informe-cierre-v-bm1-1009.md`). Teclado
real en WinUAE KS 1.2/1.3 (`shot.ps1 -Keys`, P117), historial reproducido
por la PC; el usuario jugó el vivo. Defectos `53e6453`: G5L+CUSHION+
SPR_OAM, vivo con boot BM1 (sin A501 no carga); `PROFILE=legacy` = los
cinco MD5 del informe T. BM1 KS 1.3: datos/píxeles exactos, Z1, rojo sin
A501; carga 31,96 s contra 33,02 s de trackdisk (WinUAE, TOD de CIA-A,
`-DLOADTIME`). Memmap por defecto: replay chip 483808/slow 401224 B, vivo
499432/454072 B. BENCH del defecto: 66 fotos, racha 1. D1 roja.

**Avance T/V/BM1 (2026-10-09, rama g2t-b2bis, sin integrar):**
T detenida tras dos candidatos: 66 fotos BENCH, racha 1 (base 67; control
con colchón 9); máscara especializada 65/racha 2 retirada. VBTRACE sin
BENCH 25 saltos; D1 roja. V opt-in con tres listas/reinicio/diagnóstico
verificados y 40 ms desde tick de entrada a publicación; teclado real y
defecto pendientes. BM1 MFM/fijo KS1.2/A501: datos/imagen exactos, Z1,
18920 B chip recuperados; KS1.3 y tiempo trackdisk comparable pendientes.
Commits `5461b8a`, `a728ddc`, `a41da43`, `c30ff27`; informes T/V/BM1 de 2026-10-09.
Chip vivo normal 495336 B, slow 437896 B; fijo 499432/454072 B, incluidas
reservas de vectores/loader. No se cambiaron los cinco builds normales.

**Entrega B2bis/Cpre (2026-10-08):** rama g2t-b2bis, sin merge/push.
B2bis d3e431c: G5ENV/lint/regress --level/OAM68K/hashes verdes; 3404 frames,
762496 filas y 258 bordes exactos. Cache 554/11910, captura 270; O5 Musashi
0 > PAL. WinUAE baja de 98 a 92 fotos perdidas (1,46 %, racha 2), control
27; D1 roja. Vista 0/327680 píxeles distintos. Margen slow vivo G3 con
reservas: 272 B. Cpre C2a exacta en 2288 fotos; sonda C2b sin emitir
máximo 28680 ciclos contra parada 4000, C3/C4 pendientes. B35 fuera del vivo.
Informes: `docs/informe-g2t-b2bis-rendimiento-1008.md` y
`docs/informe-g2t-cpre-1008.md`.



### Estimaciones anteriores de ROADMAP §4, textuales

2026-10-10 (R1 + S9): de 25 a 12 omitidas en una sesión. El modelo de
cola es pesimista en +2 a +5 saltos. Llegar a ≤ 5 pide G5L-R-L (1-2
sesiones, ESTIMADO) y quizá otra palanca sin identificar. Restante:
**9-12**.

2026-10-09 (noche, Q): R1 (1 sesión) da la primera medida real del
recorte; llegar a ≤ 5 saltos estimado en 3-5 sesiones más con resultado
incierto (S5, ajuste general, blitter). Restante: **10-13**, más ese
riesgo en D1.

2026-10-09 (noche, Pa): la vía de la caché queda descartada. Quedan Q
(media sesión, medida) y después recortes de asm en G5L + S5 (2-4
sesiones, ESTIMADO, según lo que diga Q). Restante sin cambios:
**10-13**.

2026-10-09 (noche, T2): medida hecha. Bajar los tirones pide dos cosas
(camino lento de G5L y S5), estimado 1 sesión de medida (P-a) + 1-2 de
implementación + 1-2 de S5, dentro del total; restante estimado sin
cambios: **10-13**. La próxima espera la autorización del usuario.

2026-10-09 (noche): V y BM1 cerradas en una sesión; queda T2 (medida de
los tirones, 1 sesión estimada) antes de otro candidato. Total restante
estimado sin cambios: **10-13**.

2026-10-09: T llegó a su parada (dos candidatos, 66/65 BENCH; segundo
retirado por racha2). V ya funciona opt-in: falta teclado real y defecto.
BM1 MFM/fijo KS1.2 entregado WIP: falta KS1.3 y control de carga comparable.
Quedan **1-2 sesiones estimadas**, condicionadas a ROM/helper, para cerrar
esas puertas; bajar los tirones requiere revisar la parada antes de otra
ronda. Resto de ola3 (L-OAM, A2, R7) sin cambios. Total restante estimado
**10-13**, con incertidumbre por D1 y los enemigos aún sin dibujar.

B2bis tiene puertas locales verdes en d3e431c; coste real 92 fotos
perdidas contra 27 del control, D1 roja. Cpre C2a exacta; sonda C2b
detenida en 28680 ciclos contra 4000, C3/C4 pendientes.
El avance no cierra D1 ni B35; informe y pasos en PROXIMO.

### Filas anteriores de estado/presupuesto, textuales

| 6.4 | Scroll en el peor frame | **NO hecha**. S1a+S2 y SX/SX2 integradas; S4 descartada (P89); P51 arreglada (+6,7 % en `build_mid`). `build_mid` máx. **89,16 %** en WinUAE (ida, replay YI1, s ≈ 4576; `docs/medida-oam-o5.md`). Vuelta solo en Musashi (94,8 % en s = 2832, ×~1,3 en la Amiga). Falta S5 (EDF), S3/S6 y S8 (cámara vertical) | `player/scroll.s`; `docs/validacion-sx.md` |

| 8.2 | Lógica ≤ 40 % | **hecha para el alcance anterior; L-OAM no cerrada**. Ambas rutinas en asm (`e8ec165`, `bbdf201`, `cd5001c`, fusión `cb8ba8f`), RAM PC=68000 exacta. WinUAE l4: YI1 con `SPR_OAM` **41,2 %** (antes 43,1 %), back 73,9 %; fotos back 295 contra 145 del control, sprites 32 contra 0. Parada explícita tras ambas asm; nueva tarjeta pendiente | `player/logic68k.s`; `docs/informe-loam-1007.md`, `docs/informe-coordinacion-1007.md` |

| 9.2 | Sprites: dibujo | Mario hecho; G0/G1/G3a/G8 y G8b opt-in verificadas. G3 acotada hecha (64528 B DMA, 72724 B tablas, loader replay/vivo). G5a fallida y revertida (`652b23c`). **G5a-bis parcial en rama** `8fe712d`: A2 y variantes exactas; 59318 ventanas vacías + 18 fallos de capacidad, B/C detenidas. Coordinador reproduce el resumen y revisa las PNG. G2T revisión entregada. **G2T-A hecha (2026-10-07): contrato fijado con medidas y puerta A-T verde** en 3404 frames (0 sin plazo, 0 errores de color/capa 1/prioridad; 69 293 transiciones; 56 casos exactos + 27 negativos en WinUAE). El candidato era inviable: el hueco entre filas admite 12 − nb MOVE (P111); codo 231→243 (P110). **B35 parcial en rama `g2t-b35` (2026-10-08, `213ba3c`/`06e777f`)**: B4/B5 exactas en 3404 frames, ABI intacta, paso 4c/regress/hashes verdes; único intento en C agotado, máximo 2 405 022 ciclos sin DMA frente a 8000. No integrada; informe `docs/informe-g2t-b35-1008.md`. Primer microbench B35-asm entregado (`a9b44fe`): transiciones exactas en 3404 frames, máximo 18 794 ciclos solo en ese núcleo; no hay ruta medida al presupuesto, integración detenida (`docs/informe-g2t-b35-asm-1008.md`). El rendimiento de B2bis, C y un nuevo diseño viable del plan, más cobertura global/G4-G7/G9, pendientes. **G5L-R (2026-10-09, `052dac2`): el Rex se ve en la Amiga** por sprites 4-7 con 4 mapas limpios, caché del plan y colchón; 67 fotos perdidas (WinUAE, replay) contra 27 del control; vivo opt-in en a728ddc; T parada en 66 fotos BENCH, control con colchón9; defecto pendiente de teclado real. B2bis/Cpre/B35 aparcadas |  `docs/informe-g3-final.md`, `docs/informe-g5bis-1007.md`, `docs/informe-coordinacion-1007.md`, `docs/informe-g2t-1007.md`, `docs/informe-g2t-a-1007.md` |

| 6b | Integración | ADF en vivo y replay, O5 por defecto y diagnóstico. Con banco G3 y L-OAM asm, memmap replay/vivo: chip 455728/467256 B, slow 287712/323944 B; 0 violaciones. Gamecheck replay integrado 6313 frames, 0 distintos; Mario 6184/6184. Falta vlink C2, compresión C3 y loader C4 | `player/game.s`; `docs/informe-coordinacion-1007.md` |

| scroll: `build_mid` + columna + lista | ida **89,16 %** (WinUAE, s ≈ 4576, con P51); vuelta 94,8 % en Musashi (s = 2832; ×~1,3 en la Amiga, **sin medir en WinUAE**). Media de la ida ~15 % | repartir los picos (S5) | ídem; `scrollprof.py` |

| lógica `level_frame` con sprites y OAM | **37,24 %** (WinUAE, replay YI1) | ≤ 40 % | `docs/medida-oam-o5.md` |


## 2026-10-10 — sesión S10 (PROXIMO archivado textual)

PRÓXIMO — lo que sigue

2026-10-10. **Código en `g2t-b2bis`, sin merge ni push**; worktree:
`C:/Users/JC/Downloads/sma/wt-g2t-b2bis-1008`. Master conserva el código
anterior.

**P123 corregida y verificada.** `columns` destruía `a2`; el bucle G5L
leía una foto falsa y `g5l_choose` pisaba `GV_TAB`. Recarga de `dc_st`
antes de leer `DC_REND`; nuevo `dc_loop_verify.py` en la regresión.
Guru viejo reproducido con watchpoint; e7234ab + arreglo, 150 s en
WinUAE cycle-exact sin excepción. Informe:
`docs/informe-p123-scroll-1010.md`.

**Perfil hecho; optimización detenida por su puerta.** Domina `bm_left`
en la vuelta. Los recortes `bm_share`/FinishOAM eran exactos y ahorraban
CPU, pero empeoraron BENCH (back 387 → 389, sprites 98 → 104), por lo
que se retiraron. No está implementado el generador de speedcode.

**D1 sigue roja con el bucle corregido:** back 387/4126 (9,38 %, racha 5),
sprites 98/1914 (5,12 %, racha 3). Normal: VBTRACE 2 omitidas; BENCH
14/6312 (0,22 %, racha 1). Las cifras de L2 con el
bucle defectuoso quedan históricas; no sirven de control para el código
corregido. Se mantienen 50 Hz y el colchón aceptado.

#### 1. La próxima sesión, en orden

| tarjeta | responsable | ficheros / puerta | instrucciones |
|---|---|---|---|
| **G5L-R-S10** | coordinador, Sol high | `mkscroll.py`, `scroll.s`, pipeline y arnés. Prototipo offline de speedcode por línea/tramo; demostrar tamaño y ahorro antes de integrar. Copper exacto en los tres replays, memoria/PIC válidos, BENCH/VBTRACE mejores contra el control con P123 corregida | `docs/instrucciones-g5l-r-s10.md` |
| **G5L-R-L3** | coordinador, Sol high; después de la puerta S10 | `logic68k.s`, `mspr68k.s`: elegir por perfil entre `mario_E2BD`, `spr_tile`, `mc_pxy`, cámara y Mario. Fuzz/copper/ABI exactos y A/B real; retirar si empeora | `docs/instrucciones-g5l-r-l3.md` |

S10 empieza por coste y memoria: MLD 3.409 cargas útiles, 125.296 B de
slow libres en BENCH back (no es el margen de todos los builds). Si
domina la espera en hardware, medirla antes de elegir copper→blitter.
No repetir recortes de CPU sin su puerta integrada. No hace falta una
elección nueva del usuario para esta investigación/optimización ya autorizada.

Antes de cada commit: `python tools/lint_port.py` y `python tools/regress.py
--baseline tools/baseline_pc.json --level --g5l --bm1`, en verde.

#### 2. Pendiente del usuario

Probar el vivo a mano en esta rama; decidir cuándo integrar a master.

### Qué se hizo (S10)

- Partida verde: lint, `regress.py --level --g5l --bm1` OK; control
  `stress_back` con `DC LOOP: OK` y `G5L GAME (pcprof): OK`; perfil de diez
  fotos 804 730 ciclos de `build_mid`, igual al informe P123.
- Desglose por tramo: bucle por carga 30,5 %, trabajo fijo por línea ≈ 53 %
  (404 líneas, ≈ 4,6 cargas por línea).
- Prototipo `tools/s10_speedcode.py` (versionado): 103 056 B de código
  (vasm) + 15 424 B de punteros = 118 480 B; −6,2 % de CPU de `build_mid`
  (cota 13,5 % con entrada/salida gratis). No cabe en el vivo (61 288 B
  libres). **Puerta no cumplida; nada integrado**; binario y hashes sin
  cambios.
- WinUAE back 180,4 % del frame contra ≈ 65 % en Musashi (≈ 2,8×; son
  máximos, pueden ser de fotos distintas): nueva tarjeta de medida M1.
- Informe `docs/informe-g5l-r-s10-1010.md`; tarjeta
  `docs/instrucciones-g5l-r-m1.md`.


## 2026-10-10 — sesión M1 (PROXIMO archivado textual)

PRÓXIMO — lo que sigue

2026-10-10. **Código en `g2t-b2bis`, sin merge ni push**; worktree:
`C:/Users/JC/Downloads/sma/wt-g2t-b2bis-1008`. Master conserva el código
anterior.

**S10 cerrada por su puerta; nada integrado.** El prototipo de speedcode
(`tools/s10_speedcode.py`) ocupa 118 480 B (vasm), contra 61 288 B de slow
libres en el vivo, y ahorra un 6,2 % de la CPU de `build_mid` en Musashi
(cota 13,5 %). El bucle por carga es solo el 30,6 % de `build_mid`; el resto
es trabajo fijo por línea. Informe: `docs/informe-g5l-r-s10-1010.md`.

**Lo que manda ahora es el hardware:** en back, `build_mid` llega al 180,4 %
del frame en WinUAE frente a ≈ 65 % en Musashi (≈ 2,8×). La lógica corre en
el borde (COPER, línea 272); `build_mid` corre en `dc_loop`, casi siempre en
líneas visibles, con 6 planos, el copper y la slow compartiendo el bus.
Esa hipótesis hay que medirla antes de otra optimización.

**D1 sigue roja** (sin cambios): back 387/4126 (9,38 %, racha 5), sprites
98/1914, normal BENCH 14/6312, VBTRACE 2. 50 Hz y colchón aceptados.

#### 1. La próxima sesión, en orden

| tarjeta | responsable | ficheros / puerta | instrucciones |
|---|---|---|---|
| **G5L-R-M1** | coordinador, Sol high | flags opt-in de medida en `game.s`/`scroll.s` (`-DM1POS`, `-DM1NOBPL`, `-DM1BW`); pares por foto Musashi↔WinUAE, histograma de líneas de pantalla, reparto CPU/planos/copper+slow/blitter. Binario sin flags idéntico | `docs/instrucciones-g5l-r-m1.md` |
| **G5L-R-L3** | coordinador, Sol high; en paralelo con M1 (no depende de S10) | `logic68k.s`, `mspr68k.s`: elegir por perfil entre `mario_E2BD`, `spr_tile`, `mc_pxy`, cámara y Mario. Fuzz/copper/ABI exactos y A/B real; retirar si empeora | `docs/instrucciones-g5l-r-l3.md` |

M1 es solo medida: entrega una propuesta de tarjeta (mover la
reconstrucción al borde o a líneas sin fetch, partirla entre frames,
reducir accesos por línea o copper→blitter), sin implementarla. No
reintentar speedcode: la cota del 30,6 % no alcanza.

Antes de cada commit: `python tools/lint_port.py` y `python tools/regress.py
--baseline tools/baseline_pc.json --level --g5l --bm1`, en verde.

#### 2. Pendiente del usuario

Probar el vivo a mano en esta rama; decidir cuándo integrar a master.
En el checkout de master quedó sin commitear una versión vieja de
`docs/investigacion-demoscene-1010.md` (264 líneas) y su fila en
`docs/README.md`; la rama tiene la versión actualizada (320 líneas,
`6797dd0`). Descartarla o no es decisión del usuario.

### Qué se hizo (M1)

- `-DM1POS`/`-DM1NOBPL` en `game.s`, `tools/m1_read.py`, `g5l.py game
  --render-list`. Sin flags: replay YI1, BENCH back, vivo y BENCH YI1
  idénticos a HEAD (`cmp`).
- WinUAE back M1POS: 408 perdidas, `build_mid` 179,2 %; ratio
  WinUAE/Musashi por foto (misma secuencia) 1,60 de mediana. Con
  M1NOBPL: 253 perdidas, 98,8 %, ratio 1,07.
- Musashi con la secuencia real: máx. 146.860 ciclos contra 92.078 con
  todas las fotos.
- Espiral de la vuelta: 86 fotos con |Δs| > 16 en la misma lista, 10.386
  ticks de media. Foto 2580: 79 líneas reescritas contra 39.
- L3 no se empezó (sigue pendiente). Informe `informe-g5l-r-m1-1010.md`;
  tarjeta `instrucciones-g5l-r-s11.md`.


## 2026-10-10 — sesión S11 (PROXIMO archivado textual)

PRÓXIMO — lo que sigue

2026-10-10. **Código en `g2t-b2bis`, sin merge ni push**; worktree:
`C:/Users/JC/Downloads/sma/wt-g2t-b2bis-1008`. Master conserva el código
anterior.

**M1 hecha (solo medida).** El ≈ 2,8× de `build_mid` en el hardware se
reparte en dos partes: fotos omitidas ≈ 1,6× (Musashi con la secuencia real
de la Amiga: 146.860 ciclos contra 92.078) y DMA de los 6 planos ≈ 1,6×
(sin planos, WinUAE queda a 1,07 de Musashi). Copper, slow y blitter juntos
suman ≈ 6-9 %. Los picos son una **espiral en la vuelta**: cada lista se
reescribe con un |Δs| creciente (−12 … −48); con |Δs| > 16 hay 86 fotos de
10.386 ticks de media. Informe: `docs/informe-g5l-r-m1-1010.md`.

S10 (speedcode) quedó cerrada antes: 118 KB, −6,2 % de CPU, no cabe en el
vivo (`docs/informe-g5l-r-s10-1010.md`).

**D1 sigue roja** (control sin cambios): back 387/4126 (9,38 %, racha 5),
sprites 98/1914, normal BENCH 14/6312, VBTRACE 2. 50 Hz y colchón aceptados.

#### 1. La próxima sesión, en orden

| tarjeta | responsable | ficheros / puerta | instrucciones |
|---|---|---|---|
| **G5L-R-S11** | coordinador, Sol high | `player/scroll.s` (`bm_left`, LNS de `mkscroll.py`): medir por línea en las fotos de la espiral; candidatos A (buscar desde `prevlt`) y B (LNS para \|Δs\| ≤ 48). Lista exacta en los tres replays y A/B WinUAE con menos fotos perdidas | `docs/instrucciones-g5l-r-s11.md` |
| **G5L-R-L3** | coordinador, Sol high; después o en paralelo | `logic68k.s`, `mspr68k.s`: elegir por perfil entre `mario_E2BD`, `spr_tile`, `mc_pxy`, cámara y Mario. Fuzz/copper/ABI exactos y A/B real; retirar si empeora | `docs/instrucciones-g5l-r-l3.md` |

Herramientas nuevas para medir: `-DM1POS` (+ `tools/m1_read.py`) da una fila
por foto dibujada en WinUAE y `g5l.py game --render-list` repite esa
secuencia en Musashi. Cada ciclo de CPU que se ahorra en la vuelta vale
doble: lo multiplican los planos y baja el Δs de la espiral.

Antes de cada commit: `python tools/lint_port.py` y `python tools/regress.py
--baseline tools/baseline_pc.json --level --g5l --bm1`, en verde.

#### 2. Pendiente del usuario

- Probar el vivo a mano en esta rama y decidir cuándo integrar a master.
- **Solo como dato (no se propone):** con 5 planos (PF2 de 2) el ≈ 1,6× de
  los planos casi desaparecería, pero cambia D8 y el fondo. Es decisión
  tuya si alguna vez se quiere evaluar.
- En el checkout de master quedó sin commitear una versión vieja de
  `docs/investigacion-demoscene-1010.md` (264 líneas) y su fila en
  `docs/README.md`; la rama tiene la versión actualizada (320 líneas,
  `6797dd0`).

### Qué se hizo (S11)

- `g5l.py game --dump-lines`; fase 1 medida (ventanas de ≈ 13 px, ≈ 90
  reescrituras por foto). A/B/C sin margen; cerrada sin integrar.
  Informe `informe-g5l-r-s11-1010.md`. Sigue L3.


## 2026-10-10 — sesión L3 (PROXIMO archivado textual)

PRÓXIMO — lo que sigue

2026-10-10. **Código en `g2t-b2bis`, sin merge ni push**; worktree:
`C:/Users/JC/Downloads/sma/wt-g2t-b2bis-1008`. Master conserva el código
anterior.

**S11 cerrada en fase 1, sin integrar** (`docs/informe-g5l-r-s11-1010.md`): en la vuelta, una línea reescrita vale ≈ 13 px y en la espiral se reescriben ≈ 90 por foto; ningún candidato del scroll tiene margen medible. **Ahora: L3 (lógica).**

**M1 hecha (solo medida).** El ≈ 2,8× de `build_mid` en el hardware se
reparte en dos partes: fotos omitidas ≈ 1,6× (Musashi con la secuencia real
de la Amiga: 146.860 ciclos contra 92.078) y DMA de los 6 planos ≈ 1,6×
(sin planos, WinUAE queda a 1,07 de Musashi). Copper, slow y blitter juntos
suman ≈ 6-9 %. Los picos son una **espiral en la vuelta**: cada lista se
reescribe con un |Δs| creciente (−12 … −48); con |Δs| > 16 hay 86 fotos de
10.386 ticks de media. Informe: `docs/informe-g5l-r-m1-1010.md`.

S10 (speedcode) quedó cerrada antes: 118 KB, −6,2 % de CPU, no cabe en el
vivo (`docs/informe-g5l-r-s10-1010.md`).

**D1 sigue roja** (control sin cambios): back 387/4126 (9,38 %, racha 5),
sprites 98/1914, normal BENCH 14/6312, VBTRACE 2. 50 Hz y colchón aceptados.

#### 1. La próxima sesión, en orden

| tarjeta | responsable | ficheros / puerta | instrucciones |
|---|---|---|---|
| **G5L-R-L3** | coordinador, Sol high; **en curso** | `logic68k.s`, `mspr68k.s`: elegir por perfil entre `mario_E2BD`, `spr_tile`, `mc_pxy`, cámara y Mario. Fuzz/copper/ABI exactos y A/B real; retirar si empeora | `docs/instrucciones-g5l-r-l3.md` |

Herramientas nuevas para medir: `-DM1POS` (+ `tools/m1_read.py`) da una fila
por foto dibujada en WinUAE y `g5l.py game --render-list` repite esa
secuencia en Musashi. Cada ciclo de CPU que se ahorra en la vuelta vale
doble: lo multiplican los planos y baja el Δs de la espiral.

Antes de cada commit: `python tools/lint_port.py` y `python tools/regress.py
--baseline tools/baseline_pc.json --level --g5l --bm1`, en verde.

#### 2. Pendiente del usuario

- Probar el vivo a mano en esta rama y decidir cuándo integrar a master.
- **Solo como dato (no se propone):** S11 indica que el estrés back
  probablemente no entre en D1 solo con CPU del scroll. Con 5 planos (PF2 de 2) el ≈ 1,6× de
  los planos casi desaparecería, pero cambia D8 y el fondo. Es decisión
  tuya si alguna vez se quiere evaluar.
- En el checkout de master quedó sin commitear una versión vieja de
  `docs/investigacion-demoscene-1010.md` (264 líneas) y su fila en
  `docs/README.md`; la rama tiene la versión actualizada (320 líneas,
  `6797dd0`).

### Qué se hizo (L3)

- Perfil por etiqueta (`tools/lprof.py`): plano, nada pasa del 10 %.
  MCACHE exacto pero con el máximo +28 %: retirado. Ningún recorte de
  lógica mueve D1. Informe `informe-g5l-r-l3-1010.md`. Sigue G4-A
  (ola 4), tarjeta `instrucciones-g4a.md`.


## 2026-10-10 — sesión G4-A (PROXIMO archivado textual)

PRÓXIMO — lo que sigue

2026-10-10. **Código en `g2t-b2bis`, sin merge ni push**; worktree:
`C:/Users/JC/Downloads/sma/wt-g2t-b2bis-1008`. Master conserva el código
anterior.

**L3 cerrada, sin integrar** (`docs/informe-g5l-r-l3-1010.md`): el perfil
de la lógica es plano (nada pasa del 10 %). La caché de `mspr_draw` era
exacta pero subía el máximo un 28 %, así que se retiró. El C que queda
pesa 0,8 % en YI1 y 5,7 % en back. Con S10, S11 y M1, el estrés no tiene
recortes de CPU con margen medido. Lo que lo separa de D1 es la
reconstrucción de la vuelta multiplicada por el DMA de los 6 planos.
**Ahora: ola 4, por G4-A.**

**D1 sigue roja** (control sin cambios): back 387/4126 (9,38 %, racha 5),
sprites 98/1914, normal BENCH 14/6312, VBTRACE 2. 50 Hz y colchón aceptados.

#### 1. La próxima sesión, en orden

| tarjeta | responsable | ficheros / puerta | instrucciones |
|---|---|---|---|
| **G4-A** | coordinador; **en curso** | `tools/g4a.py` (nuevo), solo en la PC: inventario por tipo de enemigo, columnas por línea fuera de Mario, cota de bobs y memoria de la tabla G5L para todos. Puerta de cruce: el Rex da las 48 formas del banco | `docs/instrucciones-g4a.md` |
| G4 + G6 | después de G4-A | el plan G5L para N objetos, con el formato de tabla que salga de G4-A | `docs/instrucciones-olas.md` §3 |

Antes de cada commit: `python tools/lint_port.py` y `python tools/regress.py
--baseline tools/baseline_pc.json --level --g5l --bm1`, en verde.

#### 2. Pendiente del usuario

- Probar el vivo a mano en esta rama y decidir cuándo integrar a master.
- **Solo como dato (no se propone):** S11 y L3 indican que el estrés back
  probablemente no entre en D1 solo con CPU. Con 5 planos (PF2 de 2) el
  ≈ 1,6× de los planos casi desaparecería, pero cambia D8 y el fondo. Es
  decisión tuya si alguna vez se quiere evaluar.
- En el checkout de master quedó sin commitear una versión vieja de
  `docs/investigacion-demoscene-1010.md` (264 líneas) y su fila en
  `docs/README.md`; la rama tiene la versión actualizada (320 líneas,
  `6797dd0`).

### Qué se hizo (G4-A)

- `tools/g4a.py`: inventario exacto con trazas SOT1 del host en las 30
  grabaciones, columnas por línea, cota de bobs y memoria por formato
  (estimador validado exacto contra `g5l.bin`). Hallazgo: G5L no dibuja
  el Rex aplastado con otro dy. Informe `informe-g4a-1010.md`. Sigue
  G5L-N, tarjeta `instrucciones-g5l-n.md`.


## 2026-10-10 — sesión G5L-N (PROXIMO archivado textual)

PRÓXIMO — lo que sigue

2026-10-10. **Código en `g2t-b2bis`, sin merge ni push**; worktree:
`C:/Users/JC/Downloads/sma/wt-g2t-b2bis-1008`. Master conserva el código
anterior.

**G4-A hecha (solo medida)** (`docs/informe-g4a-1010.md`). Con trazas
exactas de las 30 grabaciones aparecen 9 tipos con gráfico; ninguno pasa
de 15 colores. **Hallazgo:** G5L no dibuja el Rex aplastado cuando
aparece con otro desplazamiento vertical: 340 de 2.110 frames con Rex en
`hills2`, también en `stress_*`, `shells` y `pw_estrella`. Con la clave
normalizada, 30 de esas 33 formas ya están en el banco, y el Rex baja de
48 a 22 formas. La tabla G5L de todos los enemigos solo entra en slow con
la clave normalizada y las máscaras compartidas (83 KB con 4 mapas). El
Banzai como bob (+59 KB) y el audio no entran en chip hasta C2/C4, que
además necesitan compresión (C3). **Ahora: G5L-N.**

L3 quedó cerrada antes, sin integrar (`docs/informe-g5l-r-l3-1010.md`):
ningún recorte de la lógica mueve D1.

**D1 sigue roja** (control sin cambios): back 387/4126 (9,38 %, racha 5),
sprites 98/1914, normal BENCH 14/6312, VBTRACE 2. 50 Hz y colchón aceptados.

#### 1. La próxima sesión, en orden

| tarjeta | responsable | ficheros / puerta | instrucciones |
|---|---|---|---|
| **G5L-N** | coordinador; **en curso** | `tools/g5l.py` (formato `G5L2`), `player/g5l.s` (`g5l_choose`, `g5l_patch`): clave normalizada y máscaras una vez por forma. Puertas: `g5l.py trace` con las trazas nuevas (`rex_sin_forma` ≤ 3 formas), `g5l.py game`, regresión, memmap, A/B BENCH y captura de `hills2` | `docs/instrucciones-g5l-n.md` |
| G4 + G6 | después de G5L-N | el plan G5L para N objetos con el formato `G5L2`; Rex con 4 mapas y los demás con 1 (chip) | `docs/instrucciones-olas.md` §3, `informe-g4a-1010.md` §6 |

Antes de cada commit: `python tools/lint_port.py` y `python tools/regress.py
--baseline tools/baseline_pc.json --level --g5l --bm1`, en verde.

#### 2. Pendiente del usuario

- Probar el vivo a mano en esta rama y decidir cuándo integrar a master.
- **Solo como dato (no se propone):** S11 y L3 indican que el estrés back
  probablemente no entre en D1 solo con CPU. Con 5 planos (PF2 de 2) el
  ≈ 1,6× de los planos casi desaparecería, pero cambia D8 y el fondo. Es
  decisión tuya si alguna vez se quiere evaluar.
- En el checkout de master quedó sin commitear una versión vieja de
  `docs/investigacion-demoscene-1010.md` (264 líneas) y su fila en
  `docs/README.md`; la rama tiene la versión actualizada (320 líneas,
  `6797dd0`).

### Qué se hizo (G5L-N)

- Tabla `G5L2` (clave normalizada, máscaras por forma) en `g5l.py` y
  `g5l.s`: 128.724 → 44.810 B; el Rex aplastado ya se dibuja (hills2
  340 → 0); A/B no peor; hills2 foto 1720 exacta. P124. Informe
  `informe-g5l-n-1010.md`. Sigue G4-1, tarjeta `instrucciones-g4-1.md`.


## 2026-10-10 — sesión G4-1 (PROXIMO archivado textual)

PRÓXIMO — lo que sigue

2026-10-10. **Código en `g2t-b2bis`, sin merge ni push**; worktree:
`C:/Users/JC/Downloads/sma/wt-g2t-b2bis-1008`. Master conserva el código
anterior.

**G5L-N hecha e integrada en la rama** (`docs/informe-g5l-n-1010.md`).
La tabla del Rex pasa a `G5L2`, con la clave normalizada y las máscaras
una vez por forma. Ocupa 44.810 B en vez de 128.724, y la slow libre del
vivo sube de 61 a 145 KB. **El Rex aplastado sobre una pendiente ya se
dibuja**: en `hills2`, 340 frames → 0 sin forma. En la foto 1720, la
captura WinUAE es el control más el Rex planeado, con 0 de 327.680
píxeles distintos. El A/B BENCH no empeora (normal 14→9, back 392→373,
sprites 98→88). Trampa nueva: P124. **Ahora: G4-1.**

G4-A (medida) quedó antes (`docs/informe-g4a-1010.md`): 9 tipos con
gráfico, ninguno de más de 15 colores. El Banzai es bob, y el bob y el
audio no entran en chip hasta C2/C4 + C3.

**D1 sigue roja**: back 373/4126 (racha 4), sprites 88/1914, normal BENCH
9/6312 (tanda de G5L-N). 50 Hz y colchón aceptados.

#### 1. La próxima sesión, en orden

| tarjeta | responsable | ficheros / puerta | instrucciones |
|---|---|---|---|
| **G4-1** | coordinador; **en curso** | `tools/g5l.py` (`plan_frame_n`, `check_trace_n`, `trace --multi`), solo Python: varios Rex por foto en los pares 4-5 y 6-7, con reuso vertical y colores compartidos con Mario. Puerta: 0 errores de color en las 8 trazas; cada Rex visible queda dibujado o en la cola de bobs con su motivo | `docs/instrucciones-g4-1.md` |
| G4-2 | después de G4-1 | el 68000 de `plan_frame_n` en `g5l.s`, `g5l.py game` exacto, A/B | (la escribe G4-1) |

Antes de cada commit: `python tools/lint_port.py` y `python tools/regress.py
--baseline tools/baseline_pc.json --level --g5l --bm1`, en verde.

#### 2. Pendiente del usuario

- Probar el vivo a mano en esta rama y decidir cuándo integrar a master.
  Novedad visible: el Rex aplastado sobre pendientes.
- **Solo como dato (no se propone):** S11 y L3 indican que el estrés back
  probablemente no entre en D1 solo con CPU. Con 5 planos (PF2 de 2) el
  ≈ 1,6× de los planos casi desaparecería, pero cambia D8 y el fondo. Es
  decisión tuya si alguna vez se quiere evaluar.
- En el checkout de master quedó sin commitear una versión vieja de
  `docs/investigacion-demoscene-1010.md` (264 líneas) y su fila en
  `docs/README.md`; la rama tiene la versión actualizada (320 líneas,
  `6797dd0`).

### Qué se hizo (G4-1)

- `plan_frame_n`/`check_trace_n`/`trace --multi` en `g5l.py`: 0 errores
  de color en 8 trazas; el límite son los canales. Informe
  `informe-g4-1-1010.md`. Sigue G4-2, tarjeta `instrucciones-g4-2.md`.


## 2026-10-10 — sesión G4-2 (PROXIMO archivado textual)

PRÓXIMO — lo que sigue

2026-10-10. **Código en `g2t-b2bis`, sin merge ni push**; worktree:
`C:/Users/JC/Downloads/sma/wt-g2t-b2bis-1008`. Master conserva el código
anterior.

**G4-1 hecha (solo Python)**, ver `docs/informe-g4-1-1010.md`.
`plan_frame_n` ubica varios Rex por foto en los pares 4-5 y 6-7, con reuso
vertical (gap 1). En las 8 trazas hay 0 errores de color y 0 píxeles
tapados. Ningún Rex queda afuera por color ni por plazo: **el límite son
los canales**. hills2 sube de 1.893 a 2.498 Rex, stress_sprites de 1.040 a
1.305 y stress_back de 2.440 a 2.576. yi1 queda igual porque los Rex que
faltan comparten filas. Con un solo Rex el plan es igual al de hoy.
**Ahora: G4-2.**

Antes quedaron G5L-N (`informe-g5l-n-1010.md`), con la tabla `G5L2`, el
Rex aplastado y +84 KB de slow, y G4-A (`informe-g4a-1010.md`).

**D1 sigue roja**: back 373/4126 (racha 4), sprites 88/1914, normal BENCH
9/6312 (tanda de G5L-N). 50 Hz y colchón aceptados.

#### 1. La próxima sesión, en orden

| tarjeta | responsable | ficheros / puerta | instrucciones |
|---|---|---|---|
| **G4-2** | coordinador; **en curso** | `player/g5l.s` y `tools/g5l.py`: el 68000 de `plan_frame_n` (hasta 4 Rex en los pares 4-7, encadenado DMA por lista, sin MOVE nuevos). Puerta: `g5l.py game --multi` exacto, regresión, memmap, A/B BENCH y captura con 2 Rex | `docs/instrucciones-g4-2.md` |
| G4-3 | después de G4-2 | los pares de Mario (0-1/2-3) fuera de sus filas: la cota de G4-1 §3 | (la escribe G4-2) |

Antes de cada commit: `python tools/lint_port.py` y `python tools/regress.py
--baseline tools/baseline_pc.json --level --g5l --bm1`, en verde.

#### 2. Pendiente del usuario

- Probar el vivo a mano en esta rama y decidir cuándo integrar a master.
  Novedad visible: el Rex aplastado sobre pendientes.
- **Solo como dato (no se propone):** S11 y L3 indican que el estrés back
  probablemente no entre en D1 solo con CPU. Con 5 planos (PF2 de 2) el
  ≈ 1,6× de los planos casi desaparecería, pero cambia D8 y el fondo. Es
  decisión tuya si alguna vez se quiere evaluar.
- En el checkout de master quedó sin commitear una versión vieja de
  `docs/investigacion-demoscene-1010.md` (264 líneas) y su fila en
  `docs/README.md`; la rama tiene la versión actualizada (320 líneas,
  `6797dd0`).

### Qué se hizo (G4-2)

- El 68000 de `plan_frame_n` en `g5l.s`: hasta 2 Rex por foto, separados
  en vertical, en los pares 4-5/6-7, con encadenado DMA por lista
  (`g5l_emitn`) y sin MOVE nuevos. `g5l.py game` exacto en yi1, hills2
  (605 fotos con 2 Rex, 1.380 cadenas), stress_sprites y stress_back.
  P125.
- La foto con 2 Rex cuesta ≈ 63 k ciclos de mediana contra ≈ 25 k. El A/B
  BENCH empeora D1 (hills2 210 → 398, sprites 91 → 194, back 380 → 418;
  normal 11 = 11), así que **queda apagado por defecto** (`G5L_MAXPL` = 1,
  `-DG5L_MAXPL=2` para activarlo).
- Capturas de hills2 en las fotos 1825 y 2130 con el segundo Rex: 0
  píxeles distintos. Informe `informe-g4-2-1010.md`. Sigue G4-2o
  (abaratar), tarjeta `instrucciones-g4-2o.md`; después G4-3.
