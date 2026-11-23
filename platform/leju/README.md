# leju read-only observations

`kuavo_msgs/BatteryInfo`. Read millivolts, signed milliamperes, percentage and six NTC temperatures in degrees Celsius.

Supply a compact ROS 1 message body, starting at its first field. The accessors are `read_voltage`, `read_current`, `read_percentage`, `read_temperatures`.

C applications include `<uwrosv2/leju/observation.h>` and use the `uwrosv2_leju_` function prefix.
C++98 and later include `<uwrosv2/leju/observation.hpp>` and use namespace `uwrosv2::leju`.
C takes an output pointer and C++ takes an output reference. Both write the value on success. The Rust crate `wros_observation` returns `Option<T>`.
JS and TypeScript import the accessors from `uwrosv2/platform/leju/observation` and pass a Uint8Array. Invalid records return undefined. The 64-bit integer fields return bigint.
In the AssemblyScript bounded-driver profile, pass a staged request length or set the final argument to true to read the last successful driver reply. Each successful accessor returns true and sets the exported field value.
The standalone WAT library at `include/u2rosv2/platform/leju/wat/observation.wat` exports its memory and the named functions. Supply the input address, length, optional array index and output address. A return value of 1 stores the field at its original width in little-endian order.

## Run the example

Install `--platform leju` and the selected language. Copy `examples/leju/<language>` into a user project and set `UWVM_ROS_SDK_ROOT` and `WROS_VM`.
Run `xmake build` and `xmake test -j1`. The guest reads constructed offline samples and checks field values and truncated input.

## Upstream definitions

- [src/kuavo_msgs/msg/BatteryInfo.msg](https://github.com/LejuRobotics/kuavo-ros-opensource/blob/2634d9fa891bb9b4987cddc7977599922342a316/src/kuavo_msgs/msg/BatteryInfo.msg)

The platform.json manifest records each source revision and file SHA-256.
