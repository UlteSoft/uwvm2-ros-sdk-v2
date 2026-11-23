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
    0x00, 0x00, 0x00, 0x00, 0x00, 0x60, 0x52, 0x40, 0x00, 0x00, 0x00, 0x00,
    0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x20, 0x48, 0x40,
    0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0xf8, 0xbf, 0x00, 0x00, 0x00, 0x00,
    0x00, 0x00, 0x00, 0x00, 0x02, 0x00, 0x00, 0x00
];

fn check(data: &[u8]) {
    if read_soc(data) != Some(73.5) || read_soc(&data[..data.len() - 1]).is_some() { unreachable() }
    if read_battery_voltage(data) != Some(48.25) || read_battery_voltage(&data[..data.len() - 1]).is_some() { unreachable() }
    if read_battery_current(data) != Some(-1.5) || read_battery_current(&data[..data.len() - 1]).is_some() { unreachable() }
    if read_alarm_status_1(data) != Some(2) || read_alarm_status_1(&data[..data.len() - 1]).is_some() { unreachable() }
}

#[no_mangle]
pub extern "C" fn _start() {
    check(black_box(EXAMPLE));
}
