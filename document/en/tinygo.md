# Build a TinyGo robot application

`wrtg` compiles a local Go module into a single wasm32 command with a
conservative garbage collector. The development host is Linux x86-64. The
guest uses Core 3.0, one linear memory and one execution thread. Its only
public application entry point in the example below is `_start`. The VM
operator grants ROS and clock operations separately.

## Install the compiler inputs

Use the TinyGo development selection of the SDK. Select the SDK's patched
LLVM 23.1.5 development build and the sysroot build receipt matching the
desired address width, exception handling and MTE mode. Keep the LLVM source
headers, generated headers and libraries referenced by `bin/llvm-config` in
place. The TinyGo frontend uses them to build a small host-side IR tool.
The host C++ compiler must be ABI-compatible with those LLVM libraries.

Obtain the following two Linux x86-64 releases. Verify the complete archive
against its SHA-256 before extracting into a trusted build prefix.

| Prefix | Release archive | SHA-256 |
| --- | --- | --- |
| `GO_ROOT` | [Go 1.24.2](https://go.dev/dl/go1.24.2.linux-amd64.tar.gz) | `68097bd680839cbc9d464a0edce4f7c333975e27a90246890e9f1078c7e702ad` |
| `TINYGO_ROOT` | [TinyGo 0.38.0](https://github.com/tinygo-org/tinygo/releases/download/v0.38.0/tinygo0.38.0.linux-amd64.tar.gz) | `edc3476ec69e309f0fd4afc1ec79c34e00a14bc3848a7133ac53f814e72faebd` |

Each prefix points to the directory containing `bin`. On every build the
driver verifies the file set and SHA-256 of the Go and TinyGo components it
uses. It builds a private view of those components and the SDK's runtime
sources. Keep these compiler inputs, the LLVM installation and the sysroot
receipts under trusted build-user ownership until compilation finishes. Package
dependencies must be available locally. The compiler uses an empty module
cache, disables automatic toolchain upgrades and selects the project's
`go.mod`.

## Develop and build

Create a new directory. Set `SDK` to the absolute path of the installed SDK
and write two files from that directory.

```sh
cat > go.mod <<EOF_MOD
module example.local/robot

go 1.24

require wros.local/scene v0.0.0
replace wros.local/scene => "$SDK/language/tinygo/scene"
EOF_MOD

cat > main.go <<'EOF_GO'
package main

import "wros.local/scene"

func main() {
    if scene.Abi() != 2 { panic("unexpected ROS guest ABI") }
}
EOF_GO

"$SDK/bin/wrtg" . -o body.wasm \
    --goroot "$GO_ROOT" --tinygoroot "$TINYGO_ROOT" \
    --toolchain "$WROS_LLVM" --sysroots "$SYSROOT_RECEIPT" \
    --host-cxx /usr/bin/c++ --print-identity
```

The example imports only `uwvm_ros_v2.abi` and uses no WASIp1 services.
The raw Go bindings under `wros.local/scene` use the argument widths of the
SDK ABI, including 64-bit buffer parameters. Pass the complete tagged pointer
where the ABI takes a guest address. The VM checks the caller's grants.

| Option | Behavior |
| --- | --- |
| `PROJECT`, `-o FILE.wasm` | Build the directory with `go.mod` and `package main`. Publish the guest atomically after import validation. |
| `--goroot`, `--tinygoroot` | Select the two pinned host release directories. |
| `--toolchain`, `--sysroots` | Select the patched LLVM build and a matching sysroot receipt. Repeat `--sysroots` for separate profiles. |
| `--host-cxx` | Select the compiler for the host LLVM IR tool. Defaults to `c++` from the system binary directory. |
| `--target wasm32`, `--core 3.0` | Select the supported guest width and core level. The frontend rejects other values and thread options. |
| `--mte`, `--no-mte` | Tag guest allocations by default. The explicit opt-out selects a separate sysroot and the upstream uninstrumented collector. The build tags are `wros_mte` and `wros_nomte`. |
| `--eh`, `--no-eh` | Select the matching EH-enabled or EH-disabled C sysroot. EH is on by default. Unhandled Go panics trap in both profiles. |
| `--print-identity` | Print a JSON record containing the selected sysroot identity and SHA-256 of compiler tools, IR tool, runtime inputs, compiled stages and published guest. |

TinyGo emits LLVM bitcode for the program and the Go runtime. The SDK marks
the live functions and mutable globals for MTE, respecting LLVM's explicit
sanitizer suppression metadata. To suppress instrumentation of one function's
stack or one global, annotate it with `//go:section .wros.no_memtag`.
For a function the package must import `unsafe`. TinyGo preserves the
function boundary, and the SDK consumes the section marker before lowering.
External calls, the allocator and other tagged objects keep their own rules.
The marker uses TinyGo's existing section directive.
[TinyGo source](https://github.com/tinygo-org/tinygo/blob/v0.38.0/compiler/symbol.go)
 The patched LLVM backend uses `-O3 -g` and its
normal proof-based elision for safe stack accesses. The tagged collector
claims aligned 16-byte granules, zeroes new objects, validates tagged roots,
and clears both object data and shadow tags during sweep. Software MTE on
wasm32 uses four tag bits. The maximum guest memory is 256 MiB and the linker
reserves a 32 KiB stack. A VM runtime choice to disable tag checking is
independent of the compiler switch selecting the collector.

The scheduler is disabled. Use explicit ROS operations for waits, messages
and device access. The runtime has empty command arguments and no console.
Its wall and monotonic clock reads use the audited WASIp1 clock API. The
noncryptographic map seed has no host entropy dependency. Cryptographic
entropy, descriptors, sockets and broad POSIX imports remain subject to the
final import allowlist. A previous output survives a refused build.

The runtime regression program checks heap reuse, freshly zeroed storage,
a live linked list across collection, object tags, and actual reclamation.
Its VM matrix includes authorized and denied ROS calls, extension parsing,
and both VM engines. Qualification is scoped to these host releases and
guest profiles.
