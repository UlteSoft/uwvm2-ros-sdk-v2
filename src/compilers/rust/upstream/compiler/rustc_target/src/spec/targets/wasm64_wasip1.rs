//! WROS: UWVM's memory64 extension to the WASI Preview 1 guest ABI.
use crate::spec::{Arch, Cc, LinkerFlavor, Target, TargetMetadata};

pub(crate) fn target() -> Target {
    let mut target = super::wasm32_wasip1::target();
    target.pointer_width = 64;
    target.arch = Arch::Wasm64;
    target.llvm_target = "wasm64-wasip1".into();
    target.data_layout = super::wasm64_unknown_unknown::target().data_layout;
    target.metadata = TargetMetadata {
        description: Some("UWVM WebAssembly memory64 with extended WASI Preview 1".into()),
        tier: None, host_tools: Some(false), std: Some(false),
    };
    target.options.pre_link_args.remove(&LinkerFlavor::WasmLld(Cc::Yes));
    target.options.add_pre_link_args(LinkerFlavor::WasmLld(Cc::Yes), &["--target=wasm64-wasip1"]);
    target.options.add_pre_link_args(LinkerFlavor::WasmLld(Cc::No), &["-mwasm64"]);
    target
}
