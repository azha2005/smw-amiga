# META-R — rendimiento al final del nivel (zona de la meta)

2026-10-11. Pedido del usuario: "realmente tenemos que encontrar una
manera de mejorar el rendimiento al final del nivel". **Primero medir,
después atacar lo más grande.** No se propone ningún arreglo antes de tener
el reparto medido.

## Lo que ya se sabe

- **Scroll**: los postes de la meta son un borde vertical. Sus cargas
  "tarde" cruzan la celda en el mismo frame en que entran las nuevas
  (P81), y agrupar no baja el pico.
- **Efectos (G7)**: las 40 fotos de YI1 sin plan PF1 y las 25 sin plan ni
  en sprites (G7-S0) están todas en la meta (k6019-6070, k6229-6268). Las
  más caras del productor también (k6047, k6273).
- La cinta (`$7B`), los puntos del final y el Chuck caen cerca.

## Pasos

1. **Reparto por componente en la meta**, WinUAE cycle-exact (BENCH y
   VBTRACE, `docs/instrucciones-olas.md`). Medir sobre el tramo final del
   replay YI1 (desde la entrada de los postes hasta el final) y sobre
   `oracle_goal`, `goal_low` y `goal_miss`: `build_mid`, `level_frame`,
   G5L, Mario, y G7 opt-in por separado. Dar las fotos omitidas, la racha
   y los ciclos por componente en los 20 peores frames.
2. **Comparar con el resto del nivel**: ¿qué componente sube en la meta y
   cuánto? Una tabla, no una impresión.
3. **Propuestas con números** para lo que más pese, cada una con su puerta
   (exactitud igual que hoy, BENCH A/B). Si lo que domina es G7, cruzarlo
   con G7-S1 (`docs/instrucciones-g7-s1.md`). Si es el scroll, partir de
   P81 y de `docs/informe-p123-scroll-1010.md`.
4. Informe `docs/informe-meta-r-<fecha>.md`. Las decisiones que cambien
   la fidelidad o la memoria se le presentan al usuario.

## No hacer

- No aceptar fotos omitidas ni bajar la fidelidad sin el usuario.
- No usar tablas por número de frame ni casos especiales "si estamos en la
  meta" que no salgan del estado del juego.
