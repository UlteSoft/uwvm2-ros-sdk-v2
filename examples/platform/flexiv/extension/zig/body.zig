//! Check both grants on an isolated platform driver connection.
const scene = @import("wros_scene.zig");

const alias = "arm";

export fn _start() void {
    var handle: u64 = 0;
    var reply: u64 = 0x4321;
    var written: u64 = 0x1234;
    if (scene.wr_capability_open(0, @intFromPtr(alias.ptr), alias.len, @intFromPtr(&handle)) != 0) @trap();
    if (scene.wr_driver_connect(handle, 0, 0, 0, @intFromPtr(&reply), 8, @intFromPtr(&written)) != 13) @trap();
    if (reply != 0x4321 or written != 0x1234 or scene.wr_capability_close(handle) != 0) @trap();
}
