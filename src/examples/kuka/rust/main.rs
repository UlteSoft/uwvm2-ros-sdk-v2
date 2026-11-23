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
    0x00, 0x01, 0x00, 0x00, 0x00, 0x02, 0x01, 0x00, 0x00, 0x00, 0x00, 0x03,
    0x00
];

const BIG_ENDIAN: &[u8] = &[
    0x00, 0x00, 0x00, 0x00, 0x00, 0x02, 0x01, 0x00, 0x00, 0x00, 0x00, 0x03,
    0x00
];

fn check(data: &[u8]) {
    if read_cycle_time(data) != Some(2) || read_cycle_time(&data[..data.len() - 1]).is_some() { unreachable() }
    if read_drives_powered(data) != Some(true) || read_drives_powered(&data[..data.len() - 1]).is_some() { unreachable() }
    if read_guard_stop(data) != Some(false) || read_guard_stop(&data[..data.len() - 1]).is_some() { unreachable() }
    if read_operation_mode(data) != Some(3) || read_operation_mode(&data[..data.len() - 1]).is_some() { unreachable() }
}

#[no_mangle]
pub extern "C" fn _start() {
    check(black_box(EXAMPLE));
    check(black_box(BIG_ENDIAN));
}
