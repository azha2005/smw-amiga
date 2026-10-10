# SW-A y SW-P — postes del punto medio y prioridad de la piraña

2026-10-10. Trabajo retomado de un worktree abandonado por límite de uso
(`wt-sw-ap-1010`), integrado con master (SW-M y la cola CPU de BM1 en
slow) y medido. **Las dos quedan opcionales**: funcionan y pasan sus
puertas de imagen, pero cada una tiene un coste que la tarjeta pide
decidir. Con los defaults, el juego es el de master (regresión completa
y lint en verde).

| tarjeta | cómo se activa | qué arregla | qué cuesta |
|---|---|---|---|
| SW-A | `SW_ANIM_POSTS=0` al generar los datos (`mkbg`, `mkd8in`, `mkleveld`, `mkscroll`, también `--g5`) | los postes del punto medio se ven | CPU del copper y 2137 px de derrame (abajo) |
| SW-P | `-DG5L_PRIORITY` en `GDEFS` | la piraña detrás de la tubería | +11 fotos perdidas en D1 (abajo) |

## SW-A — los postes

- `tools/animtiles.py` reproduce `CODE_00B888` (GFX 33 de 3 a 4 bpp en
  `$7E7D00`) y `CODE_05BB39` (`AnimatedTileData`, `DATA_05B93B`,
  `DATA_05B96B/7D/8B`): las 18 ranuras, con el P-switch y el
  desplazamiento del tileset. `mklvl.load_gfx` superpone las ranuras
  `$74`-`$77` (postes) con la fase pedida.
- `snesorc --shots ... --vram` vuelca la VRAM y el estado de la foto sin
  tocar el estado del emulador (`--layers` y `--ram` también, para SW-D y
  SW-S).
- **Puerta del paso 3:** `SW-A VRAM: 12288 bytes DMA exactos; postes
  42/42 frames` (`work/swa/resume_vram.log`).
- **La animación es real:** la VRAM muestra las fases 0, 2 y 3 en fotos
  distintas (las rayas giran). El port congela la fase 0, como pide el
  paso 4 de la tarjeta. Animarlos es otra tarjeta (cuesta blits).
- **Colores (paso 5): no entran gratis.** Los cambios de color de la capa
  1 pasan de 3409 a 3779. Medido con la regresión (Musashi, sin DMA):

  | métrica | sin postes | con postes |
  |---|---:|---:|
  | `game.build_mid.max` | 81 244 | 93 746 |
  | `game.build_mid.media` | 3 513 | 4 387 |
  | `game.total.max` | 114 430 | 124 948 |
  | `scroll.ida.max` | 73 718 | 79 576 |
  | `nivel.encuadres_px_mal` | 3 966 | 6 103 |

  El derrame del asignador se ve en la barrida como 1-4 px sueltos en las
  filas 363-364 del nivel (`$777` donde la SNES tiene blanco o negro),
  en k 3799-5899.
- **Chip:** ya no es el problema. Antes de la cola CPU en slow el vivo con
  postes daba 527 136 B (fuera de 512 KB); integrado con master, 475 440
  B (margen 48 848 B), 0 violaciones.
- Prioridad del poste de adelante (columna `$32`-`$34`, prioridad 1):
  Mario pasa detrás en la SNES y delante en el port. Diferencia residual;
  no entra en esta tarjeta.

## SW-P — prioridad sprite/capa 1

- `g5l_choose` guarda la prioridad de la pose (`CA_PRI`), el plan la
  conserva por objeto (`RX_PRI`) y `g5l_prsingle`/`g5l_prmulti` agregan
  dos transiciones al pool de MOVE: `BPLCON2 = $0022` en la primera fila
  de la franja y `$0024` después de la última (i = 0 es el registro
  `$0104`). Referencia Python: `priority_trans` en `tools/g5l.py`.
- Si no hay plazo para los MOVE, el objeto no se ubica (motivo
  `sin_prioridad`), nunca con la prioridad mal.
- `sprshot_cmp.py` (G9) aplica la máscara de la capa 1 desde el Map16 y
  el GFX originales y cuenta aparte los píxeles tapados.
- **Puertas:** `g5l.py game` OK con `-DG5L_PRIORITY` en yi1,
  stress_piranha, hills2 y chuck (`work/resume_opt_*_game.log`); con el
  default, binario y ADF idénticos a HEAD (`resume_default_identical.log`).
- **D1, A/B BENCH en WinUAE** (cycle-exact, dos tandas iguales: no es
  ruido):

  | | control | `G5L_PRIORITY` |
  |---|---:|---:|
  | fotos perdidas | 113 (1,79 %) | 124 (1,96 %) |
  | total medio | 13 358 ticks | 13 374 ticks |
  | peor interrupción | 41,5 % | 42,0 % |

  La puerta de la tarjeta pedía "dentro del ruido": no la pasa.

## Barrida SW1 (yi1, 126 fotos, SW-A y SW-P activadas)

Contra la barrida original de SW1: 19 fotos mejoran y 8 empeoran (las 8
por 1-5 px, el derrame de SW-A). Fuera de la barra de estado, exactas: 50
→ 52.

- **Piraña:** k 3599, 3649, 4299, 4349, 4799, 4849, 5599 y 5649 pasan
  de 226-244 px a **0**.
- **Postes:** k 4899-5399 bajan (k 5099: 1029 → 459; k 4999: 894 → 67).
  Lo que queda son las rayas (la fase congelada) y la cinta, que en la
  SNES Mario ya rompió: es un cambio de mapa, de SW-B.
- k 2599-2949 (≈ 400 px) no son de esta tarjeta: es el Rex que la regla
  de 2 por foto deja fuera (punto 7 de SW1; ya estaba en la barrida
  original).

## Para activarlas (decisión del usuario)

Las dos mejoran la imagen y cuestan frame. Opciones:

1. activar SW-P sola (la piraña es lo que más se ve; +11 fotos);
2. las dos, aceptando el coste de `build_mid` de los postes;
3. los postes con menos colores: reasignar en `mkscroll` para que el
   derrame no crezca (trabajo nuevo, sin medir).

Logs en `work/` del worktree (regenerables): `swap_int_*.log`,
`resume_bench_*.log`, `resume_opt_*`, `swa/`, `sw1/yi1/sweep.json`.
