// RUN: %clang_cc1 -triple wasm32-unknown-wasip1 -std=c17 -fno-spell-checking -fsyntax-only -verify=off %s
// RUN: %clang_cc1 -triple wasm64-unknown-wasip1 -std=c17 -fno-spell-checking -fsyntax-only -verify=off %s
// RUN: %clang_cc1 -triple wasm32-unknown-wasip1 -x c++ -fno-spell-checking -fsyntax-only -verify=cppoff %s
// RUN: %clang_cc1 -triple wasm64-unknown-wasip1 -x c++ -fno-spell-checking -fsyntax-only -verify=cppoff %s
// RUN: %clang_cc1 -triple wasm32-unknown-wasip1 -std=c17 -fsanitize=memtag-heap -fsyntax-only -DEXPECT_MTE=1 -verify=on %s
// RUN: %clang_cc1 -triple wasm64-unknown-wasip1 -x c++ -fsanitize=memtag-globals -fsyntax-only -DEXPECT_MTE=1 -verify=on %s

typedef __UINTPTR_TYPE__ uintptr_t;
typedef __PTRDIFF_TYPE__ ptrdiff_t;
#ifndef EXPECT_MTE
#define EXPECT_MTE 0
#endif

#ifdef __cplusplus
#define ASSERT static_assert
#else
#define ASSERT _Static_assert
#endif
#define CHECK_BUILTIN(name) ASSERT(__has_builtin(__builtin_wasm_memtag_##name) == EXPECT_MTE, #name)
CHECK_BUILTIN(status);
CHECK_BUILTIN(tagbits);
CHECK_BUILTIN(startbit);
CHECK_BUILTIN(extract);
CHECK_BUILTIN(insert);
CHECK_BUILTIN(copy);
CHECK_BUILTIN(sub);
CHECK_BUILTIN(sub_raw);
CHECK_BUILTIN(sub_uintptr);
CHECK_BUILTIN(load);
CHECK_BUILTIN(store);
CHECK_BUILTIN(storez);
CHECK_BUILTIN(untag);
CHECK_BUILTIN(untagstore);
CHECK_BUILTIN(untagstorez);
CHECK_BUILTIN(random);
CHECK_BUILTIN(randomstore);
CHECK_BUILTIN(randomstorez);
CHECK_BUILTIN(add);
CHECK_BUILTIN(hint);
CHECK_BUILTIN(hintstore);
CHECK_BUILTIN(hintstorez);
CHECK_BUILTIN(claim);
CHECK_BUILTIN(claimz);
CHECK_BUILTIN(reserve);
CHECK_BUILTIN(activate);
CHECK_BUILTIN(release);
ASSERT(__has_builtin(__builtin_wasm_memory_size), "memory.size");

#if EXPECT_MTE
#ifdef __cplusplus
#define HAS_TYPE(expression, type) __is_same(decltype(expression), type)
#else
#define HAS_TYPE(expression, type) _Generic((expression), type: 1, default: 0)
#endif
ASSERT(HAS_TYPE(__builtin_wasm_memtag_sub_raw((const void *)0, (const void *)0), uintptr_t), "raw result type");
ASSERT(HAS_TYPE(__builtin_wasm_memtag_sub_uintptr(0, (uintptr_t)0, (uintptr_t)0), ptrdiff_t), "integer memtag.sub result type");
ASSERT(HAS_TYPE(__builtin_wasm_memtag_sub(0, (void *)0, (void *)0), ptrdiff_t), "pointer memtag.sub result type");
#endif

void check_calls(int index, void *p, uintptr_t word) {
#if EXPECT_MTE
  (void)__builtin_wasm_memtag_sub(index, p, p); // on-error {{argument to '__builtin_wasm_memtag_sub' must be a constant integer}}
  (void)__builtin_wasm_memtag_sub_uintptr(index, word, word); // on-error {{argument to '__builtin_wasm_memtag_sub_uintptr' must be a constant integer}}
  (void)__builtin_wasm_memtag_sub_raw(p); // on-error {{too few arguments}}
#else
  (void)__builtin_wasm_memtag_sub(0, p, p); // off-error {{use of unknown builtin '__builtin_wasm_memtag_sub'}} cppoff-error {{use of undeclared identifier '__builtin_wasm_memtag_sub'}}
  (void)__builtin_wasm_memtag_sub_raw(p, p); // off-error {{use of unknown builtin '__builtin_wasm_memtag_sub_raw'}} cppoff-error {{use of undeclared identifier '__builtin_wasm_memtag_sub_raw'}}
  (void)__builtin_wasm_memtag_sub_uintptr(0, word, word); // off-error {{use of unknown builtin '__builtin_wasm_memtag_sub_uintptr'}} cppoff-error {{use of undeclared identifier '__builtin_wasm_memtag_sub_uintptr'}}
#endif
}
