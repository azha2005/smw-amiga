# D1 — optimizar con todo activado

2026-10-10. Escrita al cerrar SW-S. **Grande**: es la compuerta de 50 Hz
(D1, ROADMAP §2) con todas las opciones de fidelidad activadas por defecto
(SW-A/B/P/M/Q, G4-2, G4-B, SW-S). El usuario quiere 1:1 primero y
optimizar después; esto es el "después".

## Dónde estamos

BENCH de yi1, WinUAE cycle-exact, master con SW-S (`informe-sw-s-1010.md`):

| | valor |
|---|---:|
| fotos perdidas | 217 (3,44 %), racha 2 |
| total medio | 13 501 ticks (95,0 % del frame) |
| frames de más de un frame | 583 |
| peor `build_mid` | 15 604 ticks (frame 4220, oráculo 9365, s 1784) |
| peor `resto de scroll_frame` | 18 798 (frame 3326, oráculo 8471) |
| peor `level_frame` | 4 640 (frame 3420, oráculo 8565) |
| peor `columna` | 2 837 |

Objetivo (ROADMAP §2): 0 fotos perdidas; mínimo ≤ 0,1 %, racha 1, ≤ 1
cada 250 frames.

## Pasos

1. **Repetir la medida de partida** en el árbol actual, para no comparar
   contra números viejos:
   ```
   OUT=work/d1o/base GDEFS="-DREPLAY -DBENCH" sh tools/bm_build.sh
   ```
   ```powershell
   & C:\Users\JC\Downloads\sma\winuae_lock.ps1 .\tools\shot.ps1 -Exact -Adf work\d1o\base\game.adf -Out work\d1o\base\shot.png -Wait 220
   ```
   ```
   python tools/game_read.py --shot work/d1o/base/shot.png --auto
   ```
   Con `tools/game_build.sh` el replay no entra en chip (pantalla roja,
   P126): siempre `bm_build.sh`.
2. **Ubicar las fotos perdidas.** Lo que importa son los tramos tarde
   (P115: rachas de ~8 fotos sobre el presupuesto), no el peor frame
   aislado. La sucesión real de imágenes la da `-DVBTRACE` +
   `tools/vbtrace.py` (P120); las trazas D1TR, `docs/medida-d1-winuae.md`.
3. **Perfil por función de esos tramos**: `g5l.py game --pcprof OUT
   --pclogic RANGOS` sobre el binario del replay y
   `tools/l_funcs.py prof.json game.lst frames.json` (cabecera de
   `l_funcs.py`). Anotar en el informe las 5 funciones que más pesan en
   los frames de las fotos perdidas.
4. **Atacar en orden de peso**, una cosa por vez, con su A/B BENCH
   (mismo binario con y sin el cambio). Candidatos conocidos:
   - `build_mid` y `resto de scroll_frame` (el scroll, plan-tecnico
     §9.2; P121: los picos vienen de a tres, uno por lista);
   - `level_frame`: el C que queda en la lógica (plan-tecnico §9.3);
     el bucle de los motores de SW-S solo cuando hay ranuras activas
     (hoy cada iteración recarga la base con `lea`);
   - G5L con 2 objetos por foto (G4-2o dejó 52 k de mediana con 2 Rex).
5. **Cada cambio de asm**: la regresión (cruce PC = 68000), las puertas
   del área (`sws_gate.sh` si toca SW-S, `oam68k_gate.sh` si toca la OAM,
   `dc_loop_verify` y G5L si toca el render) y el A/B BENCH. Una mejora
   que no se ve en el BENCH no cuenta.

## Puertas

- Fotos perdidas del BENCH de yi1 por debajo de la partida, con el A/B de
  cada cambio en el informe.
- Regresión completa y lint en verde; la base se actualiza solo con un
  coste menor o igual.
- Sin cambiar la fidelidad: las puertas de SW1/G9/SW-S siguen iguales.

## Trampas

- P30: sin `-Exact` los tiempos son falsos.
- P96: el factor del DMA no es uniforme; no convertir ciclos Musashi a
  tiempo de WinUAE.
- P115: con el colchón, un VBL repetido siempre se paga con una foto.
- P121: los picos de `build_mid` vienen de a tres.
- P126: el replay con Exec no entra en chip; BENCH con `bm_build.sh`.
