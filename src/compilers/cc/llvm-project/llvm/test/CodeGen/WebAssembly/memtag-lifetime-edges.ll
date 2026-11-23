; RUN: llc < %s -stop-after=wasm-stack-tagging | FileCheck %s --check-prefix=IR
; RUN: llc < %s -mtriple=wasm64-unknown-unknown -stop-after=wasm-stack-tagging | FileCheck %s --check-prefix=IR
; RUN: llc < %s -mattr=+exception-handling -wasm-use-legacy-eh=false -asm-verbose=false | FileCheck %s --check-prefix=ASM

target triple = "wasm32-unknown-unknown"
@external = external global i32
@weak = extern_weak global i8
declare void @escape(ptr)
declare i32 @__gxx_wasm_personality_v0(...)
declare void @llvm.lifetime.start.p0(ptr)
declare void @llvm.lifetime.end.p0(ptr)

; External-global guards must keep static allocas in entry so the next pass
; instruments them. More than one guard used to silently drop this coverage.
; IR-LABEL: define i32 @external_stack(
; IR: %a = alloca [32 x i8], align 16
; IR: call ptr @llvm.wasm.memtag.randomstore
; IR: call void @escape(ptr %a.tag)
define i32 @external_stack() sanitize_memtag {
entry:
  %a = alloca [32 x i8], align 1
  call void @escape(ptr %a)
  %x = load volatile i32, ptr @external
  %y = icmp eq ptr @weak, null
  %z = zext i1 %y to i32
  %r = add i32 %x, %z
  ret i32 %r
}

; Even a combined tag/store needs retirement on the path that bypasses the
; single explicit lifetime.end.
; IR-LABEL: define void @early_exit(
; IR: early:
; IR-NEXT: call void @llvm.wasm.memtag.store
; IR-NEXT: ret void
; IR: normal:
; IR-NEXT: call void @llvm.wasm.memtag.store
; IR: ret void
define void @early_exit(i1 %exit_early) sanitize_memtag {
entry:
  %a = alloca [32 x i8], align 16
  call void @llvm.lifetime.start.p0(ptr %a)
  call void @escape(ptr %a)
  br i1 %exit_early, label %early, label %normal
early:
  ret void
normal:
  call void @llvm.lifetime.end.p0(ptr %a)
  ret void
}

; A cleanup within the same function must not retire live stack storage.
; IR-LABEL: define void @internal_cleanup(
; IR: inner:
; IR: call void @escape(ptr %a.tag)
; IR-NOT: llvm.wasm.memtag.store
; IR: cleanupret from %inner.pad unwind label %outer
; IR: outer:
; IR: call void @escape(ptr %a.tag)
; IR-NEXT: call void @llvm.wasm.memtag.store
; IR-NEXT: cleanupret from %outer.pad unwind to caller
; ASM-LABEL: internal_cleanup:
; ASM: global.get __stack_pointer
; ASM: memtag.store 0
; ASM: global.set __stack_pointer
define void @internal_cleanup() sanitize_memtag personality ptr @__gxx_wasm_personality_v0 {
entry:
  %a = alloca [32 x i8], align 16
  invoke void @escape(ptr %a) to label %done unwind label %inner
done:
  ret void
inner:
  %inner.pad = cleanuppad within none []
  call void @escape(ptr %a) [ "funclet"(token %inner.pad) ]
  cleanupret from %inner.pad unwind label %outer
outer:
  %outer.pad = cleanuppad within none []
  call void @escape(ptr %a) [ "funclet"(token %outer.pad) ]
  cleanupret from %outer.pad unwind to caller
}
