# Review results

[简体中文](../zh/qualification.md)

Each entry identifies the revision that produced the result. Tests used Linux x86-64, a clean home and cache, a mount namespace and nested cgroups with a 64 GiB aggregate limit and zero swap. Guest execution and the independent offline rebuilds used a separate network namespace. The development checkouts, host temporary directory and shared-memory directory were unavailable for writes.

## C-family execution comparisons

The release matrix covers C, C++, Objective-C and Objective-C++ on Linux x86_64, i686, aarch64, arm soft-float and arm hard-float. Each MTE setting has sixteen cases per language and host, formed by crossing the wasm32/wasm64 ABI, EH, threads and scalar/SIMD. This gives 320 untagged and 320 tagged cases before counting individual open-source workloads. This section defines the acceptance criteria. Historical results below identify the revision and subset actually measured.

For each case, build outside a GitHub-installed binary SDK. Record the selected sysroot, frontend arguments, Wasm digest, decoded features, input and expected result. Execute that same binary in WROS INT and LLVM AOT. Compare the untagged binary with Wasmtime and the tagged binary with the WROS wire-format port of WAVM mt-2. Record each runner's host architecture and engine. A missing backend, unsupported import or unavailable ownership operation leaves the corresponding comparison open. Report a replay on another architecture separately from native or same-system-QEMU timings.

Use the same inputs and check observable results before accepting execution timings. Warm each engine, alternate sample order on the same CPU, and measure the workload with a monotonic clock inside the guest. Report the median of paired ratios and sample spread. Compilation, instantiation, startup and output formatting fall outside the timed interval. For software MTE, also compare checking enabled and disabled on the identical tagged binary. The target for this last ratio is at most 1.5. Track optional bulk-memory and SIMD fallback checks and other instruction combinations alongside the release profiles.

On x86_64, VM candidate `d1a44a22` and Wasmtime 42.0.1 executed identical untagged C++20 modules with EH and threads disabled. Across ten paired measurements per workload, the median WROS AOT / Wasmtime time ratio for libc++ sort was 0.979 on wasm32 and 1.026 on wasm64. For fast_float v8.0.2 the ratios were 0.967 and 0.943. Wasmtime used its stock CLI for wasm32 and its C API with the SDK WASIp1 imports for wasm64. The receipt includes the raw paired execution times, native ELF comparison and checksums. [C++ execution measurements](../qualification/cfamily-cpp-wasmtime-execution.json)

## Language debugging, dump restore and live update

The C, C++, Objective-C and Objective-C++ debugging matrix covers the five Linux host ABIs and the sixteen base ABI, EH, threads and MTE profiles. Each language uses its installed SDK frontend to build a program with `-O0 -g` and a second version with an observable change. The receipt identifies the SDK commit, VM commit and tree, host executable, guest hashes, profile and requested engine.

- Requesting INT with DBG must exit with an explicit unsupported-mode error. Count this as an expected rejection. The source breakpoint, step and inspection checks run on LLVM AOT.
- For source debugging, hit a breakpoint on an executable line in the selected language, inspect a source value, and step to a second mapped line.
- For dump restore, capture a full snapshot at a cooperative stop, advance or change observable state, restore the snapshot, and verify the recovered state and subsequent execution.
- For live update, run both versions in the same VM process under the production signed update coordinator. Record the result of calling the same export before and after commit, together with the published epoch.

