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
