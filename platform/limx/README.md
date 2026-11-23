# limx read-only observations

`limxsdk::msg::perception_msgs::HeightEstimateResult`. Read the LimX height estimate and header sequence from the compact little-endian mros message, including its trailing description string.

Supply a compact ROS 1 message body, starting at its first field. The accessors are `read_estimate_height`, `read_header_seq`.

C applications include `<uwrosv2/limx/observation.h>` and use the `uwrosv2_limx_` function prefix.
C++98 and later include `<uwrosv2/limx/observation.hpp>` and use namespace `uwrosv2::limx`.
C takes an output pointer and C++ takes an output reference. Both write the value on success. The Rust crate `wros_observation` returns `Option<T>`.
JS and TypeScript import the accessors from `uwrosv2/platform/limx/observation` and pass a Uint8Array. Invalid records return undefined. The 64-bit integer fields return bigint.
In the AssemblyScript bounded-driver profile, pass a staged request length or set the final argument to true to read the last successful driver reply. Each successful accessor returns true and sets the exported field value.
The standalone WAT library at `include/u2rosv2/platform/limx/wat/observation.wat` exports its memory and the named functions. Supply the input address, length, optional array index and output address. A return value of 1 stores the field at its original width in little-endian order.

## Run the example

Install `--platform limx` and the selected language. Copy `examples/limx/<language>` into a user project and set `UWVM_ROS_SDK_ROOT` and `WROS_VM`.
Run `xmake build` and `xmake test -j1`. The guest reads constructed offline samples and checks field values and truncated input.

## Upstream definitions

- [include/limxsdk/msg/perception_msgs/HeightEstimateResult.h](https://github.com/limxdynamics/limxsdk-lowlevel/blob/61624b58663b47928717069ff0eab2f1c85ec733/include/limxsdk/msg/perception_msgs/HeightEstimateResult.h)
- [include/limxsdk/codec/codec.h](https://github.com/limxdynamics/limxsdk-lowlevel/blob/61624b58663b47928717069ff0eab2f1c85ec733/include/limxsdk/codec/codec.h)

The platform.json manifest records each source revision and file SHA-256.
