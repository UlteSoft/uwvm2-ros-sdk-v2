# nvidia-isaac-ros read-only observations

`isaac_ros_tensor_list_interfaces/TensorShape`. Read declared tensor rank and an indexed dimension from its length-prefixed uint32 dimension sequence.

Supply an encapsulated ROS 2 CDR1 message, with big- or little-endian representation. The accessors are `read_rank`, `read_dims`.

C applications include `<uwrosv2/nvidia_isaac_ros/observation.h>` and use the `uwrosv2_nvidia_isaac_ros_` function prefix.
C++98 and later include `<uwrosv2/nvidia_isaac_ros/observation.hpp>` and use namespace `uwrosv2::nvidia_isaac_ros`.
C takes an output pointer and C++ takes an output reference. Both write the value on success. The Rust crate `wros_observation` returns `Option<T>`.
JS and TypeScript import the accessors from `uwrosv2/platform/nvidia-isaac-ros/observation` and pass a Uint8Array. Invalid records return undefined. The 64-bit integer fields return bigint.
In the AssemblyScript bounded-driver profile, pass a staged request length or set the final argument to true to read the last successful driver reply. Each successful accessor returns true and sets the exported field value.
The standalone WAT library at `include/u2rosv2/platform/nvidia-isaac-ros/wat/observation.wat` exports its memory and the named functions. Supply the input address, length, optional array index and output address. A return value of 1 stores the field at its original width in little-endian order.

## Run the example

Install `--platform nvidia-isaac-ros` and the selected language. Copy `examples/nvidia-isaac-ros/<language>` into a user project and set `UWVM_ROS_SDK_ROOT` and `WROS_VM`.
Run `xmake build` and `xmake test -j1`. The guest reads constructed offline samples and checks field values and truncated input.

## Upstream definitions

- [isaac_ros_tensor_list_interfaces/msg/TensorShape.msg](https://github.com/NVIDIA-ISAAC-ROS/isaac_ros_common/blob/7bec6ae5dbb2faa11617f40226e8932a4a94e6e4/isaac_ros_tensor_list_interfaces/msg/TensorShape.msg)

The platform.json manifest records each source revision and file SHA-256.
