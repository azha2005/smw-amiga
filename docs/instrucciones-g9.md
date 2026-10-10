# G9 — la imagen de los sprites contra la OAM de la SNES

2026-10-10. Sigue a G4-B. Misma rama y worktree, sin merge ni push.
Tarjeta en `SUBAGENTES.md` (G9).

## Por qué

Hasta ahora las capturas de sprites se comparan **contra otra captura**.
`g5l.py shot` toma un control, le suma los píxeles que la referencia
Python espera del objeto y compara contra el candidato. Eso tiene tres
problemas:

- depende de que exista una foto en la que el control no dibuje nada
  (con el Chuck no la había; G4-B §6 tuvo que armar un control con
  `G5L_TYPES=02`);
- hereda cualquier error que tenga el control;
- compara contra el plan del port, no contra la SNES.

Con 8 tipos dibujados por G5L, el criterio 1:1 (AGENTS §1) necesita una
comparación directa: **la OAM que grabó el oráculo, dibujada en Python,
contra la captura de WinUAE**.

## Objetivo

Un `tools/sprshot_cmp.py` (nuevo) que, para una captura de un replay en
la foto k:

1. Encuentre el frame del oráculo de esa foto:
   - `game_frames.json` (campo `f`) o la cuenta de `game_read.py`
     ("oraculo = primero + frame");
   - ojo con P75: `-DSTOPF` cuenta desde el primer frame del replay.
2. Dibuje los sprites de la SNES de ese frame a partir de las trazas
   completas `work/oamb_<nombre>.trace` (G4-B), en la resolución de la
   captura (PAL × 2, `SHOT_BOX` de `g5l.py`, P57: centro del píxel):
   - Mario, desde la OAM (`g5ref.mario_pixels` / `g2t_ref.mario_check`);
   - cada objeto, desde sus fichas (`g4a.pose_of` con la VRAM/CGRAM del
     nivel), con sus colores BGR555 → 12 bits como en `rgb12`.
3. Compare solo las **zonas de sprite**: los píxeles opacos de algún
   sprite en la SNES, más los que el port pinta con colores de sprite.
   - Fuera de esas zonas no se compara: el fondo ya lo verifican el
     scroll y `cmp_ref`.
   - Prioridad SNES contra la capa 1 (Mario detrás de las tuberías):
     contar aparte los píxeles tapados en la SNES, sin mezclarlos con
     los errores.
4. Informe **por objeto**:
   - **exacto**;
   - **no dibujado, con su motivo**. Los motivos son: otro más alto con
     un objeto por foto, `bob_canal`/`bob_color` de `plan_frame_n`, sin
     forma, o cola de bobs (Banzai, G7). Se obtienen corriendo
     `plan_frame` / `plan_frame_n` sobre la misma foto;
   - **dibujado con N píxeles distintos**.

   Y Mario aparte.

## Pasos

1. La herramienta y su autotest:
   - una foto sintética armada desde la propia referencia (OAM → imagen
     → comparar) tiene que dar 0;
   - la misma foto movida 1 px tiene que dar distinto.
2. Correrla sobre las capturas que ya hay en `work/g4b/`:
   - `pcand1705`: la piraña tiene que salir exacta;
   - `ccand2460`: el Chuck exacto, y explicar dónde caen los 12 px del
     poste;
   - `pctrl1705`, `cctrl2460`: lo que el control no dibuja tiene que
     salir como "no dibujado" con su motivo.
3. Un juego de fotos por replay elegidas solas desde `game_frames.json`
   (`plan.rex[].tipo`): al menos una por tipo dibujado y una con Mario
   cruzando un objeto (bandas). Builds con `-DSTOPF` (replay; **cuidado
   con P126: margen de chip real ≥ 0**) y capturas en serie con
   `winuae_lock.ps1`.
4. **Puerta:**
   - 0 píxeles distintos en los objetos dibujados y en Mario;
   - todo objeto no dibujado con su motivo;
   - el resumen por tipo en el informe.

   Si algo no da 0, aislar con la regla de diagnóstico de AGENTS §11
   (posición correcta pero mal: indirección).
5. Informe `docs/informe-g9-<fecha>.md` y cierre según ROADMAP §7.

## Trampas

- **P57**: muestrear el centro del píxel.
- **P75**: `STOPF` no es el frame del oráculo.
- **P99, P100**: gráficos y columnas de sprites.
- **P108**: el banco es inmutable.
- **P126**: el margen de chip del replay.
- **P81, P45**: los postes de la meta tienen cargas tarde del scroll.
  No son de sprites; si caen en una zona de sprite, separarlos.
- Las capturas no corren en paralelo: un WinUAE por vez, con el candado.
