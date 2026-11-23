#![no_std]
#[cfg(target_arch = "wasm32")]
use core::arch::wasm32::unreachable;
#[cfg(target_arch = "wasm64")]
use wros_runtime::abort as unreachable;
use core::{hint::black_box, panic::PanicInfo};
use wros_observation::cdr::{ur_dashboard_msgs::ProgramInformation, Endian, Error, Message};

mod program_information_frames;
use program_information_frames::{METADATA_BIG, METADATA_LITTLE};

#[panic_handler]
fn panic(_: &PanicInfo) -> ! { unreachable() }

fn transcode(source: &[u8], expected: &[u8], order: Endian) -> Result<bool, Error> {
    let value = ProgramInformation::decode(source)?;
    let fields = ProgramInformation {
        name: b"A",
        description: b"BC",
        created_date: 0x0102030405060708,
        last_saved_date: 0x8000000000000001,
        last_modified_date: 0xfedcba9876543210,
        program_state: ProgramInformation::PROGRAM_STATE_FINAL,
    };
    let mut output = [0; METADATA_BIG.len()];
    let size = value.encoded_size()?;
    let written = value.encode(order, &mut output)?;
    Ok(value == fields && size == output.len() && written == size && output.as_slice() == expected
        && ProgramInformation::validate(&source[..source.len() - 1]).is_err())
}

#[no_mangle]
pub extern "C" fn _start() {
    if transcode(black_box(METADATA_BIG), METADATA_LITTLE, Endian::Little) != Ok(true)
        || transcode(black_box(METADATA_LITTLE), METADATA_BIG, Endian::Big) != Ok(true) {
        unreachable()
    }
}