The restore and signed update tests use their respective VM launch profiles. The test records each capability separately for INT and LLVM AOT, including unsupported requests, failures and untested configurations. Public SDK installation, source compilation and DWARF inspection have their own results. [VM snapshot contract](https://github.com/UlteSoft/uwvm2-ros/blob/454a19a3c8c1ea388472d44589a126554067ef8b/documents/runtime/unified-snapshot.md) · [VM production update contract](https://github.com/UlteSoft/uwvm2-ros/blob/454a19a3c8c1ea388472d44589a126554067ef8b/documents/runtime/production-update.md)

## ABB standard Go candidate a5863c63

The public source installer built its host launcher with the original Go 1.24.2 host before applying the guest runtime changes. The independently rebuilt wrgo, asm, compile and link ELFs and all four tar.xz packages matched the public binary selection byte for byte. This revision closes the wrgo difference recorded below for 28466433. Independent projects also compiled 140 ROS 1 reference vectors and a RAPID/EGM application using each installation. They ran under INT and AOT directly and through Xmake. [Package hashes and isolation](../qualification/abb-a5863c63.json)

## Unitree Python candidate a524390d

The default `py` selection and the explicit `python` binary selection each installed CPython 3.14.8. Both installed interpreters executed an external Python program in the interpreter and LLVM AOT engines. The program checked the WASI platform, interpreter version, classes, exceptions, containers, math and JSON. The VM reported `fd_tell` denials and the program still completed. A separate build used the public source selection and rebuilt CPython offline with two jobs. The rebuilt target library and shared interpreter differ in bytes from the binary selection. The independent project also verified 43 Unitree types, 172 round trips and four Fast-CDR reference frames. Starting a script by guest pathname exited with status 120 with default MTE. With runtime tagging disabled, importing a sibling module still failed during directory enumeration. TinyGo passed the stderr test in its default build. Debug builds with EH enabled failed during assembly of runtime/panic.S. [CPython and TinyGo evidence](../qualification/unitree-a524390d.json) · [Install and run](languages/py.md)

## Franka candidate 17ff81a1

Both default and explicit binary selections of standard Go and TinyGo compiled a Franka project outside the SDK. Each checked 32 independent Fast-CDR frames spanning eight record types and both byte orders, plus four application samples in both byte orders. Direct and Xmake builds produced identical Wasm and ran under INT and AOT. The WAT source selection downloaded its pinned Rust 1.98.0 bootstrap and built the assembler offline without a user-supplied toolchain. The two installed `wrwat` ELF files matched. Both assembled and ran the same external Franka guest through the installed interpreter and AOT engine. The assembler rejected the optional `--version` probe. [Franka evidence](../qualification/franka-17ff81a1.json) · [Go and TinyGo samples](../../include/u2rosv2/platform/franka/go/README.md)

## GitHub candidate 28466433

ABB tried all 29 legacy selectors at this revision. Nine installed and passed their default external Xmake project on both engines. Twenty were rejected. The QuickJS process trace shows the installed private C compiler building the guest. Both Go toolchains independently matched 163 scene imports. INT and AOT each executed 163 explicit denials. Each also ran 140 genpy vectors in the installed binary and source projects, including 5,113 truncated inputs and 268 invalid Boolean or count positions.

The Go source installation reproduced the public assembler, compiler and linker. Its launcher differed from the download. Compiling the launcher before applying the Go runtime overlay reproduced its public ELF and archive. The TinyGo source run used independently built LLVM 19 and 23 inputs. Its launcher and IR preparation tool reproduced both published files, while the complete host frontend ELF differed. WAT reproduced its assembler ELF and archive with an explicit official Rust 1.98.0 bootstrap. The default WAT source installation at this revision stopped when Cargo was unavailable. [ABB](../qualification/abb-28466433.json) · [Independent Go project and wire fixtures](../../src/qualification/abb/go)

## GitHub candidate b92c100d

Unitree tried all 29 legacy selections. The default installs and external Xmake projects passed for C, C++, Rust, standard Go, TinyGo, AssemblyScript, JavaScript, TypeScript and WAT. The installer rejected the other 20 selections. Standard Go and TinyGo independently compiled the message project and ran it on both VM engines. The 43 upstream types have 257 fields. Fast-CDR 2.2.5 supplied both byte orders of the Go2 and HG reference frames. The four standard Go host tools rebuilt from public source matched the downloads. [Unitree](../qualification/unitree-b92c100d.json)

## Public candidate 1259ec52

The ABB default C, C++ and Rust installs each supplied a native compiler. The wasm32 and wasm64 modules from each language matched all 163 VM imports. Both engines exercised explicit denial. Each language also passed the external project with 140 genpy wire vectors. All eight C++ standards from C++98 through C++26 passed individually. [ABB](../qualification/abb-1259ec52.json)

The public ABB Rust source installation took 27 min 16 s. The host build ran in the online namespace with Cargo offline. Its installed prefix passed 32 project and ABI checks in a fresh offline namespace. A separate rebuild ran entirely offline. Both installations selected 64,402 Rust source files with identical paths, modes, sizes and digests. Each rebuild reproduced both distributed ELF files and both archives byte for byte. [Rust](../qualification/abb-1259ec52.json)

Franka installed WAT, C, C++, Rust, AssemblyScript, JavaScript and TypeScript from GitHub, each with Xmake and the VM. The shipped and independent Elbow projects passed direct compilation, Xmake, INT and AOT. C, C++ and Rust also ran typed XCDRv1 guests. C11/17/23 and all eight C++ standards from C++98 to C++26 passed. The C driver rejected C99. Among the remaining 22 legacy choices, Go and TinyGo lacked Franka bindings and 20 lacked a language installer. Two WAT source installs failed fetching different Git blobs. [Franka](../qualification/franka-1259ec52.json)

## GitHub candidate 947c3067

ABB projects in C, C++, AssemblyScript, JavaScript, TypeScript and WAT passed direct compilation, Xmake and both VM engines. The independent C, C++ and Rust modules matched all 163 raw imports. The ROS 1 byte tests compared 140 genpy vectors. Rust bindings mode required external Rust 1.98.0 and its wasm32 target library. The public native Rust source install failed on omitted upstream files when supplied with its official stage0. Separately, a diagnostic rebuild with those files restored produced a wrrs that ran wasm32 and wasm64 guests. [ABB guest, authority and rebuild results](../qualification/abb-947c3067.json)

Each of the 29 legacy selections was tried in a fresh Unitree installation. C, C++, Go, WAT, JavaScript, TypeScript and AssemblyScript projects passed Xmake and both VM engines. Standard Go passed direct compilation and Xmake in external projects using the default, explicit binary and source installations. All four native tools were byte-identical across those installs. The independent project checked 257 fields across 43 types and used Fast-CDR 2.2.5 frames in both byte orders for complete Go2 and HG LowState messages. TinyGo's default install lacked a registered wrtg package. Its source install failed when LLVM could not find libc. [Selection results, feature tests and artifact digests](../qualification/unitree-947c3067.json)

Eight shipped Franka projects in C, C++, WAT, JavaScript, TypeScript and AssemblyScript passed direct compilation, Xmake, INT and AOT from the GitHub installation. Two more Rust bindings projects passed with an external Rust 1.98.0 wasm32 toolchain. Each language also ran a guest against two independent Elbow messages. Separate native tests exercised all 137 XCDRv1 records with the installed bindings, using ROS 2 Jazzy rosidl and 818 Fast-CDR 2.2.5 reference frames. Each profile checked 47,612 truncation points. This revision has no Franka bindings for Go or TinyGo. [Project results](../qualification/franka-947c3067.json) · [Reference frames](../../src/qualification/franka/xcdr1-vectors.json)

## ABB ROS 1 candidate

Candidate `36c098e85098d7ccc26562972af32f47aafe7560` was installed by the public root bootstrap in an empty home and cache for each selection. The independent group tried all 29 legacy IDs. C, C++, JavaScript and WAT produced guest modules using the installed SDK and ran them offline on the interpreter and LLVM AOT engine. The JavaScript and WAT examples exercised the read-only ABB position interface. AssemblyScript and TypeScript also ran after adding Node.js 22.22.3. Rust required the bindings-only installer flags and a separate Rust 1.98.0 compiler with its wasm32 target library. The installer rejected the other 22 IDs, including standard Go, TinyGo and the C interoperability bridge. [Per-selection and per-module results](../qualification/abb-36c098e8.json)

C and C++ built the published service and system-state example both directly and with Xmake. All eight C++ modes from C++98 to C++26 passed. C, C++ and Rust each matched 140 independently serialized genpy cases across 70 payload types and all 47 ABB handshake MD5s plus `std_msgs/Header`. The tests cover ROS 1 payloads in guest memory. Driver transport, RobotStudio and controller execution remain untested. [Frozen byte vectors and upstream revisions](../../src/qualification/abb/ros1-vectors.json) · [ABB example and supported types](../../platform/abb/ros1.md)

## Franka candidate

On the same GitHub candidate, C, C++, WAT and JavaScript built the Franka example offline and ran it under INT and AOT. An independent guest tested the two public Elbow accessors using 84-byte little- and big-endian XCDRv1 fixtures produced by eProsima Fast-CDR 2.2.5. All 30 ROS 2 upstream definitions matched their source files. The other three Elbow fields and the other 29 definitions lacked typed public APIs at this revision. Importing the candidate’s Franka schema reader failed at line 43. AssemblyScript and TypeScript lacked their pinned Node.js host, and Rust lacked its compiler and wasm32 target library. The test covered 29 installation IDs. [Per-language results, fixtures and source revisions](../qualification/franka-36c098e8.json)

## Installed SDK

Revision `24e4cb6be1748d11a743393abd4cc9fce53b9eaa` was downloaded from GitHub with its root installer. The C, C++ and WAT selections installed on generic and Unitree. All six file inventories and native archives were checked. Eight shipped Xmake projects, including the zlib Adler-32 and ROS angles components, built and passed on both INT and AOT outside the SDK. The Unitree projects used a recorded Go2 state payload.

The installed wrc and wrcc each emitted a guest with all 163 registered ROS imports. Both engines exercised its deny path. Smaller guests verified on-demand imports. Both compilers emitted WasmMTE instructions in the default wasm32, Core 3.0, EH, single-thread mode. The C++ guest used native Wasm EH and a separate typed Herbceptions catch. C rejected the Herbceptions option.

At this revision the direct compilers required a manual include path for the Unitree platform header. Direct compilation and Xmake lacked prepared wasm64, threads, no-EH and no-MTE C/C++ targets. The C selection also carried the common sysroot's C++ libraries. Each subsequent revision needs its own results for these cases.

The WAT source and binary installations from `d8e730f70ef12a31eb007ff8165073d95bf7bf36` produced the same ELF on both platforms. Independent offline builds matched it byte for byte. The shared-memory thread cases used an actual WASI thread spawn and transferred a tagged pointer across threads. The shipped Xmake project failed to parse on this revision. Its corrected version was tested in the six-installation run above. [WAT evidence](../qualification/wrwat.json)

## Language bindings

The C11, C++17 and Rust binding tests compiled independent consumer projects. All three full import tables matched 163 names, namespaces and signatures, with one import in each ABI-only guest. The thirty INT/AOT cases exercised permission grants, explicit denial, a hidden import and guard resource operations. This Rust result used rustc 1.98.0 and the official wasm32 standard library. A packaged wrrs with MTE is pending. [Binding evidence](../qualification/bindings.json)

## Coverage still open

- The old v1 catalogue has 29 language entries including the C FFI bridge, and 36 platform entries including the three ROS entries and WASI. The v2 working catalogue lists the same 29 language IDs and 32 vendor/platform IDs.
- Standard Go passed the Unitree installation tests. Its compiler rejects wasm64, shared-memory threads and 32-bit Go pointers. TinyGo, Fortran, Java, Kotlin, C#, the remaining native and AOT toolchains and the interpreter runtimes still need independent release qualification. Each remaining platform and language combination needs an external project run from the installed SDK.
- The reproducible porting cohort selects 300 package names from 9,432 inventory records. The compiled angles component is one member of the cohort. Whole-package qualification is still pending. The independently compiled non-ROS zlib checksum component is recorded separately. [Source selections](../../src/qualification/corpus/selection.json)
- Full-profile qualification, multi-module applications, neighboring allocation tags, long-distance collision measurements, coroutines and performance measurements remain open for the new release. Deployment and physical-device acceptance follow SDK qualification.

## Source-built wasm64 C/C++ libraries

The wasm64 production rebuild used commit `7f6f3a1599c7722df5d56bdaf28eea46a1002cde`. With the drivers from `374b5235d70ba0bce403d589f0678274a30eaf3a`, the C and C++ guests each used eight-byte pointers and emitted memory64 and WasmMTE instructions. The C guest exercised the 64-bit WASIp1 clock, allocation and formatted output. The C++ guest exercised floating-point `to_chars`, dynamic strings and exception unwinding. Both INT and AOT returned the expected exit codes for both guests. The run used the released native tools and a locally rebuilt sysroot. [Machine-readable results and fixture hashes](../qualification/wasm64.json)

## AssemblyScript raw bindings

Frozen commit `b9fee6fe06f4876a0ca4bb473a966fe770559158` used asc 0.28.20. WABT independently read the resulting module and matched all 163 host import names, namespaces and function types against the VM contract. All 38 domains and the aggregate entry compiled independently. A guest calling only guard.trigger imported one host function. Both INT and AOT passed five cases covering granted, denied and hidden imports and the generic example. This run used compiler inputs from the source tree with external Node.js 22.22.3. Review identified two documentation issues in this revision concerning buffer overlap and the reported required length. [Individual module hashes and VM outcomes](../qualification/assemblyscript.json)

## Platform examples and strict C++ dialects

Commit `663aab60ba1acacac54d1a8c18ea8140bf84f2b4` installed all 37 selections for C, C++, WAT and experimental Rust from frozen Git objects with verified release artifacts. All 148 external Xmake projects built and passed on both VM engines. The strict dialect checks exposed a separate defect: 35 platform headers and examples used 64-bit integer literals rejected in C++98 and C++03. The 43 common C++ headers compiled independently in all eight dialects. The complete platform language expansion requires a fresh acceptance pass on its own commit. [Per-project module digests and results](../qualification/platforms-663a.json)

## JavaScript and TypeScript source drivers

At `e9ce427de3bda374304b0bf5dfc90ced43bee861`, WABT matched 163 ROS imports and their complete signatures in each of the two compiled Wasm modules. Each module also imported the WASIp1 clock. All 24 INT/AOT cases met their expectations for grants, denials, hidden imports, bigint precision and buffer handling. An external Xmake project invoking the source drivers passed four runtime cases. The stock installer and Xmake rules at that revision rejected both languages. The selected sysroot also lacked the release inputs needed to disable MTE or require strict memory qualification. The relocated installer and Xmake rules require separate acceptance at their own revision. [Frozen results and module digests](../qualification/ecmascript-e9ce.json)

The 300 selected packages come from 255 archives. The archive-to-commit index records the full Git revision embedded in each source archive after verifying its SHA-256 against the selection. Package builds and port tests are tracked separately. [Package selection](../../src/qualification/corpus/selection.json) · [Source revisions by SHA-256](../../src/qualification/corpus/archive-commits.json)
