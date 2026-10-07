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
