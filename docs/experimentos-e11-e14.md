# Ronda experimental E11–E14 — 2026-10-06

Análisis offline sobre el blob SMWD y los oráculos existentes. No cambia
el juego, no mide tiempos de WinUAE ni redefine la compuerta D1.
Base y cierre: `lint_port.py` y regresión PC completa con `--level`.

## E11a: franjas de PF2

Herramientas: `experimental_planes.py` (decodificador compartido),
`e11_planes.py` (recuento) y `e11_verify.py` (cruce independiente y PNG).
Entrada: `levels/yi1.json`, `work/yi1_d.dat`, oráculos `yi1`,
`stress_back`, `stress_vert` y `chuck`, todos en modo `$14`, nivel `$29`.
SHA256 del SMWD:
`a54c24ebcd8607e15a280e69ae59e968350c06f1a9350c37b16449da0a551970`.

Se cuenta el **índice máximo codificado**, no el número de colores. Un
índice ≤3 permite eliminar el tercer plano de PF2 conservando sus píxeles.
La ventana circular usa la cámara de capa 2. El modo `current` reproduce
el render actual (Y fija y X de PF2 = X de PF1 / 2); `oracle` usa ambas
cámaras grabadas. El origen vertical del fondo corresponde a
`--rest-l2y 192` en este blob: no es una implementación de S8.

Hay 4.041 coordenadas de cámara distintas en total; 8.538 entradas
cámara/traza, 15.755 frames y 3.529.120 líneas de pantalla.

| recuento ponderado por frames | render actual | cámaras del oráculo |
|---|---:|---:|
| líneas con máximo PF2 ≤3 | 149.872 | 151.623 |
| de ellas, PF2 vacío | 136.529 | 138.119 |
| cargas PF1 visibles analizadas | 1.116.758 | 1.116.586 |
| cargas en líneas aptas | **0** | **0** |
| cargas tardías del modelo, antes → después | 10.252 → 10.252 | 10.252 → 10.252 |

En `stress_back`, X=2832, Y=192: cero líneas aptas. En X=4580, Y=181:
34 líneas aptas actuales y 40 con las cámaras del oráculo, pero cero
cargas beneficiadas; 336 cargas PF1, 11 tardías → 11 en el modelo EDF.
El máximo de cargas tardías por cámara de la vuelta queda en 23 →23,
en X=4607. Este máximo del modelo **no es el pico de ciclos de CPU**.

**Resultado:** E11b se descarta para reducir los picos de `build_mid` con
esta representación: las franjas aptas no intersectan sus cargas PF1.
Posibles ganancias generales de DMA para otros trabajos quedan sin medir.
La fase WAIT de cinco planos no está calibrada; el descarte no depende
de esa fase, porque el recuento exacto de cargas beneficiadas es cero.
El modelo tampoco incluye el estado incremental de `bm_left`, las
recargas `BPLCON0`/`BPL6PT`, sprites ni fotos omitidas.

Verificación: casos sintéticos 0/3/4, wrap X/Y, WAIT y P51; todos los
índices, eventos y paletas cruzados con `render_d`; 1.912.512 máximos por
cámara/traza comprobados por modo. PNG original/reducido/diferencia:
cero píxeles distintos.

```text
python tools/e11_planes.py --selftest --mode current --out work/e11a_current
python tools/e11_planes.py --mode oracle --out work/e11a_oracle
python tools/e11_verify.py --report work/e11a_current.json --out work/e11a_current.png
python tools/e11_verify.py --report work/e11a_oracle.json --out work/e11a_oracle.png
```

JSON: máximos por cada línea de cada cámara y totales; CSV: una fila por
cámara/traza. Todo queda en `work/`, sin derivados versionados.

## E12: índices de PF1 por Y

`experimental_pf1.py` examina el dominio conservador completo, no solo
grabaciones: X=0..4864, Y=0..208, pantalla 256×224. Son 1.016.785 cámaras;
el barrido equivalente verifica 2.101.680 ventanas de fila del nivel.
Reconstruye el color vigente de cada registro desde el último evento,
incluidos los píxeles derramados fuera de `x_fin`.

