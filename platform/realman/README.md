# realman read-only observations

`rm_ros_interfaces/Jointerrorcode`. Read an indexed 16-bit joint error code and the separately reported degree-of-freedom count.

Supply an encapsulated ROS 2 CDR1 message, with big- or little-endian representation. The accessors are `read_joint_error`, `read_dof`.

C applications include `<uwrosv2/realman/observation.h>` and use the `uwrosv2_realman_` function prefix.
C++98 and later include `<uwrosv2/realman/observation.hpp>` and use namespace `uwrosv2::realman`.
C takes an output pointer and C++ takes an output reference. Both write the value on success. The Rust crate `wros_observation` returns `Option<T>`.
JS and TypeScript import the accessors from `uwrosv2/platform/realman/observation` and pass a Uint8Array. Invalid records return undefined. The 64-bit integer fields return bigint.
In the AssemblyScript bounded-driver profile, pass a staged request length or set the final argument to true to read the last successful driver reply. Each successful accessor returns true and sets the exported field value.
The standalone WAT library at `include/u2rosv2/platform/realman/wat/observation.wat` exports its memory and the named functions. Supply the input address, length, optional array index and output address. A return value of 1 stores the field at its original width in little-endian order.

## Run the example

Install `--platform realman` and the selected language. Copy `examples/realman/<language>` into a user project and set `UWVM_ROS_SDK_ROOT` and `WROS_VM`.
Run `xmake build` and `xmake test -j1`. The guest reads constructed offline samples and checks field values and truncated input.

## Upstream definitions

- [rm_ros_interfaces/msg/Jointerrorcode.msg](https://github.com/RealManRobot/ros2_rm_robot/blob/5fc226e93358e73c165b2af54b583389f813049e/rm_ros_interfaces/msg/Jointerrorcode.msg)

The platform.json manifest records each source revision and file SHA-256.
