# clearpath read-only observations

`clearpath_dock_msgs/DockState`. Read the docking state. The upstream enum assigns 1 to DOCKED and 3 to FAILED.

Supply a compact ROS 1 message body, starting at its first field. The accessors are `read_state`.

C applications include `<uwrosv2/clearpath/observation.h>` and use the `uwrosv2_clearpath_` function prefix.
C++98 and later include `<uwrosv2/clearpath/observation.hpp>` and use namespace `uwrosv2::clearpath`.
C takes an output pointer and C++ takes an output reference. Both write the value on success. The Rust crate `wros_observation` returns `Option<T>`.
JS and TypeScript import the accessors from `uwrosv2/platform/clearpath/observation` and pass a Uint8Array. Invalid records return undefined. The 64-bit integer fields return bigint.
In the AssemblyScript bounded-driver profile, pass a staged request length or set the final argument to true to read the last successful driver reply. Each successful accessor returns true and sets the exported field value.
The standalone WAT library at `include/u2rosv2/platform/clearpath/wat/observation.wat` exports its memory and the named functions. Supply the input address, length, optional array index and output address. A return value of 1 stores the field at its original width in little-endian order.

## Run the example

Install `--platform clearpath` and the selected language. Copy `examples/clearpath/<language>` into a user project and set `UWVM_ROS_SDK_ROOT` and `WROS_VM`.
Run `xmake build` and `xmake test -j1`. The guest reads constructed offline samples and checks field values and truncated input.

## Upstream definitions

- [clearpath_outdoornav_msgs/clearpath_dock_msgs/msg/DockState.msg](https://github.com/clearpathrobotics/clearpath_msgs/blob/c17b52e7ba7061310493b43d5b1cd4ffd33cc9b6/clearpath_outdoornav_msgs/clearpath_dock_msgs/msg/DockState.msg)

The platform.json manifest records each source revision and file SHA-256.
