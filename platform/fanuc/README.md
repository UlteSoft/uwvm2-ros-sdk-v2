# fanuc read-only observations

`fanuc_msgs/ForceSensor`. Read sensor force in newtons, moment in newton-metres and sensor type (2 denotes an external sensor).

Supply an encapsulated ROS 2 CDR1 message, with big- or little-endian representation. The accessors are `read_force_x`, `read_force_z`, `read_moment_z`, `read_fs_type`.

C applications include `<uwrosv2/fanuc/observation.h>` and use the `uwrosv2_fanuc_` function prefix.
C++98 and later include `<uwrosv2/fanuc/observation.hpp>` and use namespace `uwrosv2::fanuc`.
C takes an output pointer and C++ takes an output reference. Both write the value on success. The Rust crate `wros_observation` returns `Option<T>`.
JS and TypeScript import the accessors from `uwrosv2/platform/fanuc/observation` and pass a Uint8Array. Invalid records return undefined. The 64-bit integer fields return bigint.
In the AssemblyScript bounded-driver profile, pass a staged request length or set the final argument to true to read the last successful driver reply. Each successful accessor returns true and sets the exported field value.
The standalone WAT library at `include/u2rosv2/platform/fanuc/wat/observation.wat` exports its memory and the named functions. Supply the input address, length, optional array index and output address. A return value of 1 stores the field at its original width in little-endian order.

## Run the example

Install `--platform fanuc` and the selected language. Copy `examples/fanuc/<language>` into a user project and set `UWVM_ROS_SDK_ROOT` and `WROS_VM`.
Run `xmake build` and `xmake test -j1`. The guest reads constructed offline samples and checks field values and truncated input.

## Upstream definitions

- [fanuc_msgs/msg/ForceSensor.msg](https://github.com/FANUC-CORPORATION/fanuc_driver/blob/da5db3f611cdc9dffe687e056c4e79bea584bf5c/fanuc_msgs/msg/ForceSensor.msg)

The platform.json manifest records each source revision and file SHA-256.
