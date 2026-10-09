# BM1 — bare metal: sin el SO también al arrancar

2026-10-09. Pedido del usuario: "saltarnos la capa de OS y tocar hardware
bare metal, como en la demoscene".

## Por qué existe

En el juego el SO ya está dormido: `game.s` hace `Forbid` y `LoadView(0)`,
apaga todas las interrupciones y todo el DMA, y pone sus propios vectores
(`$68`, `$6C`). **No hay ciclos de CPU que ganar.** Lo que sí queda del SO:

| qué | dónde | coste |
|---|---|---|
| `AllocMem` (17 llamadas) | `game.s`, `scroll.s`, `boot.s` | la memoria que retiene el SO no se puede usar |
| `trackdisk.device` (`DoIO`, CMD_READ) | `boot.s`, `entry` en `game.s` | su búfer de pista (~12 KB de chip, **estimado**), carga lenta |
| `LoadView`/`WaitTOF`/`Forbid` | `game.s` ~506 | ninguno en el juego |
| bucle principal en **modo usuario** | lo lanza el SO como tarea | P103: hay que excluir interrupciones con `INTENA`, no con `SR` |

La palanca es **la chip RAM**: con G5L-R y el colchón quedan ~40 KB
(`docs/informe-g5l-r-1009.md` §2). Lo que retenga el SO (exec, librerías,
búfer de trackdisk; estimado 20-40 KB) es lugar para el Banzai, el HUD y
el audio. Encaja con D13 (direcciones fijas), que hoy se apoya en
`AllocMem`.

## Reglas que no se negocian

1. Va **después** de G5L-R-T (o antes de G5L-R-V si falta chip). Se toca
   el arranque y la carga, que hoy funcionan: tarjeta y commits propios.
2. El ADF tiene que arrancar en **KS 1.2 y KS 1.3** (D6), con y sin A501
   (sin A501 hoy el binario se queda en chip: no romper ese caso, o
   decidir con el usuario si se deja de soportar).
3. R2: nada que lea el chipset en slow. P8/P29 sobre la A501.
4. Nada derivado de la ROM en git (R9). Sin builds paralelos.
5. Puertas de siempre antes de cada commit: lint, regress `--level`,
   `tools/g5l.py game` OK si se tocó el camino G5L, 5 hashes por defecto
   (cambian a propósito en las fases 3-4: registrarlos).

## Fases (cada una con puerta de medida)

### Fase 1 — medir cuánta chip retiene el SO

1. Agregar `-DMEMPROBE` en `game.s` (solo replay): en `entry`, antes del
   primer `AllocMem` propio, y otra vez después del último, guardar
   `AvailMem(MEMF_CHIP)`, `AvailMem(MEMF_CHIP|MEMF_LARGEST)` y lo mismo
   con `MEMF_FAST`, en un bloque con firma (como `vt_sig` de `-DVBTRACE`).
2. Leerlo de la memoria de WinUAE con el método de `tools/vbtrace.py`
   (buscar la firma, `vt_self` para traducir direcciones).
3. Anotar: chip total 524 288 − libre al entrar − lo de `boot.s` = lo que
   retiene el SO. Recorrer la lista de memoria de exec (`MemList` en
   ExecBase) para separar exec/librerías/trackdisk.

Puerta: un número medido. **Si lo recuperable es < 16 KB, parar y
avisar**: el resto de BM1 no vale su riesgo solo por memoria.

### Fase 2 — bucle en modo supervisor

Pasar a supervisor una vez (`Supervisor()` de exec o un vector de trap
propio) antes de tomar la máquina. Revisar P103: con supervisor se puede
volver a `move.w #$2700,sr` donde hoy se escribe `INTENA`, pero solo
donde mida igual o mejor. Puerta: replay y vivo como antes (capturas,
`regress`, Z1).

### Fase 3 — trackloader propio

Un lector MFM: motor, búsqueda de pista 0 (`CIAB` step/dir), lectura de
una pista con el DMA de disco (`DSKPTH`, `DSKLEN`, `ADKCON`, sincronía
`$4489`), decodificación de los 11 sectores (máscara `$55555555`) y suma
de control por sector. Reemplaza el `DoIO` de `entry` (datos del scroll,
banco) y, en una segunda parte, el de `boot.s`. Puerta: el ADF arranca en
KS 1.2 y 1.3 (WinUAE), los datos leídos son byte a byte los del ADF (suma
contra `tools/mkadf.py`), tiempo de carga medido.

### Fase 4 — mapa de memoria fijo

Con el SO fuera, sin `AllocMem`: direcciones fijas para listas, búferes y
datos (D13), y la slow RAM detectada probando `$C00000` (escritura,
lectura, espejo en `$C80000`). Puerta: `tools/memmap.py` sin violaciones
y el informe de la chip recuperada frente a la fase 1.

## El informe

Chip retenida por el SO (medida y desglose), qué fases se hicieron,
tiempo de carga antes/después, memmap, hashes nuevos y en qué
Kickstart/configuración se probó el arranque.
