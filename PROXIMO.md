# PRÓXIMO — lo que sigue

2026-10-09. Rama `master` (integrada desde `g2t-b2bis` por fast-forward,
**sin push**). Worktree de trabajo: `C:/Users/JC/Downloads/sma/wt-g2t-b2bis-1008`.

**Los enemigos se ven.** G5L-R dibuja al Rex por los sprites 4-7 (opt-in
`-DG5L`); con el colchón de tercera lista (`-DCUSHION`, solo replay) el
replay de YI1 pierde **67 fotos** en WinUAE cycle-exact (1,06 %, racha 1;
control sin enemigos 27). El usuario aceptó el colchón (+20 ms) el
2026-10-09 y pidió revisar los tirones del Rex: son pares repetir/saltear
(P115), no errores del render. Informe: `docs/informe-g5l-r-1009.md`.

## 1. La próxima sesión

| tarjeta | toca | instrucciones y entrega |
|---|---|---|
| **G5L-R-T tirones** | bajar las fotos perdidas por el Rex (67 → hacia 27): patch compartido, camino rápido fallido, sweep con Mario en movimiento | `docs/instrucciones-g5l-r-tirones.md`: G5L GAME OK, WinUAE, vbtrace, parada si dos candidatos no bajan de ~55 |
| **G5L-R-V vivo** | el colchón fuera del replay (reinicio, diagnóstico, carga) y `-DG5L -DCUSHION` por defecto al final | `docs/instrucciones-g5l-r-vivo.md`: ADF jugable, Z1, memmap, latencia medida, hashes nuevos en commit propio |

Recomendado: primero T (lo que pidió el usuario), después V. No compilar
en paralelo; una sola WinUAE midiendo. R9: derivados solo en work/.

## 2. Después

Los otros enemigos de YI1 con el mismo mecanismo (Banzai Bill por bob en
PF1, piraña, Chuck), cobertura de dos Rex a la vez, D1 global (el control
tampoco la cumple: build_mid/S5), HUD, audio. B2bis/Cpre/B35 quedan como
estaban (`docs/informe-g2t-b2bis-rendimiento-1008.md`,
`docs/informe-g2t-cpre-1008.md`): G5L-R los reemplaza como ruta de dibujo;
no se retoman salvo decisión del usuario. Alcance en ROADMAP.md.

## 3. Pendiente del usuario o la PC

Decisiones tomadas por el agente con libertad creativa, para revisar:
4 mapas limpios (`CLEAN_PERMS`), quitar el banco G3 del juego con G5L
(65 KB de chip), caché del plan de 4 entradas, y dejar B2bis/Cpre/B35
aparcadas en favor de G5L-R. Consulta Cpre de presupuesto (4000) sigue
sin respuesta y queda sin efecto mientras Cpre esté aparcada.
Worktrees viejos: todos integrados o equivalentes en master salvo
`tools/g2t_probe.py` (`wt/g5bis-1007`, sonda de un enfoque superado);
borrarlos es decisión del usuario.
U1: jugar ADF vivo con teclado/KS1.2/A501. U2: capa 2 contra referencia.
U3 opcional: A500 real.
