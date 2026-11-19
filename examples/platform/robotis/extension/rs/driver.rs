//! @brief Verify the registered platform and parent authorization gates in a Rust guest.
#![no_std]
#[unsafe(no_mangle)]
pub extern "C" fn _start() {
    let mut handle = 0_u64;
    let mut reply = 0x4321_u64;
    let mut written = 0x1234_u64;
    // SAFETY: All addresses denote live Wasm objects of the reported sizes throughout each call.
    unsafe {
        if wros_scene::wr_capability_open(0, b"arm".as_ptr() as u64, 3, (&raw mut handle) as u64) != 0 ||
           wros_scene::wr_driver_connect(handle, 0, 0, 0, (&raw mut reply) as u64, 8, (&raw mut written) as u64) != 13 ||
           reply != 0x4321 || written != 0x1234 || wros_scene::wr_capability_close(handle) != 0 {
            core::arch::wasm32::unreachable();
        }
    }
}
#[panic_handler]
fn panic(_: &core::panic::PanicInfo) -> ! { core::arch::wasm32::unreachable() }
