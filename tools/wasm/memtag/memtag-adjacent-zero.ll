target triple = "wasm32-unknown-unknown"

declare void @llvm.lifetime.start.p0(ptr)
declare void @llvm.lifetime.end.p0(ptr)
declare void @llvm.memset.p0.i32(ptr, i8, i32, i1 immarg)
declare void @observe(ptr) nounwind

; CHECK-LABEL: define {{.*}}@exact(
; CHECK: call ptr @llvm.wasm.memtag.claimz.
; CHECK: call void @observe
; CHECK: call ptr @llvm.wasm.memtag.release.
; CHECK: ret void
; UNFUSED-LABEL: define void @exact(
; UNFUSED: call ptr @llvm.wasm.memtag.claim.
; UNFUSED: call void @llvm.memset
; UNFUSED: call void @observe
; ASM-LABEL: exact:
; ASM: memtag.claimz 0
; ASM: call observe
; ASM: memtag.release 0
define void @exact(i32 %size) sanitize_memtag {
entry:
  %a = alloca [256 x i8], align 16
  call void @llvm.lifetime.start.p0(ptr %a)
  call void @llvm.memset.p0.i32(ptr %a, i8 0, i32 256, i1 false)
  call void @observe(ptr %a)
  call void @llvm.lifetime.end.p0(ptr %a)
  ret void
}

; CHECK-LABEL: define {{.*}}@partial(
; CHECK: call ptr @llvm.wasm.memtag.claim.
; CHECK: call void @llvm.memset
; CHECK: call void @observe
; CHECK: call ptr @llvm.wasm.memtag.release.
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

; CHECK-LABEL: define {{.*}}@nonzero(
; CHECK: call ptr @llvm.wasm.memtag.claim.
; CHECK: call void @llvm.memset
; CHECK: call void @observe
; CHECK: call ptr @llvm.wasm.memtag.release.
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

; CHECK-LABEL: define {{.*}}@volatile_clear(
; CHECK: call ptr @llvm.wasm.memtag.claim.
; CHECK: call void @llvm.memset
; CHECK: call void @observe
; CHECK: call ptr @llvm.wasm.memtag.release.
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

; CHECK-LABEL: define {{.*}}@runtime_size(
; CHECK: call ptr @llvm.wasm.memtag.claim.
; CHECK: call void @llvm.memset
; CHECK: call void @observe
; CHECK: call ptr @llvm.wasm.memtag.release.
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

; CHECK-LABEL: define {{.*}}@intervening_load(
; CHECK: call ptr @llvm.wasm.memtag.claim.
; CHECK: call void @llvm.memset
; CHECK: call void @observe
; CHECK: call ptr @llvm.wasm.memtag.release.
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

; CHECK-LABEL: define {{.*}}@intervening_call(
; CHECK: call ptr @llvm.wasm.memtag.claim.
; CHECK: call void @llvm.memset
; CHECK: call void @observe
; CHECK: call ptr @llvm.wasm.memtag.release.
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

; CHECK-LABEL: define {{.*}}@other_object(
; CHECK: call ptr @llvm.wasm.memtag.claim.
; CHECK: call void @llvm.memset
; CHECK: call void @observe
; CHECK: call ptr @llvm.wasm.memtag.release.
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

; CHECK-LABEL: define {{.*}}@second_lifetime(
; CHECK: call ptr @llvm.wasm.memtag.reserve.
; CHECK: call ptr @llvm.wasm.memtag.activate.
; CHECK: call void @llvm.memset
; CHECK: call void @observe
; CHECK: call ptr @llvm.wasm.memtag.release.
; CHECK: call ptr @llvm.wasm.memtag.reserve.
; CHECK: call ptr @llvm.wasm.memtag.activate.
; CHECK: call void @observe
; CHECK: call ptr @llvm.wasm.memtag.release.
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
