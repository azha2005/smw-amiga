# G2T-B2bis — entrega local y límites medidos

2026-10-08. Rama `g2t-b2bis`, worktree `wt-g2t-b2bis-1008`.
Integración B2b3-5: **`ec320ab`** (git log real).
Sin merge ni push. Clave y decoder: `8a4a43d` / `a401723`; la entrega
posterior reúne caché, frontera, integración opt-in y puertas reproducibles.
**Las puertas locales de B2bis están verdes; D1 sigue roja en WinUAE.**
No hay plan B35 activo ni enemigos dibujados todavía.

## Exactitud y ciclos de CPU

`work/b2b/gate_final.log`, `tools/g5env_gate.sh` completo:

| prueba | resultado |
|---|---|
| clave MA1, 3404 frames | 245/155/139 claves por traza, 465 globales; 0 colisiones |
| fuentes MA1 reales | L1 con mspr_n envenenado, buffer libre, 63 ocultos y 3 raros C correctos |
| decoder puro ASM | 3404 exactos; máximo 10906, media YI1 10614; ABI 0 |
| negativo | alterar un píxel cambia la envolvente |
| frontera PC y vbcc | 762496 filas exactas en 3404 frames; ABI/canarios 0 |
| bordes sintéticos | 258 casos: huecos, recorte horizontal/vertical, SPR2 aislado, ancho doble, densidad y límite del pack |
| juego O5 | 6313 renders con RAM/OAM/MA1 vivos envenenados, 2288 fotos Rex exactas; también por callbacks reales |
| foto retenida | COPER avanza por buffer 2, foto/DATA antiguos intactos y render exacto |
| captura nueva | máximo 270 ciclos Musashi, incluyendo exposición de fuentes, preservación y MULU; objetivo 300 |
| O5 CPU sin DMA | máximo render B2bis 46940 (6936), total 140932 (11301); 0 > PAL |
| reinicio vivo | ambas builds, sin/con G3, RAM/mapa/fotos/muerte/vidas correctos |

Foto 5219 → oráculo 10364 comprobada; primer frame 5145 + R_FRAME.
Hay **47 SKIP + 1 SYNC** distintos del fixture PC provisional de B2:
marioverify lo emitía antes de deshacer SKIP, mientras Amiga conserva
los gráficos anteriores; SYNC carga física sin recalcular mgfx. Todas
las fotos RUN coinciden también con el fixture; todas las fotos coinciden
con `g2t_ref` del estado realmente capturado. No se cambió el modelo ni
se declara igualdad SNES de esos 48 fixtures provisionales.

## Caché y representación

N8/16/32 producen la misma tasa con el hash usado: las trazas ocupan ocho
candidatos. Se elige N8, **12452 B**: scratch 2484 + 8 entradas de 1246.
Un hit compara **los 40 B completos**, no solo el hash.

| traza | hit | miss | alias entre misses | sin clave | máximo hit / miss |
|---|---:|---:|---:|---:|---:|
| yi1 | 1878 | 410 | 234 | 63 | 558 / 11904 |
| normal | 477 | 184 | 158 | 0 | 558 / 11904 |
| spin_kill | 279 | 176 | 139 | 0 | 558 / 11904 |

Los alias prueban igualdad de imagen comprobando entradas y punteros
utilizados; cuentan como miss, nunca como hit de 600 ciclos. El negativo
altera un puntero utilizado y un píxel; otro puntero no usado solo puede
dar alias cuando la igualdad está demostrada.

El decoder mono guarda máscaras de 16 bits. La primera proyección crea
un pack de extremos relativos cuando cabe; una caja que cruza un borde
se vuelve a decodificar desde DATA de la foto para conservar los huecos.
No hubo recortes horizontales en las tres trazas; los sintéticos ejercitan
esa ruta (máximo projector recortado 46494, fuera del límite del decoder).
Las imágenes arbitrarias de dos columnas tienen exactitud/ABI comprobadas,
sin garantía de coste de 12000 para ese dibujo excepcional.

La ruta warm copia el payload compacto a una **vista propia** del render:
tag `$B2` en byte 10, x en byte 11, offsets por fila en MASK y payload en
ENV. No deja punteros hacia entradas de caché que puedan reemplazarse.
`g5_mario_mask/span` conservan sus firmas y aceptan B2 o esta vista;
son las únicas funciones de g5plan.c modificadas. El plan conserva su
algoritmo y salida: OAM68K repitió PC y 68000 en las tres trazas.

`tools/g5env_asm.py` genera el ASM. C es control independiente del PC y
fallback de dos columnas en vbcc; el formato 4 en el 68000 siempre pasa
por ASM. Todos los datos de CPU viven en slow; los sprites quedan en chip.

## Memoria y reservas

