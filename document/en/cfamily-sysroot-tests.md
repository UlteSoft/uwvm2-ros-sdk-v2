# WASIp1 sysroot qualification

The library suite compiles an upstream program through the installed `wrc` or `wrcc` and runs the resulting Core Wasm module in u2ros using INT and LLVM AOT. Both engines run the same file. The matrix crosses wasm32 and wasm64 with MTE, threads, and exception handling independently enabled and disabled.

The [manifest](../../src/qualification/cfamily/cases.json) identifies each source. The LLVM inputs come from LLVM 23.1.5. The Open POSIX tests come from the wasi-libc revision used by WASI SDK 34. The libc-test revision is the one requested by that wasi-libc release. Each pthread conformance test runs in the eight thread-enabled profiles. The remaining inputs run in all sixteen. [LLVM sources](https://github.com/llvm/llvm-project/tree/392dfff97d29b59d77e5cac6d4b6ef2585fe7117) · [wasi-libc sources](https://github.com/WebAssembly/wasi-libc/tree/2e6fb9d8ee0cdf9e431fbcabe8af3115de000a13) · [libc-test sources](https://github.com/bytecodealliance/libc-test/tree/18e28496adee3d84fefdda6efcb9c5b8996a2398)

Use the [runner](../../src/qualification/cfamily/sysroot_suite.py) inside the qualification namespace. Supply the installed C and C++ prefixes, the matching compiler sources, the installed WAT assembler, the VM, the opcode decoder, and an empty results directory on the project volume. The example uses the paths as mounted in that namespace.

The runner verifies the VM commit, source tree and executable SHA-256 before building cases. Pass `--vm-receipt /path/to/receipt.json` for a separate build. When mounting the suite separately, pass the reviewed `runtime-qualification.json` through `--vm-target`.

```sh
python3 -I -B /repo/src/qualification/cfamily/sysroot_suite.py \
  --cc-sdk /sdk/c --cxx-sdk /sdk/cpp --compiler-sources /repo/src/compilers/cc \
  --vm /opt/tools/bin/uwvm2-ros --wrwat /sdk/wat/bin/wrwat \
  --decoder /opt/tools/bin/decode-memtag --work /work/results --jobs 8
```

`inputs.json` records the tool, manifest, and runner hashes. Each line of `results.jsonl` identifies the source, profile, compiler arguments, guest digest, feature counts, WASIp1 imports, and each engine's outcome when a module was built. Each program's directory contains its compiler, decoder, INT, and AOT output. `summary.json` counts builds and executions separately. Upstream skips, unresolved POSIX outcomes, timeouts, and compiler failures have distinct labels. The runner returns a nonzero status when an applicable program did not pass both engines.

For third-party libraries, add `--suite external` and choose a second empty results directory. The fourteen programs use the same sixteen profiles. LZ4 exercises compression and decompression, cJSON runs three upstream Unity suites, uthash compares four upstream programs with their exact expected output, and fast_float runs four numeric parsing programs. The two SDK test clients exercise pugixml's XPath queries and tree mutation, and TinyXML-2's in-memory serialization and parsing. The manifest pins each project by commit and checks the Git blob of each vendored source, test and license. [Third-party inputs and programs](../../src/qualification/cfamily/external-libraries.json)

The compiler-specific subtraction fixtures live under the qualification tree. They cover the two integer widths, C and C++, ordinary typed pointer differences, the explicit subtraction builtins and the feature-off diagnostics. [Clang CodeGen and Sema regression sources](../../src/qualification/cfamily/clang)
