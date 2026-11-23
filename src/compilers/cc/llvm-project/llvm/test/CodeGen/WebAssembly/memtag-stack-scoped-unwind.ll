; RUN: llc -mtriple=wasm32 -wasm-enable-eh -wasm-use-legacy-eh=false -exception-model=wasm -mattr=+memtag,+reference-types,+exception-handling -verify-machineinstrs -verify-each -O3 %s -o - | FileCheck %s
; RUN: llc -mtriple=wasm64 -wasm-enable-eh -wasm-use-legacy-eh=false -exception-model=wasm -mattr=+memtag,+reference-types,+exception-handling -verify-machineinstrs -verify-each -O3 %s -o - | FileCheck %s
; CHECK-LABEL: frame:
; CHECK: memtag.reserve
; CHECK: memtag.activate
; CHECK: try_table {{.*}}catch_all_ref
; CHECK: memtag.release
; CHECK: throw_ref
; CHECK-LABEL: nested:
; CHECK: memtag.claim
; CHECK: try_table
; CHECK: memtag.release

target triple = "wasm32-unknown-unknown"
@count = global i32 0, align 4
@previous = global ptr null, align 16

declare i32 @__gxx_wasm_personality_v0(...)
declare void @llvm.wasm.throw(i32,ptr)
declare ptr @llvm.wasm.get.exception(token)
declare i32 @llvm.wasm.get.ehselector(token)
declare void @llvm.wasm.rethrow()
declare void @llvm.lifetime.start.p0(ptr)
declare void @llvm.lifetime.end.p0(ptr)
declare void @llvm.trap()
declare ptr @llvm.wasm.memtag.untag(i32 immarg,ptr)
define void @raise_or_continue(ptr %p, i1 %shouldthrow) noinline {
  %raw = call ptr @llvm.wasm.memtag.untag(i32 0,ptr %p)
  %old = load volatile ptr,ptr @previous
  store volatile ptr %raw,ptr @previous
  %initial = icmp eq ptr %old,null
  %same = icmp eq ptr %old,%raw
  %correct = or i1 %initial,%same
  br i1 %correct,label %dispatch,label %bad
dispatch:
  br i1 %shouldthrow,label %throw,label %return
bad:
  call void @llvm.trap()
  unreachable
throw:
  call void @llvm.wasm.throw(i32 0,ptr null)
  unreachable
return:
  ret void
}

define void @frame(i1 %throws) noinline sanitize_memtag {
  %x = alloca [16 x i8], align 16
  call void @llvm.lifetime.start.p0(ptr %x)
  store volatile i8 28,ptr %x
  call void @raise_or_continue(ptr %x,i1 %throws)
  %v = load volatile i8,ptr %x
  %ok = icmp eq i8 %v,28
  call void @llvm.lifetime.end.p0(ptr %x)
  br i1 %ok,label %return,label %bad
bad:
  call void @llvm.trap()
  unreachable
return:
  ret void
}

; A frame with a real catchswitch and explicit rethrow must allow the original
; exception to escape. Its separate stack object stays live in the handler.
define void @nested(i1 %shouldthrow) noinline sanitize_memtag personality ptr @__gxx_wasm_personality_v0 {
  %y = alloca [16 x i8],align 16
  store volatile i8 91,ptr %y
  invoke void @frame(i1 %shouldthrow) to label %normal unwind label %dispatch
dispatch:
  %cs = catchswitch within none [label %handler] unwind to caller
handler:
  %cp = catchpad within %cs [ptr null]
  %ex = call ptr @llvm.wasm.get.exception(token %cp)
  %sel = call i32 @llvm.wasm.get.ehselector(token %cp)
  %v = load volatile i8,ptr %y
  %ok = icmp eq i8 %v,91
  br i1 %ok,label %again,label %bad
again:
  call void @llvm.wasm.rethrow() [ "funclet"(token %cp) ]
  unreachable
bad:
  call void @llvm.trap()
  unreachable
normal:
  ret void
}

define void @_start() noinline personality ptr @__gxx_wasm_personality_v0 {
  br label %loop
loop:
  %i = phi i32 [0,%0],[%next,%caught]
  invoke void @nested(i1 true) to label %fail unwind label %dispatch
dispatch:
  %cs = catchswitch within none [label %handler] unwind to caller
handler:
  %pad = catchpad within %cs [ptr null]
  %ex = call ptr @llvm.wasm.get.exception(token %pad)
  %selector = call i32 @llvm.wasm.get.ehselector(token %pad)
  catchret from %pad to label %caught
caught:
  call void @nested(i1 false)
  %next = add i32 %i,1
  %repeat = icmp ult i32 %next,32
  br i1 %repeat,label %loop,label %end
fail:
  call void @llvm.trap()
  unreachable
end:
  ret void
}
