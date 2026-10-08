/* Solo en la copia instrumental del PC; el C del port queda intacto. */
#include "g5plan.h"
void g5_work_frame(u32 frame);
void g5_work_end(u16 size, const g5_work *w);
void g5_work_a3(void);
void g5_work_uses(const g5_work *w, const u8 *rows, u8 nr, u16 variant);
void g5_work_trans(const g5_work *w, u8 nt, u8 overflow);
void g5_work_probe(void);
void g5_work_schedule(void);
void g5_work_word(void);
