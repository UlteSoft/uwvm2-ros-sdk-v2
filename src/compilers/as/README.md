# AssemblyScript

Use the pinned Linux x64 Node.js 22.22.3 host with the checked-in AssemblyScript 0.28.20 compiler, Binaryen 131.0.0 and long 5.3.2. Each host compiler file and the Node executable are checked against `compiler.json`. Set `WROS_NODE` to the upstream Node executable if it is outside PATH.

```sh
python3 -B src/compilers/as/driver.py src/examples/as/main.ts --ros-abi -g -o app.wasm
python3 -B src/compilers/as/driver.py src/examples/as/driver.ts --ros-driver -o driver.wasm \
  --ros-operation capability.open --ros-operation capability.close --ros-operation driver.connect
```

The 38 public domain modules under `include/u2rosv2/universal/as/uwrosv2` declare every registered scene import with its Wasm module, external name and fixed-width signature. Import the desired operation from its domain, for example `import { wr_abi } from "./uwrosv2/capability"`. The `scene.ts` entry point re-exports all domains. Function documentation gives the caller's authority, request and reply layouts, memory ownership and return semantics. The status module contains the VM's numeric status values.

The application driver provides a zero-linear-memory scalar profile and a single-page bounded driver profile. Scalar programs may request the ABI query. With `--ros-driver`, the additional `./wros` staging module gives bounded access to five driver operations plus capability open and close. The compiled module must import exactly the selected operations. The scalar and driver profiles both accept `--build-receipt`. Scalar `-g` embeds the AssemblyScript source map.

The installed command is `bin/wras`. It loads the installed platform automatically. In a source checkout, pass `--platform <id>` to select its bindings. The platform examples use `--ros-driver` to decode observations from bounded staging.

The separate linker fixture takes raw parameters for every operation. It uses the checked-in public domain files, calls the real AssemblyScript compiler, then compares every emitted import and type with the VM contract. It writes the actual Wasm and a digest-bound inventory. The output covers import linkage. Runtime grants and application memory behavior require independent execution evidence.

```sh
python3 -B src/abi/generate_language_bindings.py
python3 -B src/compilers/as/prove_imports.py --output .tmp/as-imports
```
