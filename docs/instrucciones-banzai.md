# BANZAI — dibujar el Banzai Bill (`$9F`)

2026-10-11. Pedido del usuario. Hoy el Banzai tiene lógica (G8b: 391/391
frames exactos en PC/68000) pero **no se dibuja**: en el ADF vivo es
invisible y mata igual. Mide 64×64 px y en sprites de hardware ocuparía
los 8 canales, por eso el plan es un **bob en el PF1** con la
infraestructura de G7 (`player/g7bobs.s`: doble PF1, cola de blits por
IRQ, restauración).

## Lo que ya se sabe

- Memoria (memmap 2026-10-11):
  - vivo por defecto: chip 451.024 B (margen **73.264 B**), slow margen
    14.392 B;
  - vivo con G7_BOBS (segundo PF1 y 12 KiB de banco): chip margen
    **1.840 B**, slow 5.040 B.

  El bob del Banzai (gráficos + máscara a 3 planos) se estimó en **+59 KB
  de chip** (ROADMAP §4, G4-A).
- Hay 135.468 B de tablas que solo lee la CPU y están en chip;
  moverlas pide C2/C4 (y compresión C3, `docs/diseno-9.2.md` §5).
- Coste: Banzai + 4 Rex = 22,7-33,8 % del frame en `bench2.s` W3, y el
  tramo del Banzai es uno de los de estrés de D1 (`stress_sprites`).

## Pasos

1. **Presupuesto exacto**: bytes del bob a partir de los gráficos reales
   (GFX `20`, `tools/g7_sources.py`). Cuánto libera mover a slow las
   tablas solo de CPU, con y sin compresión, y si el slow lo admite. Una
   tabla: necesita / libera / queda, en vivo y en replay.
2. **Propuesta al usuario** si hace falta C2/C3/C4 o resignar algo.
3. **Especificación** del dibujo en Python contra la OAM de la SNES
   (`P.overlays` / `tools/g7_sources.py`; las fichas del Banzai salen de su
   OAM, G8b). Prioridad contra el terreno y los demás sprites como en
   G9, y verificador de píxeles en `stress_sprites` y en el replay de YI1
   (k5799-6077).
4. **68000** con la cola de G7, cruzado contra la especificación y con
   captura WinUAE. Medir el coste en BENCH (puerta D1, no empeorar sin
   avisar).

## No hacer

- No aproximar colores ni la forma. No usar tablas por número de frame.
- No activar por defecto algo que rompa la puerta de memoria (memmap con
  0 violaciones, P126) ni el hash del vivo sin decisión del usuario.
