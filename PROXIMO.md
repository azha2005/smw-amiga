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
