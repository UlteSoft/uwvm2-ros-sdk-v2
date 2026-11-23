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
    0x04, 0x00, 0x01, 0x00, 0x00, 0x00, 0x00, 0x00, 0x42, 0x00, 0x00, 0x00,
    0x00, 0x00, 0x00, 0x00, 0x01, 0x00, 0x00, 0x00, 0x01, 0x00, 0x00, 0x00
];

fn check(data: &[u8]) {
    if read_fs_filetype(data) != Some(4) || read_fs_filetype(&data[..data.len() - 1]).is_some() { unreachable() }
    if read_fs_flags(data) != Some(1) || read_fs_flags(&data[..data.len() - 1]).is_some() { unreachable() }
    if read_fs_rights_base(data) != Some(66) || read_fs_rights_base(&data[..data.len() - 1]).is_some() { unreachable() }
    if read_fs_rights_inheriting(data) != Some(4294967297) || read_fs_rights_inheriting(&data[..data.len() - 1]).is_some() { unreachable() }
}

#[no_mangle]
pub extern "C" fn _start() {
    check(black_box(EXAMPLE));
}
