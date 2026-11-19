# Develop a TypeScript Wasm application

On a Linux x86-64 build host, install the TypeScript developer package for the exact SDK commit you intend to deploy. The package contains Microsoft TypeScript 5.9.3, its ES2022 declarations, its Node 22.22.3 build host, the QuickJS sources and the WROS frontend. The operator's signed C site provides the reviewed compiler, wasm32 EH sysroot and target VM identity. Supply your approved site to the installer.

~~~sh
python3 install/bootstrap.py install --commit "$SDK_COMMIT" --platform unitree \
  --language typescript --prefix "$PWD/sdk" --site-profile "$C_SITE"
~~~

Set UWVM_ROS_SDK_ROOT to the directory printed by the installer. Copy the example into your project before building. Both commands below compile the same two application modules.

~~~sh
cp -r "$UWVM_ROS_SDK_ROOT/examples/typescript" ./filter
cd filter
"$UWVM_ROS_SDK_ROOT/bin/wrts" main.ts filter.ts --ros-abi --build-receipt -o filter.wasm
xmake f -p wasm-wasip1 -a wasm32 -y
xmake -v filter
WROS_RUN_QUERIES=abi,realtime-clock WROS_VM="$QUALIFIED_VM" xmake test -j1
~~~

The first input is the entry. Supply every source used by a relative import. Use --project-root DIR for projects with multiple source directories. In xmake list all inputs with add_files and select the startup file with set_wros_typescript_entry. The compiler performs strict semantic checking on the declared sources and uses ES2022 with CommonJS module initialization in the guest. Module identities are project-relative. A missing file, bare package import, dynamic import or compiler reference directive fails the build. Compilation reads the packaged standard library and the explicitly selected application files. Node runs the compiler on the build host. QuickJS executes the resulting application inside the Wasm VM. Programs should complete synchronously.

## Imports and permissions

Request each operation with --ros-operation NAME or xmake add_wros_operations. The application gets declarations for exactly these names. The abi operation provides wros.abi(). Opening a capability returns an opaque handle or a numeric error. Data operations take a handle or null, an ArrayBuffer and the reply capacity. They return status, written as a bigint and data as an ArrayBuffer or null. Missing operations produce type errors when accessed through the SDK declarations. The VM independently enforces its import policy and resource grants. QuickJS imports the WASIp1 clock_time_get clock. This example requires clock exposure, the realtime-clock grant and ROSv2 abi exposure.

## Profiles and receipts

The interpreter target is single-thread wasm32, Core 3.0, with EH. Its C code is compiled at -O3 -g with strict MTE by default. An explicit --no-mte requires a matching untagged sysroot and toolchain. With --build-receipt the Wasm is accompanied by C, QuickJS and TypeScript receipts. The TypeScript receipt records every source digest, the entry point, compiler inputs, selected imports and generated JavaScript and Wasm digests. Keep all three receipts with the binary.

[Microsoft TypeScript release](https://github.com/microsoft/TypeScript/releases/tag/v5.9.3) · [QuickJS permissions and runtime](js.md) · [xmake controls](xmake.md)
