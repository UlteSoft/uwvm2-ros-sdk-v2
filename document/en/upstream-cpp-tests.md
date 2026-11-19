# Upstream ROS C++ tests on Wasm

Run this suite against the local ROS ecosystem archive inventory. It reads the selected upstream test translation units and their package-local headers directly from archives, checks the archive SHA-256 values in the inventory, and deduplicates identical closures by relative path and file digest. The receipt retains every snapshot identity, archive-relative source path, manifest, present or absent unit, unselected C++ test file and transport-independent compiler result.

One digest-pinned velocity iterator test writes four values but compares five. The runner value-initializes the test-owned scratch array and retains all original comparisons. The fifth comparison then observes the scratch array’s initial value. The iterator produced four observable outputs. The receipt identifies the adapted test digest and records the original as unqualified.

The suite covers the listed numerical test units in angles, base_local_planner, rcpputils and nav_core2. It exercises angle wrapping and limits, grid and velocity iteration, several C++ numerical utilities and rectangular bounds. It does not create ROS nodes or connect to DDS or actuators. A passing component test does not qualify the remainder of its upstream package.

The first baseline is an actual native build with the pinned GoogleTest distribution and its XML test report. The second native build uses the restricted assertion adapter beside the runner. It records the execution count and a 64-bit trace of the assertion predicates for each test body. The Wasm reactor runs the original test bodies, checks each predicate, and must reproduce those per-case traces in both the interpreter and AOT engine. A failed assertion traps immediately. The adapter implements only the macros exercised by these suites, including GoogleTest's four-ULP floating-point equality. Compilation fails for unsupported assertion forms. Reporting uses host-side test files, so the guest needs no console, filesystem, network or WASI imports.

Invoke from the VM repository, replacing the paths with absolute local paths. Provide a fresh output directory under a project's `.tmp`. The optional lock switch yields the inherited exclusive qualification lock between batches.

```sh
/usr/bin/python3 tools/ros_scene/in_existing_cgroup.py /usr/bin/taskset -c 4-7 \
    /usr/bin/flock "$SDK/.tmp/sdk-qualification.lock" /usr/bin/python3 -B \
    "$SDK/tests/migration/upstream_cpp.py" --yield-lock "$SDK/.tmp/sdk-qualification.lock" \
    --corpus "$CORPUS" --sdk "$INSTALLED_CPP_SDK" --toolchain "$TOOLCHAIN" \
    --sysroots "$SYSROOT_RECEIPT" --vm "$VM" --output "$SDK/.tmp/upstream-cpp-run"
```

The default compiler route requires an approved strict-MTE profile for wasm32 C++17, `-O3 -g`, EH and single-thread mode. The explicit `--legacy-mte` option selects the instrumented development route and records that choice in the receipt. It does not establish strict-MTE release qualification. `results.json` distinguishes completion of the inventory traversal from successful execution of every present selected suite. The per-stage command files and logs include real compiler and VM exit codes.

For the per-package totals, run `tests/migration/upstream_cpp_report.py INPUT/results.json OUTPUT.json` under the same cgroup. The verifier checks package-local source hashes, executable identity, zero imports, native GoogleTest XML, native assertion traces, build profiles and both VM exits. It counts identical upstream translation units once per distinct local include closure. The velocity test with the corrected scratch array is reported separately from unchanged cases. Repeated archive snapshots and unselected test files have separate counts.

Strict runs verify each compiled artifact, build receipt and matching VM digest before executing the module. To record the exact SDK revision selected for compilation, pass the JSON output of the selective installation command using `--installation-receipt FILE`.

For another signed compiler/VM combination, `tests/migration/upstream_cpp_replay.py` can reuse a completed native baseline. Supply `--previous INPUT/results.json`, `--sdk`, `--installation-receipt`, `--toolchain`, `--sysroots`, `--vm` and `--output` under the same cgroup and lock. It verifies the previous source and artifact hashes, GoogleTest XML and assertion traces. It then retains those native results and rebuilds, verifies and runs every guest on both engines. The output identifies the reused receipt by SHA-256.

