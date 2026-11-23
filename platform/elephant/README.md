# elephant read-only observations

`myarm_communication/MyArmPumpStatus`. Read myArm pump status and the two signed pin fields.

Supply a compact ROS 1 message body, starting at its first field. The accessors are `read_status`, `read_pin1`, `read_pin2`.

C applications include `<uwrosv2/elephant/observation.h>` and use the `uwrosv2_elephant_` function prefix.
C++98 and later include `<uwrosv2/elephant/observation.hpp>` and use namespace `uwrosv2::elephant`.
C takes an output pointer and C++ takes an output reference. Both write the value on success. The Rust crate `wros_observation` returns `Option<T>`.
JS and TypeScript import the accessors from `uwrosv2/platform/elephant/observation` and pass a Uint8Array. Invalid records return undefined. The 64-bit integer fields return bigint.
In the AssemblyScript bounded-driver profile, pass a staged request length or set the final argument to true to read the last successful driver reply. Each successful accessor returns true and sets the exported field value.
The standalone WAT library at `include/u2rosv2/platform/elephant/wat/observation.wat` exports its memory and the named functions. Supply the input address, length, optional array index and output address. A return value of 1 stores the field at its original width in little-endian order.

## Run the example

Install `--platform elephant` and the selected language. Copy `examples/elephant/<language>` into a user project and set `UWVM_ROS_SDK_ROOT` and `WROS_VM`.
Run `xmake build` and `xmake test -j1`. The guest reads constructed offline samples and checks field values and truncated input.

## Upstream definitions

- [myArm/myarm_communication/msg/MyArmPumpStatus.msg](https://github.com/elephantrobotics/mycobot_ros/blob/3a0357d2afec2706c299f6d51ac46b6b128067f8/myArm/myarm_communication/msg/MyArmPumpStatus.msg)

The platform.json manifest records each source revision and file SHA-256.
