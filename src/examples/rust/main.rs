#![no_std]
#[cfg(target_arch = "wasm32")]
use core::arch::wasm32::unreachable;
#[cfg(target_arch = "wasm64")]
use wros_runtime::abort as unreachable;

use core::panic::PanicInfo;

#[panic_handler]
fn panic(_: &PanicInfo) -> ! { unreachable() }

#[no_mangle]
pub extern "C" fn _start() {
    if uwrosv2::abi() != 2 { unreachable() }
}
