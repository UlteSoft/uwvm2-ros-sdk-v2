# fourier read-only observations

`simulator_pub_msg`. Decode the complete Fourier Aurora MuJoCo simulator feedback message including its LCM fingerprint, signed motor count and big-endian joint and contact values.

Supply the big-endian LCM message body, starting at the eight-byte type fingerprint. The accessors are `read_timestamp`, `read_q`, `read_q_dot`, `read_lf_touch`, `read_rf_touch`.

C applications include `<uwrosv2/fourier/observation.h>` and use the `uwrosv2_fourier_` function prefix.
C++98 and later include `<uwrosv2/fourier/observation.hpp>` and use namespace `uwrosv2::fourier`.
C takes an output pointer and C++ takes an output reference. Both write the value on success. The Rust crate `wros_observation` returns `Option<T>`.
JS and TypeScript import the accessors from `uwrosv2/platform/fourier/observation` and pass a Uint8Array. Invalid records return undefined. The 64-bit integer fields return bigint.
In the AssemblyScript bounded-driver profile, pass a staged request length or set the final argument to true to read the last successful driver reply. Each successful accessor returns true and sets the exported field value.
The standalone WAT library at `include/u2rosv2/platform/fourier/wat/observation.wat` exports its memory and the named functions. Supply the input address, length, optional array index and output address. A return value of 1 stores the field at its original width in little-endian order.

## Run the example

Install `--platform fourier` and the selected language. Copy `examples/fourier/<language>` into a user project and set `UWVM_ROS_SDK_ROOT` and `WROS_VM`.
Run `xmake build` and `xmake test -j1`. The guest reads constructed offline samples and checks field values and truncated input.

## Upstream definitions

- [sim/mujoco/simulator_pub_msg.py](https://github.com/FFTAI/fourier_aurora_sdk/blob/b434869719ae256d02d8285e88ea2b22c1515602/sim/mujoco/simulator_pub_msg.py)

The platform.json manifest records each source revision and file SHA-256.
