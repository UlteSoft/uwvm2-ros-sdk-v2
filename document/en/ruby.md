# Build a Ruby guest with wrrb

The SDK embeds mruby 4.0.0 and the application in one WebAssembly Core
module. It runs the entire application and the Ruby core library inside the
VM. There are no host filesystem, process, environment, clock or socket
imports. This profile provides the embedded Ruby core. CRuby extensions,
Rubygems, file-based `require` and mirroring a host gem installation need a
separate port. The host needs Python 3.11 or later, the signed C site's
compiler and sysroot, and Ruby at `/usr/bin/ruby` for generating the pinned
interpreter's C++ symbol table.

Choose a signed C site for the target width with EH, MTE, a single thread,
and `-O3 -g`. Export the installed directory
reported by the command as `UWVM_ROS_SDK_ROOT`.

~~~sh
python3 install/bootstrap.py install --commit "$SDK_COMMIT" --language ruby \
  --platform unitree --site-profile "$C_SITE" --prefix "$PWD/sdk"
export UWVM_ROS_SDK_ROOT="$PWD/sdk/$SDK_COMMIT/unitree/ruby/development"
"$UWVM_ROS_SDK_ROOT/bin/wrrb" main.rb --ros-abi --build-receipt -o robot.wasm
~~~

The default profile uses Core 3.0, wasm32, one thread, standard Wasm EH and
WasmMTE. A signed memory64 site selects wasm64. Use `--target wasm64` to
require that width. The compiler uses `-O3 -g`. To explicitly opt out of MTE,
supply `--no-mte --toolchain PATH --sysroots FILE` with a matching plain
C/C++ sysroot. The interpreter needs standard EH for Ruby exceptions.

Ruby's GC objects use separate allocations from the selected tagged libc.
The parser uses a heap stack and places its AST storage in individually
allocated blocks that keep their ownership until the parser closes. The
runtime checks tags according to the independently configured VM policy.

## ROS calls and examples

Use `--ros-operation NAME` once for each required import. `--ros-abi` adds
`WROS.abi`. These selections determine the binary's imports. Every call is
still subject to the VM's deployment policy.

| Ruby method | Result |
| --- | --- |
| `WROS.abi` | VM's exposed ABI version. |
| `WROS.open(alias)` | Status and a typed guest capability. |
| `WROS.call(name, capability, bytes, capacity)` | Status, reply bytes or nil, and written length. |
| `WROS.close(capability)` | Host status. Success invalidates the local wrapper. |

An introspection operation that accepts capability zero can use `nil`.
Request and response transfers have a 4 MiB bound each. The bridge copies
request bytes into temporary memory and clears both transfer buffers on exit.
The Ruby reply is a guest-owned string. The runtime can trap after an
uncaught Ruby exception, including a failed assertion in a test.

Each platform includes common, extension and Noetic source migration
examples. To try a project, copy the selected example directory, enter it,
and run `xmake build`. Set `WROS_VM` to the trusted VM's absolute path and
run `xmake test -j1` for the two engine tests. A platform extension test
uses an isolated idle peer and checks that both permission denials send no
packet. See [platform examples](platform-examples.md) and [Xmake](xmake.md).
Run `xmake f -a wasm64` before building a project against a signed memory64 site.

A source checkout includes `tests/migration/noetic_costmap_ruby.py` to check
the installed migration example against Noetic's native index method. Supply
a Ruby migration installation, the VM, the pinned upstream header and a C++
compiler. The probe uses both VM engines and has zero host imports.

The source tree includes a Go2 controller for the official MuJoCo fixture.
Use the same signed Unitree SDK installation with
`tests/mujoco_guest.py --language ruby --installed-sdk "$UWVM_ROS_SDK_ROOT"`.
Supply the VM sources, executable, OpenSSL and vendor model specified in the
[simulation instructions](README.md#run-the-external-driver-simulation).
The controller obtains command deadlines through an explicitly granted
ROSv2 steady clock. Its Wasm imports no WASI operations.
