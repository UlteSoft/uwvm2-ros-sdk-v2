# ABB ROS 1 in Go and TinyGo

Use the Go module `github.com/UlteSoft/uwvm2-ros-sdk-v2/abb` to encode and decode 25 ABB messages, both bodies of 22 ABB services, and `std_msgs/Header`. The five domain packages contain 70 concrete body types. Each Go field carries its upstream name in the `ros` and `json` struct tags. Standard Go and TinyGo compile the same sources. The module uses only the Go standard library. [ABB ROS 1 definitions](https://github.com/ros-industrial/abb_robot_driver_interfaces/tree/da809cd0bb6f270c0814fca07d7d4a5c0385fc39) · [ROS Header](https://github.com/ros/std_msgs/blob/34198520757d1aab358118a0ef294fe2609fde33/msg/Header.msg)

## Install and run an external project

Start in an empty directory on Linux x86-64 with Git, curl and Python 3.11 or later. Set `toolchain=go` for standard Go or `toolchain=tinygo` for TinyGo. The commands resolve the official main branch once. To reproduce a release, assign its complete commit ID to `revision`.

```sh
toolchain=go
revision=$(git ls-remote --exit-code https://github.com/UlteSoft/uwvm2-ros-sdk-v2.git refs/heads/main | cut -f1)
mkdir -p .tmp
export TMPDIR="$PWD/.tmp" TMP="$PWD/.tmp" TEMP="$PWD/.tmp" XMAKE_TMPDIR="$PWD/.tmp"
export XMAKE_GLOBALDIR="$TMPDIR/xmake-global" XMAKE_CONFIGDIR="$TMPDIR/xmake-config"
curl -fL --retry 3 --retry-all-errors "https://raw.githubusercontent.com/UlteSoft/uwvm2-ros-sdk-v2/$revision/install.py" -o install.py
python3 -I -B install.py install --commit "$revision" --platform abb --language "$toolchain" --prefix "$PWD/sdk" > selection.json
export UWVM_ROS_SDK_ROOT="$(python3 -c 'import json; print(json.load(open("selection.json"))["directory"])')"
export PATH="$UWVM_ROS_SDK_ROOT/bin:$PATH"
unset WROS_VM XMAKE_PROGRAM_DIR
cp -R "$UWVM_ROS_SDK_ROOT/examples/abb/$toolchain" "abb-$toolchain-guest"
cd "abb-$toolchain-guest"
case "$toolchain" in
  go)    wrgo . -o direct.wasm ;;
  tinygo) wrtg . -o direct.wasm ;;
esac
xmake build
xmake test -j1
```

The direct command and Xmake compile the copied module. Xmake's two test entries run the guest through the bundled interpreter and LLVM AOT engine. The guest queries the scene ABI, exchanges a RAPID symbol request and reply in its own memory, and decodes a stamped EGM channel array. The example supplies its own observations.

Each selection contains the ABB module at `include/u2rosv2/platform/abb/go` and the scene ABI module at `include/u2rosv2/universal/go`. In a guest's `go.mod`, require the modules it imports at `v0.0.0`. Both installed compiler commands resolve those names to the selected SDK with a temporary `go.work`. The copied example includes an entire module and a working `xmake.lua`. A host Go application can also consume the wire packages by setting a local module replacement in its own project.

```sh
go mod edit -require=github.com/UlteSoft/uwvm2-ros-sdk-v2/abb@v0.0.0
go mod edit "-replace=github.com/UlteSoft/uwvm2-ros-sdk-v2/abb=$UWVM_ROS_SDK_ROOT/include/u2rosv2/platform/abb/go"
```

## Read and write a body

A pointer to every generated record implements `encoding.BinaryMarshaler` and `encoding.BinaryUnmarshaler`. Use `MarshalBinary()` to allocate an exact-size result, or supply a buffer to `MarshalROS1(dst)` and pass only the returned prefix to the next stage. Both `UnmarshalBinary(src)` and `UnmarshalROS1(src)` expect one complete body.

```go
package position

import "github.com/UlteSoft/uwvm2-ros-sdk-v2/abb/ros1/abbrapidmsgs"

// PositionX reads a serialized abb_rapid_msgs/Pos body from a caller.
func PositionX(body []byte) (float32, error) {
	var p abbrapidmsgs.Pos
	if err := p.UnmarshalROS1(body); err != nil {
		return 0, err
	}
	return p.X, nil
}

// StorePosition writes twelve bytes to dst, preserving any bytes after them.
func StorePosition(dst []byte, x, y, z float32) (int, error) {
	p := abbrapidmsgs.Pos{X: x, Y: y, Z: z}
	return p.MarshalROS1(dst)
}
```

`ROS1Size() (int, error)` reports the exact encoded length of a value. The per-type constant ending in `MinSize` gives its minimum length with empty variable fields. Encoding checks the record size against the ROS uint32 limit and the compiler's native `int`, then checks the destination length before writing. A short buffer returns zero and `ros1.ErrShortBuffer`. Empty body types encode successfully into a nil or zero-length slice.

Integers and IEEE-754 floats use little-endian bytes with no field padding. Booleans occupy one byte, either 0 or 1. A string starts with a little-endian uint32 byte count and preserves embedded NULs and arbitrary bytes. A sequence starts with a uint32 element count followed by its records in declaration order. Nil and empty Go slices both encode a zero count. A decoded empty sequence is nil. The transport supplies the connection header, outer frame length and service success byte. Pass the bytes after that framing to the body decoder. [ROS serialization](https://github.com/ros/roscpp_core/blob/noetic-devel/roscpp_serialization/include/ros/serialization.h)

Decoding first walks the complete body and validates booleans, string lengths, sequence counts, and the absence of trailing bytes. Counts must fit the remaining bytes at the element type's minimum size. The decoder creates the owned strings and element slices after that pass. On success the record owns its Go strings and slices, so the caller can reuse its input buffer. On error the receiver retains its previous value. The `ros1` package exposes `ErrNil`, `ErrLength`, `ErrTruncated`, `ErrTrailing`, `ErrBoolean` and `ErrShortBuffer`. Keep the input stable during decoding and the record stable during encoding. Applications receiving untrusted frames can limit the incoming byte count before handing the body to the decoder. Decoded Go structs and strings occupy additional memory.

## Header and EGM channel monitoring

Import `.../abb/ros1/stdmsgs` and `.../abb/ros1/abbegmmsgs` using the module prefix above. `stdmsgs.Header` contains `Seq uint32`, `Stamp ros1.Time` and `FrameID string`. A timestamp preserves the two uint32 words `Sec` and `Nsec`. A header occupies 16 bytes plus the frame name.

`abbegmmsgs.EGMState` adds a counted `[]EGMChannelState` after its header. Each channel includes a name, activation and convergence flags, EGM client state, motor state, RAPID execution state and a float64 utilization rate. The channel name contributes its byte length to a 17-byte minimum. The typed constants on the package include `EGMChannelStateEGMRunning` and `EGMChannelStateMotorsOn`. For periodic telemetry, read `received.Header.Stamp` before walking `received.EGMChannels` so observations from different channels retain their common acquisition time. [EGM interface](https://github.com/ros-industrial/abb_robot_driver_interfaces/tree/da809cd0bb6f270c0814fca07d7d4a5c0385fc39/abb_egm_msgs/msg)

## RAPID geometry, joint positions and loads

Import `.../abb/ros1/abbrapidmsgs`. The 11 geometry types preserve the float32 fields and nesting used by RAPID. `Pos` has three coordinates. `Orient` has quaternion components `Q1` through `Q4`. `Pose` stores a translation followed by an orientation for a fixed 28-byte body.

`RobJoint` stores six robot axis positions in degrees from calibration. `ExtJoint` stores six external axis positions in degrees or millimetres according to the axis. `JointTarget` contains both records. `ConfData` carries the axis configuration. `RobTarget` combines `Pos`, `Orient`, `ConfData` and `ExtJoint` in 68 bytes. Its translation is the tool centre point in millimetres in the current object coordinate system, including program displacement. The field documentation preserves the upstream frame and unit descriptions.

`LoadData` carries the mass, centre of gravity, orientation of the principal axes and their three moments of inertia. `ToolData` combines the hold flag, tool frame and load in 73 bytes. `WObjData` includes the robot-hold and user-frame flags, mechanical-unit name, user frame and object frame. Its minimum size is 62 bytes. [RAPID messages](https://github.com/ros-industrial/abb_robot_driver_interfaces/tree/da809cd0bb6f270c0814fca07d7d4a5c0385fc39/abb_rapid_msgs/msg)

## RobotWare StateMachine Add-In

Import `.../abb/ros1/abbrapidsmaddinmsgs`. `EGMSettings` aggregates `EGMSetupSettings`, `EGMActivateSettings`, `EGMRunSettings` and `EGMStopSettings`. The nested Go types expose the original units. For example, `SetupUC.CommTimeout` is in seconds, `Activate.LPFilter` in hertz, and `Activate.SampleRate` in milliseconds. `StateMachineState` holds a RAPID task name, state byte and EGM action byte. `RuntimeState` pairs a header with a variable number of those task records.

The four services are `GetEGMSettings`, `SetEGMSettings`, `SetRAPIDRoutine` and `SetSGCommand`. Each has concrete `Request` and `Response` body types. For example, `GetEGMSettingsRequest.Task` identifies the RAPID task. A successful transport reply carries `GetEGMSettingsResponse.Settings`, `ResultCode` and `Message`. Check the ABB result code before using the settings. [StateMachine messages and services](https://github.com/ros-industrial/abb_robot_driver_interfaces/tree/da809cd0bb6f270c0814fca07d7d4a5c0385fc39/abb_rapid_sm_addin_msgs)

## Controller status and RWS services

Import `.../abb/ros1/abbrobotmsgs`. `SystemState` contains a header, three boolean controller flags, a slice of `RAPIDTaskState` and a slice of `MechanicalUnitState`. An empty frame name and empty slices give a 27-byte minimum. `RAPIDSymbolPath` stores the task, module and symbol as three separate strings. `ServiceResponses` defines ABB's text constants and uint16 result codes. Its own message has an empty body. Go constant names start with the parent record, such as `ServiceResponsesRCSuccess`. String constants retain any literal quotation marks present in the upstream ROS constant definition.

The 18 services include Get and Set pairs for `FileContents`, `IOSignal`, `RAPIDBool`, `RAPIDDnum`, `RAPIDNum`, `RAPIDString`, `RAPIDSymbol` and `SpeedRatio`. They also include `GetRobotControllerDescription` and `TriggerWithResultCode`. For an empty request such as `GetSpeedRatioRequest`, pass an empty body to the codec. A successful transport exchange still carries the ABB result code and status message in the response.

`GetRAPIDNumRequest.Path` addresses a RAPID symbol. The response contains a float32, a uint16 result code and a string. The reply for 12.5, code 1 and an empty status string is ten bytes, `00 00 48 41 01 00 00 00 00 00`. `GetRAPIDDnumResponse` uses a float64 value. The installed example implements the ten-byte reply and checks that a truncated reply leaves the last result available. [Controller interfaces](https://github.com/ros-industrial/abb_robot_driver_interfaces/tree/da809cd0bb6f270c0814fca07d7d4a5c0385fc39/abb_robot_msgs)

## Connection headers and provenance

For a message, `ROS1Type()` returns the upstream `package/Message` name and `ROS1MD5()` returns its genmsg fingerprint. For either half of a service, both methods identify the service. For example, `abbrobotmsgs.GetRAPIDNumType` is `abb_robot_msgs/GetRAPIDNum` and `abbrobotmsgs.GetRAPIDNumMD5` is `50b6604c67513df1c689dbe2ae540bb1`. The Go request and successful response have distinct layouts and share that handshake identity. Constants take part in the fingerprint and occupy zero body bytes. [ROS genmsg fingerprint algorithm](https://github.com/ros/genmsg/blob/noetic-devel/src/genmsg/gentools.py)

In an SDK checkout, `python3 -B src/platform/abb/generate_go.py` regenerates the five domain files using `gofmt`. It reads the same pinned definitions, resolved field dependencies, minimum sizes and connection-header fingerprint implementation as the C, C++ and Rust generators. The source manifest records the full upstream revision, Git blob ID and SHA-256 of each retained definition. In an installed SDK, the field-level Go documentation is available directly from the local module.

```sh
cd "$UWVM_ROS_SDK_ROOT/include/u2rosv2/platform/abb/go"
"$UWVM_ROS_SDK_ROOT/libexec/go/bin/go" doc ./ros1/abbrapidmsgs RobTarget
"$UWVM_ROS_SDK_ROOT/libexec/go/bin/go" doc ./ros1/abbrobotmsgs GetRAPIDNumResponse
```
