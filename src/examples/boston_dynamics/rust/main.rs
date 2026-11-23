#![no_std]
#[cfg(target_arch = "wasm32")]
use core::arch::wasm32::unreachable;
#[cfg(target_arch = "wasm64")]
use wros_runtime::abort as unreachable;
use core::{hint::black_box, panic::PanicInfo};
use wros_observation::*;

#[panic_handler]
fn panic(_: &PanicInfo) -> ! { unreachable() }

// Constructed wire examples for the pinned upstream definition.
const EXAMPLE: &[u8] = &[
    0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
    0x00, 0x00, 0x00, 0xbf, 0x00, 0x00, 0xa0, 0x3f, 0x00, 0x00, 0x40, 0x3f
];

fn check(data: &[u8]) {
    if read_x(data, 1) != Some(-0.5) || read_x(&data[..data.len() - 1], 1).is_some() { unreachable() }
    if read_x(data, usize::MAX).is_some() { unreachable() }
    if read_y(data, 1) != Some(1.25) || read_y(&data[..data.len() - 1], 1).is_some() { unreachable() }
    if read_y(data, usize::MAX).is_some() { unreachable() }
    if read_z(data, 1) != Some(0.75) || read_z(&data[..data.len() - 1], 1).is_some() { unreachable() }
    if read_z(data, usize::MAX).is_some() { unreachable() }
}

#[no_mangle]
pub extern "C" fn _start() {
    check(black_box(EXAMPLE));
}
