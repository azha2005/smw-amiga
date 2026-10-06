# A1 — BRR a PCM firmado para Paula

2026-10-06. Rama `wt/a1`. Alcance: `tools/brr2pcm.py`, sus pruebas de CLI
y este informe. Sin cambios en player, referencias ni documentos globales.

## Resultado y contrato

El conversor reproduce los cuatro filtros BRR, rangos 0–12 y el tratamiento
especial 13–15, nibble alto primero, historia entre bloques y vueltas,
saturación a 16 bits seguida de envoltura a 15 bits. La salida PCM16 duplica
el valor interno; la salida Paula toma su byte alto firmado (`sample >> 8`).
No suma 128, normaliza amplitud ni resta la media de la muestra. Silencio
sale `$00`, el extremo negativo `$80`. Cada salida ocupa un múltiplo de
16 bytes y satisface la alineación de longitud de 2 bytes de Paula; el
loader futuro debe alinear también la dirección del buffer.

El primer bloque `end` termina la conversión después de sus 16 muestras;
los bytes completos posteriores quedan contabilizados como `trailing_bytes`.
Sin `end`, EOF termina la muestra y queda `end=false`. `loop` sólo actúa
junto a `end`. BRR raw no contiene la dirección de loop: se comunica con
`--loop-offset` o `--loop-map` JSON por nombre de fichero. También existe
`--loop-header` para ficheros con prefijo LE de 2 bytes (no es el formato
de los ficheros originales de SMW). Sin dirección conocida, se conserva
`loop=true`, pero su offset PCM queda `null`; `--loops` exige una dirección.
Cada vuelta extra preserva la historia, y los offsets quedan referidos al
BRR sin prefijo. El manifiesto describe bytes, flags, loop y presupuesto.

Se validan bloques truncados, offsets desalineados/fuera de la muestra,
repeticiones sin loop, nombres duplicados y colisiones BRR/PCM/manifiesto.
El presupuesto predeterminado es 65536 bytes; excederlo devuelve código 1
y deja el inventario y las conversiones solicitadas para su revisión.

## Puertas ejecutadas

```bash
export VBCC=$HOME/vbcc PY=python3
python3 tools/brr2pcm.py --selftest
python3 tools/test_brr2pcm.py
python3 tools/brr2pcm.py --selftest \
  --reference-dsp /home/agent/.cache/snesrev-smw/src/snes/dsp.c \
  /workspace/smw-src-master/project/mw_e10/sound/samples \
  --out work/a1-pcm --manifest work/a1-pcm.json
python3 tools/lint_port.py
python3 tools/regress.py --level
```

Autoprueba: **1024 bloques**, todos los filtros/rangos, cuatro historias
(cero, extremos opuestos y ±1), todos los nibbles, saturación/envoltura,
end/loop, continuidad de historia, PCM firmado y errores de entrada.
El primer oráculo usa coeficientes racionales en el dominio PCM16.
La comprobación independiente extrae **sin modificar** la función original
`dsp_decodeBrr` y la compila con `cc` contra su `dsp.h`, en un directorio
temporal. No descarga código ni necesita un compilador para la autoprueba
normal. La referencia es snesrev commit
`eae20c65c58930c8b62c76188d259579ad4130f1`; SHA256 de `src/snes/dsp.c`:
`b70f85b4909fb09859abadbd49b32eb61cc943339be8e6896bef2f92b2d209aa`.

Salida: **0 diferencias PCM16** en los 1024 bloques, un loop sintético y
las **20 muestras reales / 50560 bytes PCM**. La cuantización a 8 bits
reexpandida se comparó a esa referencia: correlación mínima **0,99963021**
(cymbal); todas las muestras superan 0,99. Esto mide cuantización, no R8.
También se compararon los 13 loops reales, con **tres vueltas adicionales**
cada uno: **23552 muestras PCM16, 0 diferencias** frente a la función C.
Los offsets se extrajeron de `sound/samples.S` a `work/a1-loop-map.json`;
se verificó el lote con `--loop-map`, y se generó `work/a1-pcm.json`.
No se versionan BRR, PCM ni esos manifiestos derivados.

