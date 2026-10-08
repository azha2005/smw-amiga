/* B2bis: proyectar las mascaras de la cache al formato de la frontera B2/B3.
 * Solo CPU. Conserva los campos del Rex; no lee RAM viva. */
#ifndef G5ENV_H
#define G5ENV_H
#include "g5plan.h"
#ifdef SPR_G5
#define G5E_VIEW_BYTES G5B_REX
/* Vista warm portable: blk[10]=$B2, blk[11]=HSTART relativo (0..240).
 * MASK contiene offsets de filas (FFFF fuera de pantalla), ENV una copia
 * propia del payload formato 4. No conserva punteros a una cache mutable.
 * Las funciones g5_mario_mask/span aceptan esta vista y el B2 original. */
void g5env_bind(u8 *blk, const u8 *spr, const u8 *data);
#endif
#endif
