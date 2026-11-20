# PHP 8.6 Embed SAPI probe

This test builds the official PHP 8.6.0 Zend engine and static Embed SAPI using
the SDK's verified C compiler and sysroot selection. It runs the resulting Core
Wasm module in UWVM2's interpreter and AOT engines. The program checks PHP array
iteration, arithmetic, exceptions, output capture, and denial of host file and
environment access. A C control also checks the setjmp/longjmp runtime used by
Zend's bailout mechanism.

Use a new output directory under the repository's ignored `.tmp` tree. Run the
test through the VM's existing 64 GiB cgroup gate.

```sh
PATH_TO_GATE /usr/bin/python3 -B tests/php_embed/probe.py \
    --php-source PATH_TO_PHP_8_6_0_TAR_XZ \
    --wasi-source PATH_TO_WASI_LIBC_SDK34_TAR_XZ \
    --toolchain PATH_TO_SDK_TOOLCHAIN \
    --sysroots PATH_TO_MATCHING_SYSROOTS_JSON \
    --vm PATH_TO_UWVM2_ROS \
    --output .tmp/php-embed
```

The default selects wasm32 Core 3.0, standard Wasm exceptions and the SDK's
managed-neighborhood allocation instrumentation. The test requires matching
compiler and sysroot receipts. With MTE, it checks decoded owner instructions
and runs the same module with synchronous tag checking and with runtime checking
disabled. The explicit `--no-mte` build selects an uninstrumented compiler
profile and still runs both engines. Each result records the actual compiler
closure, VM and Wasm digests.

The probe verifies the upstream release archives before extraction. The SDK's
EH sysroot currently requires the upstream wasi-libc SJLJ helper to be compiled
in the same profile for Zend's C bailout paths. The linker closes file,
descriptor and poll operations, and guest stubs refuse native POSIX operations.
The final import audit accepts only Preview 1 environment, clock and process
exit declarations. VM policy supplies an empty environment and two clocks, and
denies process exit. The SDK's package installation and WSEA qualification are
outside this probe.

The initial strict MTE build identified compiler gaps for Zend's nonlocal
bailout edges and dynamic stack allocations. The MTE configuration uses Zend's
existing heap branch for variable-sized scratch allocations, so those
allocations use the selected SDK allocator. The compiler still controls whether
the surviving stack lifetimes can receive exact ownership. The result stays
incomplete if the compiler refuses any translation unit. Threading, memory64,
native fiber switching, PHP PHPT suites, ROS bindings and device deployment
require their own qualification.

- [PHP release downloads](https://www.php.net/downloads.php)
- [WASI SDK 34 release](https://github.com/WebAssembly/wasi-sdk/releases/tag/wasi-sdk-34)
- [简体中文](README.zh-CN.md)
