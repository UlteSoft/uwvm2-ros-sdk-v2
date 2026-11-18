# Choosing a memory-tagging profile

`wrc`, `wrcc`, `wrf`, `wrlua`, `wrrs`, and `wrtg` use the same release index. The default requires a reviewed compiler, target library closure, language runtime, and matching VM for the selected profile and optimization settings. Each pair of live independent managed objects with at most 64 bytes between their extents must have different nonzero tags. A release review covers automatic storage, static storage, and the supported allocation paths. A threaded profile additionally requires per-thread storage and concurrency evidence.

| Compiler option | xmake field | Build behavior |
| --- | --- | --- |
| Default or `--mte` | `mte=true` | Refuses unlisted or altered release inputs. |
| `--legacy-mte` | `mte="legacy"` | Emits a warning and builds with the selected tagged sysroot. Close objects can have equal tags with older allocators. |
| `--no-mte` | `mte=false` | Selects an explicitly uninstrumented sysroot. |

The installed `share/qualification/memory-neighbors.json` lists reviewed combinations. The local WSEA workflow below can authorize an additional combination for that installation. Strict admission requires a matching record from one of these trusted sources. Source attributes can change local instrumentation. The compiler may also prove that an object needs no memory representation or elide a check with a static proof. The release decision is independent of any particular opcode appearing in the application.

## Reviewing a toolchain

Pin the complete SDK installation by commit and obtain the compiler and sysroots from a trusted source. A release row binds the compiler, linker, archiver, verified sysroot inventory, SDK frontend and language-specific build inputs. Rust and TinyGo also bind the LLVM tools and development inputs used by the IR marker. Rust and TinyGo frontends check their separate pinned host component inventories. The release record binds the VM binary and the digests of the independent stack, static layout, aggregate pointer, heap, language, interpreted and AOT test reports. The platform build host and its system libraries remain part of the trusted build environment.

A maintainer can inventory a trusted candidate with `tools/wasm/memtag/measure_release.py` from the source checkout. For example, pass `--language c --target wasm32 -O3 -g --toolchain PREFIX --sysroots FILE`. The result identifies unreviewed inputs. Run the independent regression suites using their test-only `--candidate-mte` switch before a release is added. Inspect the test cases, scope, binary identities, outcomes, and source changes before approving the release. A local build receipt reporting success does not authorize a change to the installed release index.

Lua builds the interpreter as Wasm and allocates its heap through the selected libc. TinyGo uses its own collector and requires independent allocation and sweep tests. The available Rust profile rebuilds `core` and compiler builtins and runs `no_std`. Application-provided arenas and interior subobjects require separate review. Numerical Fortran covers the memory paths supplied by the linked runtime subset. A general descriptor runtime, a new allocator, or an additional language requires its own evidence.

## Reviewing an application

Add `--build-receipt` to write `OUTPUT.wros-build.json` with the produced digest, profile, mode and scope. The receipt identifies frontend-reported source suppressions for Rust and TinyGo. Other frontends record `not-enumerated`, which requires source review. Review custom pools, explicit suppressions, unsafe code, input objects and the build environment before approving the artifact. Relocatable object notes check build consistency and carry no signing authority.

Keep the approved receipt digest in an independently trusted, signed deployment manifest. Check the final module against the approval and the actual VM:

```sh
python3 install/qualification.py --artifact body.wasm --receipt body.wasm.wros-build.json \
  --vm /opt/wros/uwvm2-ros --approved-receipt-sha256 "$approved_digest"
```

Approval covers the exact module/receipt/VM combination. A changed application can use the same reviewed producer. It gets its own output digest and review. Execute the same verified immutable module and VM under the authorized runtime checking policy. A deployment that disables runtime checks cannot enforce the neighbor rule.

## Local C, C++ and Lua releases

A site can authorize its own source build with its existing wasm-cosign WSEA trust. The qualification runner tests one nonthreaded language profile at a time. To qualify the default WebAssembly 3.0 configuration, select the EH sysroot and pass `--eh` to the runner. It verifies C++ destruction and rethrow across live allocation owners in both VM engines. For C or C++, select the language using `--language c` or `--language cpp`. To qualify the no-EH sysroot, omit the EH flag and select `wrc --no-eh` when building applications.

1. Use a clean, pinned SDK source checkout. Rebuild the compiler and sysroot from its source lock. Independently approve the VM digest, the SHA-256 of the freshly built sysroots.json, and the compiler program set. The producer fingerprint is the SHA-256 of compact, sorted-key JSON mapping the names `clang`, `wasm-ld`, `llc`, `llvm-objdump`, `llvm-ar`, and `FileCheck` to their individual lowercase SHA-256 digests. Trust the build host, build inputs, extracted tools and SDK checkout before running anything from them.
2. Run the source qualification suite in a 64 GiB cgroup with swap disabled. Select the address width and actual optimization/debug configuration of the application. The verifier uses the stack, global-address, nested aggregate pointer, allocator and libc suites, including two execution engines. The output folder must be new.

```sh
python3 -I -B tools/wasm/memtag/qualify_local_c.py --sdk-commit "$SDK_COMMIT" \
  --approved-producer-sha256 "$PRODUCER_SHA256" --approved-vm-sha256 "$VM_SHA256" \
  --approved-sysroots-sha256 "$SYSROOTS_SHA256" \
  --toolchain "$TOOLCHAIN" --sysroots "$SYSROOT_JSON" --runtime "$VM" \
  --target wasm32 --eh -O2 --output .tmp/site-c
```

For a Lua installation, qualify both `--language cpp --eh -O3 -g` and `--language lua --eh -O3 -g` at the same pointer width. Bundle the two releases before signing. The Lua frontend delegates the pinned interpreter closure to the C++ frontend. Lua tests build the default clock-reading guest and the guest-seeded alternative and exercise each applicable ROS grant or denial.

3. Inspect the receipts in that directory and authorize the release with the site's separate qualification-signing policy. Sign `.tmp/site-c/unsigned.wasm` using the ordinary `wasm secure sign` command with a dedicated key and a policy declaring exactly one module ID, `wros.sdk.memory.release`. To approve several profiles, pack their reviewed rows using `tools/wasm/memtag/bundle_local_releases.py --output unsigned.wasm --release-json A/release.json --release-json B/release.json` before signing. Increment the WSEA module version whenever the approved set changes. The verifier reads the WSEA policy and rollback state. The protected configuration additionally pins the approved signed bundle bytes. Install an update under a new filename, then atomically replace the configuration to change its digest. This Wasm contains only the signed qualification statement. Keep the signed module, verifier and policy in operator-controlled storage.
4. Provision `share/qualification/local-trust.json` inside the trusted **installed SDK** with the following keys. Use absolute paths and an independently established verifier digest. Access to this file and the SDK is part of the site's signing trust boundary. Application authors must have read-only access when the signing authority is separate from the application author.

```json
{
  "verifier": "/opt/wros/bin/cosign",
  "verifier_sha256": "<approved wasm-cosign binary SHA-256>",
  "policy": "/etc/wros/qualification.policy",
  "statement": "/var/lib/wros/qualification/site-releases.wasm",
  "statement_sha256": "<approved SHA-256 of the signed bundle>"
}
```

Build any C application with `wrc --toolchain ... --sysroots ... app.c -o app.wasm` for the approved settings. The SDK verifies a private snapshot of each signed statement against the configured policy and recomputes the input identities. Changes to application source are permitted. An altered signature, revoked certificate, absent trust, or changed producer does not grant strict admission. The qualification signer approves the toolchain and its evidence. Deployment still approves the final application and its permissions separately.
