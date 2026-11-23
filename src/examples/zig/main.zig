//! Read the scene ABI major version through the installed Zig binding.
const scene = @import("uwrosv2");

export fn _start() void {
    if (scene.capability.abi() != 2) @trap();
}
