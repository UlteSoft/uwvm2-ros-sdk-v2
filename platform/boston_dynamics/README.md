# boston_dynamics read-only observations

`bosdyn.api.PointCloud.data`. Read the XYZ_32F data field of a Spot point cloud. Each point contains three consecutive little-endian float32s. Pass the extracted protobuf bytes field and a zero-based point index.

Supply the field or record described above, in little-endian byte order. The accessors are `read_x`, `read_y`, `read_z`.

C applications include `<uwrosv2/boston_dynamics/observation.h>` and use the `uwrosv2_boston_dynamics_` function prefix.
C++98 and later include `<uwrosv2/boston_dynamics/observation.hpp>` and use namespace `uwrosv2::boston_dynamics`.
C takes an output pointer and C++ takes an output reference. Both write the value on success. The Rust crate `wros_observation` returns `Option<T>`.
JS and TypeScript import the accessors from `uwrosv2/platform/boston_dynamics/observation` and pass a Uint8Array. Invalid records return undefined. The 64-bit integer fields return bigint.
In the AssemblyScript bounded-driver profile, pass a staged request length or set the final argument to true to read the last successful driver reply. Each successful accessor returns true and sets the exported field value.
The standalone WAT library at `include/u2rosv2/platform/boston_dynamics/wat/observation.wat` exports its memory and the named functions. Supply the input address, length, optional array index and output address. A return value of 1 stores the field at its original width in little-endian order.

## Run the example

Install `--platform boston_dynamics` and the selected language. Copy `examples/boston_dynamics/<language>` into a user project and set `UWVM_ROS_SDK_ROOT` and `WROS_VM`.
Run `xmake build` and `xmake test -j1`. The guest reads constructed offline samples and checks field values and truncated input.

## Upstream definitions

- [protos/bosdyn/api/point_cloud.proto](https://github.com/boston-dynamics/spot-sdk/blob/16a98aae3b818082288504c6e53b59a67666aaeb/protos/bosdyn/api/point_cloud.proto)

The platform.json manifest records each source revision and file SHA-256.
