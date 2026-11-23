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
    0x00, 0x6e, 0xbe, 0x00, 0x00, 0xcc, 0xf7, 0xff, 0xff, 0x00, 0x00, 0x00,
    0x00, 0x00, 0x00, 0x00, 0x00, 0x41, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
    0x00, 0x00, 0xfd, 0xff, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
    0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00
];

fn check(data: &[u8]) {
    if read_voltage(data) != Some(48750) || read_voltage(&data[..data.len() - 1]).is_some() { unreachable() }
    if read_current(data) != Some(-2100) || read_current(&data[..data.len() - 1]).is_some() { unreachable() }
    if read_percentage(data) != Some(65) || read_percentage(&data[..data.len() - 1]).is_some() { unreachable() }
    if read_temperatures(data, 1) != Some(-3) || read_temperatures(&data[..data.len() - 1], 1).is_some() { unreachable() }
    if read_temperatures(data, usize::MAX).is_some() { unreachable() }
}

#[no_mangle]
pub extern "C" fn _start() {
    check(black_box(EXAMPLE));
}
