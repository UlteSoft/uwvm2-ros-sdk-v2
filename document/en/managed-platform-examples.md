# Managed platform projects

Install an exact SDK revision for the platform and language (`csharp`, `fsharp` or `vbnet`), using the `migration` component for the full migration examples. Set `UWVM_ROS_SDK_ROOT` to that installation. Prepare the .NET and Mono host with `language/csharp/prepare_host.py --language LANGUAGE --prefix DIR`. Set `WROS_DOTNET`, `WROS_MONO`, `WROS_TOOLCHAIN` and `WROS_VM` as described in the language guide. Copy `examples/platform/<platform>/extension/<language>` or its `migration` counterpart to a writable project directory. Run the following from the project.

```sh
xmake f -c -y -a wasm32
xmake -j1
xmake test -j1
```

The extension binds `Policy(Wros.Scene.DriverConnectionStatus("arm"))` through the public `--driver-entry Class.Method` option. The compiler verifies the two managed calls and the literal alias in ECMA-335 metadata, then compiles the user policy through Mono and LLVM. Aliases follow the VM’s canonical ASCII grammar (1–255 letters, digits, underscores, hyphens or dots, excluding the names `.` and `..`). The binding opens the named parent capability and attempts a real connection. It checks that a permission denial preserved both output slots, attempts disconnection after any other returned status, closes its handle and clears the scratch cells. A cleanup or storage-integrity error traps. This can disconnect an existing session for the same owner. Give this bounded connection check a dedicated device alias and session. It has one private memory page and four fixed imports, with no actuation or filesystem operations. The policy receives only the integer connect status.

The test fixture uses a new local authenticated socket, generated keys and the selected platform child for each run. INT and AOT each test the parent missing permission and the child disabled. The guest requires permission error 13, and the test peer must receive zero bytes. This checks VM policy and the managed binding without sending a motion command. Migration tests separately interpret all ten ROS 1 actionlib wire statuses using the scene ABI grant. [Migration semantics](platform-migration-examples.md).
