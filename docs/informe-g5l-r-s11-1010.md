# G5L-R-S11 — la espiral de la vuelta: fase 1 y cierre

2026-10-10. Rama `g2t-b2bis`. **Solo medida; nada integrado.** Tarjeta:
`instrucciones-g5l-r-s11.md`; contexto: `informe-g5l-r-m1-1010.md`.

## 1. Medida por línea (fase 1)

`g5l.py game --dump-lines` (nuevo) vuelca `linetab` de la lista que se
escribe, antes y después de `build_mid`. Con la secuencia real de la Amiga
(`--render-list work/m1/pos_back.json`), fotos 2572-2594 de la vuelta:

| k | s | líneas cambiadas | vl − s = 0 | −15..−1 | −39..−16 | ≤ −40 | ancho mediano vu − vl |
|---|---:|---:|---:|---:|---:|---:|---:|
| 2572 | 4651 | 78 | 28 | 44 | 4 | 2 | 13 |
| 2576 | 4634 | 86 | 34 | 42 | 8 | 2 | 13 |
| 2580 | 4617 | 89 | 31 | 49 | 3 | 6 | 13 |
| 2584 | 4603 | 90 | 31 | 44 | 7 | 8 | 13 |
| 2589 | 4592 | 93 | 31 | 40 | 6 | 16 | 13 |
| 2594 | 4581 | 90 | 33 | 37 | 5 | 15 | 13 |

Fuente: `work/m1/lines_pc.json`. Una línea reescrita a la izquierda
vale ≈ 13 px; la ventana es la holgura entre el fin de un tramo de color
y el principio del siguiente (`a`, `b` de la MLD), que la base s0 solo
desplaza. Cada lista vuelve 36-48 px más a la izquierda: **casi todas
las ≈ 90 líneas con cargas se reescriben en cada visita** y ninguna base
lo evita. Lo mismo vale para `prevlt` (una foto antes, Δs −13 … −17 con
fotos omitidas): por eso `bm_share` copia 10 líneas en vez de 25.

## 2. Candidatos

| candidato | margen medido | decisión |
|---|---|---|
| A: buscar lo/hi desde `prevlt` | ≈ 1,7 pasos de búsqueda por línea; el tramo lo/hi es sobre todo instrucciones fijas (249 ciclos/línea) | no se implementa |
| B: LNS para \|Δs\| ≤ 48 | `alllines` agrega ≈ 37 líneas por foto que no se reescriben, ≈ 50 ciclos cada una (≈ 2 k por foto) | no se implementa |
| C: recortes del camino de reescritura (codo fuera del bucle, agregación, registros) | **estimado** ≤ 5-8 % de `build_mid` en la espiral; perfil por instrucción en `work/m1/spiral_pc.json` | no se implementa: S10/L2 mostraron que recortes chicos de CPU se pierden en el A/B |

## 3. Conclusión

En la vuelta, el coste por foto satura en ≈ 90 líneas × ≈ 1.700 ciclos
(Musashi), y los planos lo multiplican por ≈ 1,6. Aun sin espiral, esas
fotos cuestan 60-92 k ciclos (≈ 1-1,5 frames con la lógica). **Es probable
que el estrés back no entre en D1 solo con recortes de CPU del scroll.**
Las palancas que quedan cambian el diseño y son del usuario (5 planos,
menos listas, otra frecuencia en el estrés). Se registran como dato,
sin proponerlas como decisión.

La otra palanca sin cambio de diseño es la lógica: en back la
interrupción llega al 74,8 % del frame (informe P123 §4), y ese tiempo
se le quita al render. Sigue L3.
