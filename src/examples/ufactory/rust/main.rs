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
    0x01, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0xa0, 0x3f,
    0x00, 0x00, 0x60, 0x40
];

fn check(data: &[u8]) {
    if read_digital_1(data) != Some(1) || read_digital_1(&data[..data.len() - 1]).is_some() { unreachable() }
    if read_digital_2(data) != Some(0) || read_digital_2(&data[..data.len() - 1]).is_some() { unreachable() }
    if read_analog_1(data) != Some(1.25) || read_analog_1(&data[..data.len() - 1]).is_some() { unreachable() }
    if read_analog_2(data) != Some(3.5) || read_analog_2(&data[..data.len() - 1]).is_some() { unreachable() }
}

#[no_mangle]
pub extern "C" fn _start() {
    check(black_box(EXAMPLE));
}
