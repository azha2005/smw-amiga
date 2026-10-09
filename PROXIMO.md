# PRÓXIMO — lo que sigue

2026-10-09 (noche). **Código en `g2t-b2bis`, sin merge ni push**; worktree:
`C:/Users/JC/Downloads/sma/wt-g2t-b2bis-1008`. Master conserva el código
anterior; los documentos indican el avance de la rama.

**G5L-R-V y BM1 cerradas** (`docs/informe-cierre-v-bm1-1009.md`). Teclado
real verificado en WinUAE (`shot.ps1 -Keys`, P117) en KS 1.2 y 1.3, y el
usuario jugó el vivo a mano. **Defectos nuevos** (`53e6453`, commit propio):
G5L+CUSHION+SPR_OAM; el vivo arranca con el boot BM1 (sin A501 no carga,
decisión del usuario); `PROFILE=legacy` es el control y da los cinco MD5
del informe T. BM1: KS 1.3 con datos y píxeles exactos, Z1, rojo sin A501;
carga 31,96 s contra 33,02 s de trackdisk (−3 %, `-DLOADTIME`). lint y
regress `--level --g5l --bm1` verdes. BENCH del defecto: 66 fotos, racha 1.
**D1 sigue roja.** 9 worktrees redundantes borrados.

ADF vivo por defecto: `GDEFS=" " OUT=work/live sh tools/game_build.sh`
→ `work/live/game.adf` (BM1, exige A501).

## 1. La próxima sesión

| tarjeta | toca | instrucciones y entrega |
|---|---|---|
| **G5L-R-T2** | solo medida: atribuir los 25 saltos de VBTRACE (y las 66 fotos BENCH) a las partes de G5L y a `build_mid` por frame; propuesta de candidato con coste estimado, **sin implementarla** | `docs/instrucciones-g5l-r-t2.md`: 66/25 reproducidos, CSV por frame que cuadra con G5L GAME, tabla de los 25 saltos, patrón ≥ 20/25 o su ausencia |

Builds seriales, una WinUAE midiendo, R9. Un candidato nuevo para los
tirones necesita autorización del usuario después del informe T2.

## 2. Después

Con el informe T2: el candidato que el usuario autorice y la compuerta D1.
Luego otros enemigos (dos Rex, Banzai/bobs), HUD y audio. BM1 deja 24856 B
de chip en el vivo: las tablas de CPU en chip (135468 B) todavía necesitan
C2/C4 y espacio slow. **[usuario, 2026-10-09]: el foco es G5L-R**;
B2bis/Cpre/B35 aparcadas.

## 3. Pendiente del usuario o la PC

- U2 capa 2 contra referencia; U3 opcional, A500 real (con A501).
- Worktrees con commits fuera de master, conservados: `agent-ab11…`
  (G2T-B2 parada), `agent-af1f…` (revisión L-OAM), `wt-g5bis-1007`,
  `wt-review-1007`. Borrarlos o integrarlos es decisión del usuario.
- Integrar `g2t-b2bis` a master (sin push) cuando el usuario lo pida.
