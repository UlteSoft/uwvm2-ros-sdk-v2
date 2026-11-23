# trossen read-only observations

`interbotix_xs_msgs/JointTemps`. Read a joint temperature in degrees Celsius by its index in the diagnostic message. The joint names precede the temperature sequence.

Supply a compact ROS 1 message body, starting at its first field. The accessors are `read_temps`.

C applications include `<uwrosv2/trossen/observation.h>` and use the `uwrosv2_trossen_` function prefix.
C++98 and later include `<uwrosv2/trossen/observation.hpp>` and use namespace `uwrosv2::trossen`.
C takes an output pointer and C++ takes an output reference. Both write the value on success. The Rust crate `wros_observation` returns `Option<T>`.
JS and TypeScript import the accessors from `uwrosv2/platform/trossen/observation` and pass a Uint8Array. Invalid records return undefined. The 64-bit integer fields return bigint.
In the AssemblyScript bounded-driver profile, pass a staged request length or set the final argument to true to read the last successful driver reply. Each successful accessor returns true and sets the exported field value.
The standalone WAT library at `include/u2rosv2/platform/trossen/wat/observation.wat` exports its memory and the named functions. Supply the input address, length, optional array index and output address. A return value of 1 stores the field at its original width in little-endian order.

## Run the example

Install `--platform trossen` and the selected language. Copy `examples/trossen/<language>` into a user project and set `UWVM_ROS_SDK_ROOT` and `WROS_VM`.
Run `xmake build` and `xmake test -j1`. The guest reads constructed offline samples and checks field values and truncated input.

## Upstream definitions

- [interbotix_ros_xseries/interbotix_xs_msgs/msg/JointTemps.msg](https://github.com/Interbotix/interbotix_ros_core/blob/172841ffa93f7556fff9c7455ad0e77688fa156e/interbotix_ros_xseries/interbotix_xs_msgs/msg/JointTemps.msg)

The platform.json manifest records each source revision and file SHA-256.
