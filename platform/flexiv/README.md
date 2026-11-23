# flexiv read-only observations

`flexiv_msgs/Digital`. Read the digital pin number and its boolean state from a flexiv_msgs/Digital element.

Supply an encapsulated ROS 2 CDR1 message, with big- or little-endian representation. The accessors are `read_pin`, `read_state`.

C applications include `<uwrosv2/flexiv/observation.h>` and use the `uwrosv2_flexiv_` function prefix.
C++98 and later include `<uwrosv2/flexiv/observation.hpp>` and use namespace `uwrosv2::flexiv`.
C takes an output pointer and C++ takes an output reference. Both write the value on success. The Rust crate `wros_observation` returns `Option<T>`.
JS and TypeScript import the accessors from `uwrosv2/platform/flexiv/observation` and pass a Uint8Array. Invalid records return undefined. The 64-bit integer fields return bigint.
In the AssemblyScript bounded-driver profile, pass a staged request length or set the final argument to true to read the last successful driver reply. Each successful accessor returns true and sets the exported field value.
The standalone WAT library at `include/u2rosv2/platform/flexiv/wat/observation.wat` exports its memory and the named functions. Supply the input address, length, optional array index and output address. A return value of 1 stores the field at its original width in little-endian order.

## Run the example

Install `--platform flexiv` and the selected language. Copy `examples/flexiv/<language>` into a user project and set `UWVM_ROS_SDK_ROOT` and `WROS_VM`.
Run `xmake build` and `xmake test -j1`. The guest reads constructed offline samples and checks field values and truncated input.

## Upstream definitions

- [flexiv_msgs/msg/Digital.msg](https://github.com/flexivrobotics/flexiv_ros2/blob/5188d2a4473e556a88ee0cfbe858e84ddd6979b8/flexiv_msgs/msg/Digital.msg)

The platform.json manifest records each source revision and file SHA-256.
