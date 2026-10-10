# SW-D — los detalles de 1-6 px de SW1

2026-10-10. Sale de SW1 (`informe-sw1-1010.md`, punto 11). **Fácil de
investigar**; el arreglo depende de la causa.

## Por qué

Diferencias chicas y repetidas que no explica ninguna tarjeta:

| dónde | fotos | forma |
|---|---|---|
| la esquina de arriba a la izquierda de una cornisa, filas 137-141 | k 1799-2099 (6) | 4 px, 2 de ancho, se mueve con la cámara |
| un píxel en la fila 185 | 13 fotos de k 299-1149 | 1 px, se mueve con la cámara |
| el pie del Koopa sobre la pendiente | k 49 (5 px), k 99 (33 px), k 1049 (24 px) | sprite contra la capa 1 |

Los dos primeros acompañan a la cámara: son capa 1 o capa 2, no sprites.

## Pasos

1. **Por píxel:** agregar a `sweep_cmp.py cmp` un `--px k` que liste
   cada píxel distinto con su color SNES (15 bits), el de la Amiga (12
   bits) y la coordenada de nivel (cámara del registro + x, y).
2. **Qué capa lo pone en la SNES.** Agregar a `snesorc --shots` un
   `--layers` que dibuje además la pantalla con cada fondo apagado (el
   `TM` de la PPU, guardado y restaurado como el resto). El píxel que
   cambia al apagar BG1 es de la capa 1, y así con las demás.
3. **Clasificar:**
   - un color que el plan por línea de `mkscroll.py` aproximó (D9: 7
     colores por línea en PF1) → el informe lo dice; decidir si se
     reasigna;
   - un tile distinto (otra entrada de Map16, P28, o un tile animado,
     SW-A) → arreglar en la tubería;
   - la capa 2 → `mkbg.py`/PF2;
   - el Koopa: la prioridad (SW-P) o la forma (G9/L-DER).
4. Arreglar lo que sea de datos. Lo demás, a su tarjeta.

## Puertas

- Cada caso con su causa en el informe.
- SW1 repetida: los casos arreglados, exactos.
- Regresión completa y lint.

## Trampas

- P19, P20: la capa 2 y las métricas de color.
- P57: el centro del píxel en la captura.
- P128: la alineación de filas de la barrida.
