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
    0x00, 0x01, 0x00, 0x00, 0x00, 0x01
];

const BIG_ENDIAN: &[u8] = &[
    0x00, 0x00, 0x00, 0x00, 0x00, 0x01
];

fn check(data: &[u8]) {
    if read_is_enable(data) != Some(false) || read_is_enable(&data[..data.len() - 1]).is_some() { unreachable() }
    if read_is_connected(data) != Some(true) || read_is_connected(&data[..data.len() - 1]).is_some() { unreachable() }
}

#[no_mangle]
pub extern "C" fn _start() {
    check(black_box(EXAMPLE));
    check(black_box(BIG_ENDIAN));
}
