# ABB ROS 1 status readers for Java

A Java application can decode a serialized robot-controller report, inspect its RAPID tasks and mechanical units, read EGM feedback, or inspect the result of a GetRAPIDNum query. The public classes are in the package `u2rosv2.abb.ros1`. The example consumes offline ROS 1 bodies and reads the WROS scene ABI version. [Application sources](../../../../../src/examples/abb/java/) · [Pinned ABB definitions](../../../../../src/platform/abb/upstream/ros1/) · [Independent genpy bodies](../../../../../src/qualification/abb/ros1-vectors.json)

## Domain API

- `Egm.EGMState` contains a stamped array of `Egm.EGMChannelState`. Each channel carries its name, active and convergence flags, client, motor and RAPID states, and utilization rate. The channel type declares ABB's state constants. [EGM readers](src/u2rosv2/abb/ros1/Egm.java)
- `Rapid.Pos`, `Rapid.Orient` and `Rapid.Pose` read Cartesian XYZ components, quaternion components q1 through q4, and the combined coordinate transformation. The library preserves the transmitted coordinate order. [RAPID readers](src/u2rosv2/abb/ros1/Rapid.java)
- `Robot.SystemState` exposes controller flags, a `RAPIDTaskState` array and a `MechanicalUnitState` array. `Robot.GetRAPIDNumRequest` identifies a symbol by task, module and symbol name in a `RAPIDSymbolPath`. Read `GetRAPIDNumResponse.resultCode` before using its float32 value. ABB assigns success code 1. The message bytes can contain the controller's explanation for a failure. [Controller and RWS readers](src/u2rosv2/abb/ros1/Robot.java) · [ABB result codes](../../../../../src/platform/abb/upstream/ros1/abb_robot_msgs/msg/ServiceResponses.msg)
- `StateMachine.RuntimeState` contains a stamped array of `StateMachineState`. Each entry gives the owning RAPID task, current state and reported EGM action. Its constants use the values on the ROS wire. [StateMachine readers](src/u2rosv2/abb/ros1/StateMachine.java)
- `StdMsgs.Header` gives the sequence number, timestamp and frame ID. `RosTime.sec` and `RosTime.nsec` preserve the two unsigned 32-bit timestamp fields in Java `long` values. [Header](src/u2rosv2/abb/ros1/StdMsgs.java) · [Timestamp](src/u2rosv2/abb/ros1/RosTime.java)

Each message or service body provides `TYPE`, `MD5`, `MIN_BYTES`, `decode(byte[])` and `decode(byte[], int offset, int length)`. Both service bodies carry the same handshake datatype and MD5. Pass exactly the body starting at its first field. Remove the TCPROS length prefix and, for a service reply, the transport success byte before calling the decoder.

```java
import u2rosv2.abb.ros1.Egm;

Egm.EGMState state = Egm.EGMState.decode(frame, bodyOffset, bodyLength);
if (state == null) return;
for (Egm.EGMChannelState channel : state.egmChannels) {
    if (channel.active) recordUtilization(channel.name, channel.utilizationRate);
}
```

A null result indicates a missing or invalid slice, truncation, trailing data, an out-of-bounds sequence length, or a boolean byte other than 0 or 1. Parsing verifies each uint32 length against the remaining bytes before allocating a string or sequence. Results own their strings and arrays. ROS string fields are `byte[]` and preserve embedded NULs and arbitrary octets. The reader retains unsigned state codes even when they exceed the currently named constants. Scalars use ROS little-endian order. [Wire reader](src/u2rosv2/abb/ros1/Wire.java)

## Build and replay

Install the ABB Java selection and copy its `examples/abb/java` project to an external directory. From that directory the installed `wrjava` compiles the user’s main class and all declared sources. The Xmake project uses the same native entry point. [Installation and Xmake](../../../../../document/en/languages/java.md)

```sh
wrjava --main-class example.Guest --source-root src --keep-work bytecode -o abb-state.wasm
"$UWVM_ROS_SDK_ROOT/share/toolchains/jdk/bin/javap" -J-XX:-UsePerfData -classpath bytecode/classes -c example.Replay
"$UWVM_ROS_SDK_ROOT/share/toolchains/jdk/bin/java" -XX:-UsePerfData -cp bytecode/classes example.Replay
xmake build
xmake test -j1
```

`example.Replay` exercises checked-in genpy bodies and malformed inputs on a host JVM. `example.Guest` calls the public scene ABI binding before replaying those bodies in the guest. The synchronous TeaVM port uses an empty argument array, a bounded nonmoving heap, and trap stubs for unsupported operations including console logging. The reader accepts bytes supplied by the application. Live controller transport, vendor execution and qualification of the new install and driver remain pending. [TeaVM sources](../../../../../src/compilers/jvm/README.md)
