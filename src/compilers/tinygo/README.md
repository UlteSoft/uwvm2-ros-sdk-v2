# TinyGo for WASIp1

`wrtg` uses TinyGo 0.38.0 to emit whole-program LLVM bitcode, including the Go runtime. The SDK's `prepare-ir` selects WasmMTE attributes. Its LLVM 23.1.5 Clang and wasm-ld generate the wasm32 module. The Go standard library and Go tools come from the checked Go 1.24.2 package.

## Installation modes

- **Binary** installs the registered native `wrtg` and `prepare-ir`, the SDK backend, the checked official TinyGo frontend, its WASIp1 target and runtime resources, and the SDK runtime changes listed in `upstream.json`.
- **Source** builds `wrtg`, the LLVM 23.1.5 IR tool and the TinyGo frontend. It extracts runtime resources from the checked TinyGo package while skipping its executable. The Go bootstrap builds the frontend with the upstream GNUmakefile and the static Clang, LLD and LLVM libraries compiled from `frontend/llvm-project`. The source runtime in `upstream/src/runtime` is installed into TINYGOROOT. Both installation modes use the SDK's packaged guest Clang and wasm-ld.
- **Bindings** installs the public Go interfaces and examples.

The frontend and its native dependencies are independently editable. `upstream/` contains the TinyGo sources. `frontend/llvm-project/` contains the production sources selected from Espressif LLVM 19.1.2, including the Mach-O compact-unwind definitions required by LLD. `frontend/vendor/` contains Go module sources. The source build resolves imports offline with `-mod=vendor`. [TinyGo revision](https://github.com/tinygo-org/tinygo/tree/733a17d470870afc9c821524ce291ec5062d682b) · [Espressif revision](https://github.com/espressif/llvm-project/tree/510a078c1ad4aee4460818bcb38ff0ba3fbf6a83)

## Rebuilding the native frontend separately

Use Python 3, GNU Make, CMake, Ninja, a Linux x86-64 C/C++ toolchain and the Go bootstrap from an installed SDK. Run from the SDK source checkout.

```sh
python3 -I -B src/compilers/tinygo/rebuild_frontend.py \
  --goroot "$UWVM_ROS_SDK_ROOT/libexec/go" --jobs 2 \
  --work "$PWD/.tmp/tinygo-frontend" \
  --output "$PWD/.tmp/tinygo-frontend/bin/tinygo"
```

The recipe configures the libraries under `WORK/llvm-build` and reuses that directory on retry. `--llvm-source` accepts an external checkout of the pinned commit. `--llvm-build` can resume an existing matching CMake build. `--modcache` optionally selects a checked Go module cache. Source installation calls this recipe itself and installs the resulting ELF as `libexec/tinygo/bin/tinygo`.

## Source provenance

`frontend/sources.json` records the Espressif commit and upstream tree, the source directories included, excluded test suites, content fingerprints, and the 28 modules with their upstream source and go.mod checksums. The exporter checks each LLVM file against its Git blob. It runs Go module verification and compares every exported module's two sums against TinyGo's original `upstream/go.sum`. A maintainer can reproduce the export using a checkout containing the six recorded project directories and a populated module cache.

```sh
python3 -I -B src/compilers/tinygo/vendor_frontend.py \
  --llvm-source "$ESPRESSIF_LLVM_CHECKOUT" --goroot "$GO1242_ROOT" \
  --modcache "$TINYGO_MODULE_CACHE" --work "$PWD/.tmp/vendor-work" \
  --output "$PWD/.tmp/frontend-inputs"
```

## Guest options and qualification

The ABI uses 32-bit Go int, pointer and uintptr, one unshared memory32, `scheduler=none`, the conservative collector and the WASI command entry point. `--memory64` and `--no-memory64` identify the VM's permitted grammar. Both emit memory32. The CLI rejects wasm64, shared threads, MVP and 64-bit Go words.

`--eh` emits a module-owned terminal panic tag and enables the exception-handling assembler feature. `--no-eh` uses TinyGo's trap strategy. Normal deferred calls execute on return. The upstream wasm32 frontend has no recoverable panic frames or longjmp provider. The SDK's Wasm panic path therefore dispatches to the terminal handler directly. `--mte` enables collector lifetime operations and backend instrumentation. `--no-mte` selects the upstream conservative allocation path. [Upstream wasm32 panic implementation](https://github.com/tinygo-org/tinygo/blob/733a17d470870afc9c821524ce291ec5062d682b/compiler/defer.go)

The accepted optimization levels are `-O0`, `-O1`, `-O2`, `-Os` and `-Oz`. With no level specified, the frontend uses level 2 and the backend uses level 3. Previous isolated diagnostics ran the selected Go2 and HG projects under both VM engines, with EH on and off, using the official frontend and scratch fixes for assembly and strlen. Before the target-specific panic fix, the independent `-O0` module imported an unresolved `env.tinygo_longjmp`. Cold installations, the full feature/optimization matrix and execution with the independently rebuilt native frontend still require a run against the final archives and source. [Recorded Unitree results](../../../document/qualification/unitree-947c3067.json)

## Frontend release identity

The current binary selection uses the executable from TinyGo's published Linux
archive. Its receipt is `bin/packages/linux-x86_64/wrgo/tinygo/host.json`. The SDK
source build uses the pinned source revision, Go bootstrap, native toolchain and
vendored Espressif libraries. Its ELF has a distinct build identity. For an SDK
release of this build, run two source builds in different work directories with
the same host toolchain, compare the unmodified ELFs including DWARF and GNU
build ID, and qualify the guest outputs. The Go action directories in cgo
compilation units use Go's own debug prefix map.

`src/compilers/go/rebuild.py --language tinygo --mode source --package-dir DIR`
(with `--prefix` and `--work`) writes the controlled frontend as a separate
`tinygo-frontend` release record. To promote it, publish its content-addressed
archive with the regenerated native records and add
`"tinygo-frontend": ["share/toolchains/tinygo-llvm/frontend"]` to both copies
of `native_outputs` (the Linux release catalog and the TinyGo selection source).
The installer then takes only resources from the official bundle and installs
the SDK-built ELF in `libexec/tinygo/bin/tinygo`. Keep the official input
receipt and the SDK-built release record under their respective identities.
