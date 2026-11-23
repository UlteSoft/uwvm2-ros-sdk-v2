// A module-owned exception tag for terminal TinyGo panics.
.globl u2ros_tinygo_panic_tag
.hidden u2ros_tinygo_panic_tag
.tagtype u2ros_tinygo_panic_tag i32
u2ros_tinygo_panic_tag:

.globl u2ros_tinygo_panic
.hidden u2ros_tinygo_panic
.type u2ros_tinygo_panic,@function
u2ros_tinygo_panic:
    .functype u2ros_tinygo_panic () -> ()
    i32.const 2
    throw u2ros_tinygo_panic_tag
    end_function
