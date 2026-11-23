# ABB

C, C++, Rust and Go encode and decode 25 ABB ROS 1 messages, 22 service request/response pairs and the shared Header. [ROS1 message and service records](ros1.md)

Select `--platform abb --language go` for `wrgo`, or `--platform abb --language tinygo` for `wrtg`. Each installs a complete Go module and an external Xmake project. The Go guide covers the EGM, RAPID, StateMachine and RWS packages, wire sizes and connection headers. [ABB Go module and installation](../../include/u2rosv2/platform/abb/go/README.md)

Select `--platform abb --language java` for the native `wrjava` toolchain and a user project with EGM, RAPID, controller, StateMachine and GetRAPIDNum readers. The Java selection awaits independent qualification. [Java readers and external build](../../include/u2rosv2/platform/abb/java/README.md)

## Read-only observation API

`abb_rapid_msgs/Pos`. Read X, Y and Z from the ROS representation of a RAPID pos.

Supply a compact ROS 1 message body, starting at its first field. The accessors are `read_x`, `read_y`, `read_z`.

C applications include `<uwrosv2/abb/observation.h>` and use the `uwrosv2_abb_` function prefix.
C++98 and later include `<uwrosv2/abb/observation.hpp>` and use namespace `uwrosv2::abb`.
C takes an output pointer and C++ takes an output reference. Both write the value on success. The Rust crate `wros_observation` returns `Option<T>`.
JS and TypeScript import the accessors from `uwrosv2/platform/abb/observation` and pass a Uint8Array. Invalid records return undefined. The 64-bit integer fields return bigint.
In the AssemblyScript bounded-driver profile, pass a staged request length or set the final argument to true to read the last successful driver reply. Each successful accessor returns true and sets the exported field value.
The standalone WAT library at `include/u2rosv2/platform/abb/wat/observation.wat` exports its memory and the named functions. Supply the input address, length, optional array index and output address. A return value of 1 stores the field at its original width in little-endian order.

## Run the example

Install `--platform abb` and the selected language. Copy `examples/abb/<language>` into a user project and set `UWVM_ROS_SDK_ROOT` and `WROS_VM`.
Run `xmake build` and `xmake test -j1`. The guest reads constructed offline samples and checks field values and truncated input.

## Upstream definitions

- [abb_rapid_msgs/msg/Pos.msg](https://github.com/ros-industrial/abb_robot_driver_interfaces/blob/da809cd0bb6f270c0814fca07d7d4a5c0385fc39/abb_rapid_msgs/msg/Pos.msg)

The platform.json manifest records each source revision and file SHA-256.
