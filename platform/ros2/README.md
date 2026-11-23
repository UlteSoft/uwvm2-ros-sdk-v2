# ros2 read-only observations

`builtin_interfaces/Duration`. Read normalized ROS 2 duration fields. For instance, -2 seconds and 300000000 nanoseconds represent -1.7 seconds.

Supply an encapsulated ROS 2 CDR1 message, with big- or little-endian representation. The accessors are `read_sec`, `read_nanosec`.

C applications include `<uwrosv2/ros2/observation.h>` and use the `uwrosv2_ros2_` function prefix.
C++98 and later include `<uwrosv2/ros2/observation.hpp>` and use namespace `uwrosv2::ros2`.
C takes an output pointer and C++ takes an output reference. Both write the value on success. The Rust crate `wros_observation` returns `Option<T>`.
JS and TypeScript import the accessors from `uwrosv2/platform/ros2/observation` and pass a Uint8Array. Invalid records return undefined. The 64-bit integer fields return bigint.
In the AssemblyScript bounded-driver profile, pass a staged request length or set the final argument to true to read the last successful driver reply. Each successful accessor returns true and sets the exported field value.
The standalone WAT library at `include/u2rosv2/platform/ros2/wat/observation.wat` exports its memory and the named functions. Supply the input address, length, optional array index and output address. A return value of 1 stores the field at its original width in little-endian order.

## Run the example

Install `--platform ros2` and the selected language. Copy `examples/ros2/<language>` into a user project and set `UWVM_ROS_SDK_ROOT` and `WROS_VM`.
Run `xmake build` and `xmake test -j1`. The guest reads constructed offline samples and checks field values and truncated input.

## Upstream definitions

- [builtin_interfaces/msg/Duration.msg](https://github.com/ros2/rcl_interfaces/blob/7aa3caf43377ea6ad615bc1040832e2c7566bfbe/builtin_interfaces/msg/Duration.msg)

The platform.json manifest records each source revision and file SHA-256.
