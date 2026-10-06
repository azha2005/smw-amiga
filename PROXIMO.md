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
