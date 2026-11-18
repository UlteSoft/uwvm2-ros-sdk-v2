#![no_std]
include!("simulation.rs");

use wros_scene::{wr_capability_open, wr_driver_connect, wr_driver_submit, wr_driver_result,
                 wr_driver_describe, wr_driver_disconnect};

// This single-threaded guest owns one mailbox for the entire driver session.
// Each imported operation sees the same live storage on every poll.
static mut ALIAS: [u8; 5] = *b"joint";
static mut TOKEN: u64 = 0;
static mut WRITTEN: u64 = 0;
static mut RESPONSE: [u64; 64] = [0; 64];
static mut REQUEST: [u8; TEMPLATE.len()] = TEMPLATE;
static mut KEY: u64 = 0;
type Operation = unsafe extern "C" fn(u64, u32, u64, u64, u64, u64, u64) -> u32;

fn invoke(op: Operation, token: u64, input: *const u8, size: usize) -> (u32, u64) {
    unsafe {
        (&raw mut WRITTEN).write_volatile(0);
        let status = op(token, 0, input as usize as u64, size as u64,
                        (&raw mut RESPONSE) as usize as u64, 512, (&raw mut WRITTEN) as usize as u64);
        (status, (&raw const WRITTEN).read_volatile())
    }
}

fn poll(op: Operation, token: u64, input: *const u8, size: usize) -> (u32, u64) {
    for _ in 0..10_000_000 {
        let result = invoke(op, token, input, size);
        if result.0 != 11 { return result; }
    }
    core::arch::wasm32::unreachable()
}

fn response(index: usize) -> u64 {
    unsafe { (&raw const RESPONSE).cast::<u64>().add(index).read_volatile() }
}

#[unsafe(no_mangle)]
pub extern "C" fn _start() {
    let empty = core::ptr::null();
    let status = unsafe { wr_capability_open(0, (&raw const ALIAS) as usize as u64, 5, (&raw mut TOKEN) as usize as u64) };
    assert!(status == 0);
    let token = unsafe { (&raw const TOKEN).read_volatile() };
    assert!(poll(wr_driver_connect, token, empty, 0).0 == 0);
    for sequence in 1..=STEPS {
        unsafe {
            (&raw mut KEY).write_volatile(sequence);
            let request = (&raw mut REQUEST).cast::<u8>();
            core::ptr::copy_nonoverlapping((&raw const KEY).cast::<u8>(), request, 8);
            core::ptr::copy_nonoverlapping((&raw const KEY).cast::<u8>(), request.add(32), 8);
            if SUCCESS {
                let target = if sequence % 2 == 1 { 0.5f64 } else { -0.5f64 };
                request.add(TARGET).cast::<f64>().write_unaligned(target);
            }
        }
        assert!(poll(wr_driver_submit, token, (&raw const REQUEST).cast(), TEMPLATE.len()).0 == 0);
        let (status, used) = poll(wr_driver_result, token, (&raw const KEY).cast(), 8);
        if CRASH {
            assert!(status == 5 || status == 13);
            let state = invoke(wr_driver_describe, token, empty, 0);
            assert!(state.0 == 0 && state.1 >= 32 && response(0) == 6 && response(3) == 1);
        } else {
            assert!(status == 0 && used >= 24 && response(0) == if SUCCESS { 0 } else { 13 });
            assert!(response(2) == sequence);
        }
    }
    assert!(invoke(wr_driver_disconnect, token, empty, 0).0 == 0);
}

#[panic_handler]
fn panic(_: &core::panic::PanicInfo) -> ! { core::arch::wasm32::unreachable() }
