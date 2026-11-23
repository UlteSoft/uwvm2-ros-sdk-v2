# Franka

C, C++, Rust and Go (standard Go and TinyGo) encode and decode 137 ROS 2 XCDRv1 records for the Franka arm, gripper, spine and their standard dependencies. [CDR message and service records](cdr.md)

## Read-only observation API

`franka_msgs/Elbow`. Read either component of all five elbow arrays and validate the complete record.

Supply an encapsulated ROS 2 CDR1 message, with big- or little-endian representation. The accessors are `read_position`, `read_desired_position`, `read_commanded_position`, `read_commanded_velocity`, `read_commanded_acceleration`.

C applications include `<uwrosv2/franka/observation.h>` and use the `uwrosv2_franka_` function prefix.
C++98 and later include `<uwrosv2/franka/observation.hpp>` and use namespace `uwrosv2::franka`.
C takes an output pointer and C++ takes an output reference. Both write the value on success. The Rust crate `wros_observation` returns `Option<T>`.
JS and TypeScript import the accessors from `uwrosv2/platform/franka/observation` and pass a Uint8Array. Invalid records return undefined. The 64-bit integer fields return bigint.
In the AssemblyScript bounded-driver profile, pass a staged request length or set the final argument to true to read the last successful driver reply. Each successful accessor returns true and sets the exported field value.
The standalone WAT library at `include/u2rosv2/platform/franka/wat/observation.wat` exports its memory and the named functions. Supply the input address, length, optional array index and output address. A return value of 1 stores the field at its original width in little-endian order.

## Run the example

Install `--platform franka` and the selected language. Copy `examples/franka/<language>` into a user project and set `UWVM_ROS_SDK_ROOT` and `WROS_VM`.
Run `xmake build` and `xmake test -j1`. The guest reads constructed offline samples and checks field values and truncated input.

## Upstream definitions

- [franka_msgs/msg/Elbow.msg](https://github.com/frankarobotics/franka_ros2/blob/4acc05c01ebfcdf916ee6b3df966df0ad7b2f9ec/franka_msgs/msg/Elbow.msg)

The platform.json manifest records each source revision and file SHA-256.
