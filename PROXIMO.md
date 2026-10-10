# PRÓXIMO — lo que sigue

2026-10-10. **Código en `g2t-b2bis`, sin merge ni push**; worktree:
`C:/Users/JC/Downloads/sma/wt-g2t-b2bis-1008`. Master conserva el código
anterior.

**G5L-R-L2 lote 1 hecho** (directiva del usuario: "todo asm y bare metal,
lo más optimizado posible"): la lógica caliente está en asm
(`docs/informe-g5l-r-l2-1010.md`). Replay normal de YI1, WinUAE
cycle-exact: **VBTRACE 0 fotos omitidas** (S9: 12), BENCH 10 perdidas
(0,16 %, S9: 36). **El objetivo D1 del replay normal se cumple.**

**Estrés sigue rojo:** `stress_back` 341/4126 (8,26 %, racha 4),
`stress_sprites` 92/1914 (4,81 %, racha 3). Ahí domina el scroll/render
(`build_mid` hasta 171 % del frame en la vuelta), no la lógica.

## 1. La próxima sesión, en orden

1. **El Guru 3 latente (P123, informe §4).** Con `e7234ab` +
   `stress_back`, `g5l_render` lee `GV_TAB` pisado (`$31FA0031`).
   Encontrar quién lo escribe (candidato `g5l_wcache` con segmento ≥ 224)
   antes de seguir optimizando: el render es el mismo en la rama.
   Herramientas: `-DADRTRAP` + `tools/adrtrap.py`, `tools/g5l.py game`.
   Para reconstruir el build viejo: `git stash; git checkout e7234ab;
   git apply` del parche de ADRTRAP (`git diff 222fb64 HEAD --
   player/game.s`), compilar, volver a la rama.
2. **Estrés: el render en la vuelta.** Perfil por PC de `build_mid` y
   `scroll_frame` sobre `stress_back` (`g5l.py game --pcprof`, P121) y
   bajar los picos de columnas al volver. Medir con BENCH en los dos
   replays de estrés (comandos en el informe §3). El perfil decide la
   técnica (`docs/investigacion-demoscene-1010.md` §11): si dominan las
   decisiones, speedcode por línea generado por `mkscroll.py` + corte con
   `RTS` parcheado; si domina la copia, escribir menos palabras; si
   dominan las esperas del blitter, copper → blitter o cambiar cómo se
   termina la columna al dar la vuelta. Puerta: lista del copper idéntica
   byte a byte en Musashi en los tres replays.
3. **Seguir la directiva asm** sobre lo caliente que queda
   (`finish_oam` costo fijo, `mario_E2BD`, `spr_tile`, `mc_pxy`,
   cámara, `mspr_draw`), cada cambio con `fuzzcall.py` + lint + regress.

Antes de cada commit: `python tools/lint_port.py && python tools/regress.py
--baseline tools/baseline_pc.json --level --g5l --bm1`.

## 2. Pendiente del usuario

Probar el vivo a mano en esta rama; decidir cuándo integrar a master.
