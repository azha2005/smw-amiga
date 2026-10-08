/* Observadores del PC: contar trabajo sin alterar g5_plan ni sus bytes.
   Los datos derivados solo se escriben en work/, por el driver Python. */
#define main g5_control_main
#include "g5plan_test.c"
#undef main
#include "g5plan_work.h"

static FILE *cases, *stats;
static u32 frame_id;
static unsigned long a3, attempts, uses, transitions, probes, schedules, words;
static u16 variant_id, input_len;
static u8 input[60 + G5_USEDROWS * 15 * 6];
static u8 started;
static u8 active;
static u16 plan_bytes, segments;

static void write_word(FILE *f, u16 v) { fputc(v >> 8, f); fputc(v & 255, f); }
static void write_long(FILE *f, u32 v) { write_word(f, (u16)(v >> 16)); write_word(f, (u16)v); }
static void appendw(u16 v) { input[input_len++] = v >> 8; input[input_len++] = v; }
static void flush_stats(void)
{
    if (started)
        fprintf(stats, "%lu,%lu,%lu,%lu,%lu,%lu,%lu,%lu,%u,%u\n",
                (unsigned long)frame_id, a3, attempts, uses, transitions,
                probes, schedules, words, segments, plan_bytes);
}
void g5_work_frame(u32 frame)
{
    flush_stats();
    started = active = 1; frame_id = frame;
    a3 = attempts = uses = transitions = probes = schedules = words = 0;
}
void g5_work_end(u16 size, const g5_work *w)
{
    plan_bytes = size; segments = w->nsegs; active = 0;
}
void g5_work_a3(void) { a3++; }
void g5_work_probe(void) { probes++; }
void g5_work_schedule(void) { schedules++; }
void g5_work_word(void) { if (active) words++; }
void g5_work_uses(const g5_work *w, const u8 *rows, u8 nr, u16 variant)
{
    u16 i, e, count;
    attempts++; input_len = 0; variant_id = variant;
    for (i = 1; i < 16; i++) {
        count = 0;
        for (e = 0; e < nr; e++)
            if (w->umask[rows[e]] & (u16)(1 << i)) count++;
        appendw(count); appendw(w->colors[i]);
        uses += count;
        for (e = 0; e < nr; e++) {
            u16 r = rows[e];
            if (!(w->umask[r] & (u16)(1 << i))) continue;
            appendw(r); appendw(w->ucol[r][i]); appendw(w->ulast[r][i]);
        }
    }
}
void g5_work_trans(const g5_work *w, u8 nt, u8 overflow)
{
    u16 j;
    transitions += nt;
    write_long(cases, frame_id); write_word(cases, variant_id); write_word(cases, input_len);
    write_word(cases, overflow ? 0xffff : nt);
    fwrite(input, 1, input_len, cases);
    for (j = 0; j < nt; j++) {
        const g5_tr *t = &w->tr[j];
        fputc(t->idx, cases); fputc(0, cases); write_word(cases, t->val);
        write_word(cases, (u16)t->desde); write_word(cases, (u16)t->xult); write_word(cases, (u16)t->hasta);
    }
}
int main(int argc, char **argv)
{
    int rc;
    if (argc != 10) {
        fprintf(stderr, "uso: g5plan_work cap segw segs bank.idx bank.g5env pal plan cases stats\n");
        return 2;
    }
    cases = fopen(argv[8], "wb"); stats = fopen(argv[9], "w");
    if (!cases || !stats) { perror("salidas de medida"); return 2; }
    fwrite("G5WC", 1, 4, cases);
    fprintf(stats, "frame,a3,attempts,uses,transitions,probes,schedules,segment_words,segments,plan_bytes\n");
    rc = g5_control_main(8, argv);
    flush_stats();
    if (ferror(cases) || ferror(stats)) rc = 2;
    fclose(cases); fclose(stats);
    return rc;
}

