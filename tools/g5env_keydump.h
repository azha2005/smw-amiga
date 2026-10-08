/* Solo incluido por la copia instrumental de marioverify en work/.
   Captura las entradas que mario_sprite ya esta leyendo, sin recalcular
   graficos sobre una RAM de otra fase (P35). Derivados fuera de git. */
static FILE *g5key_file;
static void g5key_dump(u32 frame)
{
    u8 h[4];
    if (!g5key_file) {
        const char *path = getenv("GAME_G5KEY_CAP");
        if (!path || !(g5key_file = fopen(path, "wb"))) {
            fprintf(stderr, "GAME_G5KEY_CAP ausente o no escribible\n"); exit(2);
        }
    }
    h[0] = frame >> 24; h[1] = frame >> 16; h[2] = frame >> 8; h[3] = frame;
    fwrite(h, 1, 4, g5key_file);
    fwrite(mario_oam, 1, 16, g5key_file);
    fwrite(mario_osz, 1, 4, g5key_file);
}
static void g5key_finish(void)
{
    if (g5key_file) {
        int bad = ferror(g5key_file);
        if (fclose(g5key_file) || bad) exit(2);
        g5key_file = NULL;
    }
}
