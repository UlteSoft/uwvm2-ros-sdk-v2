# ros1 read-only observations

`std_msgs/Time`. Read ROS 1 time as two unsigned 32-bit values, seconds and nanoseconds.

Supply a compact ROS 1 message body, starting at its first field. The accessors are `read_data_sec`, `read_data_nsec`.

C applications include `<uwrosv2/ros1/observation.h>` and use the `uwrosv2_ros1_` function prefix.
C++98 and later include `<uwrosv2/ros1/observation.hpp>` and use namespace `uwrosv2::ros1`.
C takes an output pointer and C++ takes an output reference. Both write the value on success. The Rust crate `wros_observation` returns `Option<T>`.
JS and TypeScript import the accessors from `uwrosv2/platform/ros1/observation` and pass a Uint8Array. Invalid records return undefined. The 64-bit integer fields return bigint.
In the AssemblyScript bounded-driver profile, pass a staged request length or set the final argument to true to read the last successful driver reply. Each successful accessor returns true and sets the exported field value.
The standalone WAT library at `include/u2rosv2/platform/ros1/wat/observation.wat` exports its memory and the named functions. Supply the input address, length, optional array index and output address. A return value of 1 stores the field at its original width in little-endian order.

## Run the example

Install `--platform ros1` and the selected language. Copy `examples/ros1/<language>` into a user project and set `UWVM_ROS_SDK_ROOT` and `WROS_VM`.
Run `xmake build` and `xmake test -j1`. The guest reads constructed offline samples and checks field values and truncated input.

## Upstream definitions

- [msg/Time.msg](https://github.com/ros/std_msgs/blob/34198520757d1aab358118a0ef294fe2609fde33/msg/Time.msg)

The platform.json manifest records each source revision and file SHA-256.
