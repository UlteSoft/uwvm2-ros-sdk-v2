#![no_std]

use uwrosv2::{abi, capability, guard, resource, status, Result};

#[panic_handler]
fn panic(_: &core::panic::PanicInfo<'_>) -> ! { core::arch::wasm32::unreachable() }

fn require(condition: bool) {
    if !condition { core::arch::wasm32::unreachable() }
}

fn success<T>(outcome: Result<T>) -> T {
    match outcome {
        Ok(value) => value,
        Err(_) => core::arch::wasm32::unreachable(),
    }
}

fn has_status<T>(outcome: Result<T>, status: u32) -> bool {
    matches!(outcome, Err(error) if error.status == status)
}

#[no_mangle]
pub extern "C" fn _start() {
    require(abi() == 2);
    require(has_status(capability::open("absent"), status::DENIED));
    let mut full = success(capability::open("signal"));
    let mut limited = success(capability::open("narrow"));
    require(full.id() != 0 && limited.id() != 0 && full.id() != limited.id());
    let mut first = success(guard::create(&full));
    let mut second = success(guard::create(&limited));
    require(has_status(guard::trigger(&limited, &second), status::DENIED));
    success(guard::trigger(&full, &first));
    success(guard::trigger(&full, &first));
    require(success(guard::take(&full, &first)) == 2);
    require(has_status(guard::take(&full, &first), status::AGAIN));
    success(resource::close(&limited, &mut second));
    success(resource::close(&full, &mut first));
    require(second.id() == 0 && first.id() == 0);
    success(capability::close(&mut limited));
    success(capability::close(&mut full));
    require(limited.id() == 0 && full.id() == 0);
}
