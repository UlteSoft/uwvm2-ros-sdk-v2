# Objective-C++

The wrocxx frontend builds a Core Wasm guest from .mm source using the GNUstep and WROS headers in the selected SDK. The default profile uses wasm32, EH and WasmMTE with a single thread. Select --target wasm64, --threads, --no-mte or --no-eh to request another installed profile. The current sources and local compiler candidate unwind standard Wasm exceptions through GNUstep libobjc2 and libc++abi when EH is enabled. A single `wrocxx` invocation can compile and link `.m`, `.mm` and `.cc` translation units in their respective languages. The Linux x86_64 candidate has run in both uwvm2-ros engines. The [qualification record](../../qualification/objc-library-matrix.json) tracks the five hosts and GitHub installs.

```sh
"$UWVM_ROS_SDK_ROOT/bin/wrocxx" --platform generic --reactor --export _start main.mm -o scene.wasm
```
