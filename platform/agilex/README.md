# agilex read-only observations

`scout_msgs/ScoutBmsStatus`. Read the Scout battery management system charge, voltage, current and first alarm byte.

Supply a compact ROS 1 message body, starting at its first field. The accessors are `read_soc`, `read_battery_voltage`, `read_battery_current`, `read_alarm_status_1`.

C applications include `<uwrosv2/agilex/observation.h>` and use the `uwrosv2_agilex_` function prefix.
C++98 and later include `<uwrosv2/agilex/observation.hpp>` and use namespace `uwrosv2::agilex`.
C takes an output pointer and C++ takes an output reference. Both write the value on success. The Rust crate `wros_observation` returns `Option<T>`.
JS and TypeScript import the accessors from `uwrosv2/platform/agilex/observation` and pass a Uint8Array. Invalid records return undefined. The 64-bit integer fields return bigint.
In the AssemblyScript bounded-driver profile, pass a staged request length or set the final argument to true to read the last successful driver reply. Each successful accessor returns true and sets the exported field value.
The standalone WAT library at `include/u2rosv2/platform/agilex/wat/observation.wat` exports its memory and the named functions. Supply the input address, length, optional array index and output address. A return value of 1 stores the field at its original width in little-endian order.

## Run the example

Install `--platform agilex` and the selected language. Copy `examples/agilex/<language>` into a user project and set `UWVM_ROS_SDK_ROOT` and `WROS_VM`.
Run `xmake build` and `xmake test -j1`. The guest reads constructed offline samples and checks field values and truncated input.

## Upstream definitions

- [scout_msgs/msg/ScoutBmsStatus.msg](https://github.com/agilexrobotics/scout_ros/blob/01e07881cdc566c3a657e288c59a75577992d13e/scout_msgs/msg/ScoutBmsStatus.msg)

The platform.json manifest records each source revision and file SHA-256.
