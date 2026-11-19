//! Check both grants on an isolated platform driver connection.
extern "uwvm_ros_v2" fn @"capability.open"(memory: u32, address: u64, length: u64, result: u64) u32;
extern "uwvm_ros_v2" fn @"capability.close"(handle: u64) u32;
extern "uwvm_ros_v2" fn @"driver.connect"(handle: u64, memory: u32, request: u64, size: u64, reply: u64, cap: u64, written: u64) u32;

const alias = "arm";

export fn _start() void {
    var handle: u64 = 0;
    var reply: u64 = 0x4321;
    var written: u64 = 0x1234;
    if (@"capability.open"(0, @intFromPtr(alias.ptr), alias.len, @intFromPtr(&handle)) != 0) @trap();
    if (@"driver.connect"(handle, 0, 0, 0, @intFromPtr(&reply), 8, @intFromPtr(&written)) != 13) @trap();
    if (reply != 0x4321 or written != 0x1234 or @"capability.close"(handle) != 0) @trap();
}
