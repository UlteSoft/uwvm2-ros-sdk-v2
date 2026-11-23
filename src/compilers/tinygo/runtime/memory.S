// Plain Go packages may lower LLVM's variable-size intrinsics to these C
// symbols. WebAssembly bulk operations check both complete tagged spans.
.macro copy name
.weak \name
.hidden \name
.type \name,@function
\name:
    .functype \name (i32,i32,i32) -> (i32)
    local.get 0
    local.get 1
    local.get 2
    memory.copy 0, 0
    local.get 0
    end_function
.endm
copy memcpy
copy memmove

.weak memset
.hidden memset
.type memset,@function
memset:
    .functype memset (i32,i32,i32) -> (i32)
    local.get 0
    local.get 1
    local.get 2
    memory.fill 0
    local.get 0
    end_function
