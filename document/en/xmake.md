# Building a Wasm application with xmake

## First application

Install one development selection using a full commit ID. The installer returns its absolute `directory`. The shared declarations live in `tools/xmake/ros.lua`. An application loads them once. Every target specifies its language and vendor. The source file in this example calls `uwvm_ros_v2.abi` through the SDK header.

```sh
python3 install/bootstrap.py install --commit "$REV" --platform unitree --language c --prefix "$PREFIX" --site-profile "$SITE"
export UWVM_ROS_SDK_ROOT="$PREFIX/$REV/unitree/c/development"
cp -R "$UWVM_ROS_SDK_ROOT/examples/c" ./robot-project
cd robot-project
xmake f -p wasm-wasip1 -a wasm32
xmake -v robot
```

The default release output for the example is `build/wasm-wasip1/wasm32/release/robot.wasm`. For a local execution set `WROS_VM` to the absolute path of your trusted `uwvm2-ros` binary. This example requires the ABI query. A target build does not grant runtime authority.

```sh
WROS_RUN_QUERIES=abi WROS_VM=/absolute/path/to/uwvm2-ros xmake run robot
```

Set `SITE` to the operator-provided site configuration. The C, C++, Fortran and Lua development selections use its verified compiler and sysroots during an xmake build. Leave both `WROS_TOOLCHAIN` and `WROS_SYSROOTS` unset to use the site selection. An explicit build profile must match a qualified release. For a separately provisioned toolchain, set both variables.

## Project file

```lua
includes(path.join(os.getenv("UWVM_ROS_SDK_ROOT"), "tools/xmake/ros.lua"))
target("robot")
    set_kind("binary")
    set_language("c")
    set_ros_platform("unitree")
    set_wros_profile({core = "3.0", mte = true, eh = true, std = "c17"})
    set_optimize("fastest")
    set_symbols("debug")
    add_files("body.c")
target_end()
```

### SDK declarations

| Declaration | Arguments and behavior |
| --- | --- |
| `set_language(id)` | Select the language identifier for the current target. The SDK checks the installed directory, language adapter and frontend. |
| `set_ros_platform(id)` | Select the exact installed vendor or platform. Every published guest development package is available on each registered platform. Driver access requires a separate deployment grant. |
| `set_wros_sdk(directory)` | Override the default SDK selection for one target. Supply an installed `development` or `compiler-source` directory from the same commit as the shared declarations. This supports multiple language and platform selections in one project. |
| `set_wros_profile(table)` | Set one or more target-local fields from the table below. An unknown field fails configuration. |
| `add_wros_lua_operations(name, ...)` | Import the named ROSv2 operations into a Lua guest. The compiler checks each name against the pinned VM catalog. Deployment must expose the imports and grant the requested resource actions. |
| `add_wros_exports(name, ...)` | For a C or C++ binary, export additional named Wasm functions alongside `_start`. Each name must match the frontend's C identifier syntax. |

| Profile field | Type and default | Meaning |
| --- | --- | --- |
| `core` | String, `"3.0"` | Select `"3.0"` or `"mvp"`. MVP selects the Core 1.0 baseline with wasm32, single thread, EH off. MTE follows its own target setting. |
| `mte` | Boolean or `"legacy"`, default true | The default requires a reviewed neighbor-aware release. Use false for a matching uninstrumented sysroot or `"legacy"` to build with unqualified tagged inputs and a warning. C/C++ source attributes can change local instrumentation. [Release and application review](memory-qualification.md) |
| `build_receipt` | Boolean, false | For linked Wasm targets, write the artifact-specific `.wros-build.json` sidecar next to the binary. |
| `eh` | Boolean, true for Core 3.0 | Select the matching exception runtime. Default false on MVP. |
| `herbceptions` | Boolean, true for C++ | Enable typed error returns in wrcc independently of `eh`. Other languages reject this field. |
| `std` | Optional string | C accepts `c11`, `c17`, `c23`. C++ accepts `c++17`, `c++20`, `c++23`. |
| `lua_abi` | Boolean, false | Include `wros.abi()` in a Lua application. Local VM execution also requires the operator to expose the ABI query. |
| `lua_seed` | Optional unsigned 32-bit integer | Build Lua with `--guest-seed` and no host clock import. |

For example, a Nim program can use the generic ROSv2 ABI on Booster. Install with `--platform booster --language nim` and select `set_ros_platform("booster")` and `set_language("nim")` in Xmake. A device session requires an external driver and a deployment grant. Vendor-specific operations require independent implementation and qualification.

### Xmake target controls

