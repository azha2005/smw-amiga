# PRÓXIMO — lo que sigue

2026-10-10. **Código en `g2t-b2bis`, sin merge ni push**; worktree:
`C:/Users/JC/Downloads/sma/wt-g2t-b2bis-1008`. Master conserva el código
anterior; los documentos indican el avance de la rama.

**G5L-R-R1 y S9 hechas** (autorizadas: "hacé lo que puedas, ojalá llegar
al máximo nivel de optimización", 2026-10-09). R1: reescrituras del render
G5L, −5,6 % (`docs/informe-g5l-r-r1-1009.md`). S9: `build_mid` copia la
línea de la lista anterior cuando vale; S5 (repartir) se probó y se
descartó (`docs/informe-g5l-r-s9-1010.md`, P121). WinUAE cycle-exact:

| | T2 | R1 | S9 |
|---|---:|---:|---:|
| BENCH, fotos perdidas | 66 | 53 | **36** (0,57 %) |
| VBTRACE, omitidas | 25 | 17 | **12** |

**D1 sigue roja** (objetivo ≤ 5 omitidas).

## 1. La próxima sesión

| tarjeta | toca | instrucciones y entrega |
|---|---|---|
| **G5L-R-L** (bajo la autorización de optimizar del 2026-10-09) | el racimo 3305-3364 (6 de los 12 saltos): medir la lógica por PC, camino lento de G5L (`g5l_sweep`/`g5l_plan`/`g5l_mfill`), el primer pico de `bm_left` (4218) | `docs/instrucciones-g5l-r-l.md`: ahorro medido por paso, BENCH/VBTRACE antes/después, lo que falta para ≤ 5 |

Builds seriales, una WinUAE midiendo, R9.

## 2. Después

Si G5L-R-L no deja una palanca concreta para llegar a ≤ 5, D1 vuelve al
usuario con los números (colchón aceptado; 25 Hz solo con la optimización
agotada). Luego otros enemigos (dos Rex, Banzai/bobs), HUD y audio. BM1
deja 24856 B de chip en el vivo: las tablas de CPU en chip (135468 B)
todavía necesitan C2/C4 y espacio slow. **[usuario, 2026-10-09]: el foco
es G5L-R**; B2bis/Cpre/B35 aparcadas.

## 3. Pendiente del usuario o la PC

- Probar el vivo con S9 (`work/s9/vivo`, MD5 `510e1ee3…`) a mano: el
  scroll a la izquierda es lo que cambió.
- U2 capa 2 contra referencia; U3 opcional, A500 real (con A501).
- Worktrees con commits fuera de master, conservados: `agent-ab11…`
  (G2T-B2 parada), `agent-af1f…` (revisión L-OAM), `wt-g5bis-1007`,
  `wt-review-1007`. Borrarlos o integrarlos es decisión del usuario.
- Integrar `g2t-b2bis` a master (sin push) cuando el usuario lo pida.
