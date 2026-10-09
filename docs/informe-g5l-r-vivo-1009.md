# G5L-R-V — colchón en vivo (2026-10-09)

Rama `g2t-b2bis`, opt-in. Implementación y puertas automáticas verdes;
**pendiente la prueba física del teclado/RETURN en WinUAE y el commit de
defectos**. No se cambia `tools/game_build.sh` ni la base de regresión.

## Cambio

Se admite CUSHION sin REPLAY. La cabecera de sprites se lee con GETBASE
para evitar el límite PC relativo de 32 KB. El diagnóstico modifica
`DC_FLIST`, la lista visible real; RETURN pide una carga nueva en el bucle,
fuera de la IRQ. La muerte conserva su carga anterior. Ambas cargas
reconstruyen A/B/C y fotos/punteros, e invalidan las tres paletas.
No hay cuarta lista ni más reservas DMA.

## Evidencia

`restart_verify.py --dir work/session/live` ejecuta el binario 68000 en
modo usuario. Prueba diagnóstico/retorno con cada lista visible, muerte
natural 219, fin 410, vidas y RAM persistentes, mapa completo, cinco
muertes, game over, punto medio, mando sostenido, ninguna lógica durante
carga y exactamente un tick después. Oráculos de muerte: enemigo
188/188 y caída 190/190 exactos. Carga CPU: 2.822.094 ciclos sin DMA,
19,89 frames; no es un tiempo real de Amiga.

Capturas KS 1.2, A501, PAL cycle-exact, revisadas visualmente:

| archivo ignorado | resultado de `diag_read.py` |
|---|---|
| `work/session/live-240/shot.png` | frame 240, X0010/Y0160, $71=09 (muerte) |
| `work/session/live-411/shot.png` | frame 411, X0010/Y0160, $71=00 (reiniciado) |
| `work/session/live/keyboard.png` | arranque y partida sin entrada; no es prueba de teclado |

`dc_vb` con el stamp lógico 100, 101 y 102 mantiene la imagen anterior
hasta el segundo tick: **40 ms PAL desde el tick de entrada hasta la
publicación**, +20 ms frente a dos listas. La espera de una tecla hasta
su lectura puede sumar hasta un tick; no se midió latencia del host.

`memmap.py work/session/live/game.lst --data work/yi1_s_g5.dat`:
0 violaciones, chip 495.336 B (margen 28.952), slow 437.896 B
(margen 86.392). Esto es memoria reservada por el juego; excluye la
chip que aún retiene Exec. G5L GAME verifica las tres listas/DMA en
6313 fotos. `regress.py --g5l` agrega builds independientes replay/vivo,
memmap, G5L GAME y reinicios sin reemplazar el control de la base PC.

## Puerta pendiente

Computer Use no puede listar aplicaciones: `Computer Use native pipe is
unavailable ... os error 2`. Dos intentos y reinicio del runtime dieron
el mismo fallo. No se hizo pasar entrada sintética por teclado real.
Falta flecha/Z/A en vivo, espacio en diagnóstico y RETURN para volver,
con capturas. Después, y solo después, registrar los nuevos cinco hashes
y cambiar los defectos en un commit propio. Los cinco hashes actuales
siguen byte a byte iguales al inicio; véase el informe T de esta sesión.
