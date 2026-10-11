# G7-1 — cerrar doble PF1 antes de los efectos

2026-10-10. Leer `informe-g7-1010.md`, `instrucciones-g7.md` y P132.
G7-0 está hecha. G7_DOUBLE es opt-in; los efectos aún no se dibujan.
La tercera iteración prepara el copper antes de esperar al anillo y
pasa SW1 completo; BENCH final 269 frente a 217 fotos omitidas, racha 2.
La espera ya está incluida en la medición. Los pasos de aislamiento documentan la
investigación; no volver al orden inicial. Continuación: G7-2.

## Pasos

1. Compilar control y candidato con `tools/bm_build.sh`, mismas opciones
   G5L/CUSHION/SPR_OAM y reservas; añadir G7_DOUBLE solo al candidato.
   `tools/memmap.py` debe dar 0 violaciones (chip 522.448 B).
2. Correr `tools/g7_double_verify.py` con bin/listado del candidato.
   Conservar la foto DC_REND y las dos propiedades: jamás escribir PF1
   visible ni pendiente. El copper se prepara antes de la espera. La espera con IRQ habilitada debe terminar
   cuando VERTB libera la lista; no borrar esa espera sin reemplazarla
   por un protocolo probado. Cada PF1 conserva cursor y diario propios.
3. Aislar k4599. Comparar SW1 completo, 126 fotos HOLDEVERY=50, contra
   el control: `work/g7-sweep-multi/result.json` reproduce 8 píxeles
   físicos distintos (dos lógicos, negro frente a `$777`). Revisar
   build_mid/bm_left, caché S9 y recargas al codo de 256 px (P110/P111).
   Una captura STOPF aislada puede tener otro historial de listas:
   repetir la barrida completa para aceptar un arreglo. No aflojar la
   comparación ni enmascarar esos píxeles.
4. Reducir el coste. El primer prototipo llamaba draw_window al saltar
   varias columnas; g7_columns ahora avanza por columnas intermedias.
   El pico baja 28.492 → 5.906 ticks, pero siguen 741 fotos omitidas
   frente a 217. Medir si preparar el copper antes de esperar el PF1
   recupera trabajo del colchón: separar preparación y escritura solo
   con pruebas de propiedad y estabilidad de la foto. Instrumentar la
   espera, que hoy queda fuera del total BENCH. No decidir por medias.
5. Validar vuelta de cámara, diario de bloques en ambos anillos,
   arranque/reinicio y VBL repetido. A/B BENCH cycle-exact, misma tanda:
   fotos omitidas, racha y ventana250. SW1: cero diferencias en 126 pares,
   sin capturas ausentes. Mantener opción experimental hasta cerrar
   estas puertas y justificar el coste con cifras.
6. Después continuar `instrucciones-g7-2.md` (fuentes/color/cola).

## Comandos y cierre

En Git Bash, con el entorno de `instrucciones-olas.md`:

```sh
python tools/lint_port.py
python tools/regress.py --baseline tools/baseline_pc.json --level --g5l --bm1
sh tools/sws_gate.sh
sh tools/oam68k_gate.sh
```

WinUAE por `../winuae_lock.ps1`, script shot privado y `-Exact`; no tocar
la sesión del usuario. Evidencias anteriores en `work/g7-sweep-multi/`
y `work/g7-bench-multi/`. Si falta algún temporal, regenerarlo desde
las herramientas versionadas, sin tomar un archivo viejo por evidencia.
Registrar intentos fallidos y límite de cada prueba. Cierre ROADMAP §7.
