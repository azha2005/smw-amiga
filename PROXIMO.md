# PRÓXIMO — lo que sigue

2026-10-09 (noche). **Código en `g2t-b2bis`, sin merge ni push**; worktree:
`C:/Users/JC/Downloads/sma/wt-g2t-b2bis-1008`. Master conserva el código
anterior; los documentos indican el avance de la rama.

**G5L-R-T2, Pa y Q hechas**, solo medida (`docs/informe-g5l-r-t2-1009.md`,
`docs/informe-g5l-r-pa-1009.md`, `docs/informe-g5l-r-q-1009.md`). Los 25
saltos de VBTRACE (66 fotos BENCH) son atraso acumulado; reutilizar el plan
de G5L no sirve. El perfil por PC es **plano**: las reescrituras concretas
y exactas ahorran ~8 % del render G5L y ~8 % de `build_mid` en las
ventanas de salto. Modelo (ESTIMADO): 25 → 14-16 saltos, 10-11 con S5;
≤ 5 pide además −10 % general sin bucle identificado (2-4 con S5), o el
patch por blitter (sin medir). **D1 sigue roja.**

## 1. La próxima sesión — decide el usuario

| tarjeta | toca | instrucciones y entrega |
|---|---|---|
| **G5L-R-R1** (recomendada; **pendiente de autorización**: es un candidato) | `player/g5l.s`: clave del plan con lo que cambia primero, copias con `movem`, `emit.mv` desenrollado, mapa de bits en `place.f1`; cada una con `G5L GAME: OK`; después **la primera medida en WinUAE** (BENCH, VBTRACE) de cuánto valen los ciclos de Musashi en fotos omitidas | `docs/instrucciones-g5l-r-r1.md`: ahorro medido por reescritura contra el estimado de Q, BENCH/VBTRACE antes/después, modelo recalibrado |

Con ese número el usuario elige entre S5, el patch por blitter o revisar
D1 (colchón aceptado; 25 Hz solo con la optimización agotada).

Builds seriales, una WinUAE midiendo, R9.

## 2. Después

Según R1: S5 (`build_mid`, sobre todo `bm_left` a la vuelta), el patch de
G5L por blitter, o D1 al usuario. Luego otros enemigos (dos Rex,
Banzai/bobs), HUD y audio. BM1 deja 24856 B de chip en el vivo: las tablas
de CPU en chip (135468 B) todavía necesitan C2/C4 y espacio slow.
**[usuario, 2026-10-09]: el foco es G5L-R**; B2bis/Cpre/B35 aparcadas.

## 3. Pendiente del usuario o la PC

- **Autorizar (o no) G5L-R-R1.**
- U2 capa 2 contra referencia; U3 opcional, A500 real (con A501).
- Worktrees con commits fuera de master, conservados: `agent-ab11…`
  (G2T-B2 parada), `agent-af1f…` (revisión L-OAM), `wt-g5bis-1007`,
  `wt-review-1007`. Borrarlos o integrarlos es decisión del usuario.
- Integrar `g2t-b2bis` a master (sin push) cuando el usuario lo pida.
