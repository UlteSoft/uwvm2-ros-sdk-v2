declare void @may_unwind(ptr)
define void @exceptional() sanitize_memtag {
  %a = alloca [32 x i8], align 16
  call void @may_unwind(ptr %a)
  ret void
}
