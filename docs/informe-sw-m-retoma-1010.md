# SW-M — recuperación de la paleta animada y de la cola CPU

2026-10-10. Cambios abandonados recuperados de master; sin push.

`R_COIN` captura FrameB con la foto O5. `coin_prepare` actualiza las
fuentes INI/CHG/MLD y `coin_list` repara la lista de atrás, incluidas las
copias de S9. El bit 15, ignorado por COLORxx del OCS, conserva el origen
del color; no se busca por igualdad RGB. `coinpal.event_origins` rechaza
la mezcla de píxeles estáticos y animados en un mismo evento.

La tabla heredada estaba mal: mezclaba cuatro amarillos y cuatro rojos.
Se corrigió leyendo `PALETTE_Flashing` del fuente: `$02DF $035F $27FF
$5FFF $73FF $5FFF $27FF $035F`. La referencia estática conserva `$27FF`,
ahora paso 2. `coinpal_verify.py` compara la tabla contra el fuente antes
de probar el 68000.

## Comprobaciones repetidas

- `coinpal_verify.py`: 6313 fotos y otra pasada con salto de siete (902
  fotos); ocho pasos, tres listas, RAM lógica adelantada deliberadamente;
  252520 y 36080 palabras comprobadas. Media 1586,2 ciclos/foto, máximo
  10596 sin DMA. El máximo no se presenta como ruido medido en WinUAE.
- `cputail_verify.py`: copia completa, punteros relativos, ABI y arena
  slow agotada. Recupera 51608 B chip, 490954 ciclos sólo durante carga.
- `lint_port.py` y `regress.py --baseline tools/baseline_pc.json --level
  --g5l --bm1`: OK. No se cambió la base.

La cola desde D_LNS sólo la lee la CPU. BM1 la copia a slow, ajusta los
campos de cabecera y recupera la reserva chip antes de asignar planos y
listas. `memmap.py` detecta la rutina y contabiliza ambas arenas. En el
build de regresión: chip 467848 B, slow 491808 B, cero violaciones.

## Puertas abiertas

La captura heredada de 126 fotos correspondía a la tabla incorrecta y
no valida el arreglo. Hay una barrida nueva preparada en
`work/resume-sw-m/`; debe compararse contra SNES antes de cerrar SW-M.
También falta A/B BENCH de D1. Los costes Musashi son sin DMA.
