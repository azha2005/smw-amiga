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
