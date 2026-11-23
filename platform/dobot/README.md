# dobot read-only observations

`dobot_msgs_v4/RobotStatus`. Read the independent enable and connection flags in the six-axis V4 status message.

Supply an encapsulated ROS 2 CDR1 message, with big- or little-endian representation. The accessors are `read_is_enable`, `read_is_connected`.

C applications include `<uwrosv2/dobot/observation.h>` and use the `uwrosv2_dobot_` function prefix.
C++98 and later include `<uwrosv2/dobot/observation.hpp>` and use namespace `uwrosv2::dobot`.
C takes an output pointer and C++ takes an output reference. Both write the value on success. The Rust crate `wros_observation` returns `Option<T>`.
JS and TypeScript import the accessors from `uwrosv2/platform/dobot/observation` and pass a Uint8Array. Invalid records return undefined. The 64-bit integer fields return bigint.
In the AssemblyScript bounded-driver profile, pass a staged request length or set the final argument to true to read the last successful driver reply. Each successful accessor returns true and sets the exported field value.
The standalone WAT library at `include/u2rosv2/platform/dobot/wat/observation.wat` exports its memory and the named functions. Supply the input address, length, optional array index and output address. A return value of 1 stores the field at its original width in little-endian order.

## Run the example

Install `--platform dobot` and the selected language. Copy `examples/dobot/<language>` into a user project and set `UWVM_ROS_SDK_ROOT` and `WROS_VM`.
Run `xmake build` and `xmake test -j1`. The guest reads constructed offline samples and checks field values and truncated input.

## Upstream definitions

- [dobot_msgs_v4/msg/RobotStatus.msg](https://github.com/Dobot-Arm/DOBOT_6Axis_ROS2_V4/blob/ec201c40d5db63185a3593ec9c39f80fe25aa527/dobot_msgs_v4/msg/RobotStatus.msg)

The platform.json manifest records each source revision and file SHA-256.
