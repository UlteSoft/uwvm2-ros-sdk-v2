; RUN: llc < %s -verify-each -stop-after=wasm-stack-tagging | FileCheck %s
; RUN: llc < %s -mtriple=wasm64-unknown-unknown -verify-each -stop-after=wasm-stack-tagging | FileCheck %s
; RUN: llc < %s -verify-each -filetype=obj -o /dev/null
; RUN: llc < %s -mtriple=wasm64-unknown-unknown -verify-each -filetype=obj -o /dev/null
target triple = "wasm32-unknown-unknown"

declare void @use(ptr)
declare ptr @llvm.stacksave.p0()
declare void @llvm.stackrestore.p0(ptr)

; Each dynamic object is padded and tagged after checked size arithmetic. Both
; block stackrestore and function return retire discarded ranges, so loops do
; not require a bounded allocation list. Saved stack positions are raw pointers.
; CHECK-LABEL: define void @dynamic(
; CHECK: %memtag.dynamic.base = call ptr @llvm.stacksave.p0()
; CHECK: call { i{{32|64}}, i1 } @llvm.umul.with.overflow
; CHECK: call { i{{32|64}}, i1 } @llvm.uadd.with.overflow
; CHECK: call void @llvm.trap()
; CHECK: %object.raw = alloca i8, i{{32|64}} %memtag.dynamic.size, align 16
; CHECK: %object.tag = call ptr @llvm.wasm.memtag.randomstore
; CHECK: call void @use(ptr %object.tag)
; CHECK: %memtag.dynamic.current = call ptr @llvm.stacksave.p0()
; CHECK: call void @llvm.wasm.memtag.store
; CHECK: call void @llvm.stackrestore.p0(ptr %saved)
; CHECK: call void @llvm.wasm.memtag.store
; CHECK: ret void
define void @dynamic(i64 %count) sanitize_memtag {
entry:
  %saved = call ptr @llvm.stacksave.p0()
  %object = alloca i64, i64 %count, align 8
  call void @use(ptr %object)
  call void @llvm.stackrestore.p0(ptr %saved)
  ret void
}

; CHECK-LABEL: define void @plain(
; CHECK-NOT: @llvm.wasm.memtag
; CHECK: ret void
define void @plain(i64 %count) {
  %object = alloca i64, i64 %count, align 8
  call void @use(ptr %object)
  ret void
}
