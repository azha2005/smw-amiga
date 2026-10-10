# PRÓXIMO — lo que sigue

2026-10-09 (noche). **Código en `g2t-b2bis`, sin merge ni push**; worktree:
`C:/Users/JC/Downloads/sma/wt-g2t-b2bis-1008`. Master conserva el código
anterior; los documentos indican el avance de la rama.

**G5L-R-T2 y G5L-R-Pa hechas**, solo medida (`docs/informe-g5l-r-t2-1009.md`,
`docs/informe-g5l-r-pa-1009.md`). Los 25 saltos de VBTRACE (66 fotos
BENCH) son atraso acumulado por rachas de fotos caras. **Reutilizar el
plan de G5L no sirve**: sin la altura absoluta el plan corrido es igual,
pero casi nunca acierta (0 con N = 4); sin la relativa acierta, pero el
plan es otro en el 92 %. El exceso está repartido entre el render de G5L
y `build_mid` en los dos sentidos. Para ≤ 5 saltos (modelo, ESTIMADO):

- S5 (`build_mid` −50 % del exceso) + camino lento −50 %: 2-6;
- S5 + `g5l_render` −20 %: 1-2;
- `g5l_render` −30 % sin S5: 4-5.

**D1 sigue roja.**

## 1. La próxima sesión — decide el usuario

| tarjeta | toca | instrucciones y entrega |
|---|---|---|
| **G5L-R-Q** (recomendada; **pendiente de autorización**) | solo medida: histograma por PC de `g5l_render` (ventanas de salto y fallos) y de `build_mid` (picos), una reescritura concreta por bucle caliente con su recorte estimado, y el modelo con esos recortes | `docs/instrucciones-g5l-r-q.md`: puerta del histograma = ciclos de `game_frames.json`; informe con qué meta es alcanzable |

Sin Q, cualquier candidato sería elegir un porcentaje sin saber si se
puede. Si Q dice que ninguna meta es alcanzable, D1 vuelve al usuario con
números (colchón aceptado; 25 Hz solo con la optimización agotada).

Builds seriales, una WinUAE midiendo, R9.

## 2. Después

El candidato que Q haga posible (S5 + recortes de asm en G5L), con la
puerta BENCH ≤ 9 fotos (control sin G5L), VBTRACE ≤ 5, `G5L GAME: OK`,
0 píxeles distintos en el frame 1700 y la compuerta D1. Luego otros
enemigos (dos Rex, Banzai/bobs), HUD y audio. BM1 deja 24856 B de chip en
el vivo: las tablas de CPU en chip (135468 B) todavía necesitan C2/C4 y
espacio slow. **[usuario, 2026-10-09]: el foco es G5L-R**; B2bis/Cpre/B35
aparcadas.

## 3. Pendiente del usuario o la PC

- **Autorizar (o no) G5L-R-Q.**
- U2 capa 2 contra referencia; U3 opcional, A500 real (con A501).
- Worktrees con commits fuera de master, conservados: `agent-ab11…`
  (G2T-B2 parada), `agent-af1f…` (revisión L-OAM), `wt-g5bis-1007`,
  `wt-review-1007`. Borrarlos o integrarlos es decisión del usuario.
- Integrar `g2t-b2bis` a master (sin push) cuando el usuario lo pida.
