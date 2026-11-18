# Objective-C development for u2ros

The installation language ID is `objectc`. The compiler command is `wrobjc`. It compiles `.m` translation units, including Objective-C class metadata, through the WebAssembly-only Clang frontend. GNUstep libobjc2 performs class registration, message lookup, inheritance and allocation inside the same guest module. The base C++ linker and all linked libraries use the selected Wasm sysroot. The current runtime targets a single thread with manual object ownership. It provides the Objective-C runtime headers. Foundation, ARC and Objective-C exception handling are outside this profile.

## Prepare the host compiler and guest runtime

Select an installed `objectc` development package and its matching compiler-source package. Set `SDK` to its root. The base Wasm toolchain, sysroot receipt and host bootstrap must be provided explicitly. Use absolute paths. Preparation uses Python, CMake, Ninja and patch. The source build targets only WebAssembly. The local host compiler is used to compile the development tools.

```sh
python3 "$SDK/language/objectc/build_frontend.py" \
  --bootstrap "$HOST_LLVM" --source-work "$WORK/llvm-source" \
  --work "$WORK/objc-build" --output "$TOOLCHAIN/bin/wros-objc-clang"
python3 "$SDK/language/objectc/build_runtime.py" \
  --toolchain "$TOOLCHAIN" --sysroots "$SYSROOTS" --target wasm32 --eh --mte \
  --output "$WORK/objc32" --jobs 2
```

`build_runtime.py` checks the pinned GNUstep and robin-map sources, records SHA-256 digests of the static library and public headers in `runtime.json`, and records the Objective-C compiler and base sysroot identities. Keep a separate output directory for each width, MTE mode and EH sysroot. Selecting an EH sysroot provides its C/C++ link ABI. The Objective-C runtime itself uses its no-exceptions implementation for either sysroot.

## Compile and link

```sh
"$SDK/bin/wrobjc" "$SDK/examples/objectc/body.m" --target wasm32 \
  --toolchain "$TOOLCHAIN" --sysroots "$SYSROOTS" --objc-runtime "$WORK/objc32" \
  --mte --eh --reactor --export _start -O3 -g -o robot.wasm
```

Default MTE requires a reviewed release entry for the exact language toolchain, runtime, sysroot and VM. For development with an unreviewed producer, `--legacy-mte` requests instrumentation and prints a warning. `--no-mte` selects the separate uninstrumented sysroot and runtime. The compiler audits imports before publishing the module. Use `-c` for one `.m` translation unit, then pass its WROS-sealed object to the final link. `--reactor` allows the application to define its own entry. `--export` selects a named Wasm function. `--build-receipt` emits the artifact receipt; `-I`, `-D`, `--std`, `-O` and `-g` control source compilation.

Use `--objc-clang` or `WROS_OBJC_CLANG` to select a separately prepared frontend. The default is `TOOLCHAIN/bin/wros-objc-clang`. Use `--objc-runtime` or `WROS_OBJC_RUNTIME` to select a language runtime. The default directory is `TOOLCHAIN/share/wros/objectc/PROFILE`, where an example profile identity is `wasm32-wasip1-core3.0-eh-mte`.

## ROS permissions and platform selection

Import `<wros/scene.h>` from Objective-C sources. Its typed functions use the same ROSv2 imports and caller memory as C. Application methods can open a deployment-provided capability by alias and close its handle. The VM enforces grants for each imported operation. Platform selection in xmake uses the platform's installed descriptor. A platform permission narrows the common driver routes; control operations also require a suitable parent grant and an external driver session. The language runtime neither loads a host driver nor grants hardware access.

The example xmake target uses `set_language("objectc")`. Set `WROS_TOOLCHAIN`, `WROS_SYSROOTS` and `WROS_OBJC_RUNTIME` to the matching local paths. For a matching uninstrumented build use `WROS_SYSROOTS_NO_MTE` and its corresponding runtime. The real-VM test at `tests/objectc.py` runs a subclass override, super and nil messages, object allocation and capability denial/grant on the interpreter and AOT engines. The integration test at `tests/objectc_platform.py` exercises each common platform permission profile using a local test peer. It checks the enabled route, denial at the platform and denial at the parent capability. Its external peer accepts registration and release over pinned mutual TLS 1.3 on an authenticated local socket. The test records the peer, VM, package and guest identities. Vendor device protocols and physical hardware need separate qualification.


## Qualify the default MTE profile

Run the source qualification command in the compiler-source checkout as described in [local release qualification](memory-qualification.md). Select `--language objectc --target wasm32 -O3 -g --eh`. Supply `--objc-clang`, `--objc-runtime` and `--approved-objc-inputs-sha256`. The last digest covers the canonical JSON map of three SHA-256 values: `objc_frontend` for the dedicated compiler, `objc_runtime` for its runtime.json, and `objc_archive` for libobjc.a. Review these inputs separately from the base compiler and sysroot. The language proof runs real class instances through allocation, copying scalar values through messages, retirement and capability checks on both VM engines. It requires repeated close heap allocations of different sizes and checks the hidden reference-count header in the pinned GNUstep allocator. The resulting qualification statement must be reviewed, signed and installed according to the operator's local trust policy.

## Signed site installation

A site operator places the approved Wasm Objective-C compiler and its compiler receipt at `TOOLCHAIN/bin/wros-objc-clang` and `TOOLCHAIN/bin/wros-objc-clang.json`. Put the matching single-threaded GNUstep runtime, headers and `runtime.json` in `TOOLCHAIN/share/wros/objectc/PROFILE`. Use the profile identity from the runtime build. The site file points to this toolchain, a matching sysroot receipt, and the operator's independently approved signed Objective-C qualification.

With the SDK's fixed installer, install the selected language and platform into a fresh prefix in one command.

```sh
python3 install/bootstrap.py install --commit "$SDK_COMMIT" --platform unitree --language objectc --prefix "$PREFIX" --site-profile "$SITE"
```

The installation output identifies the SDK directory. In that directory, compile the installed example with `bin/wrobjc examples/objectc/body.m --reactor --export _start -o body.wasm --build-receipt`. The `examples/objectc/xmake.lua` project uses the same signed inputs when `UWVM_ROS_SDK_ROOT` points to the installed directory. Each build checks its Objective-C producer, GNUstep archive and headers, and sysroot against the qualification.
