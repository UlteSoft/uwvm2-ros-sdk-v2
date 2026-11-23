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
    0x03, 0x00, 0x00, 0x87, 0x42
];

fn check(data: &[u8]) {
    if read_charge_state(data) != Some(3) || read_charge_state(&data[..data.len() - 1]).is_some() { unreachable() }
    if read_battery_percentage(data) != Some(67.5) || read_battery_percentage(&data[..data.len() - 1]).is_some() { unreachable() }
}

#[no_mangle]
pub extern "C" fn _start() {
    check(black_box(EXAMPLE));
}
