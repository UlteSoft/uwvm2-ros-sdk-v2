# Objective-C and Objective-C++ toolchains

[中文](README.zh.md)

The common LLVM 23.1.5 source tree contains the native entry points for `wroc` and `wrocxx`. Clang accepts the GNUstep 2.0 ABI on WebAssembly and emits a zero value of the declared result type when messaging a nil receiver. The provenance record identifies the integrated files and their upstream Git blobs. [Compiler revisions](upstream.json)

The source build uses the same WASIp1 libc, libc++, compiler-rt and LLD as C and C++. For every selected sysroot it builds GNUstep libobjc2 v2.3 and the WROS binding archive with the matching pointer ABI, memory tagging and thread model. The frontend verifies the target archives and their headers before compiling an application. The EH profiles build native Wasm exception support using libc++abi. The no-EH profiles reject exception syntax. The runtime disables executable block trampolines. The [qualification record](../../../document/qualification/objc-library-matrix.json) lists results by profile and host. [Runtime sources](../../runtimes/objc/upstream.json)
