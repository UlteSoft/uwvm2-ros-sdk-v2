# Python applications

`wrpy` builds one WebAssembly Core module containing CPython 3.14.8, UTF-8 application source and any explicitly bundled Python modules. On startup the guest interpreter parses and runs this source. The default development profile uses wasm32, Core 3.0, a single thread, standard EH and WasmMTE instrumentation. A signed wasm64 C site selects 64-bit Python objects and linear addresses. This version of CPython matches the original SDK's Python port. The VM controls MTE enforcement at execution.

## Install and build

Select an immutable SDK revision, an installed platform ID and an operator-approved C site profile for that revision. The following installs the Python frontend, its target interpreter material, the platform adapter and Xmake integration.

```sh
python3 install/bootstrap.py install --commit "$REV" --platform unitree --language py \
  --prefix "$PREFIX" --site-profile "$C_SITE"
export UWVM_ROS_SDK_ROOT="$PREFIX/$REV/unitree/py/development"
"$UWVM_ROS_SDK_ROOT/bin/wrpy" main.py -o robot.wasm --build-receipt
```

For a 64-bit project, select the signed wasm64 C site and append `-- --python-target wasm64` to the installer command. Its installer fetches one matching runtime archive. Use separate prefixes when both pointer widths are required at this revision. Configure an Xmake project with `xmake f -a wasm64` or pass `--target wasm64` to the compiler.

The migration selection accepts the same target option. Pass `-- --component migration --python-target wasm64` to fetch the wasm64 runtime and the selected platform's editable migration project.

The default linker uses the locally authenticated C toolchain. The distributed CPython target archive carries the compiler, libc closure, source release and build recipe hashes. An exact match permits a fast link using the verified archive. An unmatched runtime is built from the vendored Python.org source. A cold build currently requires a Linux development host with GNU Make, POSIX shell, system C compiler, binutils and writable executable temporary storage beside the output. It builds the matching host Python solely to freeze startup encodings. Cross-compilation uses the selected Wasm compiler and sysroot.

| Option | Behavior |
| --- | --- |
| `--ros-operation NAME` | Include one ROSv2 import. Repeat for each required operation. The VM must independently expose and authorize it. |
| `--ros-abi` | Include the read-only `wros.abi()` query. |
| `--module NAME=FILE` | Embed a UTF-8 Python module. Map package names to their `__init__.py`; relative imports and normal module caching work inside the guest. Up to 256 modules, 1 MiB per source, 4 MiB total. |
| `--target wasm32`, `--target wasm64` | Select the linear address width and matching CPython object layout. The site supplies the width when omitted. |
| `--eh`, `--no-eh` | Select the matching libc profile. Python exceptions operate independently of Wasm's native EH mode. |
| `--mte`, `--no-mte` | MTE defaults on. Turning it off requires explicit matching `--toolchain` and `--sysroots`. |
| `--from-source`, `--jobs N` | Rebuild the interpreter from pinned source. Limit the Make build to 1–32 jobs, default 4. |
| `--build-receipt` | Emit the C backend receipt and a Python receipt identifying sources, runtime and actual imports next to the module. |

Xmake projects include `tools/xmake/ros.lua`, call `set_language("py")`, select the installed platform, and pass one main script through `add_files("main.py")`. Add application modules using `add_wros_python_modules("robot=robot/__init__.py", "robot.math=robot/math.py")`. Declare operations with `add_wros_operations("abi")`. The install includes `examples/py/xmake.lua` and platform examples under `examples/platform/unitree/{common,extension,migration}/py` for a Unitree selection.

## Host boundary

The default module imports the two Preview 1 clock functions `clock_res_get` and `clock_time_get`. The VM uses the `_wasm64` suffix for its memory64 Preview 1 ABI. Grant clock interfaces and resources according to the clocks needed by the application. Real OS filesystem, stream, environment, network, dynamic-library, process and random-device access is unavailable to this interpreter. A developer can use the common ROSv2 APIs for authorized storage, message transport and modeled devices. The runtime checks the type and name of every final import. It includes the CPython language core, frozen interpreter startup and selected built-ins such as `math`, `_struct` and `array`. Bundling Python source provides additional pure-Python modules; applications depending on native wheels or POSIX APIs require adaptation. CPython uses a deterministic internal hash seed in the isolated profile. Use an explicitly authorized service for security-sensitive random data.

`wros.open(alias)` returns an opaque Python capsule on success, or an integer status. Call `wros.close(handle)` to release it. `wros.call(name, handle_or_None, request_bytes, output_capacity)` returns `(status, response_or_None, written)`. Both buffers are capped at 4 MiB. The VM copies only the designated buffers; the interpreter wipes its call-scoped copies before releasing them. User-owned Python values retain their usual Python lifetimes. A selected platform driver operation still requires both the platform child permission and its parent driver grant.

The MTE build disables pymalloc, mimalloc and the interpreter's shared object freelists. Independently allocated Python objects pass through the reviewed tagged libc allocator. Python objects with inline contents, cached constants, raw static tables and interpreter stack slots do not constitute independent allocations.

The official upstream source and license ship alongside its locked SHA-256. The Python fixture checks real ROS 1 Noetic `genpy` and ROS 2 Jazzy Fast RTPS serialization of `geometry_msgs/Twist`. Its scope covers this message and encoding. The hardware fixture attempts an unauthorized connection and checks that the peer received zero bytes. See [CPython 3.14.8](https://www.python.org/downloads/release/python-3148/).

The example Xmake targets register both interpreter and AOT executions with `add_wros_tests("int", "aot")`. Run `xmake build` followed by `xmake test` in the selected example directory with `WROS_VM` set to the actual VM executable. The extension test provisions only an ephemeral local test channel, exercises both parent-denied and child-disabled policies, and checks that neither wrote a handshake byte.
