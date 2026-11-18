; Exercise full, adjacent zero initialization of an escaping stack allocation.
; The tagged object is observable, so StackSafety cannot elide its tag.
; CHECK validates the stack-tagging IR, ASM validates the fused opcode, and
; UNFUSED checks the same input with the producer's fusion switch disabled.
target triple = "wasm32-unknown-unknown"

declare void @llvm.lifetime.start.p0(ptr)
declare void @llvm.lifetime.end.p0(ptr)
declare void @llvm.memset.p0.i32(ptr, i8, i32, i1 immarg)
declare void @observe(ptr)

; CHECK-LABEL: define void @exact(
; CHECK: %a.tag = call ptr @llvm.wasm.memtag.randomstorez.i{{32|64}}(i32 0, ptr %a, i{{32|64}} 256)
; CHECK-NOT: call void @llvm.memset
; CHECK: call void @observe(ptr %a.tag)
; CHECK: call void @llvm.wasm.memtag.store.i{{32|64}}(i32 0, ptr %a, i{{32|64}} 256)
; CHECK: ret void
; UNFUSED-LABEL: define void @exact(
; UNFUSED: %a.tag = call ptr @llvm.wasm.memtag.randomstore.i{{32|64}}
; UNFUSED: call void @llvm.memset.p0.i32(ptr %a.tag, i8 0, i32 256, i1 false)
; UNFUSED: call void @observe(ptr %a.tag)
; ASM-LABEL: exact:
; ASM: memtag.randomstorez 0
; ASM: call observe
; ASM: memtag.store 0
define void @exact(i32 %size) sanitize_memtag {
entry:
  %a = alloca [256 x i8], align 16
  call void @llvm.lifetime.start.p0(ptr %a)
  call void @llvm.memset.p0.i32(ptr %a, i8 0, i32 256, i1 false)
  call void @observe(ptr %a)
  call void @llvm.lifetime.end.p0(ptr %a)
  ret void
}

; CHECK-LABEL: define void @partial(
; CHECK: %a.tag = call ptr @llvm.wasm.memtag.randomstore.i{{32|64}}(
; CHECK: call void @llvm.memset.p0.i32(ptr %a.tag, i8 0, i32 240, i1 false)
; CHECK: call void @observe(ptr %a.tag)
; CHECK: call void @llvm.wasm.memtag.store.i{{32|64}}(i32 0, ptr %a, i{{32|64}} 256)
; CHECK: ret void
define void @partial(i32 %size) sanitize_memtag {
entry:
  %a = alloca [256 x i8], align 16
  call void @llvm.lifetime.start.p0(ptr %a)
  call void @llvm.memset.p0.i32(ptr %a, i8 0, i32 240, i1 false)
  call void @observe(ptr %a)
  call void @llvm.lifetime.end.p0(ptr %a)
  ret void
}

; CHECK-LABEL: define void @nonzero(
; CHECK: %a.tag = call ptr @llvm.wasm.memtag.randomstore.i{{32|64}}(
; CHECK: call void @llvm.memset.p0.i32(ptr %a.tag, i8 1, i32 256, i1 false)
; CHECK: call void @observe(ptr %a.tag)
; CHECK: call void @llvm.wasm.memtag.store.i{{32|64}}(i32 0, ptr %a, i{{32|64}} 256)
; CHECK: ret void
define void @nonzero(i32 %size) sanitize_memtag {
entry:
  %a = alloca [256 x i8], align 16
  call void @llvm.lifetime.start.p0(ptr %a)
  call void @llvm.memset.p0.i32(ptr %a, i8 1, i32 256, i1 false)
  call void @observe(ptr %a)
  call void @llvm.lifetime.end.p0(ptr %a)
  ret void
}

; CHECK-LABEL: define void @volatile_clear(
; CHECK: %a.tag = call ptr @llvm.wasm.memtag.randomstore.i{{32|64}}(
; CHECK: call void @llvm.memset.p0.i32(ptr %a.tag, i8 0, i32 256, i1 true)
; CHECK: call void @observe(ptr %a.tag)
; CHECK: call void @llvm.wasm.memtag.store.i{{32|64}}(i32 0, ptr %a, i{{32|64}} 256)
; CHECK: ret void
define void @volatile_clear(i32 %size) sanitize_memtag {
entry:
  %a = alloca [256 x i8], align 16
  call void @llvm.lifetime.start.p0(ptr %a)
  call void @llvm.memset.p0.i32(ptr %a, i8 0, i32 256, i1 true)
  call void @observe(ptr %a)
  call void @llvm.lifetime.end.p0(ptr %a)
  ret void
}

; CHECK-LABEL: define void @runtime_size(
; CHECK: %a.tag = call ptr @llvm.wasm.memtag.randomstore.i{{32|64}}(
; CHECK: call void @llvm.memset.p0.i32(ptr %a.tag, i8 0, i32 %size, i1 false)
; CHECK: call void @observe(ptr %a.tag)
; CHECK: call void @llvm.wasm.memtag.store.i{{32|64}}(i32 0, ptr %a, i{{32|64}} 256)
; CHECK: ret void
define void @runtime_size(i32 %size) sanitize_memtag {
entry:
  %a = alloca [256 x i8], align 16
  call void @llvm.lifetime.start.p0(ptr %a)
  call void @llvm.memset.p0.i32(ptr %a, i8 0, i32 %size, i1 false)
  call void @observe(ptr %a)
  call void @llvm.lifetime.end.p0(ptr %a)
  ret void
}

; CHECK-LABEL: define void @intervening_load(
; CHECK: %a.tag = call ptr @llvm.wasm.memtag.randomstore.i{{32|64}}(
; CHECK: %prior = load volatile i8, ptr %a.tag
; CHECK: call void @llvm.memset.p0.i32(ptr %a.tag, i8 0, i32 256, i1 false)
; CHECK: call void @observe(ptr %a.tag)
; CHECK: call void @llvm.wasm.memtag.store.i{{32|64}}(i32 0, ptr %a, i{{32|64}} 256)
; CHECK: ret void
define void @intervening_load(i32 %size) sanitize_memtag {
entry:
  %a = alloca [256 x i8], align 16
  call void @llvm.lifetime.start.p0(ptr %a)
  %prior = load volatile i8, ptr %a
  call void @llvm.memset.p0.i32(ptr %a, i8 0, i32 256, i1 false)
  call void @observe(ptr %a)
  call void @llvm.lifetime.end.p0(ptr %a)
  ret void
}

; CHECK-LABEL: define void @intervening_call(
; CHECK: %a.tag = call ptr @llvm.wasm.memtag.randomstore.i{{32|64}}(
; CHECK: call void @observe(ptr %a.tag)
; CHECK: call void @llvm.memset.p0.i32(ptr %a.tag, i8 0, i32 256, i1 false)
; CHECK: call void @observe(ptr %a.tag)
; CHECK: call void @llvm.wasm.memtag.store.i{{32|64}}(i32 0, ptr %a, i{{32|64}} 256)
; CHECK: ret void
define void @intervening_call(i32 %size) sanitize_memtag {
entry:
  %a = alloca [256 x i8], align 16
  call void @llvm.lifetime.start.p0(ptr %a)
  call void @observe(ptr %a)
  call void @llvm.memset.p0.i32(ptr %a, i8 0, i32 256, i1 false)
  call void @observe(ptr %a)
  call void @llvm.lifetime.end.p0(ptr %a)
  ret void
}

; CHECK-LABEL: define void @other_object(
; CHECK: %a.tag = call ptr @llvm.wasm.memtag.randomstore.i{{32|64}}(
; CHECK: call void @llvm.memset.p0.i32(ptr %b, i8 0, i32 256, i1 false)
; CHECK: call void @observe(ptr %a.tag)
; CHECK: call void @llvm.wasm.memtag.store.i{{32|64}}(i32 0, ptr %a, i{{32|64}} 256)
; CHECK: ret void
define void @other_object(i32 %size) sanitize_memtag {
entry:
  %a = alloca [256 x i8], align 16
  %b = alloca [256 x i8], align 16
  call void @llvm.lifetime.start.p0(ptr %a)
  call void @llvm.memset.p0.i32(ptr %b, i8 0, i32 256, i1 false)
  call void @observe(ptr %a)
  call void @llvm.lifetime.end.p0(ptr %a)
  ret void
}

; CHECK-LABEL: define void @second_lifetime(
; CHECK: %a.tag = call ptr @llvm.wasm.memtag.random(
; CHECK: call void @llvm.memset.p0.i32(ptr %a.tag, i8 0, i32 256, i1 false)
; CHECK: call void @observe(ptr %a.tag)
; CHECK: call void @llvm.wasm.memtag.store.i{{32|64}}(i32 0, ptr %a, i{{32|64}} 256)
; CHECK: call void @observe(ptr %a.tag)
; CHECK: call void @llvm.wasm.memtag.store.i{{32|64}}(i32 0, ptr %a, i{{32|64}} 256)
; CHECK: ret void
define void @second_lifetime(i32 %size) sanitize_memtag {
entry:
  %a = alloca [256 x i8], align 16
  call void @llvm.lifetime.start.p0(ptr %a)
  call void @llvm.memset.p0.i32(ptr %a, i8 0, i32 256, i1 false)
  call void @observe(ptr %a)
  call void @llvm.lifetime.end.p0(ptr %a)
  call void @llvm.lifetime.start.p0(ptr %a)
  call void @observe(ptr %a)
  call void @llvm.lifetime.end.p0(ptr %a)
  ret void
}
