# Developing a scalar controller with Go

`wrgo` uses the standard Go 1.24.2 compiler on Linux x86-64. It type-checks and optimizes one source file and emits a core wasm32 module. The producer supports pure scalar functions using `int32`, `uint32`, `int64`, `uint64` and `bool`. Arithmetic includes addition, subtraction, multiplication, bitwise operations and integer comparisons. A function may use forward conditionals, early returns and branch-dependent scalar assignments. Each function is limited to 64 control-flow blocks and 1,024 optimized values. A control-flow cycle or an unsupported optimized operation fails the build. The general Go heap, goroutines, standard library, initialization, pointers, slices, memory64 and threads require additional producer work.

## Install and build

Use the full SDK commit for `$REV`. Select one platform such as `unitree`.

```sh
python3 install/bootstrap.py install --commit "$REV" --platform unitree --language go --prefix "$PWD/sdk"
```

Set `UWVM_ROS_SDK_ROOT` to the installation directory printed by the installer. It contains `bin/wrgo`, a Linux x86-64 compiler, the guest encoder, examples and the matching Xmake adapter. Normal installation fetches this language and the selected platform. The optional `-- --component compiler-source` includes the upstream source, license and producer build script. To rebuild the host compiler, supply the matching official Linux x86-64 Go bootstrap archive to `language/go/producer/build.py --source <source.tar.gz> --bootstrap <linux-amd64.tar.gz> --output <new-directory>`. Both inputs must match the fixed release hashes. [Official Go release archives](https://go.dev/dl/#go1.24.2)

```sh
cd "$UWVM_ROS_SDK_ROOT/examples/shared/common/go"
"$UWVM_ROS_SDK_ROOT/bin/wrgo" controller.go -o controller.wasm --build-receipt
xmake f -p wasm-wasip1 -a wasm32
xmake
WROS_VM=/absolute/path/to/uwvm2-ros xmake test -j1
WROS_VM=/absolute/path/to/uwvm2-ros xmake run
```

The compiler exports each named scalar function. Define `func Start() uint32` as the guest entry. A nonzero return traps. The extension preflight opts into `uwvm_ros_v2.abi` with `add_wros_operations("abi")` or `wrgo --ros-abi`; its `Start` takes the queried ABI as a `uint32`. The VM operator authorizes this query separately. For this preflight use `WROS_RUN_QUERIES=abi` with `xmake run`. It checks the parent ABI only. Driver authority and platform child status remain separate.

For a bounded sensor conversion, a scalar export can select an adjusted value and return it to its Wasm caller.

```go
func Limit(speed int32) int32 {
    if speed > 120 {
        return 120
    }
    if speed < -120 {
        return -120
    }
    return speed
}
```

## Memory and authority

MTE defaults on. Every emitted function must pass an instruction allowlist and preserve its initial SSA memory token at every return. The encoder verifies that each operand is available on every path that reaches its use. A branch-dependent assignment selects the value from the actual incoming edge. Wasm callers pass Go booleans as i32 values, with every nonzero value normalized to true on entry. The encoder emits no memory, loads, stores or indirect calls. This proves that the published function needs no tags. The same constraint applies to explicit `--no-mte`. No WASI imports, native guest programs, components or host Go compiler fallbacks are exposed. The optional build receipt records the exact input, producer and guest digests, imports and MTE policy.

The output includes Wasm function names for the debugger. Go source lines and variable inspection require source metadata beyond this profile.

Installations may additionally pass an operator-provided `--site-profile <file>`. It pins a specific WSEA-signed release for this scalar profile, the exact host compiler and encoder, both VM engine test receipts and an admission and Xmake receipt. Each build rechecks the signed statement. An ordinary commit-pinned installation needs no site statement.

The shared migration example reproduces unsigned grid indexing and checks interior, row-boundary and wraparound cases. It ports one operation. [ROS Noetic Costmap2D::getIndex](https://github.com/ros-planning/navigation/blob/noetic-devel/costmap_2d/include/costmap_2d/costmap_2d.h#L171-L174)