| Control | Guest build behavior |
| --- | --- |
| `target(name)`, `target_end()` | Define the scope for an application or library. |
| `set_kind("binary")` | Produce a Wasm module. C and C++ entry points use the reactor link mode and export `_start`. |
| `set_kind("static")` | Compile C, C++ or Fortran sources into a deterministic archive of matching, verified Wasm objects. Static producers currently accept sources only. |
| `add_files(...)` | C accepts `.c`. C++ accepts `.cpp`, `.cc`, `.cxx`, `.C`. Binary links can include SDK-validated `.o` and `.a`. A Lua target takes one `.lua` application. |
| `add_deps(name, ...)` | Link C, C++ and Fortran applications against SDK-built static targets. The frontend checks object profiles and compiler digests. |
| `set_plat(id)`, `xmake f -p id` | `wasm-wasip1` by default. Use `wasm-wasip1-threads` for a matching threaded toolchain and sysroot. |
| `set_arch(id)`, `xmake f -a id` | Select `wasm32` (default) or `wasm64`. In the project use `get_config("arch")` to honor the command-line selection. |
| `add_includedirs(...)`, `add_defines(...)` | Pass include directories and object-like preprocessor definitions to the C/C++ frontend. |
| `set_optimize(level)` | For C/C++, `none`, `fast`, `faster`, `fastest`, `smallest` map to `-O0`, `-O1`, `-O2` (default), `-O3`, `-Os`. |
| `set_symbols("debug")` | Include C/C++ debug information. Combine with `set_optimize("fastest")` for source-level profiling. |
| `set_filename(name)`, `set_targetdir(directory)` | Change the artifact name or directory. A binary filename must end in `.wasm` and a static archive in `.a`. |
| `includes(...)`, `path.join(...)`, `os.getenv(...)` | Load the common declarations and read the operator's selected SDK directory. |

Raw C/compiler/linker flags, host packages, host library directories and frameworks are rejected on SDK targets. Host-side build scripts run with the developer's permissions. Runtime permission enforcement belongs to the VM. The [upstream API index](xmake-api-index.md) covers Xmake's description functions, built-in script modules and extension modules, with links to signatures and examples.

### Tools, language profiles and local execution

| Variable | Meaning |
| --- | --- |
| `UWVM_ROS_SDK_ROOT` | Installed SDK selection containing the common xmake entry. |
| `WROS_PLATFORM` | Platform selected by the bundled C example (default `unitree`). Other projects can call `set_ros_platform` directly. |
| `WROS_TOOLCHAIN`, `WROS_SYSROOTS` | C/C++ and Lua toolchain prefix and exact sysroot receipt. A missing matching profile fails the build. |
| `WROS_SYSROOTS_NO_MTE` | Optional receipt selected for targets with mte = false. If unset, WROS_SYSROOTS must contain the requested profile. |
| `WROS_VM` | Absolute path of the developer-selected VM for `xmake run`. |
| `WROS_RUN_QUERIES` | Optional comma-separated local test grants. Allowed names are `abi`, `realtime-clock`, `monotonic-clock`, `realtime-resolution`, and `monotonic-resolution`. Empty by default. For a full deployment policy use the deployer or the VM CLI. |

Lua builds with Core 3.0, single thread, selectable MTE, EH and `-O3 -g`. The TinyGo adapter builds a wasm32 Go module with a conservative collector. The numerical Fortran adapter supports wasm32 and wasm64. Standard Go uses a separate compiler and runtime. A missing compiler, incompatible sysroot, unavailable adapter or disallowed final import ends the build. Processor or platform inventory entries alone do not enable compilation.

### Selective installation and adapter layout

Each development installation contains the common declarations plus `platform/<platform>/xmake/platform.lua` and `language/<language>/xmake/adapter.lua`. The isolated revision hook checks the pair before installation. The bootstrap fetches the selected files, verifies their lengths and hashes and reuses identical blobs. The protocol and raw bindings components can be installed independently. To add a second target, install its specific pair and point that target's `set_wros_sdk` at the second selection.

Platform adapters export `describe()` with `id`, `languages`, and `admission`. Language adapters export `describe()` with `id`, `program` and `extensions`. C-family adapters select the common C builder. Other adapters can implement `validate(target, request)` for configuration and `build(target, request, sources)` for compilation. The loader verifies the selection before invoking either. Shared code controls artifact naming and executes local test guests through the VM.

### TinyGo and numerical Fortran

Use `set_language("tinygo")` and `add_files("go.mod")` for a Go main module. Set `WROS_GOROOT` and `WROS_TINYGOROOT` to the verified Go and TinyGo releases. The optional `WROS_HOST_CXX` selects the host C++ compiler used to build the LLVM helper. This guest uses wasm32, Core 3.0, a single thread and `-O3 -g`. See [TinyGo](tinygo.md).

Use `set_language("fortran")` and add the Fortran sources for a numerical program. The frontend defaults to `bin/flang` and `bin/wros-flang-mte` under the toolchain. `WROS_FLANG` and `WROS_FLANG_MTE_TOOL` may select verified tools explicitly. Checked Wasm static libraries can be added with `add_deps`. The xmake adapter exposes Core 3.0, both pointer widths and both EH modes, with one guest thread. Each build uses its selected MTE mode. See [Fortran](fortran.md).

### Rust no_std

Rust targets use `set_language("rs")` and one crate root such as `add_files("src/lib.rs")`. Set `WROS_RUSTROOT` to the pinned Rust host prefix. The adapter defaults to Wasm32 Core 3.0, panic=abort, a single thread and MTE. Use `WROS_SYSROOTS_NO_MTE` with `set_wros_profile({mte=false})` for the matching untagged profile. Optimization levels through `fastest` and debug symbols map to the Rust driver. See the [Rust guide](rust.md).

The optional Java and Kotlin synchronous AOT component uses `set_wros_jvm_main(class_name)`. See [JVM compiler and Xmake options](jvm.md).

Lua, JavaScript, JVM and C# targets select ROS imports through `add_wros_operations(...)`. C# scene programs accept `abi`. [C# scene entry](csharp.md) · [JVM compiler options](jvm.md).