`tools/g5env_memory.py`, cuatro memmap con `--data work/yi1_s_g5.dat`:

| build | chip | slow actual | slow con reservas | margen final |
|---|---:|---:|---:|---:|
| replay sin G3 | 407088 | 243248 | 413008 | 111280 |
| vivo sin G3 | 418616 | 280000 | 449760 | 74528 |
| replay G3 | 472112 | 317520 | 487280 | 37008 |
| vivo G3 | 483640 | 354264 | 524024 | **264** |

0 violaciones. Cache 12452, vista 1292, tres registros de 50 B y pila IRQ
8192 ya forman parte del binario y no se cuentan dos veces. Reservas:
G5EV 133040, work B35 29952, fotos Rex 3120, salida 2048, pila del render
1536 y margen del allocator 64. B1 tiene cota 48 + 255×3 + 224×5 = 1933 B.
El projector conserva el canario inferior de 1260 B en los arneses;
1536 incluye además los argumentos/retornos y salvados del caller. IRQ
usa su pila separada. Estas reservas no significan que B35 ya se cargue.
**264 B no es margen operativo para añadir código:** revisar memoria antes
de activar el plan, integrar nuevos datos o elegir N16/32.

## WinUAE cycle-exact y visual

KS1.2, PAL OCS, 512K chip + 512K slow, cycle_exact, CPU real, blits
reales; candado compartido y tres copias de shot.ps1. Control asm C1 de
`a52e2ba` construido con el mismo C. `work/b2b/shot_summary.json`:

| build | fotos lógicas | publicadas | perdidas | racha | total medio CIA |
|---|---:|---:|---:|---:|---:|
| control | 6312 | 6285 | 27 (0,43 %) | 1 | 5414 ticks |
| B2bis final | 6312 | 6214 | 98 (1,55 %) | 2 | 6876 ticks |
| B2bis G5BENCHSCREEN | 6312 | 6214 | 98 | 2 | 6876 ticks |

Antes de la vista compacta: 100 perdidas, media 7037 ticks. La mejora
es pequeña; **no cierra D1** (mínimo ≤0,1 %, racha 1). BENCH registra
65 ticks máximos de copia (oráculo 10987), 7393 de render (7256).
Los 270 son ciclos Musashi, no una afirmación de 270 ciclos con DMA.
El BENCH final normal da total máximo 28655 ticks (9363), 69 > PAL.

`G5BENCHSCREEN` reemplaza las partes 0/1 por copia/render para conservar
las 21 filas y los contadores O5. BENCH normal mantiene su formato.
La tanda opt-in añade sellos y su contabilización; no afecta hashes por defecto.

Vista congelada STOPF=1800 (oráculo 6945), espera 95 s:
**0/327680 píxeles distintos** contra control, imagen inspeccionada en
`work/b2b/view_control_ab.png` (control arriba). La primera espera de
65 s fotografiaba el build mayor antes de terminar; se repitieron ambas
capturas. No se ajustó el comparador para hacerlas coincidir.

## Red final y reproducción

`work/b2b/lint_final.log`: `RESULTADO: OK`.
`work/b2b/regress_final.log`: `RESULTADO: OK`, incluye test_g5env.py.
`work/b2b/oam_final.log`: `OAM68K: OK` (4c, tres planes PC/68000 exactos).
`work/b2b/gate_final.log`: `G5ENV: OK`.
Cinco hashes comparados byte a byte con la base anterior:

```
c03b569643c7bf5ac62f55cdd2813951a6895a6d4801d1eef241e96cfa422769
9403f71c76bc2df9a92a3cc24d8db1e9e67c47e5e62a558e441c3994d0538109
2bc486d77af939aedfb183457e33cc41eba172521959bb0192ddbe6f594363bb
71071566e75a0c1a9dd5391d8398fc44f69ace2e1a4dd489e936c5f7c8bbfad4
ec8147ac1989ab7e7714f1db3f3cebbc723730a980aa33158a6a41173e4dc37e
```

Git Bash: export PATH="$TEMP/pyshim:/c/msys64/ucrt64/bin:$PATH",
VBCC=/c/Users/JC/vbcc y PY=python; `sh tools/g5env_gate.sh`.
`python tools/g5env_shot.py` lee la evidencia WinUAE existente.
Wrappers de construcción/captura en work/b2b_shotbuild.sh y b2b_shots.ps1.
Los assets, ADF, fotos y logs quedan ignorados en work/.

P112 recoge los dos fallos encontrados exclusivamente por sintéticos:
a1 destruido al recortar un pack y límite de payload con cabecera.
B35 sigue inviable (la repetición actual da máximo 2423094 ciclos).
Cpre y el rendimiento global siguen pendientes; no se integra la rama
como un resultado que ya cumple 50 Hz.
