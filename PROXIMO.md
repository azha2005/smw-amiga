# PRÓXIMO — lo que sigue

2026-10-09 (noche). **Código en `g2t-b2bis`, sin merge ni push**; worktree:
`C:/Users/JC/Downloads/sma/wt-g2t-b2bis-1008`. Master conserva el código
anterior; los documentos indican el avance de la rama.

**G5L-R-T2 hecha** (`docs/informe-g5l-r-t2-1009.md`), solo medida. Con el
defecto nuevo: BENCH 66 fotos, racha 1; VBTRACE 25 omitidas, los frames
del informe T. Los saltos son **atraso acumulado** por rachas de 3-6 fotos
caras (modelo de cola: 21 de 25). Dos fuentes independientes:

- **camino lento de G5L**: 145 fotos con sweep/plan, `g5l_render` 66 k
  ciclos contra 9 k. El Rex cambia de forma mientras se solapa con Mario y
  la altura relativa cambia; agrandar la caché no sirve (26/145 sin límite);
- **picos de `build_mid`** (S5).

Estimado: el camino lento gratis deja 8-12 saltos, S5 al 50 % 13-18, las
dos juntas 0-4. **D1 sigue roja.**

## 1. La próxima sesión — decide el usuario

La parada de T sigue: **un candidato nuevo necesita autorización.**
Recomendación: empezar por la fase de medida de P-a, que no toca el juego.

| tarjeta | toca | instrucciones y entrega |
|---|---|---|
| **G5L-R-Pa** (recomendada; **pendiente de autorización**) | solo medida, offline: ¿el plan de G5L de un fallo es el de un fallo anterior corrido en Δr0? Si sí en ≥ 80 % de los aciertos, la caché con clave sin la altura vale | `docs/instrucciones-g5l-r-pa.md`: planes por foto, comparación con corrimiento, puerta ≥ 80 %, informe con contrafáctico |

Las otras opciones del informe T2 §5, para que el usuario elija:

- **P-b, S5 en `build_mid`** (cola por plazo, `docs/plan-tecnico.md`
  §9.2): necesaria igual, pero sola deja 13-18 saltos (estimado).
- **Recorte uniforme del 20-30 % de `g5l_render`** más S5: sin diseño
  todavía.

Builds seriales, una WinUAE midiendo, R9.

## 2. Después

Con P-a: la implementación (clave reducida o sweep/plan en asm) y S5, con
la puerta BENCH ≤ 9 fotos (control sin G5L), VBTRACE ≤ 5, `G5L GAME: OK`,
0 píxeles distintos en el frame 1700 y la compuerta D1. Luego otros
enemigos (dos Rex, Banzai/bobs), HUD y audio. BM1 deja 24856 B de chip en
el vivo: las tablas de CPU en chip (135468 B) todavía necesitan C2/C4 y
espacio slow. **[usuario, 2026-10-09]: el foco es G5L-R**; B2bis/Cpre/B35
aparcadas.

## 3. Pendiente del usuario o la PC

- **Autorizar (o no) G5L-R-Pa**, o elegir otra opción de §1.
- U2 capa 2 contra referencia; U3 opcional, A500 real (con A501).
- Worktrees con commits fuera de master, conservados: `agent-ab11…`
  (G2T-B2 parada), `agent-af1f…` (revisión L-OAM), `wt-g5bis-1007`,
  `wt-review-1007`. Borrarlos o integrarlos es decisión del usuario.
- Integrar `g2t-b2bis` a master (sin push) cuando el usuario lo pida.
