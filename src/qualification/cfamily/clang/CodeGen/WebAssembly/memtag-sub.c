// DEFINE: %{mte} = -fsanitize=memtag-stack,memtag-heap,memtag-globals -DEXPECT_MTE=1
// DEFINE: %{ir} = -emit-llvm -disable-llvm-passes -o -
// RUN: %clang_cc1 -triple wasm32-unknown-wasip1 %{ir} %{mte} %s | FileCheck %s --check-prefixes=CHECK,MTE -DW=i32
// RUN: %clang_cc1 -triple wasm64-unknown-wasip1 %{ir} %{mte} %s | FileCheck %s --check-prefixes=CHECK,MTE,MTE64 -DW=i64
// RUN: %clang_cc1 -triple wasm32-unknown-wasip1 -x c++ %{ir} %{mte} %s | FileCheck %s --check-prefixes=CHECK,MTE -DW=i32
// RUN: %clang_cc1 -triple wasm64-unknown-wasip1 -x c++ %{ir} %{mte} %s | FileCheck %s --check-prefixes=CHECK,MTE,MTE64 -DW=i64
// RUN: %clang_cc1 -triple wasm32-unknown-wasip1 %{ir} %s | FileCheck %s --check-prefixes=CHECK,RAW -DW=i32 --implicit-check-not=llvm.wasm.memtag
// RUN: %clang_cc1 -triple wasm64-unknown-wasip1 %{ir} %s | FileCheck %s --check-prefixes=CHECK,RAW -DW=i64 --implicit-check-not=llvm.wasm.memtag
// RUN: %clang_cc1 -triple wasm32-unknown-wasip1 -x c++ %{ir} %s | FileCheck %s --check-prefixes=CHECK,RAW -DW=i32 --implicit-check-not=llvm.wasm.memtag
// RUN: %clang_cc1 -triple wasm64-unknown-wasip1 -x c++ %{ir} %s | FileCheck %s --check-prefixes=CHECK,RAW -DW=i64 --implicit-check-not=llvm.wasm.memtag
// RUN: %clang_cc1 -triple wasm32-unknown-wasip1 %{ir} %{mte} %s | FileCheck %s --check-prefix=C-EXT -DW=i32
// RUN: %clang_cc1 -triple wasm64-unknown-wasip1 %{ir} %{mte} %s | FileCheck %s --check-prefix=C-EXT -DW=i64
// RUN: %if aarch64-registered-target %{ %clang_cc1 -triple aarch64-unknown-linux -fsanitize=memtag-stack %{ir} %s | FileCheck %s --check-prefixes=CHECK,RAW -DW=i64 --implicit-check-not=llvm.wasm.memtag %}

#ifndef EXPECT_MTE
#define EXPECT_MTE 0
#endif

#if __has_builtin(__builtin_wasm_memtag_status) != EXPECT_MTE || \
    __has_builtin(__builtin_wasm_memtag_sub) != EXPECT_MTE || \
    __has_builtin(__builtin_wasm_memtag_sub_uintptr) != EXPECT_MTE || \
    __has_builtin(__builtin_wasm_memtag_sub_raw) != EXPECT_MTE || \
    __has_builtin(__builtin_wasm_memtag_release) != EXPECT_MTE
#error unexpected WasmMTE builtin availability
#endif
#if defined(__wasm__) && !__has_builtin(__builtin_wasm_memory_size)
#error memory.size must be available in both profiles
#endif

typedef __PTRDIFF_TYPE__ ptrdiff_t;
typedef __UINTPTR_TYPE__ uintptr_t;
struct element { unsigned char bytes[12]; };

