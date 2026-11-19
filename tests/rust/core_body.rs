#![no_std]

#[unsafe(export_name = "__wros_no_memtag_state")]
static mut STATE: u32 = 1;

#[unsafe(no_mangle)]
static READ_ONLY: [u32; 8] = [31; 8];

#[inline(never)]
#[unsafe(no_mangle)]
pub extern "C" fn read_static(index: u32) -> u32 {
    let ptr = core::hint::black_box(&READ_ONLY).as_ptr();
    unsafe { ptr.add((index & 7) as usize).read_volatile() }
}

#[inline(never)]
#[unsafe(no_mangle)]
pub extern "C" fn tagged(value: u32) -> u32 {
    let mut data = [value; 8];
    let observed = core::hint::black_box(&mut data);
    observed[(value & 7) as usize] = value.wrapping_add(7);
    core::hint::black_box(observed[(value & 7) as usize])
}

#[inline(never)]
#[unsafe(link_section = ".wros.no_memtag")]
#[unsafe(no_mangle)]
pub extern "C" fn safe_wrapper(value: u32) -> u32 {
    let mut data = [value; 8];
    let observed = core::hint::black_box(&mut data);
    observed[(value & 7) as usize] = value.wrapping_add(8);
    // This safe API uses a bounded raw pointer. The call to black_box keeps
    // the allocation observable so the test exercises actual Wasm memory.
    let index = (value & 7) as usize;
    unsafe { observed.as_ptr().add(index).read_volatile() }
}

#[inline(never)]
#[unsafe(link_section = ".wros.no_memtag")]
#[unsafe(no_mangle)]
pub extern "C" fn proven_scalar() -> u32 { 17 }

#[inline(never)]
#[unsafe(link_section = ".wros.no_memtag")]
#[unsafe(no_mangle)]
pub fn wide_word(value: u128) -> u128 { value }

#[unsafe(no_mangle)]
pub extern "C" fn _start() {
    assert_eq!(core::hint::black_box(proven_scalar as extern "C" fn() -> u32)(), 17);
    assert_eq!(core::hint::black_box(wide_word as fn(u128) -> u128)(1 << 88), 1 << 88);
    assert_eq!(read_static(core::hint::black_box(3)), 31);
    // Exercise the separately built ROS binding, including the VM grant.
    let version = unsafe { wros_scene::wr_abi() };
    assert_eq!(version, 2);
    unsafe {
        (&raw mut STATE).write_volatile(version);
        assert_eq!((&raw const STATE).read_volatile(), 2);
    }
    let mut values = [11, safe_wrapper(version), tagged(version), 1];
    values.sort_unstable();
    assert_eq!(core::hint::black_box(values), [1, 9, 10, 11]);
}

#[panic_handler]
fn panic(_: &core::panic::PanicInfo) -> ! {
    core::arch::wasm32::unreachable()
}
