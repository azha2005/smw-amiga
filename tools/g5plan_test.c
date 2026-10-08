/*
 * g5plan_test.c - G2T-B3/B4 en el PC (docs/instrucciones-g2t-b35.md).
 *
 * Por cada frame con Rex de un volcado de B2 (work/g2tb/cap_<traza>.bin,
 * el bloque de g5_capture) arma la lista del copper de ese frame desde
 * work/g2tb35/segw_<traza>.bin (g2t_segdump.py), comprueba g5_segment fila
 * a fila contra segs_<traza>.bin (B3-2) y escribe el plan de g5_plan en
 * formato B1 (B4: tiene que ser identico a work/g2t_ref/plan_<traza>.bin).
 *
 *   gcc -O2 -DNOOAM -DSPR_OAM -DSPR_G5 -Iplayer -o work/g2tb35/g5plan_test \
 *       tools/g5plan_test.c player/g5plan.c
 *   work/g2tb35/g5plan_test cap.bin segw.bin segs.bin bank.idx bank.g5env \
 *       mario_pal.bin plan.bin
 */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stddef.h>
#include "g5plan.h"

/* lo que g5_capture lee del juego (aqui no se llama) */
u8 ram[0x2000];
u8 mario_pal;
u8 spr_oam_first[12], spr_oam_n[12];

#define CL 216
#define SEG 220
#define SPRB (4 * G5_SPRW * 2)
#define CAP_REC (6 + 24 + 0x2000 + SPRB + G5_BLK)

static u8 *load(const char *path, long *len)
{
    FILE *f = fopen(path, "rb");
    u8 *b;
    if (!f) { perror(path); exit(2); }
    fseek(f, 0, SEEK_END);
    *len = ftell(f);
    fseek(f, 0, SEEK_SET);
    b = malloc(*len + 1);
    if (fread(b, 1, *len, f) != (size_t)*len) { perror(path); exit(2); }
    fclose(f);
    return b;
}

static u32 be32(const u8 *p) { return (u32)p[0] << 24 | (u32)p[1] << 16 | (u32)p[2] << 8 | p[3]; }

int main(int argc, char **argv)
{
    long ncap, nsw, nss, nt, ne, np, o, so = 0, ss = 0;
    u8 *cap, *sw, *sg, *tab, *env, *pal, *list, out[2048];
    static g5_work w;
    long frames = 0, segbad = 0, segrows = 0, frontierbad = 0, frontierpairs = 0;
    FILE *fo;

    if (argc != 8) {
        fprintf(stderr, "uso: g5plan_test cap segw segs bank.idx bank.g5env mario_pal.bin plan.bin\n");
        return 2;
    }
    printf("g5_work: %lu B; nsegs offset %lu\n", (unsigned long)sizeof(w),
           (unsigned long)offsetof(g5_work, nsegs));
    cap = load(argv[1], &ncap);
    sw = load(argv[2], &nsw);
    sg = load(argv[3], &nss);
    tab = load(argv[4], &nt);
    env = load(argv[5], &ne);
    pal = load(argv[6], &np);
    if (ncap % CAP_REC) { fprintf(stderr, "%s: no es multiplo de %d\n", argv[1], CAP_REC); return 2; }
    list = calloc(CL + SEG * G5_ROWS + 4, 1);
    memset(&w, 0xA5, sizeof(w));       /* no depender de tablas borradas */
    fo = fopen(argv[7], "wb");
    if (!fo) { perror(argv[7]); return 2; }
    for (o = 0; o < ncap; o += CAP_REC) {
        u32 frame = be32(cap + o);
        const u8 *blk = cap + o + 6 + 24 + 0x2000 + SPRB;
        s16 r;
        u16 len;
        if (so >= nsw || be32(sw + so) != frame || be32(sg + ss) != frame) {
            fprintf(stderr, "frame %lu: sin segw/segs alineado\n", (unsigned long)frame);
            return 1;
        }
        so += 4;
        ss += 4;
        memset(list, 0, CL + SEG * G5_ROWS + 4);
        for (r = 0; r < G5_ROWS; r++) {
            u8 n = sw[so++];
            memcpy(list + CL + SEG * r, sw + so, 4 * n);
            so += 4 * n;
        }
        for (r = 0; r < G5_ROWS; r++, ss += 4) {    /* B3-2 */
            g5_seg s;
            s16 mrow = (s16)(blk[G5B_MROW] << 8 | blk[G5B_MROW + 1]);
            s16 j = (s16)(r - mrow);
            u16 mask = j < 0 || j >= G5_WIN ? 0 :
                (u16)((blk[G5B_MASK + 2 * j] << 8 | blk[G5B_MASK + 2 * j + 1]) & 0xfffe);
            u8 i;
            s16 last = (s16)(sg[ss + 1] << 8 | sg[ss + 2]);
            frontierbad += g5_mario_mask(blk, r) != mask;
            for (i = 1; i < 16; i++) {
                if (mask & (u16)(1 << i)) {
                    u8 a, b;
                    const u8 *want = blk + G5B_ENV + 30 * j + 2 * (i - 1);
                    g5_mario_span(blk, r, i, &a, &b);
                    frontierbad += a != want[0] || b != want[1];
                    frontierpairs++;
                }
            }
            g5_segment(list, CL, SEG, r, &s);
            segrows++;
            if (!s.ok || s.nb != sg[ss] || s.last != last || s.wrap != sg[ss + 3]) {
                if (segbad < 5)
                    fprintf(stderr, "segmento distinto: frame %lu fila %d: C nb=%d last=%d wrap=%d ok=%d, ref nb=%d last=%d wrap=%d\n",
                            (unsigned long)frame, r, s.nb, s.last, s.wrap, s.ok, sg[ss], last, sg[ss + 3]);
                segbad++;
            }
        }
        len = g5_plan(frame, blk, tab, env, pal, list, CL, SEG, &w, out);
        fwrite(out, 1, len, fo);
        frames++;
    }
    fclose(fo);
    if (!frames || so != nsw || ss != nss) {
        fprintf(stderr, "captura vacia o registros de segmentos sobrantes\n");
        return 1;
    }
    printf("frontera B2/B3: %ld filas, %ld pares; diferencias %ld\n", segrows, frontierpairs, frontierbad);
    printf("g5plan_test: %ld frames; segmentos distintos %ld de %ld filas; plan -> %s\n",
           frames, segbad, segrows, argv[7]);
    return segbad || frontierbad ? 1 : 0;
}
