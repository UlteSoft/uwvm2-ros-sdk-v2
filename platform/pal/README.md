# pal read-only observations

`pal_device_msgs/BatteryState`. Read PAL battery charge state and percentage. The MEDIUM charge state has value 3.

Supply a compact ROS 1 message body, starting at its first field. The accessors are `read_charge_state`, `read_battery_percentage`.

C applications include `<uwrosv2/pal/observation.h>` and use the `uwrosv2_pal_` function prefix.
C++98 and later include `<uwrosv2/pal/observation.hpp>` and use namespace `uwrosv2::pal`.
C takes an output pointer and C++ takes an output reference. Both write the value on success. The Rust crate `wros_observation` returns `Option<T>`.
JS and TypeScript import the accessors from `uwrosv2/platform/pal/observation` and pass a Uint8Array. Invalid records return undefined. The 64-bit integer fields return bigint.
In the AssemblyScript bounded-driver profile, pass a staged request length or set the final argument to true to read the last successful driver reply. Each successful accessor returns true and sets the exported field value.
The standalone WAT library at `include/u2rosv2/platform/pal/wat/observation.wat` exports its memory and the named functions. Supply the input address, length, optional array index and output address. A return value of 1 stores the field at its original width in little-endian order.

## Run the example

Install `--platform pal` and the selected language. Copy `examples/pal/<language>` into a user project and set `UWVM_ROS_SDK_ROOT` and `WROS_VM`.
Run `xmake build` and `xmake test -j1`. The guest reads constructed offline samples and checks field values and truncated input.

## Upstream definitions

- [pal_device_msgs/msg/BatteryState.msg](https://github.com/pal-robotics/pal_msgs/blob/a9b3d52908626e0cf1f230b4dc4a962299d232f3/pal_device_msgs/msg/BatteryState.msg)

The platform.json manifest records each source revision and file SHA-256.
