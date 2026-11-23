# kuka read-only observations

`kuka_driver_interfaces/KssStatus`. Read the reported RSI cycle (1 means 4 ms, 2 means 12 ms), drive power, guard stop and operation mode.

Supply an encapsulated ROS 2 CDR1 message, with big- or little-endian representation. The accessors are `read_cycle_time`, `read_drives_powered`, `read_guard_stop`, `read_operation_mode`.

C applications include `<uwrosv2/kuka/observation.h>` and use the `uwrosv2_kuka_` function prefix.
C++98 and later include `<uwrosv2/kuka/observation.hpp>` and use namespace `uwrosv2::kuka`.
C takes an output pointer and C++ takes an output reference. Both write the value on success. The Rust crate `wros_observation` returns `Option<T>`.
JS and TypeScript import the accessors from `uwrosv2/platform/kuka/observation` and pass a Uint8Array. Invalid records return undefined. The 64-bit integer fields return bigint.
In the AssemblyScript bounded-driver profile, pass a staged request length or set the final argument to true to read the last successful driver reply. Each successful accessor returns true and sets the exported field value.
The standalone WAT library at `include/u2rosv2/platform/kuka/wat/observation.wat` exports its memory and the named functions. Supply the input address, length, optional array index and output address. A return value of 1 stores the field at its original width in little-endian order.

## Run the example

Install `--platform kuka` and the selected language. Copy `examples/kuka/<language>` into a user project and set `UWVM_ROS_SDK_ROOT` and `WROS_VM`.
Run `xmake build` and `xmake test -j1`. The guest reads constructed offline samples and checks field values and truncated input.

## Upstream definitions

- [kuka_driver_interfaces/msg/KssStatus.msg](https://github.com/kuka-ros/kuka_drivers/blob/15fbb6941356390c38bbd135a0676dfd96a050c0/kuka_driver_interfaces/msg/KssStatus.msg)

The platform.json manifest records each source revision and file SHA-256.
