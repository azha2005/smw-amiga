# G2T-B2bis — cierre de puertas del worktree existente

Estado 2026-10-08: procedimiento ejecutado, entrega `ec320ab`;
informe `docs/informe-g2t-b2bis-1008.md`. Lint y la red final verdes.
Los pendientes antiguos de abajo ya se comprobaron; el rendimiento real
sigue rojo (98 fotos frente a 27 del control). El trabajo actual está en
PROXIMO.md y `docs/instrucciones-g2t-b2bis-rendimiento.md`.

2026-10-08. Leer `docs/handoff-g2t-b2bis-1008.md` completo y la tarjeta
original `docs/instrucciones-g2t-b2bis.md`. Aplican AGENTS.md,
`docs/instrucciones-olas.md` Parte 1 y `docs/reglas-ola-pc.md`.

1. Situarse en `C:/Users/JC/Downloads/sma/wt-g2t-b2bis-1008`, rama
   `g2t-b2bis`; revisar diff y los dos commits existentes. No copiar el
   trabajo de nuevo ni cambiar a master. Mantener los archivos sin commit.
2. Resolver los 12 errores V3 de lint en dc_capture, probablemente por
   marcadores globales que cortan la rutina para asmlint. No desactivar
   controles. Luego recompilar replay con work/b2b_gamebuild.sh; correr decode, cache,
   front, project y game con los comandos del handoff. Compilar front
   con su wrapper. Game/decode del build final ya verdes; el soporte C sigue sin repetir front/project.
3. Añadir casos sintéticos que materialicen formato 4 y lo recorten a
   través de huecos, más casos verticales, ancho doble sin clave y exceso
   de densidad del pack. Comprobar ASM contra píxeles y C, ABI/canarios.
4. Verificar retorno MA1 en L1 con mspr_n envenenado, buffer 2 y sin clave.
   Probar una foto retenida mientras dc_cop fuerza el buffer libre.
5. Añadir BENCH opt-in para clave/render. Escribir g5env_gate.sh y tests
   significativos, incluidos en regress. No cambiar el modelo ni umbrales.
6. Ejecutar gamecheck, restart del vivo y memmap replay/vivo con/sin G3.
   Sumar G5EV, work, cache, fotos, salidas y stack; ningún desborde ni
   violación chip/slow. No reutilizar cifras de memoria antiguas.
7. Probar WinUAE cycle-exact por el candado, control en misma tanda;
   inspeccionar y comparar imágenes. Separar esa medida de Musashi y
   no declarar D1 cerrada. Documentar los 47 SKIP + 1 SYNC del fixture.
8. Ejecutar g5env_gate entero, lint, regress baseline_pc --level,
   OAM68K entero y hashes por defecto. Corregir rojos antes de commit;
   no actualizar baseline para ocultarlos ni bajar requisitos.
9. Guardar commits por pasos cerrados, informe completo y cierre AGENTS
   §10/ROADMAP §7. Sin merge ni push. B35 y Cpre siguen separados.
