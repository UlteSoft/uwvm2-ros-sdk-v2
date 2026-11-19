# QuickJS source

These sources are the QuickJS 2026-06-04 core distributed in the original WROS SDK. The license and source-file notices accompany the code. This directory omits QuickJS's command shell, native modules and OS library. The source snapshot is available in [SDK commit 466ec1647ae8577bc2c16bd4f8df8162636817f4](https://github.com/UlteSoft/uwvm2-ros-sdk/tree/466ec1647ae8577bc2c16bd4f8df8162636817f4/src/language/js/upstream).

Run <code>python3 third-parties/quickjs/verify_release.py</code> for an offline comparison of all 16 C sources and headers and the license against the original distribution plus the recorded SDK patch. The installation pins the source inventory used by each build. The full patch also includes the original SDK formatting changes. [Official source release](https://bellard.org/quickjs/quickjs-2026-06-04.tar.xz)

The separate call-storage patch records the changes from the earlier SDK snapshot. The three argument buffers and synchronous bytecode frames use the QuickJS allocator and a cumulative stack-storage budget. Suspended generators retain their original frame ownership. The Wasm build uses an individual libc allocation per QuickJS object and accounts for allocation size through the tagged sysroot. Bounds checks accommodate the guest's finite downward-growing stack. A denied clock yields an invalid date and a defined non-secret seed.
