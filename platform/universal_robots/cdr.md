# Universal Robots dashboard messages

C, C++ and Rust provide in-memory XCDRv1 codecs for the eight message types registered by `ur_dashboard_msgs` in Universal Robots ROS 2 Driver 7.3.0, commit `9efe5e9ec2ce2f7a01e80c315dfcf10ab933e7a8`. Together they expose 16 fields and 57 named constants. The package also registers 25 services and one action. Those 26 interfaces and all 21 interfaces in `ur_msgs` are outside this release of the codecs. Independent installation and wire qualification are pending. [Pinned dashboard declarations](https://github.com/UniversalRobots/Universal_Robots_ROS2_Driver/tree/9efe5e9ec2ce2f7a01e80c315dfcf10ab933e7a8/ur_dashboard_msgs/msg) · [Upstream registration](https://github.com/UniversalRobots/Universal_Robots_ROS2_Driver/blob/9efe5e9ec2ce2f7a01e80c315dfcf10ab933e7a8/ur_dashboard_msgs/CMakeLists.txt)

## Message fields in wire order

- `OperationalMode` carries `string mode`, with the upstream values `MANUAL` and `AUTOMATIC`.
- `ProgramInformation` carries `string name`, `string description`, `uint64 created_date`, `uint64 last_saved_date`, `uint64 last_modified_date` and `string program_state`. The three dates keep the dashboard’s integer values. The declared revision states are `DRAFT` and `FINAL`.
- `ProgramState` carries `string state`. Its execution states are `STOPPED`, `PLAYING` and `PAUSED`.
- `RobotMode` carries `int8 mode`. Its ten named codes range from `NO_CONTROLLER` (−1) to `UPDATING_FIRMWARE` (8).
- `SafetyMode` carries `uint8 mode` and defines 13 named codes.
- `SafetyStatus` carries `int8 status` and defines 22 named codes. `IO_PLANE_STOP` is 23. The upstream definition leaves code 21 unnamed.
- `UserRole` carries `string role`, with the five names `PROGRAMMER`, `OPERATOR`, `NONE`, `LOCKED` and `RESTRICTED`.
- `VersionInformation` carries four `uint32` fields in order — `major`, `minor`, `bugfix` and `build`.

Each public record identifies its upstream type as `ur_dashboard_msgs/msg/<Name>`. The driver copies the three dates and program state from its dashboard response. The codecs preserve unknown numeric codes and string values. Named constants take no space in the message. [Dashboard response mapping](https://github.com/UniversalRobots/Universal_Robots_ROS2_Driver/blob/9efe5e9ec2ce2f7a01e80c315dfcf10ab933e7a8/ur_robot_driver/src/dashboard_client_ros.cpp#L377-L384)

## Framing and ownership

Supply a complete PLAIN_CDR frame. The first four bytes are the representation identifier and options. The identifier is `00 00` for big endian and `00 01` for little endian. Alignment begins at the first byte after the header. A string starts with an aligned `uint32` byte count that includes its terminal NUL. The public view exposes the bytes before that terminator. A zero-length string has a wire count of one.

Encoding measures first, writes zero alignment bytes, and emits zero options. Decoding checks the entire frame, all declared string lengths, their terminators and the final size. When the low two option bits declare transport padding, the decoder accepts the declared number of tail bytes or a frame from which the transport removed that whole tail. Other option bits and unrelated trailing bytes fail validation.

## C

Include `<uwrosv2/universal_robots/cdr/ur_dashboard_msgs.h>`. Each record has the prefix `uwrosv2_universal_robots_cdr_ur_dashboard_msgs_` followed by its ROS name. Append `_defaults`, `_encoded_size`, `_encode`, `_decode` or `_validate`. Append an upstream constant name to the record name to access that constant. String constants and decoded strings have type `uwrosv2_universal_robots_cdr_string`, with `data` and `size` members.

For example, `uwrosv2_universal_robots_cdr_ur_dashboard_msgs_RobotMode_decode(frame, length, &mode)` returns 1 on success and assigns `mode.mode`. For encoding, pass a value pointer, `uwrosv2_universal_robots_cdr_big_endian` or `uwrosv2_universal_robots_cdr_little_endian`, destination, capacity and an output byte-count pointer. On failure the public decoder leaves the value intact. Encoding expects disjoint input spans, output storage and count storage. Keep a decoded string’s source frame readable and immutable for its full lifetime.

## C++98 and later

Include `<uwrosv2/universal_robots/cdr/ur_dashboard_msgs.hpp>`. Under `namespace cdr = uwrosv2::universal_robots::cdr`, create a record with `cdr::ur_dashboard_msgs::ProgramInformation::defaults()`. Call `cdr::encoded_size(value, size)`, `cdr::encode(value, cdr::big_endian, out, capacity, written)`, `cdr::decode(frame, size, value)` or `cdr::validate<T>(frame, size)`. They return `bool`. Each message exposes `T::datatype()`. Named constants live in sibling namespaces, for example `cdr::ur_dashboard_msgs::ProgramInformation_Constants::PROGRAM_STATE_FINAL`. A `cdr::string` uses the same borrowing and destination-disjointness rules as C.

## Rust

Import `wros_observation::cdr::{Endian, Message}` and select types from `wros_observation::cdr::ur_dashboard_msgs`. Use `T::default()`, `value.encoded_size()`, `value.encode(Endian::Little, &mut out)`, `T::decode(frame)` and `T::validate(frame)`. The framing operations return `Result`. `T::TYPE` identifies the ROS type and associated constants use upstream spellings such as `ProgramState::PAUSED`. The crate uses `no_std` and string fields borrow `&[u8]` with a lifetime tied to the frame.

## Installed projects

Select `--platform universal_robots` and language `c`, `cpp` or `rust`. Copy the entire `examples/universal_robots/<language>/cdr` directory from that SDK installation to a new project. With `UWVM_ROS_SDK_ROOT` set to that installation, the project supports `xmake build` and `xmake test -j1`. Each example transcodes a hand-authored dashboard metadata frame and compares both byte orders, entirely in guest memory. The existing `observation` API and its projects expose the separate `SafetyStatus.status` accessor.
