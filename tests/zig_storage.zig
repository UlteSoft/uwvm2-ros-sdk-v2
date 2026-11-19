//! Check that independently addressable Zig storage receives distinct tags.
var global_left: [48]u8 = @splat(19);
var global_right: [48]u8 = @splat(23);
const read_only: [48]u8 = @splat(7);
const shift = if (@sizeOf(usize) == 4) 28 else 56;

noinline fn distinct(left: *volatile u8, right: *volatile u8, expect_left: u8, expect_right: u8) void {
    const left_tag = @intFromPtr(left) >> shift;
    const right_tag = @intFromPtr(right) >> shift;
    if (left_tag == 0 or left_tag == right_tag or right_tag == 0) @trap();
    if (left.* != expect_left or right.* != expect_right) @trap();
}

noinline fn checkReadOnly(address: *const volatile u8) void {
    if (@intFromPtr(address) >> shift == 0 or address.* != 7) @trap();
}

export fn _start() void {
    var stack_left: [48]u8 = @splat(11);
    var stack_right: [48]u8 = @splat(13);
    distinct(&global_left[0], &global_right[0], 19, 23);
    distinct(&stack_left[0], &stack_right[0], 11, 13);
    checkReadOnly(&read_only[0]);
}
