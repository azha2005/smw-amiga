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

## 1. La próxima sesión — decide el usuario

G5L-R-L paso 1 (`docs/informe-g5l-r-l1-1010.md`): la lógica también es
**plana** (la función más cara 6,5 %, casi todo asm ya escrito); el racimo
3305-3364 sube por tener más sprites vivos. Según el modelo de cola, ≤ 5
omitidas pide **−20 % de toda la lógica** o **una cuarta lista**.

| opción | qué | costo |
|---|---|---|
| **A. Lógica a asm, por partes** (recomendada si se sigue a 50 Hz sin más latencia) | `_level_frame`, `mcoll.c`, `_banzai_gfx`, `_sprites_all` y el resto del C de sprites, cada uno con el cruce PC = 68000 (V1); `docs/instrucciones-g5l-r-l2.md` | varias sesiones; −6-9 k por foto ESTIMADO pasando casi todo el C |
| B. Cuarta lista del copper | otra foto de holgura: modelo 1-8 saltos | **+20 ms de latencia** (decisión del usuario); 57 692 B de chip (`CL_SIZE`) que hoy no hay (24 856 B libres en el vivo): antes C2/C4 |
| C. G5L (camino lento) y el primer pico de `bm_left` | `instrucciones-g5l-r-l.md` pasos 2-3 | 1-3 saltos según el modelo |

Builds seriales, una WinUAE midiendo, R9.

## 2. Después

Si G5L-R-L no deja una palanca concreta para llegar a ≤ 5, D1 vuelve al
usuario con los números (colchón aceptado; 25 Hz solo con la optimización
agotada). Luego otros enemigos (dos Rex, Banzai/bobs), HUD y audio. BM1
deja 24856 B de chip en el vivo: las tablas de CPU en chip (135468 B)
todavía necesitan C2/C4 y espacio slow. **[usuario, 2026-10-09]: el foco
es G5L-R**; B2bis/Cpre/B35 aparcadas.

## 3. Pendiente del usuario o la PC

- **Elegir A, B o C** (o D1: dejarlo así, 12 omitidas en el replay).
- Probar el vivo con S9 (`work/s9/vivo`, MD5 `510e1ee3…`) a mano: el
  scroll a la izquierda es lo que cambió.
- U2 capa 2 contra referencia; U3 opcional, A500 real (con A501).
- Worktrees con commits fuera de master, conservados: `agent-ab11…`
  (G2T-B2 parada), `agent-af1f…` (revisión L-OAM), `wt-g5bis-1007`,
  `wt-review-1007`. Borrarlos o integrarlos es decisión del usuario.
- Integrar `g2t-b2bis` a master (sin push) cuando el usuario lo pida.
