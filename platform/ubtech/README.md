# ubtech read-only observations

`grab_demo_msgs/GraspCandidate`. Read the detection confidence and candidate height reported by the perception node. The message includes two stamped frames, group and class strings.

Supply an encapsulated ROS 2 CDR1 message, with big- or little-endian representation. The accessors are `read_confidence`, `read_pose_pose_position_z`.

C applications include `<uwrosv2/ubtech/observation.h>` and use the `uwrosv2_ubtech_` function prefix.
C++98 and later include `<uwrosv2/ubtech/observation.hpp>` and use namespace `uwrosv2::ubtech`.
C takes an output pointer and C++ takes an output reference. Both write the value on success. The Rust crate `wros_observation` returns `Option<T>`.
JS and TypeScript import the accessors from `uwrosv2/platform/ubtech/observation` and pass a Uint8Array. Invalid records return undefined. The 64-bit integer fields return bigint.
In the AssemblyScript bounded-driver profile, pass a staged request length or set the final argument to true to read the last successful driver reply. Each successful accessor returns true and sets the exported field value.
The standalone WAT library at `include/u2rosv2/platform/ubtech/wat/observation.wat` exports its memory and the named functions. Supply the input address, length, optional array index and output address. A return value of 1 stores the field at its original width in little-endian order.

## Run the example

Install `--platform ubtech` and the selected language. Copy `examples/ubtech/<language>` into a user project and set `UWVM_ROS_SDK_ROOT` and `WROS_VM`.
Run `xmake build` and `xmake test -j1`. The guest reads constructed offline samples and checks field values and truncated input.

## Upstream definitions

- [src/grab_demo_msgs/msg/GraspCandidate.msg](https://github.com/UBTECH-Robot/tk_sdk_demo/blob/3df9f9dc7689203fb673a21d8205bb597ed4fafe/src/grab_demo_msgs/msg/GraspCandidate.msg)
- [std_msgs/msg/Header.msg](https://github.com/ros2/common_interfaces/blob/a941f14bb318d8d904505ed935ccbb97f24a70a4/std_msgs/msg/Header.msg)
- [builtin_interfaces/msg/Time.msg](https://github.com/ros2/rcl_interfaces/blob/7aa3caf43377ea6ad615bc1040832e2c7566bfbe/builtin_interfaces/msg/Time.msg)
- [geometry_msgs/msg/PoseStamped.msg](https://github.com/ros2/common_interfaces/blob/a941f14bb318d8d904505ed935ccbb97f24a70a4/geometry_msgs/msg/PoseStamped.msg)
- [geometry_msgs/msg/Pose.msg](https://github.com/ros2/common_interfaces/blob/a941f14bb318d8d904505ed935ccbb97f24a70a4/geometry_msgs/msg/Pose.msg)
- [geometry_msgs/msg/Point.msg](https://github.com/ros2/common_interfaces/blob/a941f14bb318d8d904505ed935ccbb97f24a70a4/geometry_msgs/msg/Point.msg)
- [geometry_msgs/msg/Quaternion.msg](https://github.com/ros2/common_interfaces/blob/a941f14bb318d8d904505ed935ccbb97f24a70a4/geometry_msgs/msg/Quaternion.msg)

The platform.json manifest records each source revision and file SHA-256.
