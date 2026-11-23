# Franka ROS 2 in Go and TinyGo

The module `github.com/UlteSoft/uwvm2-ros-sdk-v2/franka` supplies typed XCDRv1 PLAIN_CDR encoders and decoders for all 137 records derived from the 53 pinned ROS 2 declarations. Standard Go 1.24.2 and TinyGo 0.38.0 use the same local package. Each Go file links its upstream declaration and documents the units, reference frame, range or protocol meaning of each field. [中文](README.zh.md) · [Platform CDR guide](../../../../../platform/franka/cdr.md)

## Messages and services

- Import `.../franka/cdr/frankamsgs` for 77 records covering arm state, impedance, collision thresholds, payloads, frames, gripper and point-to-point actions. `FrankaRobotState.MeasuredJointState` carries the joint names, positions in rad, velocities in rad/s and link-side torques in N·m. The semantic component translates the libfranka joint sample into these fields, stamps them in the base frame and publishes the Elbow, pose, inertia, wrench and accelerometer fields in the same record. `GraspFeedbackMessage` pairs the goal UUID with the current gripper width in metres. [Franka semantic component](https://github.com/frankarobotics/franka_ros2/blob/4acc05c01ebfcdf916ee6b3df966df0ad7b2f9ec/franka_semantic_components/src/franka_robot_state.cpp) · [Grasp action](https://github.com/frankarobotics/franka_ros2/blob/4acc05c01ebfcdf916ee6b3df966df0ad7b2f9ec/franka_msgs/action/Grasp.action)
- Import `.../franka/cdr/frankaspinemsgs` for 35 records covering the spine state and position, user travel limits, seven services and the MoveAbsolute action. `GetPositionResponse.Position` carries metres. `GetPositionEvent` associates its optional request and response with the client GID and sequence number. [Spine definitions](https://github.com/frankarobotics/franka_ros2/tree/4acc05c01ebfcdf916ee6b3df966df0ad7b2f9ec/franka_spine/franka_spine_msgs)
- The other 25 records live in `cdr/actionmsgs`, `cdr/builtininterfaces`, `cdr/geometrymsgs`, `cdr/sensormsgs`, `cdr/servicemsgs`, `cdr/stdmsgs` and `cdr/uniqueidentifiermsgs`. Nested fields use these concrete Go types. For example, `actionmsgs.GoalStatusArray.StatusList` is a slice of goal status records, and `servicemsgs.ServiceEventInfo.ClientGID` is a 16-octet array. Jazzy rosidl supplies each action's Goal, Result, Feedback, FeedbackMessage and both service envelopes. [Jazzy rosidl definitions](https://github.com/ros2/rosidl/blob/9bcfabf3eddf8e63fb4332dca6da7ec6f3140d65/rosidl_parser/rosidl_parser/definition.py)

Use the Go component name without underscores, such as `frankamsgs.PTPMotionSendGoalRequest`. Its `ROS2Type()` returns `franka_msgs/action/PTPMotion_SendGoal_Request`. The `ros` struct tag gives the original field spelling. Constants keep the declared integer width. The ordinary Go zero value sets all numbers to zero. Use `DefaultGraspGoal()` for the declared inner and outer tolerances of 0.005 m, and `geometrymsgs.DefaultQuaternion()` for W = 1. Constructors also apply nested declaration defaults. [GraspEpsilon](https://github.com/frankarobotics/franka_ros2/blob/4acc05c01ebfcdf916ee6b3df966df0ad7b2f9ec/franka_msgs/msg/GraspEpsilon.msg) · [Quaternion](https://github.com/ros2/common_interfaces/blob/a941f14bb318d8d904505ed935ccbb97f24a70a4/geometry_msgs/msg/Quaternion.msg)

## Frames and ownership

`UnmarshalCDR(frame)` and `UnmarshalBinary(frame)` accept a complete four-byte encapsulation header and payload. The identifier selects big or little endian. Every nested scalar aligns from the byte immediately after the header. A fixed array has no count prefix. A sequence has a uint32 element count, bounded to one for each service-event request and response. A string's uint32 byte count includes the required final NUL. The Go value preserves all preceding bytes, including embedded NULs. Booleans accept only 0 and 1. Rosidl empty components serialize their one-byte placeholder. [CDR framing and transport padding](../../../../../platform/franka/cdr.md)

The decoder scans the entire frame before allocating strings or element slices. It checks native integer limits, counts against the remaining payload, schema bounds and tail padding. Keep the input stable until the call returns. On success the record owns its strings and slices and the transport buffer can be recycled. Empty decoded sequences are nil slices. An error preserves the receiver. `frankamsgs.ValidateElbow(frame)` and the corresponding per-record functions validate without materializing dynamic fields.

`CDRSize()` includes the four-byte header. `MarshalCDR(cdr.BigEndian, dst)` or `MarshalCDR(cdr.LittleEndian, dst)` returns the number of bytes written. It measures lengths and checks the destination capacity first. Keep the source stable and disjoint from the output. `MarshalBinary()` allocates an exact-size little-endian frame. Writers zero alignment padding and encapsulation options. Readers accept the declared low two-bit tail count with the tail either present or removed by the transport. An inconsistent count returns `cdr.ErrPadding`, and extra bytes return `cdr.ErrTrailing`.

## Build an external project

Start in an empty directory on Linux x86-64 with Python 3.11+, Git and curl. The commands pin the public Franka candidate under independent qualification. The standard Go project transcodes two independent 84-byte Fast-CDR Elbow frames and decodes a semantic-component state sample. The TinyGo project reads gripper feedback and a 0.42 m spine service reply. Both call the scene ABI in the guest. The example payloads come from local buffers. [Elbow frame provenance](https://github.com/eProsima/Fast-CDR/tree/9f4e60f7ac958e0fbbfe949102de3929cbbc226f) · [Upstream spine controller sample](https://github.com/frankarobotics/franka_ros2/blob/4acc05c01ebfcdf916ee6b3df966df0ad7b2f9ec/franka_spine/franka_spine_server/test/test_spine_controller.py#L311)

```sh
set -eu
revision=17ff81a1662824a25f81cd056c02232dfbe23541
curl -fLsS --retry 3 "https://raw.githubusercontent.com/UlteSoft/uwvm2-ros-sdk-v2/$revision/install.py" -o install.py
mkdir -p .tmp
export TMPDIR="$PWD/.tmp" TMP="$PWD/.tmp" TEMP="$PWD/.tmp" XMAKE_TMPDIR="$PWD/.tmp"
export XMAKE_GLOBALDIR="$TMPDIR/xmake-global" XMAKE_CONFIGDIR="$TMPDIR/xmake-config"
export GOPROXY=off
unset WROS_VM XMAKE_PROGRAM_DIR

for language in go tinygo; do (
    python3 -I -B install.py install --commit "$revision" --platform franka --language "$language" \
        --prefix "$PWD/sdk" > "$language-selection.json"
    export UWVM_ROS_SDK_ROOT="$(python3 -c 'import json,sys; print(json.load(open(sys.argv[1]))["directory"])' "$language-selection.json")"
    cp -R "$UWVM_ROS_SDK_ROOT/examples/franka/$language" "$language-project"
    cd "$language-project"
    case "$language" in go) compiler=wrgo ;; tinygo) compiler=wrtg ;; esac
    "$UWVM_ROS_SDK_ROOT/bin/$compiler" . -o direct.wasm
    for engine in int aot; do
        python3 -I -B "$UWVM_ROS_SDK_ROOT/tools/xmake/run_guest.py" direct.wasm \
            --engine "$engine" --core 3.0 --mte --eh --memory64 --no-threads --query abi --query go-runtime
    done
    "$UWVM_ROS_SDK_ROOT/bin/xmake" build
    "$UWVM_ROS_SDK_ROOT/bin/xmake" test -j1
); done
```

The selected SDK supplies its own real `wrgo` or `wrtg`, Xmake, VM and Go modules. The launcher binds the public module names in the project's `go.mod` to that installation. In an SDK source checkout, `python3 -B src/platform/franka/generate_go.py` regenerates the domain files using the pinned schema, source digests, documentation and `gofmt`.
