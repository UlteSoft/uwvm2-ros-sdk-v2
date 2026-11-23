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
    0x0c, 0x02, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
    0x05, 0x00, 0x00, 0x00, 0x66, 0x72, 0x61, 0x6d, 0x65, 0x00, 0x00, 0x00,
    0x00, 0x00, 0x00, 0xe4, 0x3f, 0x05, 0x00, 0x00, 0x00, 0x66, 0x72, 0x61,
    0x6d, 0x65
];

fn check(data: &[u8]) {
    if read_estimate_height(data) != Some(0.625) || read_estimate_height(&data[..data.len() - 1]).is_some() { unreachable() }
    if read_header_seq(data) != Some(524) || read_header_seq(&data[..data.len() - 1]).is_some() { unreachable() }
}

#[no_mangle]
pub extern "C" fn _start() {
    check(black_box(EXAMPLE));
}
