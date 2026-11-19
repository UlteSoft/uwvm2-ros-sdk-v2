//! @brief Check the ROSv2 ABI inside the guest and fail on mismatch.
#![no_std]

#[unsafe(no_mangle)]
pub extern "C" fn _start() {
    if unsafe { wros_scene::wr_abi() } != 2 {
        core::arch::wasm32::unreachable();
    }
}

#[panic_handler]
fn panic(_: &core::panic::PanicInfo) -> ! {
    core::arch::wasm32::unreachable()
}
