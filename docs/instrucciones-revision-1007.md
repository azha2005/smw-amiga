# Revisión tras las paradas L-OAM / G5a-bis

2026-10-07. Instrucciones propuestas para la revisión de la sesión siguiente.
No se ejecutaron estas revisiones en el cierre. Las tarjetas originales
conservaron sus umbrales y se detuvieron en sus condiciones expresas.

## 0. Alcance común

Modelo: GPT-6.1 Sol high, worktree propio por revisión. Leer
`docs/reglas-ola-pc.md`, `docs/instrucciones-olas.md` parte 1 y
`docs/informe-coordinacion-1007.md`. Baselines intactas, R1-R9 vigentes.
No empezar G5 B/C, G4/G6 ni optimizar otras funciones para saltar las
puertas rojas. No implementar todavía otra representación de sprites.

La entrega es una propuesta concreta de instrucciones para una nueva
tarjeta, con presupuesto, comprobación y condición de parada. El contrato
que sustituya al actual tiene que quedar decidido antes de implementarlo.

## 1. Revisión L-OAM: margen y siguiente tarjeta

1. Leer `docs/instrucciones-loam.md` §3-§6 y el informe
   `docs/informe-loam-1007.md`. Confirmar en `git log` los commits
   `e8ec165`, `bbdf201`, `cd5001c` y la fusión `cb8ba8f`.
2. Examinar las dos tandas `l4` y `coord4`, con sus controles. Distinguir
   lógica, interrupción completa, render y fotos omitidas; no sumar
   máximos de frames diferentes ni convertir Musashi en tiempos reales.
3. Leer los perfiles del frame 3097 preservados en
   `../wt-loam-1007/work/loam_*_oam_prof.txt`, comparados con el control
   sin OAM. Ambos asm ya fueron medidos; no repetir los dos intentos C
   descartados ni modificar la limpieza completa de OAM.
4. Identificar qué coste de OAM queda y qué parte pertenece al scroll.
   Proponer una sola tarjeta acotada, ficheros exactos, presupuesto de
   ciclos, RAM que debe conservarse y oráculos que la ejercitan.
5. La propuesta conserva YI1 ≤ 40 % y estrés con OAM no peor que el
   control. Si no hay un cambio justificable dentro del alcance, entregar
   esa conclusión con cifras, sin iniciar más intentos.

Puerta de esta revisión: diagnóstico sustentado en logs y una propuesta
revisable. No equivale a cerrar L-OAM ni habilita el render con la lógica
en rojo. La nueva implementación volverá a pasar lint, regress --level,
OAM68K, abcheck y WinUAE con controles como la tarjeta original.

## 2. Revisión G2T: viabilidad temporal del contrato

1. Leer `docs/instrucciones-g5a-bis.md` A3-A7, `docs/diseno-9.2.md` §2,
   `docs/medida-g0.md`, P108 y `docs/informe-g5bis-1007.md`.
2. Examinar `wt/g5bis-1007` (`8fe712d`), sus herramientas y tests. La
   ejecución original y la repetición del coordinador produjeron el
   mismo resumen; la rama conserva los planes y las listas de frames.
3. Reproducir como testigo el frame 5811: índice 1 negro en y168 y
   blanco en y169, ventana vacía `[169,168]`. Separar falta de variante,
   ventana vacía y capacidad. Una capacidad mayor no arregla ese testigo.
4. Evaluar por separado propuestas de selección con plazos viables,
   remapeos temporalmente estables y recargas con ventanas horizontales.
   Etiquetarlas como alternativas nuevas, sin alterar silenciosamente
   la regla vigente de primera variante compatible del directorio.
5. Para ventanas horizontales, especificar intervalos reales de píxeles
   Mario/Rex, DMA de control, MOVE/WAIT y cargas de `build_mid`. No dar
   por válido un slot sin el modelo de h y su medida cycle-exact.
6. Presupuestar banco ≤ 65536 B chip, tablas ≤ 98304 B slow, trabajo
   ≤ 32768 B y fotos acordadas. Los flujos son inmutables; cambiar el
   contrato o ampliar el banco requiere una auditoría explícita.
7. Entregar una especificación candidata con tests para el testigo,
   las reservas de Mario y la temporización. Si no se justifica ninguna
   alternativa, informar el bloqueo y detener la revisión.

Puerta de esta revisión: propuesta de contrato temporal con evidencia y
límites explícitos. Antes de retomar B/C, la nueva fase A deberá producir
0 sin_variante, 0 sin_plazo y 0 errores_color en las tres trazas completas,
con fidelidad y prioridad informadas; el coordinador repetirá la puerta
y revisará las imágenes. Una propuesta no es una implementación medida.

## 3. Entrega y cierre

Un informe por revisión, enlazado en `docs/README.md`, con fuentes de
cada cifra, límites y lo no ejecutado. No hacer push. Cierre según
`ROADMAP.md` §7: archivar el PROXIMO sustituido, reescribirlo, actualizar
estados y pasar lint/regress antes de cada commit. Las implementaciones
posteriores tendrán sus propias instrucciones, sin rebajar puertas.
