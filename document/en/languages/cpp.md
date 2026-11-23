# C++ guest projects

Install the C++ selection with `--language cpp`, then set `UWVM_ROS_SDK_ROOT` and `WROS_VM` as described in the [installation guide](../install-xmake.md). The native `wrcc` driver finds the installed C++ headers and the selected platform's public headers. The `examples/cpp` project checks the guest ABI version. Run the compiler from a copy of that directory.

```sh
"$UWVM_ROS_SDK_ROOT/bin/wrcc" --reactor --export _start --std c++20 main.cpp -o guest.wasm
```

The available `--std` values are `c++98`, `c++03`, `c++11`, `c++14`, `c++17`, `c++20`, `c++23` and `c++26`. Xmake takes the same value in `set_wros_profile({std = "c++98"})`. Each domain has its own header. Include `<uwrosv2/scene.hpp>` to access the full interface. Guest calls return a VM status or a typed result such as `result<uint64_t>`. When compiling against both language interfaces, add the C selection's `include/u2rosv2/universal/c` to the C++ project's include directories. The C and C++ headers declare calls as `throw()` in C++98/03 and `noexcept` from C++11 onward. The bundled profile enables Wasm EH and Herbceptions. Xmake exposes these as the independent fields `eh` and `herbceptions`.

The SDK ships the libc++ headers as files in `include/sysroot/c++/`, including `vector`, `string` and the Herbceptions extension `herbceptions/error`. Use their usual include names, such as `<vector>` or `<herbceptions/error>`. The driver selects the libc++ configuration for the requested thread model.

The C-family driver supports tagged pointer differences and explicit byte subtraction in C++. [WasmMTE pointer subtraction](c.md#wasmmte-pointer-subtraction)

## Own a capability and its resources

A capability authorizes specific operations for one deployed alias. A guard, timer, clock or waitset created through that capability has its own resource identity. The C++ bindings provide two exclusive owners in `<uwrosv2/owner.hpp>`. The C++98 function below opens the configured alias, creates a guard and signals it once.

```cpp
#include <uwrosv2/guard.hpp>

uint32_t notify() UWROSV2_CPP_NOEXCEPT {
    uwrosv2::capability_owner grant;
    uint32_t code = grant.open("signal");
    if (code) return code;

    uwrosv2::resource_owner guard;
    code = uwrosv2::guard::create(grant.get(), guard);
    if (code) return code;
    return uwrosv2::guard::trigger(grant.get(), guard.get());
}
```

Declare the capability before the resources that borrow it. Use a grant that authorizes `resource.close` for the resource being adopted. On scope exit each resource calls `resource.close` using its issuing capability. The capability then calls `capability.close`. Borrowed identities from `get()` can be passed to other calls while the owner remains live. To carry a resource beyond the capability's original scope, finish the other borrows and call `resource.take_capability(grant)`. That resource now owns both identities and retires them in dependency order.

Call `close()` to inspect a cleanup failure and retry while the owner is alive. If the resource closes and its capability close fails, retrying attempts only the capability. A destructor attempts any remaining cleanup and discards the returned status. Calling `close()` on an empty owner succeeds.

Owners support `source.transfer_to(destination)`, `swap` and `release` in every language mode. A transfer retires the destination's previous resource. If the destination owns the incoming resource's capability, it keeps that capability for the incoming resource. If that fails, the source keeps its ownership and the destination keeps its remaining cleanup responsibilities. C++11 and later also support move construction and move assignment. Use `transfer_to` when the caller needs the destination cleanup status. A capability's `release()` returns its raw handle. A resource's `release()` returns both identities and the `owns_capability` flag. Pass that value to an empty owner's `adopt` to resume automatic cleanup.

## Run the ownership example

Copy this project into a writable directory. It creates two guards under a shared capability, closes one at scope exit, and carries the remaining guard and its capability back to its caller. Its launcher configures a local scene with the `signal` alias and the six imports used by the example.

```sh
cp -R "$UWVM_ROS_SDK_ROOT/examples/cpp/raii" scoped-guard
cd scoped-guard
"$UWVM_ROS_SDK_ROOT/bin/wrcc" --std c++98 --reactor --export _start main.cpp -o guard.wasm
sh run.sh guard.wasm int
sh run.sh guard.wasm aot
```

Both invocations return exit code zero on success. The project's `xmake.lua` also supports `xmake build`. The separate `examples/cpp/migration/angles` project demonstrates using the ROS angles library in a guest.
