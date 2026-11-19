# Nim applications

The SDK's private Nim 2.2.4 front end lowers one standalone application to C with the layout of the selected Wasm target. WROS Clang compiles the application, Nim runtime and ARC allocations to the same guest profile. The public compiler writes a core Wasm module with one entry point, `_start`. The supported guest configuration is single-threaded ARC with Nim's goto exception handling. The EH switch selects the guest sysroot ABI.

Select a platform that lists Nim, such as `unitree`, and select `compiler-source` to obtain the pinned producer inputs. Build the private producer with a trusted host Nim compiler. Nim's compile-time evaluation runs during development. The guest executes within the VM.

```sh
python3 language/nim/build_producer.py --bootstrap /usr/bin/nim --output /absolute/build/wrnim-lower
bin/wrnim app.nim --producer /absolute/build/wrnim-lower --toolchain "$WROS_TOOLCHAIN" \
  --sysroots "$WROS_SYSROOTS" --target wasm32 -O3 -g -o app.wasm
```

The default requires a reviewed MTE profile. An explicitly selected `--legacy-mte` tests a tagged candidate before approval. `--no-mte` requires the corresponding untagged sysroot. Use `--target wasm64` with a memory64 sysroot. Set `WROS_NIM_PRODUCER` for the Xmake rule and add the application's one entry file. Import additional Nim modules from that entry.

`import wros_scene` exposes the common ROSv2 operations using fixed-width integers. Pass guest addresses through `wrAddress` with the correct linear memory index. SDK bindings confer no runtime grant. Compile and run `examples/nim/body.nim` with the ROSv2 ABI query enabled to check the toolchain. The SDK rejects WASI Preview 2/3 and Component Model interfaces. Native libraries and object link inputs from a Nim build plan are rejected. The language route does not carry native vendor drivers.

For a site installation, place the approved Nim producer at `TOOLCHAIN/bin/wrnim-lower`. Pass the signed site configuration to the installer with `--site-profile FILE`. Running `bin/wrnim app.nim -o app.wasm --build-receipt` then uses the approved producer and sysroot. The xmake adapter reads the same installation.

## Debug an application in UWVM

Build with `-g`, or use `set_symbols("debug")` in Xmake. The Nim C backend emits source line directives and Clang records them in the guest's DWARF. Set breakpoints on executable lines in the original `.nim` files. When the debugger uses a separate copy of the source, use DAP `sourceMap` to map the recorded absolute paths to local paths.

With `-O3`, the debugger steps between the locations that remain after optimization. The column numbers and variable representations come from generated C. A local may be renamed or optimized out. Nim's runtime stack and line tracing options remain disabled.

The compiler driver is part of the site release measurement. When upgrading the driver, qualify the exact SDK and producer before signing the corresponding release statement.
