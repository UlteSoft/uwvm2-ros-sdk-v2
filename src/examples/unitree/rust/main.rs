#![no_std]

#[cfg(target_arch = "wasm32")]
use core::arch::wasm32::unreachable;
#[cfg(target_arch = "wasm64")]
use wros_runtime::abort as unreachable;
use core::hint::black_box;
use core::panic::PanicInfo;
use unitree_go2::{decode_result, encode_read, LowState};

#[panic_handler]
fn panic(_: &PanicInfo) -> ! { unreachable() }

#[no_mangle]
pub extern "C" fn _start() {
    let request = encode_read(black_box(7), 1024);
    if request[0] != 7 || request[9] != 4 || request[16] != 24 || request[24] != 1 || request[40] != 16 {
        unreachable();
    }
    let mut frame = [0u8; 40];
    frame[8] = 24;
    frame[16] = 16;
    frame[24..26].copy_from_slice(&41347u16.to_le_bytes());
    frame[32..36].copy_from_slice(&0.125f32.to_bits().to_le_bytes());
    let frame = black_box(frame);
    let sample = LowState { tick: 41347, first_joint_position: 0.125 };
    if decode_result(&frame) != Some(sample) || decode_result(&frame[..39]).is_some() { unreachable() }
}
