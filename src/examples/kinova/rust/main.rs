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
    0xd2, 0x04, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x96, 0x00, 0x00, 0x00,
    0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
    0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x3e, 0x42, 0x00, 0x00, 0x29, 0x42,
    0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
    0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00
];

fn check(data: &[u8]) {
    if read_feedback_id_identifier(data) != Some(1234) || read_feedback_id_identifier(&data[..data.len() - 1]).is_some() { unreachable() }
    if read_jitter_comm(data) != Some(150) || read_jitter_comm(&data[..data.len() - 1]).is_some() { unreachable() }
    if read_voltage(data) != Some(47.5) || read_voltage(&data[..data.len() - 1]).is_some() { unreachable() }
    if read_temperature_motor(data) != Some(42.25) || read_temperature_motor(&data[..data.len() - 1]).is_some() { unreachable() }
}

#[no_mangle]
pub extern "C" fn _start() {
    check(black_box(EXAMPLE));
}
