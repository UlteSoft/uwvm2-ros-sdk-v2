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
    0x00, 0x00, 0x00, 0x3f, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x18, 0x41,
    0x88, 0xff, 0x00, 0x00, 0x00, 0x00, 0x01, 0x02, 0x00, 0x00, 0x00, 0x00,
    0x00, 0x00, 0x78, 0x56, 0x34, 0x12, 0x00, 0x00, 0x00, 0x00
];

fn check(data: &[u8]) {
    if read_ax(data) != Some(0.5) || read_ax(&data[..data.len() - 1]).is_some() { unreachable() }
    if read_az(data) != Some(9.5) || read_az(&data[..data.len() - 1]).is_some() { unreachable() }
    if read_a0(data) != Some(-120) || read_a0(&data[..data.len() - 1]).is_some() { unreachable() }
    if read_single_tap_count(data) != Some(513) || read_single_tap_count(&data[..data.len() - 1]).is_some() { unreachable() }
    if read_timestamp(data) != Some(305419896) || read_timestamp(&data[..data.len() - 1]).is_some() { unreachable() }
}

#[no_mangle]
pub extern "C" fn _start() {
    check(black_box(EXAMPLE));
}
