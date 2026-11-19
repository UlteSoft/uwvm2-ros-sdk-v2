# Running a platform migration example

Each registered platform has a C and an F# project under `examples/platform/<platform>/migration/<language>`. Select the language at installation, copy its project into a writable directory, then use Xmake to build and test it. The C resource example and the F# action example exercise different ROS semantics.

## Install and run

Set `REV` to an SDK commit, `PREFIX` to an installation directory and `PLATFORM` to the selected registry identifier. For C, provide a trusted, signed site profile for the wasm32 MTE/EH producer. It supplies the compiler and sysroot paths.

```sh
python3 install/bootstrap.py install --commit "$REV" --platform "$PLATFORM" \
    --language c --prefix "$PREFIX" --site-profile "$C_SITE" -- --component migration
export UWVM_ROS_SDK_ROOT="$PREFIX/$REV/$PLATFORM/c/migration"
export WROS_VM=/absolute/path/to/uwvm2-ros
cp -R "$UWVM_ROS_SDK_ROOT/examples/platform/$PLATFORM/migration/c" ./resource-example
cd resource-example
xmake f -c -y -a wasm32
xmake -j1
xmake test -j1
```

The build checks the original ROS 2 `sensor_msgs` manifest and `msg/Imu.msg`, then embeds the resource in the guest. To select the platform project's upstream resource instead, point `WROS_ROS_PACKAGE_ROOT` to the directory containing the exact package manifest specified by its README, then rebuild and rerun the tests. Resources in externally supplied vendor packages stay local. Both the resource bytes and manifest must match the SHA-256 digests in `upstream.lock`. The guest checks exact URI lookup, byte count, content checksum and a missing-resource result. It needs no filesystem or network grant.

For F#, install the same component with `--language fsharp`, omitting the C site profile. Prepare the checked Microsoft SDK and Mono compiler, then copy the F# project.

```sh
export UWVM_ROS_SDK_ROOT="$PREFIX/$REV/$PLATFORM/fsharp/migration"
python3 "$UWVM_ROS_SDK_ROOT/language/csharp/prepare_host.py" --language fsharp --prefix "$HOST_TOOLS"
export WROS_DOTNET="$HOST_TOOLS/dotnet" WROS_MONO="$HOST_TOOLS/compiler"
export WROS_TOOLCHAIN=/absolute/path/to/wasm-llvm
export WROS_VM=/absolute/path/to/uwvm2-ros WROS_RUN_QUERIES=abi
cp -R "$UWVM_ROS_SDK_ROOT/examples/platform/$PLATFORM/migration/fsharp" ./goal-example
cd goal-example
xmake f -c -y -a wasm32
xmake -j1
xmake test -j1
```

The F# guest checks all ten ROS 1 wire status values. It expects the terminal states PREEMPTED, SUCCEEDED, ABORTED, REJECTED, RECALLED and LOST. LOST is a client-side determination. The scene ABI query seeds the traversal and checks that the guest runs against ABI 2. The test grants only this query. These two projects verify resource migration and local status interpretation. Device control, DDS interoperability and robot dynamics require independent tests. [ROS 1 wire values](https://github.com/ros/common_msgs/blob/092bc230c8153dd4cfee0c84c9796cc7e6b09fdb/actionlib_msgs/msg/GoalStatus.msg) and [actionlib client semantics](https://github.com/ros/actionlib/blob/noetic-devel/actionlib/include/actionlib/client/simple_client_goal_state.h).
