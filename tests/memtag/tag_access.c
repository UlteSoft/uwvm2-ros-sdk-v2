/* The separate translation unit makes the stack object's address escape.
   All source-level accesses are inside the 48-byte object. */
void check_word(unsigned char *storage, unsigned delta, unsigned store, unsigned cross);

void check_access(unsigned delta, unsigned store, unsigned cross) {
    _Alignas(16) unsigned char storage[48] = {0};
    check_word(storage, delta, store, cross);
}
