# Python projects with CPython 3.14.8

The Linux x86-64 SDK installs a WebAssembly CPython interpreter, the target static library and an executable Python project packager named `wrpy.py`. Select `py` or `python` with platform `unitree` or `generic`. The guest compiles and executes Python source using CPython's parser, compiler, object model and import machinery. Host Python runs the SDK tools.

## Install an immutable revision

Start in a new working directory. The commands pin the public Unitree Python candidate used in the external projects below. The installer checks Git blob identities and LFS payload hashes. The selected prefix includes Xmake, uwvm2-ros, the private Wasm C backend and the inputs needed to link projects offline.

```sh
mkdir -p .tmp
export TMPDIR="$PWD/.tmp" TMP="$PWD/.tmp" TEMP="$PWD/.tmp"
export XMAKE_TMPDIR="$TMPDIR" XMAKE_GLOBALDIR="$TMPDIR/xmake-global"
revision=a524390de584d690d773ab0fe09142f0bcb4d4fd
curl -fL --retry 3 "https://raw.githubusercontent.com/UlteSoft/uwvm2-ros-sdk-v2/$revision/install.py" -o install.py
python3 -I -B install.py install --commit "$revision" --language python --platform unitree --prefix "$PWD/sdk" > selection.json
export UWVM_ROS_SDK_ROOT="$(python3 -c 'import json; print(json.load(open("selection.json"))["directory"])')"
export PATH="$UWVM_ROS_SDK_ROOT/bin:$PATH"
unset WROS_VM XMAKE_PROGRAM_DIR
```

## Run one file with the shared interpreter

`shared/wasm32-wasip1/core3.0-eh-mte/cpython.wasm` is an executable WASI command. Its initial argument selects a guest script filename. With no script argument or with `-`, the interpreter reads Python source from stdin. The host helper below feeds the file into the same installed Wasm module on each invocation. The project working directory must be writable for the execution snapshot.

```sh
cat > measure.py <<'PY'
import math
import sys

class Series(list):
    def magnitude(self):
        return math.sqrt(sum(value ** 2 for value in self))

assert sys.version_info[:3] == (3, 14, 8)
print(Series([3, 4]).magnitude())
PY
wrpy.py --run int measure.py
wrpy.py --run aot measure.py
```

The local stdin runner explicitly enables args, console reads and writes, console metadata, clocks and process exit. It installs an empty environment and zero directory preopens. Its exact Preview1 allow and deny entries are derived from the module's imports. Starting a script by guest pathname has a known failure at this revision. With synchronous MTE and a read-only directory preopen, a one-line print script exited with status 120. In a diagnostic run with runtime tagging disabled, the script could read a file. Importing a sibling module still failed during directory enumeration. Use the packaged project below for multiple files. [Revision evidence](../../qualification/unitree-a524390d.json)

## Package a project outside the SDK

```sh
cp -R "$UWVM_ROS_SDK_ROOT/examples/unitree/py" my-unitree
cd my-unitree
wrpy.py --entry main.py --project-root "$PWD" --ros-operation abi --ros-operation capability.open main.py vectors.py -o direct.wasm
xmake build
xmake test -j1
```

Declare each source with `add_files`, the entry with `set_wros_entry`, and each ROS import with `add_wros_operations`. The packager stores source bytes and their package paths in the linked command. The guest compiles each application module on import. Include a parent package's `__init__.py` for dotted application imports. The generic example uses `collections.Counter`, a generator and a second Python file. The Unitree example exercises permission denial and checks Go2 and HG samples against four Fast-CDR fixtures. The independent `prove.py` entry starts both copies of the shared interpreter and tests an external Xmake project.

```sh
python3 -I -B "$UWVM_ROS_SDK_ROOT/examples/unitree/py/prove.py" --sdk "$UWVM_ROS_SDK_ROOT" --work "$TMPDIR"
```

## Runtime and ABI

The default target has one unshared wasm32 memory, Core 3.0, standard exception handling and packed WasmMTE. The `--memory64` and `--no-memory64` options select the VM grammar for this memory32 command. Memory64 output, shared threads, other core baselines, alternate optimization profiles, and EH- or MTE-disabled variants are outside this release. The public source rebuilt offline. The rebuilt and downloaded interpreters both ran a stdin script under INT and AOT. The two interpreters and static libraries had different hashes. Guest Python exceptions ran successfully. The modules also validate with native Wasm EH disabled.

The standard library consists of the pinned release's selected pure-Python modules, CPython's bootstrap and built-in extensions, and the statically chosen extensions in the source recipe, including `math`, `_struct`, `array`, `_json` and `_random`. Imports requiring an unavailable native extension fail in the guest. Native wheels, subprocesses and dynamically loaded host libraries are outside this build. The isolated configuration ignores host environment variables and user site packages.

Each of the 163 registered ROS imports has a function in its domain under `include/u2rosv2/universal/py/uwrosv2`. For example, `uwrosv2.capability.wr_capability_open(memory, offset, size, output)` takes the identical four integer operands as the core import. Its docstring covers the checked alias, buffer lifetime, grant, status and handle-slot semantics. Allocate a `uwrosv2.Buffer` to obtain a pinned writable view and its tagged guest address. Keep the buffer alive across all host access. The single-memory profile cannot satisfy the shared, unexported memory contract for module exchange operations. Selecting an import links that function into the module. Authority is supplied by the deployment. The shared standalone command carries no ROS imports.

The Unitree selection includes the pinned `unitree_api.msg`, `unitree_go.msg` and `unitree_hg.msg` classes. Each supports `Message.from_cdr(payload)` and `message.to_cdr("little")` or `message.to_cdr("big")`. The 43 schemas include nested records, fixed arrays, sequences and UTF-8 strings. The codec supports plain XCDRv1 with zero encapsulation options and an explicit byte limit, initially 4 MiB. It rejects other representations, truncation and trailing bytes. Python float conversions can normalize signaling NaN payloads. The fixtures cover the 1,180-byte Go2 and 2,092-byte HG LowState messages in both byte orders. The bundled adapter processes message bytes locally. Device access requires a separately authorized provider. [Unitree ROS 2 v0.3.0 message definitions](https://github.com/unitreerobotics/unitree_ros2/tree/66ae09858245ac3d2231c0cc209e36a88f8d7d03/cyclonedds_ws/src/unitree)

## Rebuild the interpreter

With the current SDK, use `install.py rebuild --jobs 2` with the matching root installer, SDK revision, selection and prefix. The SDK selects the editable 3.14.8 tree, builds a native freezer from that release, then compiles the Wasm target with the packaged compiler and WASI sysroot. A Linux host C toolchain with libc development headers, GNU Make and the CPython configure utilities is required. The source installation writes its own archive, generated headers and shared command. Local MTE allocator and WASI clock changes are recorded with their upstream hashes.

The binary selection publishes `lib/wasm32-wasip1/cpython3.14/libpython3.14.a`. Its producer receipt retains the original compiler and closure hashes. The separate shared-command receipt records the SDK linker inputs, import types and final module hash for this release. The two producer identities can be inspected independently. [Source inventory](../../../src/runtimes/cpython/upstream.json)
