#ifndef WROS_TAG_ACCESS_H
#define WROS_TAG_ACCESS_H
#include <stdint.h>

#if __has_builtin(__builtin_wasm_memtag_insert) != TEST_MTE
#error WasmMTE builtins differ from the selected test profile
#endif

#ifdef __cplusplus
extern "C" {
#endif
void check_access(unsigned mode, unsigned delta);
void check_word(unsigned char *storage, unsigned mode, unsigned delta);
uint32_t read_word(const unsigned char *p);
void write_word(unsigned char *p, uint32_t value);
void observe(unsigned mode, unsigned delta, uintptr_t address, unsigned logical,
             unsigned first, unsigned last);
void completed(uint32_t value);
#if TEST_MTE
static inline unsigned shadow_tag(uintptr_t address) {
    return (unsigned)__builtin_wasm_memtag_extract(0, __builtin_wasm_memtag_load(0, (void *)address));
}
void check_lifecycle(unsigned mode);
#endif
#ifdef __cplusplus
}
#endif
#endif
