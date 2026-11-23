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
    0x01, 0xff, 0x02
];

fn check(data: &[u8]) {
    if read_status(data) != Some(true) || read_status(&data[..data.len() - 1]).is_some() { unreachable() }
    if read_pin1(data) != Some(-1) || read_pin1(&data[..data.len() - 1]).is_some() { unreachable() }
    if read_pin2(data) != Some(2) || read_pin2(&data[..data.len() - 1]).is_some() { unreachable() }
}

#[no_mangle]
pub extern "C" fn _start() {
    check(black_box(EXAMPLE));
}
