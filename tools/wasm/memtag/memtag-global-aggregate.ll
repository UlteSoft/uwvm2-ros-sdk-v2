; Optimized value operands may contain pointers in vectors and nested aggregate
; constants. Exercise both incoming edges of a PHI across two independent calls.
; The unusual alignment/padding of nested fields is left to the target ABI.
@left = internal constant [4 x i8] c"abcd", sanitize_memtag, !wasm.memtag.object !0
@right = internal global [4 x i8] c"wxyz", sanitize_memtag
%record = type { [2 x ptr], i16, <2 x ptr> }
@stored = internal global %record zeroinitializer
declare void @llvm.trap()

define internal void @publish(i1 %cond) sanitize_memtag noinline nounwind {
entry:
  br i1 %cond, label %left_edge, label %right_edge
left_edge:
  br label %both
right_edge:
  br label %both
both:
  %value = phi %record [
    { [2 x ptr] [ptr null, ptr @left], i16 734,
      <2 x ptr> <ptr getelementptr ([4 x i8], ptr @right, i32 0, i32 2), ptr @right> },
      %left_edge ], [
    { [2 x ptr] [ptr null, ptr @right], i16 801,
      <2 x ptr> <ptr getelementptr ([4 x i8], ptr @left, i32 0, i32 1), ptr @left> },
      %right_edge ]
  store volatile %record %value, ptr @stored
  ret void
}

define internal i1 @check(i1 %cond) noinline nounwind {
  %r = load volatile %record, ptr @stored
  %nullslot = extractvalue %record %r, 0, 0
  %base = extractvalue %record %r, 0, 1
  %n = extractvalue %record %r, 1
  %vec = extractvalue %record %r, 2
  %interior = extractelement <2 x ptr> %vec, i32 0
  %other = extractelement <2 x ptr> %vec, i32 1
  %first = load volatile i8, ptr %base
  %second = load volatile i8, ptr %interior
  %third = load volatile i8, ptr %other
  %e1 = select i1 %cond, i8 97, i8 119
  %e2 = select i1 %cond, i8 121, i8 98
  %e3 = select i1 %cond, i8 119, i8 97
  %en = select i1 %cond, i16 734, i16 801
  %a = icmp eq i8 %first, %e1
  %b = icmp eq i8 %second, %e2
  %c = icmp eq i8 %third, %e3
  %d = icmp eq i16 %n, %en
  %e = icmp eq ptr %nullslot, null
  %ab = and i1 %a, %b
  %cd = and i1 %c, %d
  %abcd = and i1 %ab, %cd
  %ok = and i1 %abcd, %e
  ret i1 %ok
}

define void @_start() {
  call void @publish(i1 true)
  %one = call i1 @check(i1 true)
  call void @publish(i1 false)
  %two = call i1 @check(i1 false)
  %ok = and i1 %one, %two
  br i1 %ok, label %done, label %fail
fail:
  call void @llvm.trap()
  unreachable
done:
  ret void
}
!0 = !{}
