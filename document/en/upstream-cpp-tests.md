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
