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
    0x00, 0x01, 0x00, 0x00, 0x03, 0x04, 0x00, 0x00, 0x06, 0x00, 0x00, 0x00,
    0x66, 0x72, 0x61, 0x6d, 0x65, 0x00, 0x00, 0x00, 0xfe, 0xff, 0xff, 0xff,
    0xff, 0xff, 0xff, 0xff, 0xe8, 0x03, 0x00, 0x00
];

const BIG_ENDIAN: &[u8] = &[
    0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x04, 0x03, 0x00, 0x00, 0x00, 0x06,
    0x66, 0x72, 0x61, 0x6d, 0x65, 0x00, 0x00, 0x00, 0xff, 0xff, 0xff, 0xfe,
    0xff, 0xff, 0xff, 0xff, 0x00, 0x00, 0x03, 0xe8
];

fn check(data: &[u8]) {
    if read_number(data) != Some(1027) || read_number(&data[..data.len() - 1]).is_some() { unreachable() }
    if read_sub_code(data) != Some(-2) || read_sub_code(&data[..data.len() - 1]).is_some() { unreachable() }
    if read_datetime_sec(data) != Some(-1) || read_datetime_sec(&data[..data.len() - 1]).is_some() { unreachable() }
    if read_datetime_nanosec(data) != Some(1000) || read_datetime_nanosec(&data[..data.len() - 1]).is_some() { unreachable() }
}

#[no_mangle]
pub extern "C" fn _start() {
    check(black_box(EXAMPLE));
    check(black_box(BIG_ENDIAN));
}
