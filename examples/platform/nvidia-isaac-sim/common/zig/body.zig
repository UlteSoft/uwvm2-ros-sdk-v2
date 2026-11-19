//! Query the installed ROS ABI before starting the controller.
const scene = @import("wros_scene.zig");

export fn _start() void {
    if (scene.wr_abi() != 2) @trap();
}