## Depth-image RVL

`tests/migration/depth_rvl.py` checks the RVL codec in
`compressed_depth_image_transport` against an independent encoder. From the
SDK checkout, run the following command inside the qualification cgroup and
under the shared SDK qualification lock. Supply the source corpus root, an
installed C++ development SDK with an approved strict wasm32 MTE site profile,
the corresponding VM, and a fresh output directory in `.tmp`.

```sh
/usr/bin/python3 -B tests/migration/depth_rvl.py \
  --corpus "$ROS_SOURCE_CORPUS" --sdk "$INSTALLED_CPP_SDK" \
  --vm "$UWVM_ROS" --output "$PWD/.tmp/depth-rvl"
```

The runner checks the recorded source archive for each package instance
and groups identical implementation and header bytes. In the tested inventory,
6 of 16 snapshots contain RVL. They yield two source variants, one shared by
Indigo and Noetic and one by Jazzy, Kilted, Lyrical and Rolling. For each
variant the original codec processes empty, zero, constant, alternating-delta,
variable-length integer boundary and synthetic scan frames. Every encoded
word must match the reference. Every decoded pixel must match the input.
Changing an expected word must cause the native probe to fail and both VM
engines to trap. Both engines run the same strict guest with zero imports.

This result covers little-endian, valid, locally owned RVL frames. The original
decompression API takes a pixel count and has no compressed byte length.
External frame admission, ROS image-transport plugins, PNG and the remaining
package sources require separate validation.

## Rigid coordinate transforms

Run `tests/migration/tf2_transforms.py` with the same `--corpus`, `--sdk`,
`--vm`, qualification cgroup and lock as the RVL test. Give it a fresh
`--output` directory. It selects the original tf2 LinearMath header from each
archive, including the Groovy Bullet API. Older headers that include
`ros/macros.h` use that file from the recorded ROS `cpp_common` snapshot. The run checked all 22 indexed tf2 snapshots and executed 13
distinct header sets.

Eight pose scenarios exercise parent/child transform composition, frame origin,
inverse, inverse application, relative transforms and quaternion reconstruction.
They include noncommuting rotations, an optical frame, near-zero and near-half-turn
angles, and equivalent non-unit quaternion inputs. A separate Python reference
computes positions from axis-angle rotations using Rodrigues' formula. The C++
probe loads its inputs at runtime, checks the results against that reference,
and compares native, interpreter and AOT behavior. A one-metre change in the
expected coordinate must fail on each target. The absolute error bound is
0.00003 m with float scalars and 0.00000000002 m with double scalars for these
test poses. This run covers local transform arithmetic. Timed buffer lookup,
frame-tree ownership and DDS delivery require their own integration tests.

## Jazzy BufferCore and transform history

`tests/migration/tf2_buffer_layers.py` builds the Jazzy `tf2` and `rcutils`
sources from their digest-checked archives. The full BufferCore test also
uses generated C++ message headers from a Jazzy installation. The native
compiler builds the source translation units for the test. The Wasm compiler
uses the selected strict MTE development SDK. Run each layer and target
independently under the qualification cgroup and lock.

```sh
/usr/bin/python3 -B tests/migration/tf2_buffer_layers.py \
  --layer buffer --target native --corpus "$ROS_SOURCE_CORPUS" \
  --sdk "$INSTALLED_CPP_SDK" --vm "$UWVM_ROS" \
  --ros-prefix "$JAZZY_PREFIX" --output "$PWD/.tmp/tf2-buffer-native"
```

Use `--layer cache` for the original `TimeCache`, and `--target wasm` for
strict interpreter and AOT execution. Use a different output directory on
each invocation. A failed build leaves the original diagnostic and a receipt
with `complete=false`. The fixtures use deterministic timestamps.

