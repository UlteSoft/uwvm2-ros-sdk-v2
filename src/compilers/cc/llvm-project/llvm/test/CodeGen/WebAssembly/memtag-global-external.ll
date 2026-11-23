; RUN: llc < %s -verify-each -stop-after=WebAssembly-globals-tagging | FileCheck %s
; RUN: llc < %s -verify-each -filetype=obj -o /dev/null
target triple = "wasm32-unknown-unknown"
@external_data = external global i32
@external_tls = external thread_local global i32
@__heap_end = external global i8
@dummy = internal global ptr null, sanitize_memtag
@weak_data = weak alias ptr, ptr @dummy
@function_alias = weak alias void (), ptr @plain_function

; Even a TU with no locally taggable definitions must repair external and weak
; data references in instrumented functions after final symbol resolution.
; CHECK-LABEL: define i32 @external_use(
; CHECK: call ptr @llvm.wasm.memtag.load(i32 0, ptr @external_data)
; CHECK: load volatile i32
define i32 @external_use() sanitize_memtag {
  %x = load volatile i32, ptr @external_data
  ret i32 %x
}
; CHECK-LABEL: define ptr @alias_use(
; CHECK: call ptr @llvm.wasm.memtag.load(i32 0, ptr @weak_data)
; CHECK: load volatile ptr
define ptr @alias_use() sanitize_memtag {
  %x = load volatile ptr, ptr @weak_data
  ret ptr %x
}
; Do not introduce an extension into an uninstrumented external reference.
; CHECK-LABEL: define i32 @uninstrumented(
; CHECK-NOT: call ptr @llvm.wasm.memtag.load
; CHECK: load volatile i32, ptr @external_data
define i32 @uninstrumented() {
  %x = load volatile i32, ptr @external_data
  ret i32 %x
}
; Do not treat a function/table alias as a linear-memory pointer.
; CHECK-LABEL: define ptr @function_pointer(
; CHECK-NOT: call ptr @llvm.wasm.memtag.load
; CHECK: ret ptr @function_alias
define ptr @function_pointer() sanitize_memtag {
  ret ptr @function_alias
}
define void @plain_function() { ret void }

; Linker addresses and external data use a runtime in-range guard, avoiding an
; invalid tag load when a symbol denotes one-past-the-end instead of an object.
; CHECK-LABEL: define i32 @linker_address(
; CHECK: [[STATUS:%.*]] = call i32 @llvm.wasm.memtag.status.i32(i32 0)
; CHECK: [[ENABLED:%.*]] = icmp ne i32 [[STATUS]], 0
; CHECK: br i1 [[ENABLED]], label %memtag.global.check, label %memtag.global.cont
; CHECK: memtag.global.check:
; CHECK: call i32 @llvm.wasm.memory.size.i32(i32 0)
; CHECK: icmp ult
; CHECK: br i1
; CHECK: memtag.global.load:
; CHECK: call ptr @llvm.wasm.memtag.load(i32 0, ptr @__heap_end)
; CHECK: memtag.global.cont:
; CHECK: phi ptr [ @__heap_end, %0 ],
define i32 @linker_address() sanitize_memtag {
  ret i32 ptrtoint (ptr @__heap_end to i32)
}

@optional_data = extern_weak global i32
; Do not let a nonzero tag on address zero turn an absent weak symbol nonnull.
; CHECK-LABEL: define i1 @weak_null(
; CHECK: icmp ult
; CHECK: [[NONNULL:%.*]] = icmp ne ptr @optional_data, null
; CHECK: and i1 {{.*}}, [[NONNULL]]
; CHECK: br i1
; CHECK: call ptr @llvm.wasm.memtag.load(i32 0, ptr @optional_data)
; CHECK: phi ptr [ @optional_data,
define i1 @weak_null() sanitize_memtag {
  %present = icmp ne ptr @optional_data, null
  ret i1 %present
}
