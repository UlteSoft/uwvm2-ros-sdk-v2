#include <stddef.h>
#include <stdint.h>
#include <string.h>

void *mwpm_alloc_range(size_t bytes, uint8_t zero);
void mwpm_free_range(void *page, size_t bytes);

/* Only reached when the upstream implementation reports or asserts.
   Either situation fails this bounded, allocation-success test. */
_Noreturn void mono_assertion_message(const char *file, int line, const char *condition) {
    (void)file;
    (void)line;
    (void)condition;
    __builtin_trap();
}
void monoeg_g_print(const char *format, ...) {
    (void)format;
    __builtin_trap();
}
enum { page_size = 65536, object_bytes = 32 };
static void check(int condition) {
    if (!condition)
        __builtin_trap();
}
static void *raw(void *p) { return __builtin_wasm_memtag_untag(0, p); }
static unsigned color(void *p) { return __builtin_wasm_memtag_extract(0, p); }
static void check_adjacent(void *first, void *neighbor) {
    check((uintptr_t)raw(first) + object_bytes == (uintptr_t)raw(neighbor));
    if (__builtin_wasm_memtag_status(0))
        check(color(first) && color(neighbor) && color(first) != color(neighbor));
    else
        check(!color(first) && !color(neighbor));
}
void check_pages(int tagged) {
    if (!!__builtin_wasm_memtag_status(0) != tagged)
        __builtin_trap();
    check(!mwpm_alloc_range(0, 1));
    unsigned char *pages = mwpm_alloc_range(2 * page_size, 1);
    check(pages && color(pages) == 0 && (uintptr_t)pages % page_size == 0);
    unsigned char *second_page = pages + page_size;
    check(!second_page[0] && !pages[0]);
    unsigned char *first = __builtin_wasm_memtag_claimz(0, pages, object_bytes);
    unsigned char *neighbor = __builtin_wasm_memtag_claimz(0, pages + object_bytes, object_bytes);
    unsigned char *copy = __builtin_wasm_memtag_claimz(0, second_page, object_bytes);
    check_adjacent(first, neighbor);
    for (unsigned i = 0; i < object_bytes; i++) {
        first[i] = (unsigned char)(2 * i + 7);
        neighbor[i] = (unsigned char)(4 * i + 1);
    }
    memcpy(copy, first, object_bytes);
    for (unsigned i = 0; i < object_bytes; i++) {
        check(copy[i] == (unsigned char)(2 * i + 7));
        check(neighbor[i] == (unsigned char)(4 * i + 1));
    }
    check(__builtin_wasm_memtag_release(0, first, object_bytes) == pages);
    first = __builtin_wasm_memtag_claimz(0, pages, object_bytes);
    check_adjacent(first, neighbor);
    for (unsigned i = 0; i < object_bytes; i++)
        check(first[i] == 0 && neighbor[i] == (unsigned char)(4 * i + 1));
    check(__builtin_wasm_memtag_release(0, first, object_bytes) == pages);
    check(__builtin_wasm_memtag_release(0, neighbor, object_bytes) == pages + object_bytes);
    /* The partial page release must preserve the live object in the second page. */
    mwpm_free_range(pages, page_size);
    unsigned char *reused = mwpm_alloc_range(page_size, 1);
    check(reused == pages);
    for (unsigned i = 0; i < object_bytes; i++)
        check(!reused[object_bytes + i] && copy[i] == (unsigned char)(2 * i + 7));
    check(__builtin_wasm_memtag_release(0, copy, object_bytes) == second_page);
    mwpm_free_range(reused, 2 * page_size);
}
