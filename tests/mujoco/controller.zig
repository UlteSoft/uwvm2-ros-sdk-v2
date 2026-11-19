//! Exercise the signed Zig controller and isolated driver through the typed ABI.
extern "uwvm_ros_v2" fn @"capability.open"(memory: u32, address: u64, length: u64, result: u64) u32;
extern "uwvm_ros_v2" fn @"driver.connect"(handle: u64, memory: u32, request: u64, size: u64, reply: u64, cap: u64, written: u64) u32;
extern "uwvm_ros_v2" fn @"driver.submit"(handle: u64, memory: u32, request: u64, size: u64, reply: u64, cap: u64, written: u64) u32;
extern "uwvm_ros_v2" fn @"driver.result"(handle: u64, memory: u32, request: u64, size: u64, reply: u64, cap: u64, written: u64) u32;
extern "uwvm_ros_v2" fn @"driver.describe"(handle: u64, memory: u32, request: u64, size: u64, reply: u64, cap: u64, written: u64) u32;
extern "uwvm_ros_v2" fn @"driver.disconnect"(handle: u64, memory: u32, request: u64, size: u64, reply: u64, cap: u64, written: u64) u32;

const alias = "joint";
var joint: u64 = 0;
var used: u64 = 0;
var sequence: u64 = 0;
var response: [64]u64 = @splat(0);
var request = template;

fn invoke(comptime operation: anytype, address: u64, length: u64) u32 {
    return operation(joint, 0, address, length, @intFromPtr(&response), @sizeOf(@TypeOf(response)), @intFromPtr(&used));
}

fn poll(comptime operation: anytype, address: u64, length: u64) u32 {
    for (0..10_000_000) |_| {
        const status = invoke(operation, address, length);
        if (status != 11) return status;
    }
    return 11;
}

fn put64(offset: usize, value: u64) void {
    inline for (0..8) |i| {
        request[offset + i] = @truncate(value >> (i * 8));
    }
}

export fn _start() void {
    if (@"capability.open"(0, @intFromPtr(alias.ptr), alias.len, @intFromPtr(&joint)) != 0) @trap();
    if (poll(@"driver.connect", 0, 0) != 0) @trap();

    sequence = 1;
    while (sequence <= steps) : (sequence += 1) {
        put64(0, sequence);
        put64(32, sequence);
        if (success) {
            put64(target_offset, if (sequence % 2 != 0) 0x3fe0000000000000 else 0xbfe0000000000000);
        }
        if (poll(@"driver.submit", @intFromPtr(&request), request.len) != 0) @trap();
        const status = poll(@"driver.result", @intFromPtr(&sequence), @sizeOf(u64));
        if (crash) {
            if (status != 5 and status != 13) @trap();
            if (invoke(@"driver.describe", 0, 0) != 0) @trap();
            if (used < 32 or response[0] != 6 or response[3] != 1) @trap();
        } else {
            if (status != 0 or used < 24 or response[0] != @as(u64, if (success) 0 else 13)) @trap();
            if (response[2] != sequence) @trap();
        }
    }
    if (invoke(@"driver.disconnect", 0, 0) != 0) @trap();
}
