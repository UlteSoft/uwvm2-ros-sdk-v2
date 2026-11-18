declare void @llvm.lifetime.start.p0(ptr)
declare void @llvm.lifetime.end.p0(ptr)
declare void @observe(ptr) nounwind
declare void @pair(ptr, ptr) nounwind

; CHECK-LABEL: define {{.*}}@join(
; CHECK: call ptr @llvm.wasm.memtag.reserve.
; CHECK: left:
; CHECK: call ptr @llvm.wasm.memtag.activate.
; CHECK: call void @observe
; CHECK: right:
; CHECK: call ptr @llvm.wasm.memtag.activate.
; CHECK: call void @observe
; CHECK: join:
; CHECK: phi ptr
; CHECK: call void @observe
; CHECK: call ptr @llvm.wasm.memtag.release.
define void @join(i1 %side) sanitize_memtag {
entry:
  %obj = alloca [64 x i8], align 16
  br i1 %side, label %left, label %right
left:
  call void @llvm.lifetime.start.p0(ptr %obj)
  call void @observe(ptr %obj)
  br label %join
right:
  call void @llvm.lifetime.start.p0(ptr %obj)
  call void @observe(ptr %obj)
  br label %join
join:
  call void @observe(ptr %obj)
  call void @llvm.lifetime.end.p0(ptr %obj)
  ret void
}

; CHECK-LABEL: define {{.*}}@loop(
; CHECK: call ptr @llvm.wasm.memtag.reserve.
; CHECK: body:
; CHECK: %[[CUR:[^ ]+]] = call ptr @llvm.wasm.memtag.activate.
; CHECK: %previous = load volatile ptr, ptr %saved
; CHECK: %[[FIELD:[^ ]+]] = getelementptr i8, ptr %[[CUR]], i32 16
; CHECK: call void @pair(ptr %previous, ptr %[[FIELD]])
; CHECK: call ptr @llvm.wasm.memtag.release.
; CHECK: call ptr @llvm.wasm.memtag.reserve.
define void @loop(ptr %saved, i32 %n) sanitize_memtag {
entry:
  %obj = alloca [64 x i8], align 16
  %field = getelementptr i8, ptr %obj, i32 16
  br label %body
body:
  %i = phi i32 [0, %entry], [%next, %body]
  call void @llvm.lifetime.start.p0(ptr %obj)
  %previous = load volatile ptr, ptr %saved
  call void @pair(ptr %previous, ptr %field)
  store volatile ptr %field, ptr %saved
  call void @llvm.lifetime.end.p0(ptr %obj)
  %next = add i32 %i, 1
  %again = icmp ult i32 %next, %n
  br i1 %again, label %body, label %exit
exit:
  ret void
}

; CHECK-LABEL: define {{.*}}@early(
; CHECK: %[[A:[^ ]+]] = call ptr @llvm.wasm.memtag.reserve.
; CHECK: call void @observe(ptr %[[A]])
; CHECK: %[[ACT:[^ ]+]] = call ptr @llvm.wasm.memtag.activate.i{{32|64}}(i32 0, ptr %[[A]],
; CHECK: call void @observe(ptr %[[ACT]])
; CHECK: call ptr @llvm.wasm.memtag.release.
; CHECK: %[[B:[^ ]+]] = call ptr @llvm.wasm.memtag.reserve.
; CHECK: call void @observe(ptr %[[B]])
; CHECK: call ptr @llvm.wasm.memtag.activate.
define void @early() sanitize_memtag {
entry:
  %obj = alloca [64 x i8], align 16
  call void @observe(ptr %obj)
  call void @llvm.lifetime.start.p0(ptr %obj)
  call void @observe(ptr %obj)
  call void @llvm.lifetime.end.p0(ptr %obj)
  call void @observe(ptr %obj)
  call void @llvm.lifetime.start.p0(ptr %obj)
  call void @observe(ptr %obj)
  call void @llvm.lifetime.end.p0(ptr %obj)
  ret void
}

; CHECK-LABEL: define {{.*}}@mixed(
; CHECK: call ptr @llvm.wasm.memtag.reserve.
; CHECK: branch:
; CHECK: call ptr @llvm.wasm.memtag.activate.
; CHECK: join:
; CHECK: phi
; CHECK: br i1
; CHECK: call ptr @llvm.wasm.memtag.release.
; CHECK: call ptr @llvm.wasm.memtag.claim.
; CHECK: call ptr @llvm.wasm.memtag.activate.
; CHECK: call void @pair(ptr %edge, ptr %
define void @mixed(i1 %another) sanitize_memtag {
entry:
  %obj = alloca [64 x i8], align 16
  call void @observe(ptr %obj)
  br i1 %another, label %branch, label %join
branch:
  call void @llvm.lifetime.start.p0(ptr %obj)
  call void @observe(ptr %obj)
  br label %join
join:
  %edge = phi ptr [%obj, %entry], [%obj, %branch]
  call void @llvm.lifetime.start.p0(ptr %obj)
  call void @pair(ptr %edge, ptr %obj)
  call void @llvm.lifetime.end.p0(ptr %obj)
  ret void
}
