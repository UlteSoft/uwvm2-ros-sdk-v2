# agibot read-only observations

`aimdk_msgs/JointState`. Read joint feedback after the variable-length joint name. The final uint16 is the joint error code.

Supply an encapsulated ROS 2 CDR1 message, with big- or little-endian representation. The accessors are `read_position`, `read_velocity`, `read_effort`, `read_error_code`.

C applications include `<uwrosv2/agibot/observation.h>` and use the `uwrosv2_agibot_` function prefix.
C++98 and later include `<uwrosv2/agibot/observation.hpp>` and use namespace `uwrosv2::agibot`.
C takes an output pointer and C++ takes an output reference. Both write the value on success. The Rust crate `wros_observation` returns `Option<T>`.
JS and TypeScript import the accessors from `uwrosv2/platform/agibot/observation` and pass a Uint8Array. Invalid records return undefined. The 64-bit integer fields return bigint.
In the AssemblyScript bounded-driver profile, pass a staged request length or set the final argument to true to read the last successful driver reply. Each successful accessor returns true and sets the exported field value.
The standalone WAT library at `include/u2rosv2/platform/agibot/wat/observation.wat` exports its memory and the named functions. Supply the input address, length, optional array index and output address. A return value of 1 stores the field at its original width in little-endian order.

## Run the example

Install `--platform agibot` and the selected language. Copy `examples/agibot/<language>` into a user project and set `UWVM_ROS_SDK_ROOT` and `WROS_VM`.
Run `xmake build` and `xmake test -j1`. The guest reads constructed offline samples and checks field values and truncated input.

## Upstream definitions

- [src/aimdk_msgs/interface/robot/hal/msg/JointState.msg](https://x2-aimdk.agibot.com/downloads/aimdk-sdk-v1_0_0-aimdk-aarch64-a424add7-artifacts.zip)

The platform.json manifest records each source revision and file SHA-256.
