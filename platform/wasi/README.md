# wasi read-only observations

`__wasi_fdstat_t`. Read the WASI Preview 1 fd_fdstat_get result in guest memory, including both 64-bit rights masks. The ABI places these masks at offsets 8 and 16.

Supply the field or record described above, in little-endian byte order. The accessors are `read_fs_filetype`, `read_fs_flags`, `read_fs_rights_base`, `read_fs_rights_inheriting`.

C applications include `<uwrosv2/wasi/observation.h>` and use the `uwrosv2_wasi_` function prefix.
C++98 and later include `<uwrosv2/wasi/observation.hpp>` and use namespace `uwrosv2::wasi`.
C takes an output pointer and C++ takes an output reference. Both write the value on success. The Rust crate `wros_observation` returns `Option<T>`.
JS and TypeScript import the accessors from `uwrosv2/platform/wasi/observation` and pass a Uint8Array. Invalid records return undefined. The 64-bit integer fields return bigint.
In the AssemblyScript bounded-driver profile, pass a staged request length or set the final argument to true to read the last successful driver reply. Each successful accessor returns true and sets the exported field value.
The standalone WAT library at `include/u2rosv2/platform/wasi/wat/observation.wat` exports its memory and the named functions. Supply the input address, length, optional array index and output address. A return value of 1 stores the field at its original width in little-endian order.

## Run the example

Install `--platform wasi` and the selected language. Copy `examples/wasi/<language>` into a user project and set `UWVM_ROS_SDK_ROOT` and `WROS_VM`.
Run `xmake build` and `xmake test -j1`. The guest reads constructed offline samples and checks field values and truncated input.

## Upstream definitions

- [libc-bottom-half/headers/public/wasi/wasip1.h](https://github.com/WebAssembly/wasi-libc/blob/2e6fb9d8ee0cdf9e431fbcabe8af3115de000a13/libc-bottom-half/headers/public/wasi/wasip1.h)

The platform.json manifest records each source revision and file SHA-256.
