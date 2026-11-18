declare void @consume(ptr) nounwind
declare void @llvm.lifetime.start.p0(ptr)
declare void @llvm.lifetime.end.p0(ptr)
declare void @llvm.memset.p0.i32(ptr, i8, i32, i1)
; CHECK-LABEL: define {{.*}}@known_bounded(
; CHECK: call ptr @llvm.wasm.memtag.claim.
; CHECK: store volatile i32
; CHECK: load volatile i32
; CHECK: call ptr @llvm.wasm.memtag.release.
; CHECK: ret i32
define i32 @known_bounded(i32 %x) nounwind sanitize_memtag {
  %a = alloca [32 x i32], align 16
  %sub = and i32 %x, 31
  %p = getelementptr [32 x i32], ptr %a, i32 0, i32 %sub
  store volatile i32 42, ptr %p
  %r = load volatile i32, ptr %p
  ret i32 %r
}
; CHECK-LABEL: define {{.*}}@reg(
; CHECK-NOT: alloca
; CHECK-NOT: llvm.wasm.memtag.
; CHECK: ret i32 %x
define i32 @reg(i32 %x) nounwind sanitize_memtag {
  %a = alloca i32
  store i32 %x, ptr %a
  %r = load i32, ptr %a
  ret i32 %r
}
; CHECK-LABEL: define {{.*}}@normal(
; CHECK: call ptr @llvm.wasm.memtag.claimz.
; CHECK: call void @consume
; CHECK: call ptr @llvm.wasm.memtag.release.
; CHECK: ret void
define void @normal() nounwind sanitize_memtag {
  %a = alloca [64 x i8], align 16
  call void @llvm.lifetime.start.p0(ptr %a)
  call void @llvm.memset.p0.i32(ptr %a, i8 0, i32 64, i1 false)
  call void @consume(ptr %a)
  call void @llvm.lifetime.end.p0(ptr %a)
  ret void
}
; CHECK-LABEL: define {{.*}}@early(
; CHECK: call ptr @llvm.wasm.memtag.reserve.
; CHECK: call void @consume
; CHECK: call ptr @llvm.wasm.memtag.activate.
; CHECK: call void @consume
; CHECK: br i1
; CHECK: call ptr @llvm.wasm.memtag.release.
; CHECK: ret void
define void @early(i1 %again) nounwind sanitize_memtag {
  %a = alloca [64 x i8], align 16
  call void @consume(ptr %a)
  br i1 %again, label %first, label %join
first:
  call void @llvm.lifetime.start.p0(ptr %a)
  call void @consume(ptr %a)
  br label %join
join:
  call void @llvm.lifetime.start.p0(ptr %a)
  call void @consume(ptr %a)
  call void @llvm.lifetime.end.p0(ptr %a)
  ret void
}
declare void @opaque_pair(ptr, ptr) nounwind
; CHECK-LABEL: define {{.*}}@pair_escapes_together(
; CHECK-DAG: call ptr @llvm.wasm.memtag.claim.i{{32|64}}(i32 0, ptr %a,
; CHECK-DAG: call ptr @llvm.wasm.memtag.reserve.i{{32|64}}(i32 0, ptr %b,
; CHECK: call void @opaque_pair
; CHECK: call ptr @llvm.wasm.memtag.activate.
; CHECK: call void @opaque_pair
; CHECK: call ptr @llvm.wasm.memtag.release.
; CHECK: ret void
define void @pair_escapes_together() nounwind sanitize_memtag {
  %a = alloca [16 x i8], align 16
  %b = alloca [16 x i8], align 16
  call void @llvm.lifetime.start.p0(ptr %a)
  call void @opaque_pair(ptr %a, ptr %b)
  call void @llvm.lifetime.start.p0(ptr %b)
  call void @opaque_pair(ptr %a, ptr %b)
  call void @llvm.lifetime.end.p0(ptr %b)
  call void @llvm.lifetime.end.p0(ptr %a)
  ret void
}

; CHECK-LABEL: define void @initially_live(
; CHECK: call ptr @llvm.wasm.memtag.claim.
; CHECK: call void @consume
; CHECK: call ptr @llvm.wasm.memtag.release.
; CHECK: call ptr @llvm.wasm.memtag.reserve.
; CHECK-NOT: call void @llvm.lifetime.end
; CHECK: call ptr @llvm.wasm.memtag.release.
; CHECK: ret void
define void @initially_live() nounwind sanitize_memtag {
  %obj = alloca [16 x i8], align 16
  call void @consume(ptr %obj)
  call void @llvm.lifetime.end.p0(ptr %obj)
  call void @llvm.lifetime.end.p0(ptr %obj)
  ret void
}
