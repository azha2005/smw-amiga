# SW-D — causa de los detalles de color al retomar los worktrees

2026-10-10. Se recupera `sweep_cmp.py cmp --px`, dejado sin commit en
master. No se cambia el reparto de colores ni se aproxima otro píxel.

## Evidencia

Las capturas heredadas de SW1 y los volcados por capas están en
`work/sw1/yi1/`. Se repitió el diagnóstico del asignador sobre
`work/fg15.npy`: `mkleveld.quantize` y `dpfsplit.allocate(fila, 48)`.

| coordenada de nivel | SNES BGR555 | color OCS deseado | color actual | causa |
|---|---|---|---|---|
| (947,329), (947,330), (948,332), (948,333) | `$25E0` | `$074` | `$080` | intervalo de un píxel con registro `None`: derrame del asignador |
| (324,377) | `$0200` | `$080` | `$0F0` | intervalo de un píxel con registro `None`: derrame del asignador |

Apagar BG1 en la SNES cambia esos píxeles; apagar BG2 no. El color de
entrada `fg15.npy`, convertido a 12 bits, coincide con la SNES. La
diferencia aparece al asignar los siete registros de PF1 y sus ventanas
de recarga. No es un tile ausente ni un error de la capa 2.

En k1799 el diagnóstico separa cuatro píxeles BG1 y 82 OBJ. En k299
separa un píxel BG1 y 16 OBJ. Las diferencias de k49 (6 píxeles) y k99
(33) pertenecen a OBJ. En k1049 hay 3616 OBJ y un BG1: no debe describirse
esa foto entera como un pequeño defecto del pie. El dibujo exacto contra
la OAM del port ya está medido en G9; identificar la causa particular de
cada diferencia OBJ requiere L-DER y el estado del replay.

## Herramienta recuperada

```
python tools/sweep_cmp.py cmp --dir work/sw1/yi1 --px 1799
python tools/sweep_cmp.py cmp --dir work/sw1/yi1 --px 299
```

Produce `px_<k>.json` con colores, coordenadas y capas. Ahora escribe
`sweep_px_<k>.json` sin sustituir la barrida completa `sweep.json`. La
sesión abandonada ya había sustituido esta última por una foto; los PNG
y `pairs.json` originales se conservan y permiten regenerarla.

SW-D queda investigada para los dos casos BG1, sin arreglo visual.
Cambiar la asignación requiere demostrar que no desplaza errores a otros
píxeles y repetir scrollsim y SW1. Los casos OBJ siguen en L-DER.

## Cierre (2026-10-10, noche): no hay arreglo de datos que convenga

Se probaron las dos palancas que deciden los derrames de PF1, sobre el
nivel con SW-A y SW-B activadas.

1. **Asignador óptimo.** El voraz de `dpfsplit.allocate` derrama, cuando
   no queda registro, el intervalo de menos píxeles en ese momento. Se
   escribió la selección exacta: el subconjunto de intervalos de mayor
   peso que entra en 7 registros, cada uno ocupando `[inicio, fin + GAP)`.
   Es un flujo de coste mínimo sobre la recta (Carlisle-Lloyd). Resultado
   (prueba fuera del repo):

   | | peso derramado | píxeles mal tras elegir el color vivo más cercano |
   |---|---:|---:|
   | voraz | 445 | 380 |
   | óptimo | 439 | 390 |

   El voraz queda a 6 px del óptimo, y en la imagen da mejor por casualidad:
   varios derrames suyos caen sobre un color igual que está vivo. No se
   cambia.

2. **El tiempo de recarga (`mkleveld --gap`).** Toda la cadena, de
   `mkleveld` a `render_d`:

   | gap | derrame fijo | encuadres mal | bloques |
   |---|---:|---:|---:|
   | 48 | 419 px | 6 103 | 251 |
   | 40 | 409 | 11 965 | 246 |
   | 32 | 243 | 31 164 | 250 |
   | 24 | — | — | 258 (> 256 con SW-B) |

   Cada píxel del nivel aparece en ≈ 10 encuadres del barrido (22,2 M
   vistas, 2,2 M píxeles). Con gap 32 se ahorran ≈ 1 760 vistas de
   derrame y se pierden ≈ 25 000 de encuadre. **48 sigue siendo el mejor
   punto.**

**Conclusión:** los píxeles BG1 de SW1 (la esquina de la cornisa, el de
la fila 185 y el derrame de los postes) son el límite de 7 registros de
PF1 con este modelo de copper. Bajarlos exige más registros (otro reparto
entre PF1/PF2 o sprites, decisión D8) o un copper que recargue más rápido.
Los casos OBJ (el pie del Koopa) son deriva de lógica: L-DER. **SW-D
cerrada sin cambio de datos.**
