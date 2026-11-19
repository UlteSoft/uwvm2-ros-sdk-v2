# Port Jazzy tf2 BufferCore to Wasm

Install the C++ migration component at a pinned SDK commit. Supply a local ROS
Jazzy geometry2 source tree and the generated C++ headers from the matching
Jazzy installation. The tool verifies the exact three upstream files that
affect this port before creating an output directory.

```sh
python3 -I install/bootstrap.py install --commit "$SDK_COMMIT" --platform unitree \
  --language cpp --prefix "$SDK_PREFIX" -- --component migration
migration="$SDK_PREFIX/$SDK_COMMIT/unitree/cpp/migration"
python3 -I "$migration/tools/migration/tf2_buffer_port.py" \
  --tf2-source "$GEOMETRY2/tf2" --ros-prefix "$JAZZY_PREFIX" \
  --execution single-executor --output "$BUILD/tf2-port"
```

Put `$BUILD/tf2-port/include` first in every translation unit's include
search path. Compile the BufferCore translation unit specified in
`$BUILD/tf2-port/port.json`, followed by the original tf2 cache, static cache
and time sources and their rcutils dependencies. Use the C++ development
installation of `wrcc` with a signed wasm32 Core 3.0, MTE, EH profile.
The single-executor selection requires a separate, nonshared guest memory
and serial entry into that guest. The deployment must keep the module's
private memory inaccessible to other modules. A threaded build uses
`--execution threaded` and `wrcc -pthread` with a matching signed profile.

Both modes preserve Jazzy's UTF-16 YAML output, including its treatment of a
NUL character and its escaping of non-ASCII code units. The single-executor
port preserves each upstream lock scope, refuses reentrant acquisition with
a C++ exception, and releases the lock on stack unwinding. Its header
rejects atomic or pthread Wasm builds. The threaded selection retains all
original tf2 mutexes and the original BufferCore translation unit.

The tests check composition across dynamic and static edges, interpolation,
disconnected frames, past and future extrapolation, eviction, clearing and
UTF-16 serialization. The single-executor Wasm build ran on both VM engines
with all four linked Preview1 imports denied. Two native readers and one
writer exercised the threaded mode. The tested site only supplied a signed
nonthreaded compiler profile. Wasm concurrency, DDS delivery and real-time
scheduling remain separate qualification tasks.
