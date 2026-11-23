#ifndef __wasilibc___macro_PAGESIZE_h
#define __wasilibc___macro_PAGESIZE_h

/*
 * Without custom-page-sizes proposal, the page size in WebAssembly
 * is fixed at 64 KiB.
 *
 * The LLVM versions with a support of custom-page-sizes proposal
 * provides __wasm_first_page_end global to allow page-size-agnostic
 * objects.
 *
 * If this ever needs to be a value outside the range of an `int`, the
 * `getpagesize` function which returns this value will need special
 * consideration. POSIX has deprecated `getpagesize` in favor of
 * `sysconf(_SC_PAGESIZE)` which does not have this problem.
 */
// FIXME(#778): `__wasm_first_page_end` is broken for PIC as of this writing and
// will likely require `wasm-ld` changes, at which point we can re-enable it.
#if __clang_major__ >= 22 && !defined __pic__
extern char __wasm_first_page_end;
// The linker supplies a number through the symbol address. Its value may
// coincide with tagged storage that belongs to an unrelated data object.
#if __has_feature(memtag_globals) && __has_builtin(__builtin_wasm_memtag_untag)
#define PAGESIZE ((unsigned long)__builtin_wasm_memtag_untag(0, &__wasm_first_page_end))
#else
#define PAGESIZE ((unsigned long)&__wasm_first_page_end)
#endif
#else
#define PAGESIZE (0x10000)
#endif

#endif