**Resultado:** cero de los siete índices son constantes por Y; cero de
los siete evitan conflictos en todas las ventanas posibles. Ahorro:
**0 MOVE, 0 palabras, 0 cargas tardías**. Se descarta E12 sobre la
asignación actual. Reasignar el bitmap sigue siendo un experimento distinto
(E09/S7), que este resultado no descarta.

Cruce de 2.211.840 píxeles: cero diferencias. El JSON deja un testigo de
dos colores coexistentes por cada índice; el coordinador verificó los
siete contra `render_d`. La autoprueba también tiene un caso positivo de
color que cambia solo por Y, además de conflictos y derrames.
PNG apilado de PF1 original/candidato: cámara (4564,133), sin cambios.

```text
python tools/experimental_pf1.py --selftest --png work/experimental_pf1.png
```

## E13: prioridad por franja

No se abre: falta un caso de YI1 que lo requiera. El recurso `BPLCON2`
queda anotado en `docs/plan-tecnico.md` §9.2.

## E14a: Banzai en ocho sprites

`experimental_banzai.py` atribuye la grilla por las tablas de
`sprite_2-2.s` (`DATA_02D5A4`, `DATA_02D5B4`, `BanzaiBillTiles`,
`DATA_02D5D4`) y el origen de la ranura activa. Compara las coordenadas
bajas con wrap; para la ocupación usa las posiciones OAM reales, con
clipping 256×224. El dibujo precede al movimiento: el origen permite
±2 px frente al snapshot de la ranura. Una ficha aislada sin el chequeo
de posición/atributos no determina dueño.

El denominador visible exige al menos una ficha con píxeles en pantalla.
Las 64 líneas completas exigen 64 filas OAM visibles y contiguas; no basta
con una caja nominal 64×64. Una ranura activa puede no escribir OAM.

| recuento | `oracle_stress_sprites` | `oracle_banzai` |
|---|---:|---:|
| frames de la grabación | 1.915 | 1.081 |
| frames con Banzai visible | 234 | 347 |
| de ellos, con 64 filas visibles completas | 202 | 331 |
| **64 filas libres de cualquier otra OAM** | **0 / 202** | **16 / 331 (4,83 %)** |
| porción visible libre, incluidos recortes verticales | 16 / 234 | 32 / 347 |
| ranura activa sin OAM dibujada | 4 | 4 |
| atribución ambigua / compatibles visibles sin dueño | 0 / 0 | 0 / 0 |

Los únicos 16 frames con las 64 líneas libres son 2449..2464 de
`oracle_banzai`. El coordinador repitió el recuento por firmas de ficha y
atributo, sin el asignador geométrico: todas las entradas atribuidas y
los tres contadores (visible, 64 filas, libres) coinciden en ambos oráculos.
Mario y toda otra OAM visible ocupan canales aunque estén lejos en X.

**Resultado:** se descarta E14 como vía para mejorar el caso de estrés:
no tiene un solo frame completo disponible. Los 16 frames aislados de
la otra grabación quedan como dato; no justifican ahora implementar
el cambio bob/sprite. El peor caso sigue siendo el bob E04/G7, y nada
de este recuento demuestra DMA, paleta, prioridad ni fotos omitidas.

Autopruebas: solapamiento con Mario, OAM fuera de pantalla, fichas
repetidas, recortes de una columna, wrap de coordenadas y dos Banzai.
JSON: totales, frames e intervalos; CSV: evidencia por frame.

```text
python tools/experimental_banzai.py --selftest
```

## Integración y cierre

E11a: `a658b95`; E12: `28b94c8`; E14a: `3fa4241`. El cierre documental
queda identificado en el historial git de esta sesión. Ningún fichero de
`player/`, baseline o asset derivado se modificó. Los números del frame
de `ROADMAP.md` §2 conservan su fuente anterior.
