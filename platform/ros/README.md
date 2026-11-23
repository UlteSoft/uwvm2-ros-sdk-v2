# ros read-only observations

`geometry_msgs/Quaternion`. Read quaternion components in ROS x, y, z, w order. The decoder accepts a packed ROS 1 body or an encapsulated ROS 2 CDR1 body.

Supply a 32-byte ROS 1 quaternion or a CDR1-encapsulated ROS 2 quaternion. The accessors are `read_x`, `read_y`, `read_z`, `read_w`.

C applications include `<uwrosv2/ros/observation.h>` and use the `uwrosv2_ros_` function prefix.
C++98 and later include `<uwrosv2/ros/observation.hpp>` and use namespace `uwrosv2::ros`.
C takes an output pointer and C++ takes an output reference. Both write the value on success. The Rust crate `wros_observation` returns `Option<T>`.
JS and TypeScript import the accessors from `uwrosv2/platform/ros/observation` and pass a Uint8Array. Invalid records return undefined. The 64-bit integer fields return bigint.
In the AssemblyScript bounded-driver profile, pass a staged request length or set the final argument to true to read the last successful driver reply. Each successful accessor returns true and sets the exported field value.
The standalone WAT library at `include/u2rosv2/platform/ros/wat/observation.wat` exports its memory and the named functions. Supply the input address, length, optional array index and output address. A return value of 1 stores the field at its original width in little-endian order.

## Run the example

Install `--platform ros` and the selected language. Copy `examples/ros/<language>` into a user project and set `UWVM_ROS_SDK_ROOT` and `WROS_VM`.
Run `xmake build` and `xmake test -j1`. The guest reads constructed offline samples and checks field values and truncated input.

## Upstream definitions

- [geometry_msgs/msg/Quaternion.msg](https://github.com/ros/common_msgs/blob/092bc230c8153dd4cfee0c84c9796cc7e6b09fdb/geometry_msgs/msg/Quaternion.msg)
- [geometry_msgs/msg/Quaternion.msg](https://github.com/ros2/common_interfaces/blob/a941f14bb318d8d904505ed935ccbb97f24a70a4/geometry_msgs/msg/Quaternion.msg)

The platform.json manifest records each source revision and file SHA-256.
