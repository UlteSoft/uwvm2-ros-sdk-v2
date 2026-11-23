# hello_robot read-only observations

`Wacc_Protocol_P0.unpack_status`. Read the unextended Stretch wrist accelerometer P0 status body on its little-endian host, after the RPC identifier or optional extension. Timestamp is the raw device counter before host-side conversion.

Supply the field or record described above, in little-endian byte order. The accessors are `read_ax`, `read_az`, `read_a0`, `read_single_tap_count`, `read_timestamp`.

C applications include `<uwrosv2/hello_robot/observation.h>` and use the `uwrosv2_hello_robot_` function prefix.
C++98 and later include `<uwrosv2/hello_robot/observation.hpp>` and use namespace `uwrosv2::hello_robot`.
C takes an output pointer and C++ takes an output reference. Both write the value on success. The Rust crate `wros_observation` returns `Option<T>`.
JS and TypeScript import the accessors from `uwrosv2/platform/hello_robot/observation` and pass a Uint8Array. Invalid records return undefined. The 64-bit integer fields return bigint.
In the AssemblyScript bounded-driver profile, pass a staged request length or set the final argument to true to read the last successful driver reply. Each successful accessor returns true and sets the exported field value.
The standalone WAT library at `include/u2rosv2/platform/hello_robot/wat/observation.wat` exports its memory and the named functions. Supply the input address, length, optional array index and output address. A return value of 1 stores the field at its original width in little-endian order.

## Run the example

Install `--platform hello_robot` and the selected language. Copy `examples/hello_robot/<language>` into a user project and set `UWVM_ROS_SDK_ROOT` and `WROS_VM`.
Run `xmake build` and `xmake test -j1`. The guest reads constructed offline samples and checks field values and truncated input.

## Upstream definitions

- [body/stretch_body/wacc.py](https://github.com/hello-robot/stretch_body/blob/92c9db0cc9ade6535f822e83bbf10cbd0c68136a/body/stretch_body/wacc.py)
- [body/stretch_body/transport.py](https://github.com/hello-robot/stretch_body/blob/92c9db0cc9ade6535f822e83bbf10cbd0c68136a/body/stretch_body/transport.py)

The platform.json manifest records each source revision and file SHA-256.
