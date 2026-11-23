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
    0x2d, 0x01, 0x00, 0x00, 0x80, 0x17, 0xb4, 0x2c
];

fn check(data: &[u8]) {
    if read_data_sec(data) != Some(301) || read_data_sec(&data[..data.len() - 1]).is_some() { unreachable() }
    if read_data_nsec(data) != Some(750000000) || read_data_nsec(&data[..data.len() - 1]).is_some() { unreachable() }
}

#[no_mangle]
pub extern "C" fn _start() {
    check(black_box(EXAMPLE));
}
