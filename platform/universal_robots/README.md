# Universal Robots

C, C++ and Rust provide typed XCDRv1 codecs for all eight ur_dashboard_msgs messages from Universal Robots ROS 2 Driver 7.3.0. Independent qualification is pending. [Dashboard message codecs](cdr.md)

## Read-only observation API

`ur_dashboard_msgs/SafetyStatus`. Read the dashboard safety-state code. The named constants include PROTECTIVE_STOP (3) and SAFEGUARD_STOP (5).

Supply an encapsulated ROS 2 CDR1 message, with big- or little-endian representation. The accessors are `read_status`.

C applications include `<uwrosv2/universal_robots/observation.h>` and use the `uwrosv2_universal_robots_` function prefix.
C++98 and later include `<uwrosv2/universal_robots/observation.hpp>` and use namespace `uwrosv2::universal_robots`.
C takes an output pointer and C++ takes an output reference. Both write the value on success. The Rust crate `wros_observation` returns `Option<T>`.
JS and TypeScript import the accessors from `uwrosv2/platform/universal_robots/observation` and pass a Uint8Array. Invalid records return undefined. The 64-bit integer fields return bigint.
In the AssemblyScript bounded-driver profile, pass a staged request length or set the final argument to true to read the last successful driver reply. Each successful accessor returns true and sets the exported field value.
The standalone WAT library at `include/u2rosv2/platform/universal_robots/wat/observation.wat` exports its memory and the named functions. Supply the input address, length, optional array index and output address. A return value of 1 stores the field at its original width in little-endian order.

## Run the example

Install `--platform universal_robots` and the selected language. Copy `examples/universal_robots/<language>` into a user project and set `UWVM_ROS_SDK_ROOT` and `WROS_VM`.
Run `xmake build` and `xmake test -j1`. The guest reads constructed offline samples and checks field values and truncated input.

## Upstream definitions

- [ur_dashboard_msgs/msg/SafetyStatus.msg](https://github.com/UniversalRobots/Universal_Robots_ROS2_Driver/blob/262330ed9b5467a17c8ceae09567991e22d13944/ur_dashboard_msgs/msg/SafetyStatus.msg)

The platform.json manifest records each source revision and file SHA-256.