#ifdef __cplusplus
extern "C" {
#endif

// CHECK-LABEL: @elements(
// MTE: call [[W]] @llvm.wasm.memtag.sub.[[W]](i32 0, ptr {{[^,]+}}, ptr {{[^)]+}})
// RAW: ptrtoint ptr {{.*}} to [[W]]
// RAW: ptrtoint ptr {{.*}} to [[W]]
// RAW: = sub [[W]]
// CHECK: sdiv exact [[W]] {{.*}}, 12
ptrdiff_t elements(const struct element *lhs, const struct element *rhs) {
  return lhs - rhs;
}

// CHECK-LABEL: @unsigned_words(
// CHECK-NOT: llvm.wasm.memtag.sub
// CHECK: [[D:%.*]] = sub [[W]]
// CHECK-NEXT: ret [[W]] [[D]]
uintptr_t unsigned_words(uintptr_t lhs, uintptr_t rhs) { return lhs - rhs; }

// CHECK-LABEL: @integer_casts(
// CHECK: ptrtoint ptr {{.*}} to [[W]]
// CHECK: ptrtoint ptr {{.*}} to [[W]]
// CHECK: = sub [[W]]
uintptr_t integer_casts(const void *lhs, const void *rhs) {
  return (uintptr_t)lhs - (uintptr_t)rhs;
}

// CHECK-LABEL: @offset(
// CHECK: getelementptr {{.*}}i8, ptr
unsigned char *offset(unsigned char *p, ptrdiff_t count) { return p - count; }

// CHECK-LABEL: @other_space(
// CHECK: ptrtoint ptr addrspace(1) {{.*}} to [[W]]
// CHECK: ptrtoint ptr addrspace(1) {{.*}} to [[W]]
// CHECK: = sub [[W]]
typedef char __attribute__((address_space(1))) other_char;
ptrdiff_t other_space(other_char *lhs, other_char *rhs) { return lhs - rhs; }

// CHECK-LABEL: @unmarked(
// CHECK: ptrtoint ptr {{.*}} to [[W]]
// CHECK: = sub [[W]]
__attribute__((no_sanitize("memtag")))
ptrdiff_t unmarked(const char *lhs, const char *rhs) { return lhs - rhs; }

// CHECK-LABEL: @disable_instrumentation(
// CHECK: ptrtoint ptr {{.*}} to [[W]]
// CHECK: = sub [[W]]
__attribute__((disable_sanitizer_instrumentation))
ptrdiff_t disable_instrumentation(const char *lhs, const char *rhs) {
  return lhs - rhs;
}

#if EXPECT_MTE
// MTE-LABEL: @raw_bytes(
// MTE: ptrtoint ptr {{.*}} to [[W]]
// MTE: ptrtoint ptr {{.*}} to [[W]]
// MTE: [[RAW:%.*]] = sub [[W]]
// MTE-NEXT: ret [[W]] [[RAW]]
uintptr_t raw_bytes(const struct element *lhs, const struct element *rhs) {
  return __builtin_wasm_memtag_sub_raw(lhs, rhs);
}

// MTE-LABEL: @word_bytes(
// MTE: inttoptr [[W]] {{.*}} to ptr
// MTE: inttoptr [[W]] {{.*}} to ptr
// MTE: call [[W]] @llvm.wasm.memtag.sub.[[W]](i32 0, ptr {{[^,]+}}, ptr {{[^)]+}})
__attribute__((no_sanitize("memtag")))
ptrdiff_t word_bytes(uintptr_t lhs, uintptr_t rhs) {
  return __builtin_wasm_memtag_sub_uintptr(0, lhs, rhs);
}

// MTE-LABEL: @u32_bytes(
// MTE64: zext i32 {{.*}} to i64
// MTE64: zext i32 {{.*}} to i64
// MTE: inttoptr [[W]] {{.*}} to ptr
// MTE: inttoptr [[W]] {{.*}} to ptr
// MTE: call [[W]] @llvm.wasm.memtag.sub.[[W]](i32 0, ptr {{[^,]+}}, ptr {{[^)]+}})
ptrdiff_t u32_bytes(unsigned lhs, unsigned rhs) {
  return __builtin_wasm_memtag_sub_uintptr(0, lhs, rhs);
}
#endif

#ifndef __cplusplus
// C-EXT-LABEL: @function_indices(
// C-EXT: ptrtoint ptr {{.*}} to [[W]]
// C-EXT: ptrtoint ptr {{.*}} to [[W]]
// C-EXT: = sub [[W]]
typedef void (*function_ptr)(void);
ptrdiff_t function_indices(function_ptr lhs, function_ptr rhs) { return lhs - rhs; }

// C-EXT-LABEL: @arrays(
// C-EXT: call [[W]] @llvm.wasm.memtag.sub.[[W]](i32 0,
// C-EXT: sdiv exact [[W]] {{.*}}, %
ptrdiff_t arrays(int count, int (*lhs)[count], int (*rhs)[count]) {
  return lhs - rhs;
}
#endif

#ifdef __cplusplus
}
#endif
