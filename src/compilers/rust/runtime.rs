// Derived from Rust 1.98.0 library/std/src/sys/personality/mod.rs.
// LLVM recognizes __gxx_wasm_personality_v0 when lowering WebAssembly EH.
// The upstream language item has no executable role in that lowering.
#![no_std]
#![feature(lang_items, core_intrinsics)]
#![allow(internal_features)]
/// Trap immediately on either Wasm pointer ABI.
pub fn abort() -> ! {
    core::intrinsics::abort()
}

#[cfg(panic = "unwind")]
#[lang = "eh_personality"]
fn rust_eh_personality() {
    core::intrinsics::abort()
}
