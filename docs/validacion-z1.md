# Z1 — muerte y carga del nivel

El juego en vivo termina la animación original y vuelve a cargar YI1 cuando
`wm_GameMode=$0B`, quedan vidas y no hay punto medio. El replay conserva su
bucle original. `$15` (game over/time up) y un punto medio activo siguen en
el diagnóstico: no se sustituyen por una reaparición incorrecta.

La SNES sale al overworld después de `$0B`. Este demo recarga directamente
el único nivel; no implementa overworld ni los fundidos (Z5). Durante la carga
no hay ticks de juego y la pantalla queda negra. No se pretende esconder
este tiempo dentro del presupuesto de un frame de juego.

## Estado y fuente

- `player.s:MarioDeathAni/DeathNotGameOver`: animación P8 sin cambios,
  descuento de una vida y elección `$0B/$15`. El asm no descuenta otra vida.
- `game.s:_009E17`: un juego nuevo comienza con `$0DBE=4` (cinco vidas
  mostradas). El estado de replay no incluye esta dirección y antes se
  comenzaba con cero. En vivo también se inicializa `$100=$14`.
- `lv_read.s:TimerTable/LoadLevel`, cabecera YI1 byte 3 `$80`: tiempo 300.
  Sin inicializarlo, la muerte terminaba en TIME UP aunque no hubiera pasado
  tiempo. La cuenta del reloj sigue fuera de Z1.
- `game.s:CODE_0091A6`: GreenStarCoins vuelve a 30 al entrar al nivel.
- `game.s:Clear_1A_13D3/GAMEMODE_LoadOverworld`: se conservan vidas,
  monedas, reserva, puntos, bonus stars y el estado Yoshi que dejó la muerte.
  Se conservan también las tres tablas permanentes de 12 bytes en `$1F2F`,
  `$1F3C` y `$1FEE`; los contadores temporales del nivel y el mapa se cargan
  de nuevo. La lógica que marca/usa esos flags de coleccionables no se amplía
  en esta tarjeta.

## Transacción O5

`live_logic` pide la carga y entrega la última foto de muerte. Las siguientes
COPER no ejecutan lógica ni toman fotos mientras la carga está pendiente.
El bucle espera a que esa foto se vea y a que no haya publicación pendiente.
`dc_restart` deshabilita MASTER de INTENA, espera el blitter y detiene DMA
de copper, planos y sprites. Restaura RAM y mapa, genera la OAM de entrada
sin tick de física, reconstruye PF1 y ambas listas, invalida sus cachés de
paleta y crea las fotos/punteros/colas nuevos. Finalmente descarta las
peticiones COPER/VERTB acumuladas durante la carga y restaura DMA e INTENA.
La próxima COPER ejecuta exactamente un tick nuevo.

El historial y `g_frame` abarcan todo el juego nuevo, incluidos los reinicios:
la carga no borra el mando anterior ni convierte una tecla sostenida en una
pulsación nueva. `diag_read.py` reproduce las cargas de CPU a partir del
historial completo. RETURN en un diagnóstico conserva su función de empezar
un juego nuevo. La ruta `-DNODECOUPLE` también restaura RAM, mapa y ambas
listas fuera de la lógica de la muerte.

## Verificación

`python tools/restart_verify.py` ejecuta el binario en Musashi M68000 en
modo usuario, como el bucle real. Comprueba muerte natural sin teclas en
219, fin en 410, vidas 4→3, estado persistente no trivial, mapa completo,
cámara, fotos y punteros de ambas listas, restauración de INTENA, ausencia
de ticks durante carga y exactamente uno después. Comprueba cinco muertes
sucesivas (3,2,1,0,$FF), game over, punto medio pendiente y mando sostenido.
Comprueba expresamente los campos de Mario de los pares de muerte grabados:
enemigo **188/188**, caída **190/190**, incluyendo `$71/$19`. El verificador
`m68kverify --mode full` omite las animaciones y por sí solo no prueba esto.

`python tools/diag_read.py --sim` reproduce cinco muertes hasta game over en
2050; lectura de ambas páginas a escalas 2 y 2,125 y reproducción: TODO OK.
`python tools/gamecheck.py --spr`: 6313 frames, cero diferencias de estado,
6184/6184 gráficos y caché alternada exactos. `lint_port.py` y
`regress.py --baseline tools/baseline_pc.json --level`: OK, sin cambiar bases.

Capturas finales con `tools/shot.ps1 -Exact`, KS 1.2 y el candado común:

| evidencia | build | lectura |
|---|---|---|
| `work/z1-death.png` | `GDEFS=-DZ1STOP=240 OUT=work/z1-death` | frame 240, `$71=09`, animación de muerte visible |
| `work/z1-return.png` | `GDEFS=-DZ1STOP=411 OUT=work/z1-return` | frame 411, `$71=00`, Mario visible de nuevo en X `$10`, Y `$160`, cámara 0 |
| `work/z1-time.png` | `GDEFS="-DZ1MEASURE -DDIAGPAGE=2" OUT=work/z1-time` | página 2: FRAME de 32 bits = **212946 ticks CIA** |

`Z1MEASURE` es un arnés: TA de CIA-B cuenta ticks y TB cuenta sus underflows.
Mide desde antes de esperar el blitter hasta después de reconstruir listas,
fotos y restaurar DMA; excluye el dibujo posterior del diagnóstico. Vuelca
los ticks en el campo FRAME, que aquí no representa frames de juego.
`diag_read.py --shot work/z1-time.png --bin work/z1-time/game.bin` lo lee
sin truncar a 16 bits: **2.129.460 ciclos**, **300,19 ms**, **15,01 frames PAL**.
El mismo camino final en Musashi cuesta **2.122.584 ciclos sin DMA** (14,96
frames), 0,32 % menos. La carga detiene el DMA de lectores durante casi todo
su intervalo; no extrapolar este factor a los frames de juego.

`restart_verify.py --node`: ruta anterior en modo usuario, RAM/mapa/contadores
y el siguiente tick correctos; **2.126.220 ciclos sin DMA**. No se tomó una
captura separada de NODECOUPLE. Todos los binarios, ADF y PNG viven en
`work/`, ignorado por git. Se generan con `NOCC=1 sh tools/game_build.sh`
después de compilar el C normal; los flags Z1 no forman parte del ADF vivo.

Auditoría del vivo final: `memmap.py work/live/game.lst`, **0 violaciones**,
chip **402.232 B**, slow **242.520 B** (margen slow 281.768 B; incluye copia
de C/mapa de 29.324 B). Stage2 213.188 B; ADF ocupado 444.928 B de 901.120.
`piccheck.py --lst work/live/game.lst`: **16185 instrucciones, cero llamadas
o saltos absolutos**. La A501 sigue siendo necesaria.

## Trampa nueva

El bucle principal corre en modo usuario; las ISR corren en supervisor.
`MOVE ...,SR` en una rutina llamada desde el bucle produce Guru `$80000008`
en KS 1.2. El primer arnés supervisor lo ocultaba; la captura real lo
detectó. El reinicio ahora excluye interrupciones mediante INTENA y el
verificador corre explícitamente en modo usuario.
