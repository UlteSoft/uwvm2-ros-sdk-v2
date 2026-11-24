# WAVM-mt qualification reference

The source is `trcrsired/WAVM`, branch `mt-2`, commit `cd7107792bf69ffe62d245ab9479ec5421f13c75`. The pin has no release tag. The fork uses the BSD 3-Clause license and includes copyright notices for WAVM and WAVM-MEMTAG. [Pinned upstream tree](https://github.com/trcrsired/WAVM/tree/cd7107792bf69ffe62d245ab9479ec5421f13c75) · [Upstream license](LICENSE.txt)

The wire-format patch changes `Lib/WASM/WASMSerialization.cpp`. Its SHA-256 is `ea30bc3d7681946984c9ccd89aa8ecacb3e3ad9353a0885d43c127e062fe7ca6`. The patched source file has SHA-256 `68f172ea5efddd0553ddf9c4172d0e5e2bc767e5c9e4f34892cbf62d49c2b31b`. [Source patch](wros-memtag-wire.patch)

The LLVM compatibility patch adapts the subtarget feature query and Darwin AArch64 DWARF unwind selection in `Lib/LLVMJIT/LLVMJIT.cpp`. Its SHA-256 is `c8ac238e1f650ea8b4d9c09bf2625b5ca974ca5593360b6f51fd3433249e2714`. The patched source file has SHA-256 `881d27bfbe2729d177506e44fbc5ef5ac1e164aa780d8f6b6a053292588cbfce`. [LLVM compatibility patch](llvm23-api.patch) · [中文说明](UPSTREAM.zh-CN.md)

The WAT printer patch corrects the root keyword emitted by `Lib/WASTPrint/Print.cpp`. The patch SHA-256 is `e4a6d3018b44de06e2fe1b840cbdb7705a06f2964a10d6009b23c612e5d88117` and the patched file SHA-256 is `6299721c4c60b699517f145a49cad920f29e3b7141eb13c71cfd6dcec3682538`. [WAT printer patch](wat-module-keyword.patch)

## Wire format and scope

WAVM reads the 19 shared operations at `0x20..0x2f` and `0x36..0x38` directly from WROS modules. Each instruction consists of `0xff`, a ULEB32 word equal to `0x01010000 | operation`, and one ULEB32 memory index. WAVM validates the memory index and checks operands and results against the selected memory's address type. Execution uses the corresponding upstream mt-2 implementation. [WROS instruction signatures](../../../host-tools/uwvm2-ros/upstream/src/uwvm2/extension/memtag/instruction.h) · [WROS encoding](../../../host-tools/uwvm2-ros/upstream/src/uwvm2/extension/memtag/encoding.h)

The reader also accepts the original mt-2 `0xfc` encoding for those shared instructions. Assembly and binary serialization emit the WROS form with minimal ULEB32 values. A read/write cycle therefore canonicalizes a legacy encoding or a padded integer while preserving the instruction and its memory index. The pre-existing WAVM `0xff` subopcodes `0x00..0x17` still identify interleaved SIMD.

With the wire patch alone, the decoder rejects unknown WROS versions, domains and operations, and the reserved `memtag.add`. It recognizes `memtag.claim`, `memtag.claimz`, `memtag.reserve`, `memtag.activate` and `memtag.release` and rejects the module at load time with the instruction name. These five operations require ownership and lifetime tracking beyond the allocation tags implemented by mt-2. A workload that contains any of them falls outside this reference's executable coverage, even if the operation is in an uncalled function.

## Private allocation ownership

The optional ownership patch implements five WROS allocation instructions in the WAVM IR, validator, LLVM JIT and runtime. Apply it after the wire and LLVM compatibility patches. Its SHA-256 is `e49757fef93d47ed43542ad9b8c264712019cc4382bec8888fa2886b8f815609`. The added source `Lib/Runtime/WROSOwnership.cpp` has SHA-256 `bcdb556a236d6c9c1850629cc7e1b95d9374c7c6d1a9e82deeaf6aeb4bfaf03c`. The behavioral source pin is `UlteSoft/uwvm2-ros` commit `eeab6e7da6de83ae0bbf8fc49fb93398386af302`. [Ownership patch](wros-private-ownership.patch) · [Allocation transitions](https://github.com/UlteSoft/uwvm2-ros/blob/eeab6e7da6de83ae0bbf8fc49fb93398386af302/src/uwvm2/extension/memtag/allocation_transition.h) · [Static color selection](https://github.com/UlteSoft/uwvm2-ros/blob/eeab6e7da6de83ae0bbf8fc49fb93398386af302/src/uwvm2/runtime/memtag/static_allocation.h)

Enable `wros-ownership` for modules using this layer. A locally defined private wasm32 or wasm64 memory owns the live allocation directory. Checked execution requires whole, nonempty, initially untagged 16-byte granules. A claim immediately tags the extent, and claimz also clears its bytes. A reservation selects and records a tag while the original pointer remains accessible. Activation publishes the reserved tag. Release requires the exact extent and tag, restores the parent tag and removes the record. Legacy tag writes check overlapping and nearby ownership records. Allocation excludes tags held by neighbors separated by up to 64 bytes. Static version-2 descriptors are validated before tag publication and receive permanent extents, with preference for the least-used legal colors.

WAVM's software checks cover every granule touched by a scalar, bulk or host-buffer access in this profile. The identity configuration returns the input pointer from ownership instructions and preserves the bounds-checked byte clearing required by claimz. The profile rejects shared and imported memory, WASI thread spawning, hardware MTE, guest-supplied precompiled objects and host page unmapping. The reference runs one guest thread per instance on a 64-bit host. It uses the WAVM exception and host allocation mechanisms. WROS-specific allocator quotas, replayable entropy, asynchronous reporting and migrations are outside this comparison.

The SDK cJSON qualification guests contain all five allocation instruction encodings and 15 version-2 static descriptors per module. The wasm32 guest SHA-256 is `7f68b9c7ab1b93d6403786af17c1c48e3be1bc681c71de755d76b326457eefc1`. The wasm64 guest SHA-256 is `ab824190f3513714178bc097d35de271a7e2c1cbba9e5df3bf79956999396967`. These identities describe input artifacts. The fifth and sixth layers implement the direct tail calls used by the original guests and correct SIMD lane checks on the tagged LZ4 workload. [Native ABI, access widths and source hashes](RETURN-CALL.md)

## Rebuild

From a writable build directory, set `WAVM_REFERENCE_DIR` to the absolute path of this directory in the SDK and `LLVM_ROOT` to a Clang/LLVM install prefix with libc++. The x86-64 Linux host toolchain reports Clang and LLVM `23.0.0git` from LLVM revision `4c4c1db7c69a6fda6cfa6bc6066bb09a433edc89`. The same prefix provides the compiler, CMake package and libc++. This pin identifies the WAVM host toolchain. The WROS SDK records its guest compiler separately. [LLVM source revision](https://github.com/llvm/llvm-project/tree/4c4c1db7c69a6fda6cfa6bc6066bb09a433edc89)

```sh
git clone --branch mt-2 https://github.com/trcrsired/WAVM.git WAVM
git -C WAVM checkout --detach cd7107792bf69ffe62d245ab9479ec5421f13c75
git -C WAVM apply "$WAVM_REFERENCE_DIR/wros-memtag-wire.patch" "$WAVM_REFERENCE_DIR/llvm23-api.patch"
git -C WAVM apply "$WAVM_REFERENCE_DIR/wat-module-keyword.patch"
git -C WAVM apply "$WAVM_REFERENCE_DIR/wros-private-ownership.patch"
git -C WAVM apply "$WAVM_REFERENCE_DIR/core-return-call.patch"
git -C WAVM apply "$WAVM_REFERENCE_DIR/tailcc-simd-lanes.patch"
(cd WAVM && sha256sum -c "$WAVM_REFERENCE_DIR/PATCHED-SOURCES.sha256")
cmake -S WAVM -B wavm-build -G Ninja -DCMAKE_BUILD_TYPE=RelWithDebInfo \
  -DCMAKE_C_COMPILER="$LLVM_ROOT/bin/clang" -DCMAKE_CXX_COMPILER="$LLVM_ROOT/bin/clang++" \
  -DLLVM_DIR="$LLVM_ROOT/lib/cmake/llvm" -DCMAKE_CXX_FLAGS=-stdlib=libc++ \
  -DCMAKE_EXE_LINKER_FLAGS=-stdlib=libc++ -DCMAKE_SHARED_LINKER_FLAGS=-stdlib=libc++ \
  '-DCMAKE_CXX_FLAGS_RELWITHDEBINFO=-O3 -g -DNDEBUG' '-DCMAKE_C_FLAGS_RELWITHDEBINFO=-O3 -g -DNDEBUG' \
  -DLINKER_HAS_WL___GDB_INDEX:INTERNAL=0 -DCMAKE_EXPORT_COMPILE_COMMANDS=ON -DWAVM_ENABLE_FUZZ_TARGETS=OFF
cmake --build wavm-build --target wavm --parallel 6
sha256sum wavm-build/bin/wavm wavm-build/libWAVM.so.0.0.0
```

For wire-format qualification alone, apply the first three patches and use the individual hashes above. For the complete build, set `GUEST` to the original wasm32 or wasm64 cJSON artifact. Both commands pass the same iteration count.

```sh
wavm-build/bin/wavm run --nocache --enable return-call --enable wros-ownership --enable memtag-soft-debug "$GUEST" 100
wavm-build/bin/wavm run --nocache --enable return-call --enable wros-ownership "$GUEST" 100
```
