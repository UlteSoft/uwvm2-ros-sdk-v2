# ABB ROS 1 message and service bodies

C, C++, Rust and Go expose 25 ABB messages, both bodies of 22 services, and the shared `std_msgs/Header`. Fields, constants, package names and handshake MD5s follow the pinned definitions. The examples exchange payloads in guest memory. Hardware, a ROS master and RobotStudio were outside the development environment. [ABB interface definitions](https://github.com/ros-industrial/abb_robot_driver_interfaces/tree/da809cd0bb6f270c0814fca07d7d4a5c0385fc39) · [std_msgs/Header](https://github.com/ros/std_msgs/blob/34198520757d1aab358118a0ef294fe2609fde33/msg/Header.msg)

## Interface coverage

- `abb_egm_msgs` supplies `EGMChannelState` and `EGMState`. A state report includes a stamped sequence of EGM channels.
- `abb_rapid_msgs` supplies `ConfData`, `ExtJoint`, `JointTarget`, `LoadData`, `Orient`, `Pos`, `Pose`, `RobJoint`, `RobTarget`, `ToolData` and `WObjData`. The header and Rust field documentation include the units and coordinate frames given by ABB. For example, `RobJoint` gives degrees from the calibration position. External axes use degrees or millimetres according to axis type.
- `abb_rapid_sm_addin_msgs` supplies `EGMActivateSettings`, `EGMRunSettings`, `EGMSettings`, `EGMSetupSettings`, `EGMStopSettings`, `RuntimeState` and `StateMachineState`. Its four services are `GetEGMSettings`, `SetEGMSettings`, `SetRAPIDRoutine` and `SetSGCommand`.
- `abb_robot_msgs` supplies `MechanicalUnitState`, `RAPIDSymbolPath`, `RAPIDTaskState`, `ServiceResponses` and `SystemState`. Eight families provide Get and Set services for file contents, I/O signals, RAPID bool/dnum/num/string/symbol values and speed ratio. `GetRobotControllerDescription` and `TriggerWithResultCode` complete the 18 services.

## Wire format

Pass a body starting at its first field. Scalars are little-endian. Strings begin with a uint32 byte length and can contain embedded NULs. A variable-length sequence begins with a uint32 element count. Nested records appear directly in declaration order. Time contains two uint32 words, seconds and nanoseconds. Constants occupy zero bytes. `GetSpeedRatioRequest`, for example, has a valid length of zero. The transport supplies connection headers, outer lengths and the service transport success byte. [ROS serialization](https://github.com/ros/roscpp_core/blob/noetic-devel/roscpp_serialization/include/ros/serialization.h) · [ROS service transport](https://github.com/ros/ros_comm/blob/noetic-devel/clients/roscpp/src/libros/service_client_link.cpp)

Decoding and validation check all nested lengths, reject trailing or truncated input and require boolean bytes of 0 or 1. Codecs preserve integer words, timestamp fields and IEEE-754 float bit patterns. Upstream field documentation describes application constraints, such as the speed ratio range of 0–100. A ROS string constant retains literal quotation marks when they appear in the ABB declaration. [ROS constant parser](https://github.com/ros/genmsg/blob/noetic-devel/src/genmsg/msg_loader.py) · [ROS type fingerprints](https://github.com/ros/genmsg/blob/noetic-devel/src/genmsg/gentools.py)

In C, C++ and Rust, decoded strings and sequences borrow immutable input bytes. Keep their storage alive until the final access, including iteration or re-encoding. To construct a sequence, borrow a readable typed array or slice. All three bindings work without a heap. Encoding checks the complete size before writing. In C and C++, keep the input record and its borrowed spans disjoint from the output buffer and byte-count slot.

## C

Include `<uwrosv2/abb/ros1/records.h>`. Record names concatenate `uwrosv2_abb_ros1_`, the upstream package, an underscore and the exact type name. For example, `uwrosv2_abb_ros1_abb_robot_msgs_GetRAPIDNumResponse` has `value`, `result_code` and `message`. Append these suffixes to each record name. All return 1 on success and 0 on error.

- `_encoded_size(&record, &size)` assigns the exact body length.
- `_encode(&record, data, capacity, &written)` writes the body. Invalid input or insufficient capacity preserves the output and count.
- `_decode(data, size, &record)` assigns the typed result after validating the complete input.
- `_validate(data, size)` checks the complete body.

Strings have `data` and `size`. A sequence element type `T` provides `T_array_values(values, count)`, `T_array_iter(&seq)` and `T_array_next(&iter, &element)`. Read `seq.count` for the element count. Message and service identity macros end in `_DATATYPE` and `_MD5`.

## C++98 through C++26

Include `<uwrosv2/abb/ros1/records.hpp>` and define `namespace r = uwrosv2::abb::ros1;`. A service such as `r::abb_robot_msgs::GetRAPIDNum` provides `Request`, `Response`, `datatype()` and `md5()`. The independent C++ headers use `throw()` in C++98/03 and `noexcept` starting with C++11.

Use `r::encoded_size(record, size)`, `r::encode(record, data, capacity, written)`, `r::decode(data, size, record)` and `r::validate<T>(data, size)`. All return `bool` and assign outputs on success. `r::Sequence<T>::from_values(values, count)` borrows typed elements. Keep the iterator from `seq.iter()` and call `next(element)` to advance.

## Rust

Import `wros_observation::ros1::Message` to use `T::decode(data)`, `T::validate(data)`, `record.encoded_size()` and `record.encode(&mut bytes)`. These return `Result` with distinct errors for truncation, trailing bytes, invalid booleans, length overflow and insufficient capacity. Strings are `&[u8]`. Variable-length arrays have `Sequence::from_values(&items)`, `.len()` and `.iter()`. Rust lifetimes tie borrowed fields to the source. The `Service` trait associates a service with its two payload types, datatype and MD5. The crate uses `no_std`.

## Go and TinyGo

The `github.com/UlteSoft/uwvm2-ros-sdk-v2/abb` module provides a package for each upstream domain. Each record offers `ROS1Size`, `MarshalROS1`, `UnmarshalROS1` and the standard Go binary marshal interfaces. Go owns the decoded strings and slices. The installed guests are `examples/abb/go` and `examples/abb/tinygo`. [Domain API, buffers and external builds](../../include/u2rosv2/platform/abb/go/README.md)

## Read a RAPID number

The RWS service provider registers `get_rapid_num` in its configured namespace. `GetRAPIDNumRequest` contains the task, module and symbol as three strings in a `RAPIDSymbolPath`. The reply contains a float32 value, uint16 result code and status string. Check the result code before consuming the value. A reply containing 12.5, success code 1 and an empty status string occupies ten bytes, `00 00 48 41 01 00 00 00 00 00`. [ABB service definition](https://github.com/ros-industrial/abb_robot_driver_interfaces/blob/da809cd0bb6f270c0814fca07d7d4a5c0385fc39/abb_robot_msgs/srv/GetRAPIDNum.srv) · [RWS registration](https://github.com/ros-industrial/abb_robot_driver/blob/d1678957d3792e6aa54582ff894db62b6a51dac0/abb_rws_service_provider/src/rws_service_provider.cpp#L143)

With the ABB selection installed, open `examples/abb/<language>/ros1` for `c`, `cpp` or `rust`. Each Xmake project encodes a request, decodes it in a local sample handler, returns a reply and decodes it at the caller. It also constructs a stamped `SystemState` and walks the RAPID task and mechanical-unit arrays. Repository sources are under `src/examples/abb/<language>/ros1`.
