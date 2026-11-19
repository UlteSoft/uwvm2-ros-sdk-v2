//! Require the VM to reject a changed tag on otherwise valid stack storage.
const shift = if (@sizeOf(usize) == 4) 28 else 56;

noinline fn read(address: usize) u8 {
    const buffer: *const volatile u8 = @ptrFromInt(address);
    return buffer.*;
}

export fn _start() void {
    var storage: [48]u8 = @splat(53);
    const address = @intFromPtr(&storage[0]);
    if (read(address) != 53) @trap();
    // This operation alters just one tag bit. The physical byte stays in bounds.
    _ = read(address ^ (@as(usize, 1) << shift));
}
