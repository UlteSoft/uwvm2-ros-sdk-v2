# doosan read-only observations

`dsr_msgs/LogAlarm`. Read alarm level, group and index, with bounds checks on all three trailing parameter strings.

Supply a compact ROS 1 message body, starting at its first field. The accessors are `read_level`, `read_group`, `read_index`.

C applications include `<uwrosv2/doosan/observation.h>` and use the `uwrosv2_doosan_` function prefix.
C++98 and later include `<uwrosv2/doosan/observation.hpp>` and use namespace `uwrosv2::doosan`.
C takes an output pointer and C++ takes an output reference. Both write the value on success. The Rust crate `wros_observation` returns `Option<T>`.
JS and TypeScript import the accessors from `uwrosv2/platform/doosan/observation` and pass a Uint8Array. Invalid records return undefined. The 64-bit integer fields return bigint.
In the AssemblyScript bounded-driver profile, pass a staged request length or set the final argument to true to read the last successful driver reply. Each successful accessor returns true and sets the exported field value.
The standalone WAT library at `include/u2rosv2/platform/doosan/wat/observation.wat` exports its memory and the named functions. Supply the input address, length, optional array index and output address. A return value of 1 stores the field at its original width in little-endian order.

## Run the example

Install `--platform doosan` and the selected language. Copy `examples/doosan/<language>` into a user project and set `UWVM_ROS_SDK_ROOT` and `WROS_VM`.
Run `xmake build` and `xmake test -j1`. The guest reads constructed offline samples and checks field values and truncated input.

## Upstream definitions

- [robot_ws/src/dsr_msgs/msg/LogAlarm.msg](https://github.com/DoosanRobotics/doosan-robot/blob/19d520d7df599dc9751f3e8a41337c399c418a47/robot_ws/src/dsr_msgs/msg/LogAlarm.msg)

The platform.json manifest records each source revision and file SHA-256.
