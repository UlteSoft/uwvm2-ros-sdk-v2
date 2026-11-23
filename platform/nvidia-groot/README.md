# nvidia-groot read-only observations

`DROID observation.state`. Read one DROID sample from the GR00T demonstration dataset. Supply the 17 decoded float32 values in little-endian order. The end-effector slice is [0,9), gripper [9,10), and seven joints [10,17).

Supply the field or record described above, in little-endian byte order. The accessors are `read_eef_9d`, `read_gripper_position`, `read_joint_position`.

C applications include `<uwrosv2/nvidia_groot/observation.h>` and use the `uwrosv2_nvidia_groot_` function prefix.
C++98 and later include `<uwrosv2/nvidia_groot/observation.hpp>` and use namespace `uwrosv2::nvidia_groot`.
C takes an output pointer and C++ takes an output reference. Both write the value on success. The Rust crate `wros_observation` returns `Option<T>`.
JS and TypeScript import the accessors from `uwrosv2/platform/nvidia-groot/observation` and pass a Uint8Array. Invalid records return undefined. The 64-bit integer fields return bigint.
In the AssemblyScript bounded-driver profile, pass a staged request length or set the final argument to true to read the last successful driver reply. Each successful accessor returns true and sets the exported field value.
The standalone WAT library at `include/u2rosv2/platform/nvidia-groot/wat/observation.wat` exports its memory and the named functions. Supply the input address, length, optional array index and output address. A return value of 1 stores the field at its original width in little-endian order.

## Run the example

Install `--platform nvidia-groot` and the selected language. Copy `examples/nvidia-groot/<language>` into a user project and set `UWVM_ROS_SDK_ROOT` and `WROS_VM`.
Run `xmake build` and `xmake test -j1`. The guest reads constructed offline samples and checks field values and truncated input.

## Upstream definitions

- [demo_data/droid_sample/meta/modality.json](https://github.com/NVIDIA/Isaac-GR00T/blob/dac54b313160c201c450f97df0fd74ebd379c892/demo_data/droid_sample/meta/modality.json)
- [demo_data/droid_sample/meta/info.json](https://github.com/NVIDIA/Isaac-GR00T/blob/dac54b313160c201c450f97df0fd74ebd379c892/demo_data/droid_sample/meta/info.json)

The platform.json manifest records each source revision and file SHA-256.
