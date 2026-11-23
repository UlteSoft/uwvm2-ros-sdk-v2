# ufactory read-only observations

`xarm_msgs/IOState`. Read both digital and both analog input-port states from xArm IOState.

Supply a compact ROS 1 message body, starting at its first field. The accessors are `read_digital_1`, `read_digital_2`, `read_analog_1`, `read_analog_2`.

C applications include `<uwrosv2/ufactory/observation.h>` and use the `uwrosv2_ufactory_` function prefix.
C++98 and later include `<uwrosv2/ufactory/observation.hpp>` and use namespace `uwrosv2::ufactory`.
C takes an output pointer and C++ takes an output reference. Both write the value on success. The Rust crate `wros_observation` returns `Option<T>`.
JS and TypeScript import the accessors from `uwrosv2/platform/ufactory/observation` and pass a Uint8Array. Invalid records return undefined. The 64-bit integer fields return bigint.
In the AssemblyScript bounded-driver profile, pass a staged request length or set the final argument to true to read the last successful driver reply. Each successful accessor returns true and sets the exported field value.
The standalone WAT library at `include/u2rosv2/platform/ufactory/wat/observation.wat` exports its memory and the named functions. Supply the input address, length, optional array index and output address. A return value of 1 stores the field at its original width in little-endian order.

## Run the example

Install `--platform ufactory` and the selected language. Copy `examples/ufactory/<language>` into a user project and set `UWVM_ROS_SDK_ROOT` and `WROS_VM`.
Run `xmake build` and `xmake test -j1`. The guest reads constructed offline samples and checks field values and truncated input.

## Upstream definitions

- [xarm_msgs/msg/IOState.msg](https://github.com/xArm-Developer/xarm_ros/blob/3bc6c4da51769d90ce2a6d1419a0b65446d177e3/xarm_msgs/msg/IOState.msg)

The platform.json manifest records each source revision and file SHA-256.
