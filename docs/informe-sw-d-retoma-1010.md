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
