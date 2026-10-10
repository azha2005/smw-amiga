# G4-1 — varios Rex por foto: la referencia en Python

2026-10-10. Primera parte de G4+G6 (`instrucciones-olas.md` §3). Sigue a
G5L-N. Misma rama y worktree, sin merge ni push. **Solo Python; el binario
no cambia.** El 68000 es G4-2, con su propia tarjeta.

## Por qué

G5L dibuja **un** Rex por foto, el visible más alto (`plan_frame`:
`best`). En las grabaciones llega a haber 5 a la vez (`informe-g4a-1010.md`
§2), y en `yi1` hay 245 fotos con un Rex que no se dibuja
(`sin_rex_dibujado`; también lo cuentan los que están fuera de pantalla).
Medir cuántos de esos son por la regla de uno es el primer número.

## Modelo (lo que hay que respetar)

- Canales: Mario en 0-3 (dos pares acoplados). Los Rex, en los pares 4-5
  y 6-7. Un par se puede reusar en vertical si queda **una línea libre**
  entre el fin de un objeto y el principio del siguiente (G0, PT en la
  línea anterior; `docs/medida-g0.md`). El Rex mide 20 px: dos columnas
  (P100); hoy G5L lo resuelve con un par por columna, y esa regla se
  conserva.
- Colores: los pares acoplados comparten COLOR17-31 con Mario. Un segundo
  Rex en las mismas filas suma sus índices a las filas ocupadas. Para
  `band_assign` y `sweep`, Mario y los Rex ya ubicados son "lo que ya
  usa el índice en esa fila". El orden de ubicación es el de la SNES
  (prioridad OAM: primera entrada opaca) o, si no importa, el de la fila.
- La capacidad de las recargas por segmento (`place`) es la misma; lo que
  no entra se reporta, nunca se descarta en silencio.
- Lo que no entra en sprites va a una **cola de bobs explícita** (D8), por
  ahora solo contada: tipo, foto y motivo (canal, color o plazo).

## Pasos

1. Línea de base: en las 8 trazas de G5L-N (`yi1 normal spin_kill hills2
   shells stress_back stress_sprites pw_estrella`), contar por foto los Rex
   visibles y los dibujados con la regla actual. Separar `sin_rex_dibujado`
   en: fuera de pantalla, sin forma y "no es el más alto".
2. `plan_frame_n` en `tools/g5l.py` (sin tocar `plan_frame`, que sigue
   siendo la referencia del 68000 hasta G4-2). Asignar pares y reusos.
   Para colores, generalizar `band_need`/`band_assign` con las filas ya
   ocupadas, y `sweep`/`place` con la unión de las transiciones.
3. `check_trace_n`: los errores de color de cada píxel de Mario y de
   **todos** los Rex dibujados (`g2t_ref.simulate`, como `check_trace`).
4. `g5l.py trace --multi`. Puerta: 0 errores de color en las 8 trazas;
   cada Rex visible queda dibujado o en la cola de bobs con su motivo;
   tabla de dibujados por foto contra la línea de base.
5. Informe `docs/informe-g4-1-1010.md`: cuántos Rex más se dibujan, los
   motivos de la cola de bobs, el costo estimado del plan en el 68000
   (transiciones, sufijos y VBL por foto, contra los máximos de hoy:
   `G5L_MAXTR` 200, `G5L_NPOOL` 32) y la tarjeta G4-2.

## No toca

`player/*`, `plan_frame` (lo usa `g5l.py game`), el banco G3.
