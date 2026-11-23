# deep_robotics read-only observations

`drdds/ImuDataValue`. Read attitude and inertial components from the ImuDataValue carried inside drdds/ImuData.

Supply an encapsulated ROS 2 CDR1 message, with big- or little-endian representation. The accessors are `read_roll`, `read_yaw`, `read_omega_z`, `read_acc_z`.

C applications include `<uwrosv2/deep_robotics/observation.h>` and use the `uwrosv2_deep_robotics_` function prefix.
C++98 and later include `<uwrosv2/deep_robotics/observation.hpp>` and use namespace `uwrosv2::deep_robotics`.
C takes an output pointer and C++ takes an output reference. Both write the value on success. The Rust crate `wros_observation` returns `Option<T>`.
JS and TypeScript import the accessors from `uwrosv2/platform/deep_robotics/observation` and pass a Uint8Array. Invalid records return undefined. The 64-bit integer fields return bigint.
In the AssemblyScript bounded-driver profile, pass a staged request length or set the final argument to true to read the last successful driver reply. Each successful accessor returns true and sets the exported field value.
The standalone WAT library at `include/u2rosv2/platform/deep_robotics/wat/observation.wat` exports its memory and the named functions. Supply the input address, length, optional array index and output address. A return value of 1 stores the field at its original width in little-endian order.

## Run the example

Install `--platform deep_robotics` and the selected language. Copy `examples/deep_robotics/<language>` into a user project and set `UWVM_ROS_SDK_ROOT` and `WROS_VM`.
Run `xmake build` and `xmake test -j1`. The guest reads constructed offline samples and checks field values and truncated input.

## Upstream definitions

- [src/drdds/msg/ImuDataValue.msg](https://github.com/DeepRoboticsLab/sdk_deploy/blob/9ea6ee94bfe90c9a36f5799d39f8dc1d821128db/src/drdds/msg/ImuDataValue.msg)

The platform.json manifest records each source revision and file SHA-256.
