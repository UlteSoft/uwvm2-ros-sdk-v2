# TypeScript guest frontend

Set `WROS_NODE` to the pinned Linux x64 Node.js 22.22.3 executable. The installed `bin/wrts` uses its bundled JavaScript modules and private C backend. When running the frontend from a source checkout, set `UWVM_ROS_SDK_ROOT` to a native wasm32 C installation. TypeScript 5.9.3 and its ES2022 library declarations are under `compiler/`. A checkout accepts `--platform <id>` to select the platform declarations and runtime modules together.

```sh
python3 -B src/compilers/typescript/driver.py src/examples/typescript/main.ts \
  src/examples/typescript/filter.ts --ros-abi --build-receipt -o app.wasm
```

The build type-checks the supplied TypeScript project and the selected SDK declarations in strict mode. Its emitted ES modules retain real imports, cyclic initialization and live bindings. QuickJS resolves the SDK imports against the same JavaScript modules used by JavaScript guests. Raw i64 operands use bigint and i32 operands use number. Each selection type-checks only its enabled raw ROSv2 methods. The resulting Wasm embeds QuickJS and executes the emitted JavaScript inside the guest. It needs the deployment's clock and its explicitly selected ROSv2 operations.
