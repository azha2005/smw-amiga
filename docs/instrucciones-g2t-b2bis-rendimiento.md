# G2T-B2bis — reducir el coste real antes de integrar

2026-10-08. Leer el informe B2bis y PROXIMO.md. Las puertas locales están
verdes; WinUAE pierde 98 fotos frente a 27 del control. D1 sigue roja.
La autorización del usuario es iterar sin rebajar exactitud ni umbrales.

1. Mantener el worktree g2t-b2bis, sin merge ni push. Conservar modelo,
   contrato, scroll.s, banco y cinco hashes por defecto. Leer P112.
2. Correr g5env_gate.sh y guardar JSON/logs; no partir de datos stale.
   Perfilizar primero los misses/proyecciones iniciales y el caso sin
   clave. La vista warm ya es compacta; medir cambios en ella por separado.
3. Intentar reducir el trabajo frío de convertir máscaras y empaquetar,
   manteniendo decoder ≤12000, lookup hit ≤600, miss ≤12000 y captura
   ≤300 de Musashi. No contar alias como hit ni saltar una foto para ocultar
   coste. No leer RAM viva; la vista debe ser propia, sin punteros mutables.
4. Repetir front, game y los 258 bordes reales; agregar un negativo si se
   cambia el formato. Comprobar ambas bases, ABI y canarios del pack/pila.
   La fila densa de 64 B no puede empezar después de ocupación 1136.
5. Auditar cuatro builds con g5env_memory.py: el vivo G3 solo deja 264 B
   tras reservas. Para cambios grandes, reducir memoria primero; no quitar
   reservas de fotos/salida/pila solo para que pase la suma.
6. Construir BENCH normal y G5BENCHSCREEN y el control C1 a52e2ba en
   work/, con el mismo C. Repetir en la misma tanda WinUAE cycle-exact por
   candado y copias de shot.ps1. Esperar 190 s; visualizar STOPF=1800
   con 95 s en ambos. Usar g5env_shot.py, comparador intacto.
7. Exigir mejora contra el control y documentar fotos perdidas, rachas,
   total/captura/render. El control también incumple D1: no declararla
   cerrada por acercarse a sus 27. Si hace falta scroll/S5/L-OAM, abrir su
   tarjeta con sus instrucciones antes de tocar archivos fuera de B2bis.
8. Red antes de commit: lint, regress baseline_pc --level, OAM68K entero,
   G5ENV y cinco hashes. Mantener B35 fuera del vivo. Cerrar documentación
   según ROADMAP §7; Cpre sigue siendo una prueba independiente offline.
