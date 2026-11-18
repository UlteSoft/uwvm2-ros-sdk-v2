; CHECK-LABEL: define internal i8 @read_byte(
; CHECK: phi ptr [ [[ADDRESS:%[a-zA-Z0-9_.]+]], %[[PRED:[a-zA-Z0-9_.]+]] ], [ [[ADDRESS]], %[[PRED]] ]
; Two switch cases reach the same PHI from the same predecessor. The merged
; value contains an interior address, which the Wasm backend materializes.
@left = internal global [4 x i8] c"ABCD", sanitize_memtag
@right = internal constant [4 x i8] c"PQRS", sanitize_memtag, !wasm.memtag.object !0
@notice = internal global i32 0
declare void @llvm.trap()

define internal i8 @read_byte(i32 %which) sanitize_memtag noinline nounwind {
entry:
  switch i32 %which, label %else [
    i32 1, label %join
    i32 7, label %alternate
    i32 9, label %join
  ]
else:
  store volatile i32 11, ptr @notice
  br label %join
alternate:
  store volatile i32 7, ptr @notice
  br label %join
join:
  %address = phi ptr [
    getelementptr ([4 x i8], ptr @left, i32 0, i32 1), %entry ], [
    getelementptr ([4 x i8], ptr @left, i32 0, i32 1), %entry ], [
    getelementptr ([4 x i8], ptr @right, i32 0, i32 2), %else ], [
    getelementptr ([4 x i8], ptr @right, i32 0, i32 3), %alternate ]
  %value = load volatile i8, ptr %address
  ret i8 %value
}

define void @_start() nounwind {
  %a = call i8 @read_byte(i32 1)
  %b = call i8 @read_byte(i32 9)
  %c = call i8 @read_byte(i32 7)
  %d = call i8 @read_byte(i32 0)
  %aok = icmp eq i8 %a, 66
  %bok = icmp eq i8 %b, 66
  %cok = icmp eq i8 %c, 83
  %dok = icmp eq i8 %d, 82
  %p = and i1 %aok, %bok
  %q = and i1 %cok, %dok
  %r = and i1 %p, %q
  br i1 %r, label %done, label %failed
failed:
  call void @llvm.trap()
  unreachable
done:
  ret void
}
!0 = !{}
