# booster read-only observations

`booster_interface/ImuState`. Read an indexed roll/pitch/yaw, gyroscope or accelerometer component. Each array has three elements.

Supply an encapsulated ROS 2 CDR1 message, with big- or little-endian representation. The accessors are `read_rpy`, `read_gyro`, `read_acc`.

C applications include `<uwrosv2/booster/observation.h>` and use the `uwrosv2_booster_` function prefix.
C++98 and later include `<uwrosv2/booster/observation.hpp>` and use namespace `uwrosv2::booster`.
C takes an output pointer and C++ takes an output reference. Both write the value on success. The Rust crate `wros_observation` returns `Option<T>`.
JS and TypeScript import the accessors from `uwrosv2/platform/booster/observation` and pass a Uint8Array. Invalid records return undefined. The 64-bit integer fields return bigint.
In the AssemblyScript bounded-driver profile, pass a staged request length or set the final argument to true to read the last successful driver reply. Each successful accessor returns true and sets the exported field value.
The standalone WAT library at `include/u2rosv2/platform/booster/wat/observation.wat` exports its memory and the named functions. Supply the input address, length, optional array index and output address. A return value of 1 stores the field at its original width in little-endian order.

## Run the example

Install `--platform booster` and the selected language. Copy `examples/booster/<language>` into a user project and set `UWVM_ROS_SDK_ROOT` and `WROS_VM`.
Run `xmake build` and `xmake test -j1`. The guest reads constructed offline samples and checks field values and truncated input.

## Upstream definitions

- [src/interface/booster_ros2_interface/msg/ImuState.msg](https://github.com/BoosterRobotics/robocup_demo/blob/fa4f31ccb4428a9e60e90b4f54eb80499caeb0ca/src/interface/booster_ros2_interface/msg/ImuState.msg)

The platform.json manifest records each source revision and file SHA-256.
