#![no_std]

#[panic_handler]
fn panic(_: &core::panic::PanicInfo<'_>) -> ! { core::arch::wasm32::unreachable() }

#[no_mangle]
pub extern "C" fn test_abi(expected: u32) {
    if uwrosv2::abi() != expected { core::arch::wasm32::unreachable() }
}
