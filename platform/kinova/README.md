# kinova read-only observations

`kortex_driver/ActuatorCyclic_Feedback`. Read Kortex actuator feedback ID, communication jitter, main-board voltage and motor temperature from the generated ROS message.

Supply a compact ROS 1 message body, starting at its first field. The accessors are `read_feedback_id_identifier`, `read_jitter_comm`, `read_voltage`, `read_temperature_motor`.

C applications include `<uwrosv2/kinova/observation.h>` and use the `uwrosv2_kinova_` function prefix.
C++98 and later include `<uwrosv2/kinova/observation.hpp>` and use namespace `uwrosv2::kinova`.
C takes an output pointer and C++ takes an output reference. Both write the value on success. The Rust crate `wros_observation` returns `Option<T>`.
JS and TypeScript import the accessors from `uwrosv2/platform/kinova/observation` and pass a Uint8Array. Invalid records return undefined. The 64-bit integer fields return bigint.
In the AssemblyScript bounded-driver profile, pass a staged request length or set the final argument to true to read the last successful driver reply. Each successful accessor returns true and sets the exported field value.
The standalone WAT library at `include/u2rosv2/platform/kinova/wat/observation.wat` exports its memory and the named functions. Supply the input address, length, optional array index and output address. A return value of 1 stores the field at its original width in little-endian order.

## Run the example

Install `--platform kinova` and the selected language. Copy `examples/kinova/<language>` into a user project and set `UWVM_ROS_SDK_ROOT` and `WROS_VM`.
Run `xmake build` and `xmake test -j1`. The guest reads constructed offline samples and checks field values and truncated input.

## Upstream definitions

- [kortex_driver/msg/generated/actuator_cyclic/ActuatorCyclic_Feedback.msg](https://github.com/Kinovarobotics/ros_kortex/blob/c3280d8a6a6b5d96590d51538e3f265710a6c77d/kortex_driver/msg/generated/actuator_cyclic/ActuatorCyclic_Feedback.msg)
- [kortex_driver/msg/generated/actuator_cyclic/ActuatorCyclic_MessageId.msg](https://github.com/Kinovarobotics/ros_kortex/blob/c3280d8a6a6b5d96590d51538e3f265710a6c77d/kortex_driver/msg/generated/actuator_cyclic/ActuatorCyclic_MessageId.msg)

The platform.json manifest records each source revision and file SHA-256.
