#![no_std]

const TAG_DELTA: usize = 1;

#[repr(align(16))]
struct Storage([u32; 8]);

#[inline(always)]
#[unsafe(link_section = ".wros.no_memtag")]
unsafe fn read_pointer(pointer: *mut u32) -> u32 {
    unsafe { core::ptr::read_volatile(pointer) }
}

#[inline(never)]
#[unsafe(link_section = ".wros.no_memtag")]
fn read_word(storage: &mut Storage, delta: usize) -> u32 {
    // A synchronous VM fault is the expected result for the negative case.
    // Keep the byte address unchanged and vary only one Wasm32 logical tag bit.
    let ptr = core::hint::black_box(storage.0.as_mut_ptr());
    let selected = ptr.map_addr(|address| address ^ (delta << 28));
    unsafe { read_pointer(core::hint::black_box(selected)) }
}

#[unsafe(no_mangle)]
pub extern "C" fn _start() {
    let mut storage = Storage([42; 8]);
    assert_eq!(read_word(core::hint::black_box(&mut storage), core::hint::black_box(TAG_DELTA)), 42);
}

#[panic_handler]
fn panic(_: &core::panic::PanicInfo) -> ! { core::arch::wasm32::unreachable() }
