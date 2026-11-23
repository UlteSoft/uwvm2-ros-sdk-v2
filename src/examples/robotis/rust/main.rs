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
    0x05, 0x00, 0x00, 0x00, 0x66, 0x72, 0x61, 0x6d, 0x65, 0x03, 0x00, 0x00,
    0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
    0x00, 0x97, 0xff, 0xff, 0xff, 0x2c, 0x01, 0x00, 0x00, 0x00, 0x00, 0x44,
    0x41
];

fn check(data: &[u8]) {
    if read_bumper(data) != Some(3) || read_bumper(&data[..data.len() - 1]).is_some() { unreachable() }
    if read_left_encoder(data) != Some(-105) || read_left_encoder(&data[..data.len() - 1]).is_some() { unreachable() }
    if read_right_encoder(data) != Some(300) || read_right_encoder(&data[..data.len() - 1]).is_some() { unreachable() }
    if read_battery(data) != Some(12.25) || read_battery(&data[..data.len() - 1]).is_some() { unreachable() }
}

#[no_mangle]
pub extern "C" fn _start() {
    check(black_box(EXAMPLE));
}
