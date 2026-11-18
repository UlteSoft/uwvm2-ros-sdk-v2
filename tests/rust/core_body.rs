#![no_std]

#[unsafe(export_name = "__wros_no_memtag_state")]
static mut UNTAGGED_STATE: u32 = 1;

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
pub extern "C" fn suppressed(value: u32) -> u32 {
    let mut data = [value; 8];
    let observed = core::hint::black_box(&mut data);
    observed[(value & 7) as usize] = value.wrapping_add(8);
    core::hint::black_box(observed[(value & 7) as usize])
}

#[unsafe(no_mangle)]
pub extern "C" fn _start() {
    // Exercise the separately built ROS binding, including the VM grant.
    let version = unsafe { wros_scene::wr_abi() };
    assert_eq!(version, 2);
    unsafe {
        (&raw mut UNTAGGED_STATE).write_volatile(version);
        assert_eq!((&raw const UNTAGGED_STATE).read_volatile(), 2);
    }
    let mut values = [11, suppressed(version), tagged(version), 1];
    values.sort_unstable();
    assert_eq!(core::hint::black_box(values), [1, 9, 10, 11]);
}

#[panic_handler]
fn panic(_: &core::panic::PanicInfo) -> ! {
    core::arch::wasm32::unreachable()
}
