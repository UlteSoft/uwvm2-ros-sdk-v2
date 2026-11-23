; RUN: llc < %s -mattr=+memtag,+atomics -stop-after=wasm-stack-tagging | FileCheck %s
; RUN: llc < %s -mtriple=wasm64-unknown-unknown -mattr=+memtag,+atomics -stop-after=wasm-stack-tagging | FileCheck %s

; A proof must include bounds, lifetime and every reachable use. Safe stack
; objects retain ordinary Wasm memory access semantics without tag maintenance.
; Unknown callees, escaping pointers and incomplete range proofs stay tagged.

; CHECK-LABEL: define {{.*}}@safe_constant(
; CHECK-NOT: llvm.wasm.memtag.
; CHECK: ret i32

; CHECK-LABEL: define {{.*}}@safe_masked(
; CHECK-NOT: llvm.wasm.memtag.
; CHECK: ret i32

; CHECK-LABEL: define {{.*}}@safe_atomic(
; CHECK-NOT: llvm.wasm.memtag.
; CHECK: ret i32

; CHECK-LABEL: define {{.*}}@bounded_callee(
; CHECK: ret i32

; CHECK-LABEL: define {{.*}}@safe_known_call(
; CHECK-NOT: llvm.wasm.memtag.
; CHECK: ret i32

; CHECK-LABEL: define {{.*}}@safe_bulk(
; CHECK-NOT: llvm.wasm.memtag.
; CHECK: ret i32

; CHECK-LABEL: define {{.*}}@unsafe_index(
; CHECK: %buf.tag = call ptr @llvm.wasm.memtag.random
; CHECK: call void @llvm.wasm.memtag.store

; CHECK-LABEL: define {{.*}}@unsafe_oob(
; CHECK: %buf.tag = call ptr @llvm.wasm.memtag.random
; CHECK: call void @llvm.wasm.memtag.store

; CHECK-LABEL: define {{.*}}@unsafe_after_lifetime(
; CHECK: %buf.tag = call ptr @llvm.wasm.memtag.random
; CHECK: call void @llvm.wasm.memtag.store

; CHECK-LABEL: define {{.*}}@unsafe_before_lifetime(
; CHECK: %{{[^ ]+}} = call ptr @llvm.wasm.memtag.random
; CHECK: call void @llvm.wasm.memtag.store

; CHECK-LABEL: define {{.*}}@unsafe_unknown_call(
; CHECK: %buf.tag = call ptr @llvm.wasm.memtag.random
; CHECK: call void @llvm.wasm.memtag.store

; CHECK-LABEL: define {{.*}}@unsafe_indirect_call(
; CHECK: %buf.tag = call ptr @llvm.wasm.memtag.random
; CHECK: call void @llvm.wasm.memtag.store

; CHECK-LABEL: define {{.*}}@unsafe_escape(
; CHECK: %buf.tag = call ptr @llvm.wasm.memtag.random
; CHECK: call void @llvm.wasm.memtag.store

; CHECK-LABEL: define {{.*}}@unsafe_return(
; CHECK: %buf.tag = call ptr @llvm.wasm.memtag.random
; CHECK: call void @llvm.wasm.memtag.store
target triple = "wasm32-unknown-unknown"
@escaped = external global ptr
declare void @unknown(ptr)
declare void @llvm.lifetime.start.p0(ptr)
declare void @llvm.lifetime.end.p0(ptr)
declare void @llvm.memset.p0.i32(ptr, i8, i32, i1)

define i32 @safe_constant() sanitize_memtag {
entry:
  %buf = alloca [32 x i8], align 16
  %p = getelementptr i8, ptr %buf, i32 28
  store volatile i32 42, ptr %p, align 4
  %r = load volatile i32, ptr %p, align 4
  ret i32 %r
}
define i32 @safe_masked(i32 %x) sanitize_memtag {
entry:
  %buf = alloca [32 x i8], align 16
  %i = and i32 %x, 7
  %p = getelementptr i32, ptr %buf, i32 %i
  store volatile i32 42, ptr %p, align 4
  %r = load volatile i32, ptr %p, align 4
  ret i32 %r
}
define i32 @safe_atomic() sanitize_memtag {
entry:
  %buf = alloca [32 x i8], align 16
  %p = getelementptr i8, ptr %buf, i32 28
  store atomic i32 42, ptr %p seq_cst, align 4
  %r = load atomic i32, ptr %p seq_cst, align 4
  ret i32 %r
}
define internal i32 @bounded_callee(ptr %p) noinline {
entry:
  store volatile i32 42, ptr %p, align 4
  %r = load volatile i32, ptr %p, align 4
  ret i32 %r
}
define i32 @safe_known_call() sanitize_memtag {
entry:
  %buf = alloca [32 x i8], align 16
  %p = getelementptr i8, ptr %buf, i32 28
  %r = call i32 @bounded_callee(ptr %p)
  ret i32 %r
}
define i32 @safe_bulk() sanitize_memtag {
entry:
  %buf = alloca [32 x i8], align 16
  call void @llvm.memset.p0.i32(ptr %buf, i8 42, i32 32, i1 true)
  %p = getelementptr i8, ptr %buf, i32 31
  %r = load volatile i8, ptr %p
  %z = zext i8 %r to i32
  ret i32 %z
}
define i32 @unsafe_index(i32 %i) sanitize_memtag {
entry:
  %buf = alloca [32 x i8], align 16
  %p = getelementptr i8, ptr %buf, i32 %i
  %r = load volatile i32, ptr %p, align 1
  ret i32 %r
}
define i32 @unsafe_oob() sanitize_memtag {
entry:
  %buf = alloca [32 x i8], align 16
  %p = getelementptr i8, ptr %buf, i32 32
  %r = load volatile i32, ptr %p, align 1
  ret i32 %r
}
define i32 @unsafe_after_lifetime() sanitize_memtag {
entry:
  %buf = alloca [32 x i8], align 16
  call void @llvm.lifetime.start.p0(ptr %buf)
  store volatile i32 42, ptr %buf
  call void @llvm.lifetime.end.p0(ptr %buf)
  %r = load volatile i32, ptr %buf
  ret i32 %r
}
define i32 @unsafe_before_lifetime() sanitize_memtag {
entry:
  %buf = alloca [32 x i8], align 16
  %r = load volatile i32, ptr %buf
  call void @llvm.lifetime.start.p0(ptr %buf)
  store volatile i32 42, ptr %buf
  call void @llvm.lifetime.end.p0(ptr %buf)
  ret i32 %r
}
define void @unsafe_unknown_call() sanitize_memtag {
entry:
  %buf = alloca [32 x i8], align 16
  call void @unknown(ptr %buf)
  ret void
}
define void @unsafe_indirect_call(ptr %fn) sanitize_memtag {
entry:
  %buf = alloca [32 x i8], align 16
  call void %fn(ptr %buf)
  ret void
}
define void @unsafe_escape() sanitize_memtag {
entry:
  %buf = alloca [32 x i8], align 16
  store ptr %buf, ptr @escaped
  ret void
}
define ptr @unsafe_return() sanitize_memtag {
entry:
  %buf = alloca [32 x i8], align 16
  ret ptr %buf
}
