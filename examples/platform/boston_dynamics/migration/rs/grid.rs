//! @brief Port the ROS Noetic Costmap2D cell-index calculation and check non-square map coordinates.
#![no_std]
fn cell(width:u32, x:u32, y:u32) -> u32 { y.wrapping_mul(width).wrapping_add(x) }
#[unsafe(no_mangle)]
pub extern "C" fn _start() {
    if cell(400,7,3) != 1207 || cell(17,16,0) != 16 || cell(9,0,5) != 45 { core::arch::wasm32::unreachable(); }
}
#[panic_handler]
fn panic(_: &core::panic::PanicInfo) -> ! { core::arch::wasm32::unreachable() }
