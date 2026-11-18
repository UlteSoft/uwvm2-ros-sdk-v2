extern int Body_Body_Rotate_int(int, void*);
extern int Body_Body_TagNeighbors_int(int, void*);
void check(int enabled) {
    for (int n = -80; n <= 80; ++n)
        if (Body_Body_Rotate_int(n, 0) != ((n * 17 + 3) ^ (n >> 4))) __builtin_trap();
    int v = Body_Body_TagNeighbors_int(290, 0);
    int a = v & 15, b = v >> 4;
    if (enabled ? (!a || !b || a == b) : (a || b)) __builtin_trap();
}
