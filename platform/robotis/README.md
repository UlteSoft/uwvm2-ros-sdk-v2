# robotis read-only observations

`turtlebot3_msgs/SensorState`. Read the TurtleBot3 bumper bitmask, signed wheel encoders and battery field after its variable-size ROS header.

Supply a compact ROS 1 message body, starting at its first field. The accessors are `read_bumper`, `read_left_encoder`, `read_right_encoder`, `read_battery`.

C applications include `<uwrosv2/robotis/observation.h>` and use the `uwrosv2_robotis_` function prefix.
C++98 and later include `<uwrosv2/robotis/observation.hpp>` and use namespace `uwrosv2::robotis`.
C takes an output pointer and C++ takes an output reference. Both write the value on success. The Rust crate `wros_observation` returns `Option<T>`.
JS and TypeScript import the accessors from `uwrosv2/platform/robotis/observation` and pass a Uint8Array. Invalid records return undefined. The 64-bit integer fields return bigint.
In the AssemblyScript bounded-driver profile, pass a staged request length or set the final argument to true to read the last successful driver reply. Each successful accessor returns true and sets the exported field value.
The standalone WAT library at `include/u2rosv2/platform/robotis/wat/observation.wat` exports its memory and the named functions. Supply the input address, length, optional array index and output address. A return value of 1 stores the field at its original width in little-endian order.

## Run the example

Install `--platform robotis` and the selected language. Copy `examples/robotis/<language>` into a user project and set `UWVM_ROS_SDK_ROOT` and `WROS_VM`.
Run `xmake build` and `xmake test -j1`. The guest reads constructed offline samples and checks field values and truncated input.

## Upstream definitions

- [msg/SensorState.msg](https://github.com/ROBOTIS-GIT/turtlebot3_msgs/blob/76e78b0a34e07cf1dd16dafdc54c44f35c5b83eb/msg/SensorState.msg)
- [msg/Header.msg](https://github.com/ros/std_msgs/blob/34198520757d1aab358118a0ef294fe2609fde33/msg/Header.msg)

The platform.json manifest records each source revision and file SHA-256.