| Layer | Native | Strict wasm32, no threads |
| --- | --- | --- |
| BufferCore | Passed out-of-order insertion, interpolation across a dynamic and a static edge, latest time, disconnected trees, forward and backward extrapolation, and clearing the graph | Build blocked. The C++ sysroot lacks `std::mutex` required by BufferCore and `std::wstring_convert` used by Jazzy's generated ROS message headers |
| TimeCache | Passed ordered lookup after out-of-order insertion, interpolation, latest time, extrapolation, eviction and clear | Passed interpreter and AOT with all imported WASI operations denied |

The negative control offsets the expected interpolation by one metre. Native
execution returns a mismatch and the Wasm cache probe traps in both engines.
For the cache, the linked C++ library retains `environ_get`, `environ_sizes_get`,
`clock_time_get` and `proc_exit`. Each is exposed with the per-module
`deny` disposition. The test grants no filesystem, socket, environment or clock
access. The WASI build selects the original XSI `strerror_r` branch of
`rcutils` in one translation unit. The buffer builds compile ROS logging
macros at the upstream `NONE` level. These results cover in-memory behavior.
DDS reception, logging, the threaded profile and concurrent tree mutation
need separate validation.

The C++ migration component also includes a digest-pinned Jazzy BufferCore
port. Add `--port single-executor` to the Wasm buffer command for the
registered adaptation or `--port threaded` for the genuine mutex profile.
Original source results use the default `--port upstream`. See the
[installation and build instructions](tf2-buffer-port.md).

### Run the Jazzy upstream test suite

Add `--upstream-tests` to a native `--layer buffer --target native` run.
This extracts the matching Jazzy `test/simple_tf2_core.cpp` from the archive,
runs its original tests with GoogleTest, and records each test's assertion
count and predicate trace. To replay those bodies on Wasm, use
`--layer buffer --target wasm --port single-executor --upstream-tests`
and add `--native-oracle "$NATIVE_OUTPUT/results.json"`. The runner checks
that the tf2 sources, rcutils sources, installed message headers, fixture
and assertion adapter match the native receipt. The suite includes three
wall-clock tests, so this invocation allows `clock_time_get` and grants
`realtime-clock` to the named module. The guest verifies that it receives a
valid date. A separate run omits the resource grant and checks the denial. Filesystem and
network access are unnecessary. An additional build deliberately changes
the expected callback assertion count to check that a mismatch is detected.

Jazzy tf2 0.36.23 passed all 17 original test bodies in six suites on native
GoogleTest and both Wasm engines. The native trace observed 78 assertions.
The display-time test performed its original formatting call with zero
assertions. Both engines rejected an intentionally changed callback assertion
count and the clock check with its resource grant removed.

### Camera image encoding metadata

A camera, an image decoder and a Wasm algorithm must agree on channel count
and sample depth. Run the original ROS 1 or ROS 2 `sensor_msgs` header against
known pixel layouts in the qualification cgroup:

```sh
python3 tests/migration/image_encodings.py --corpus "$ROS_CORPUS" \
  --sdk "$INSTALLED_CPP" --vm "$QUALIFIED_VM" --output "$NEW_RESULTS"
```

The run examined 23 package snapshots and compiled 10 distinct header versions.
Each version ran natively and in strict-MTE wasm32 interpreter and AOT modes.
The cases cover 39 monochrome, RGB, alpha, Bayer and generic pixel layouts,
including 12-channel inputs. Older headers explicitly recognize only one
through four generic channels and must reject the 12-channel input. Both
channel and depth queries must reject unknown formats. A deliberately
wrong bit-depth reference must fail in native and both Wasm engines.

Some ROS 1 headers rely on the caller to include the C declaration of
`atoi`. The fixture supplies that declaration before the original header.
Some newer headers use C++ regular expressions. Their linked libc++ may
reference environment, clock and exit imports. The harness checks their
signatures and denies each operation. All metadata computations run with
zero granted host operations. Camera acquisition and pixel-buffer conversion
require separate qualification.
