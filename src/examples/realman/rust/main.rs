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
    0x00, 0x01, 0x00, 0x00, 0x02, 0x00, 0x00, 0x00, 0x00, 0x00, 0x02, 0x01,
    0x02
];

const BIG_ENDIAN: &[u8] = &[
    0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x02, 0x00, 0x00, 0x01, 0x02,
    0x02
];

fn check(data: &[u8]) {
    if read_joint_error(data, 1) != Some(258) || read_joint_error(&data[..data.len() - 1], 1).is_some() { unreachable() }
    if read_joint_error(data, usize::MAX).is_some() { unreachable() }
    if read_dof(data) != Some(2) || read_dof(&data[..data.len() - 1]).is_some() { unreachable() }
}

#[no_mangle]
pub extern "C" fn _start() {
    check(black_box(EXAMPLE));
    check(black_box(BIG_ENDIAN));
}
