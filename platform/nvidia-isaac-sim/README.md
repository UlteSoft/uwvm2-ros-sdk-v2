# nvidia-isaac-sim read-only observations

`Isaac Sim ROS2 Publish Clock / rosgraph_msgs/Clock`. Read simulator time from the ROS2 Clock output of the Isaac Sim ROS2 Publish Clock graph node. Its timeStamp input is expressed in seconds.

Supply an encapsulated ROS 2 CDR1 message, with big- or little-endian representation. The accessors are `read_clock_sec`, `read_clock_nanosec`.

C applications include `<uwrosv2/nvidia_isaac_sim/observation.h>` and use the `uwrosv2_nvidia_isaac_sim_` function prefix.
C++98 and later include `<uwrosv2/nvidia_isaac_sim/observation.hpp>` and use namespace `uwrosv2::nvidia_isaac_sim`.
C takes an output pointer and C++ takes an output reference. Both write the value on success. The Rust crate `wros_observation` returns `Option<T>`.
JS and TypeScript import the accessors from `uwrosv2/platform/nvidia-isaac-sim/observation` and pass a Uint8Array. Invalid records return undefined. The 64-bit integer fields return bigint.
In the AssemblyScript bounded-driver profile, pass a staged request length or set the final argument to true to read the last successful driver reply. Each successful accessor returns true and sets the exported field value.
The standalone WAT library at `include/u2rosv2/platform/nvidia-isaac-sim/wat/observation.wat` exports its memory and the named functions. Supply the input address, length, optional array index and output address. A return value of 1 stores the field at its original width in little-endian order.

## Run the example

Install `--platform nvidia-isaac-sim` and the selected language. Copy `examples/nvidia-isaac-sim/<language>` into a user project and set `UWVM_ROS_SDK_ROOT` and `WROS_VM`.
Run `xmake build` and `xmake test -j1`. The guest reads constructed offline samples and checks field values and truncated input.

## Upstream definitions

- [source/extensions/isaacsim.ros2.nodes/nodes/OgnROS2PublishClock.ogn](https://github.com/isaac-sim/IsaacSim/blob/87c95274f50836068b44eeb030bf62aa2108bdf8/source/extensions/isaacsim.ros2.nodes/nodes/OgnROS2PublishClock.ogn)
- [rosgraph_msgs/msg/Clock.msg](https://github.com/ros2/rcl_interfaces/blob/7aa3caf43377ea6ad615bc1040832e2c7566bfbe/rosgraph_msgs/msg/Clock.msg)
- [builtin_interfaces/msg/Time.msg](https://github.com/ros2/rcl_interfaces/blob/7aa3caf43377ea6ad615bc1040832e2c7566bfbe/builtin_interfaces/msg/Time.msg)

The platform.json manifest records each source revision and file SHA-256.
