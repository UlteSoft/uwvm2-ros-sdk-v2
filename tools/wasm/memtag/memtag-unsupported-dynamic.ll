declare void @consume(ptr) nounwind
define void @variable(i32 %n) nounwind sanitize_memtag {
  %a = alloca i8, i32 %n, align 16
  call void @consume(ptr %a)
  ret void
}
