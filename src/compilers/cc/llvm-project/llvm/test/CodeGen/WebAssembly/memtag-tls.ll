; RUN: llc < %s -mattr=+atomics,+bulk-memory -verify-each -stop-after=WebAssembly-globals-tagging | FileCheck %s --check-prefix=IR
; RUN: llc < %s -mattr=+atomics,+bulk-memory -verify-each | FileCheck %s --check-prefix=ASM
; RUN: llc < %s -mattr=+atomics,+bulk-memory -verify-each -filetype=obj -o /dev/null

target triple = "wasm32-unknown-wasip1-threads"
@initialized = thread_local global i32 17, sanitize_memtag
@zeroed = thread_local global [8 x i8] zeroinitializer, sanitize_memtag
@foreign = external thread_local global i32

declare ptr @llvm.threadlocal.address.p0(ptr)

; Padding must preserve TLS storage and the resolved address must be retagged.
; The symbol operand of llvm.threadlocal.address must remain a constant.
; IR: @initialized = thread_local global { i32, [12 x i8] }
; IR: @zeroed = thread_local global { [8 x i8], [8 x i8] }
; IR-LABEL: define ptr @get_initialized(
; IR: [[P:%.*]] = call ptr @llvm.threadlocal.address.p0(ptr @initialized)
; IR-NEXT: [[T:%.*]] = call ptr @llvm.wasm.memtag.load(i32 0, ptr [[P]])
; IR: ret ptr [[T]]
define ptr @get_initialized() sanitize_memtag {
  %p = call ptr @llvm.threadlocal.address.p0(ptr @initialized)
  ret ptr %p
}
; IR-LABEL: define i32 @get_foreign(
; IR: [[P:%.*]] = call ptr @llvm.threadlocal.address.p0(ptr @foreign)
; IR-NEXT: [[T:%.*]] = call ptr @llvm.wasm.memtag.load(i32 0, ptr [[P]])
; IR: load volatile i32, ptr [[T]]
define i32 @get_foreign() sanitize_memtag {
  %p = call ptr @llvm.threadlocal.address.p0(ptr @foreign)
  %v = load volatile i32, ptr %p
  ret i32 %v
}
; ASM-DAG: .memtag initialized
; ASM-DAG: .memtag zeroed
; ASM-DAG: .section .tdata.initialized
; ASM-DAG: .section .tbss.zeroed
