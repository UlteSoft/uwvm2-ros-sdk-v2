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
    0x02, 0x00, 0x00, 0x00, 0x06, 0x00, 0x00, 0x00, 0x6a, 0x6f, 0x69, 0x6e,
    0x74, 0x30, 0x06, 0x00, 0x00, 0x00, 0x6a, 0x6f, 0x69, 0x6e, 0x74, 0x31,
    0x02, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x29, 0x00, 0x00, 0x00
];

fn check(data: &[u8]) {
    if read_temps(data, 1) != Some(41) || read_temps(&data[..data.len() - 1], 1).is_some() { unreachable() }
    if read_temps(data, usize::MAX).is_some() { unreachable() }
}

#[no_mangle]
pub extern "C" fn _start() {
    check(black_box(EXAMPLE));
}