Las cuatro pruebas de CLI pasan: bytes firmados y exceso de presupuesto,
equivalencia prefijo/offset con loops, lote con mapa y parada en end,
validación previa a las escrituras y protección de entradas.

Lint: **RESULTADO: OK**. Regresión cloud `tools/baseline.json` con `--level`:
**RESULTADO: OK**, cruce RAM PC/68000 **0 diferencias** (6547 llamadas loop,
6549 spr); `memmap` **390704 B chip, 0 violaciones**. Las métricas mejoradas
y nuevas ya estaban en la base de esta sesión y no proceden de A1.
`baseline_pc.json` tiene tiempos del compilador Windows y no se alteró.
No hay impacto en el coste del frame: la herramienta corre fuera del juego.

## Inventario medido

BRR raw original: **28440 B**. PCM firmado sin remuestreo: **50560 B**,
77,15 % de 65536 B, **14976 B de margen**. Todas las muestras tienen end y
no hay bytes posteriores. El conjunto medido contiene 20 muestras; las
cifras históricas de 92 KB BRR / 164 KB PCM de plan técnico §10.9 no
describen este directorio. Esta medida no demuestra que audio más todas
las otras reservas quepan conjuntamente en la chip RAM actual.

| Muestra | PCM bytes | Inicio loop PCM (bytes) |
|---|---:|---:|
| acoustic_bass | 1008 | 528 |
| acoustic_piano | 8416 | — |
| bass_drum | 1136 | — |
| bongo | 4048 | — |
| cello | 112 | 64 |
| cymbal | 2016 | — |
| distortion_guitar | 2464 | 2304 |
| electric_piano | 112 | 64 |
| flute | 112 | 64 |
| glockenspiel | 464 | 416 |
| orchestra_hit | 4256 | — |
| slap_bass | 1296 | 1184 |
| snare_drum | 3008 | — |
| steel_drum | 5584 | 5536 |
| steel_guitar | 2912 | 2800 |
| thunder | 8016 | — |
| trumpet | 112 | 64 |
| violin | 112 | 64 |
| woodblock | 4800 | 4752 |
| xylophone | 576 | 528 |
| **Total** | **50560** | |

## Límites y trampas para el coordinador

R8 WAV no está disponible. La antigua puerta de correlación contra ese
WAV queda **pendiente**; sí está satisfecha la puerta de PROXIMO A1 contra
el decodificador de referencia. No se probó escucha/WinUAE/Paula real ni
render de una nota completa con interpolación gaussiana, ADSR o eco.
La herramienta convierte muestras, no el DSP completo ni secuencias N-SPC.

**Pnn — BRR satura y después envuelve:** saturar directamente a 15 bits
cambia resultados. Los rangos 13–15 tampoco equivalen a desplazar el
nibble sin límite. El oráculo C y el vector de saturación detectan ambos.

**Pnn — La historia BRR atraviesa el salto de loop:** resetearla es erróneo.
En 12 de los 13 loops de SMW difiere el PCM8 de la primera y segunda
vuelta; cello difiere en 48/48 bytes. Woodblock es el único que coincide.
Repetir por DMA una única vuelta PCM congelada no reproduce esa evolución
del BRR. `--loops` sirve para renderizarla y verificarla; la representación
del loop para A3/A4 requerirá una decisión explícita del coordinador.

**Pnn — Dirección de loop externa:** los BRR del fuente no llevan prefijo;
sus loops están en la tabla de `sound/samples.S`. Inferir el loop del primer
bloque o quitar automáticamente dos bytes destruye datos válidos.

Los hashes del commit de entrega se comunican en el cierre de la tarjeta;
el propio informe pertenece a ese commit.
