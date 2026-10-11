# G7-3 — implementación parcial, 2026-10-11

Cierre solicitado por el usuario por límite de uso. **Experimental opt-in;
puerta física roja, no activar por defecto y no declarar G7-3 terminada.**

## Implementación

`player/g7bobs.s`: cola de descriptores de 16 B; minterm CA, tres planos,
dos copias de anillo; IRQ BLIT solo avanza. Restauración por bloques sucios
antes de columnas/diario. Journal original de copper (8 KiB por lista)
y cabecera VBL privados, restaurados antes de las cachés del render.
Fuentes hardware de apoyo privadas por lista en los 12 KiB existentes.
`player/g7prod.c`: OAM de DC_REND válida, clipping/flip/orden, matching de
prefijo, plan temporal y parejas detenidas 2/3 o 6/7; prioridad/paleta
exactas. Error explícito conserva la última foto; no oculta los rechazos.
NOSWS retorna sin producir; clean/restore siguen quitando residuos.

Banco 7.616 B; RLE 2.330 B, cinco sectores ADF, expandido al arrancar.
Se trasladó el CDMA G5L de 34.760 B fuera del binario a 68 sectores ADF:
sin esa duplicación, código y journal caben en slow. No derivados en git.

## Verificaciones y límites

Core Musashi: expansión byte exacta, minterm, IRQ, doble copia,
restauración, cola vacía/capacidad, journal/VBL, FRONT/PEND intactas y
capacidad rechazada. 8 tests de color y 16 de apoyo hardware verdes.
SWS RAM/OAM/PHOTO en las cinco trazas y OAM68K verdes. Regresión completa
verde también sobre el árbol final del cierre (`work/g73-regress-final.log`). Default vivo SHA256
33f2250a1b4231069ab975bfdc4f7d2336cd814a0e4e95d13bd862659c5b638b.

La tabla siguiente corresponde al prototipo ANTERIOR a los últimos
cambios de búsqueda/lectura del PF1; no es cobertura del código final.

| traza | fotos aceptadas | píxeles | rechazos | máximo ciclos CPU sin DMA |
|---|---:|---:|---:|---:|
| yi1 | 6313 | 88550 | 0 | 82181366 |
| pw_bloques | 2076 | 36543 | 0 | 61340058 |
| chuck_kill | 2940 | 48685 | 15 | 158975196 |
| spin_kill | 1007 | 26875 | 0 | 56971308 |
| stress_piranha | 3018 | 33840 | 0 | 61340058 |

Los píxeles de efectos y terreno se cruzaron sobre el PF1 efectivo;
apoyos comparados con la composición y con el hardware original.
El journal máximo observado fue 2.124 B de los 8.192 B por lista.
Reordenar candidatos redujo el peor tramo YI1 571 M → 82 M ciclos.
Esto sigue sin presupuesto de frame viable: D1 roja. No hay caché.

Se encontró P134: la máscara offline anterior usaba GV_NPL/GV_RX,
scratch del camino múltiple, y fallaba con un objeto. Ahora lee DMA y
BPLCON2 efectivos. Los conteos históricos de G7-C deben recalcularse;
sus siete sondas físicas no se vuelven falsas por corregir la máscara.

## Dos puertas pendientes concretas

WinUAE cycle-exact, KS1.2, candidato/control k409: ambos cargaron y
terminaron, g_left=0, g7b_error=0 y cola vacía. Imágenes miradas en
`work/g73/shot409/check.png`: 1.484 píxeles distintos, principalmente
terreno; meta espera siete píxeles de humo. No se considera validada
la cola en movimiento por ese resultado. Las capturas y logs quedan
ignorados en work/g73, sin distribuir material derivado.

Después se añadió espera de blitter y lectura de índices del PF1
materializado: el mapa global puede avanzar respecto de R_TSEQ y no
representa necesariamente lo que se muestra. Es una corrección pendiente
de captura, no una causa física demostrada. No se repitió SW1 ni BENCH
cycle-exact; solo se generaron builds. G7-3 queda parcial.

chuck_kill: ampliar búsqueda 64→3.000 al fallar los apoyos quitó dos
rechazos, pero siguen 13: k2681,2682,2684,2685,2686,2687,2688,
2814,2815,2816,2817,2820,2821. Último cruce acotado 2500..2830:
318 fotos aceptadas, 1.310 píxeles, máximo 283.591.840 ciclos.
La referencia resuelve k2681, 12 filas. La búsqueda C es incompleta;
no hay prueba de imposibilidad de Amiga ni motivo para otra decisión D8.

## Memoria y cierre final

Build final vivo: chip 522.448 B, slow 520.680 B, 0 violaciones.
Build final replay BENCH: chip 510.920 B, slow 524.136 B,
0 violaciones, **solo 152 B de margen slow**. No ampliar código/datos
sin volver a medir; falta margen práctico para futuras opciones.
`work/g73-live-final-mem.log` y `work/g73-bench-final-mem.log`.
El arnés BENCH emite avisos de lectura CIA porque no emula ese timer;
no se tomó como medida de rendimiento. Core se cruza con un binario
normal; las cifras de ciclos de la tabla tampoco incluyen DMA.

Lint final y regresión completa finales: OK; SWS en cinco trazas y
OAM68K: OK. No quedan emuladores ni pruebas G7-3 corriendo.
Cierre PROXIMO/ROADMAP/SUBAGENTES e instrucciones de retoma escritos.

## Continuación

`instrucciones-g7-3-retoma.md`: corregir primero fidelidad física y
rechazos; repetir cinco trazas sobre el árbol final y las puertas de
propiedad/NOSWS, luego SW1 y A/B BENCH. El default permanece intacto.
