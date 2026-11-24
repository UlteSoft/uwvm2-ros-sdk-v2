# Objective-C and Objective-C++ library qualification

[中文](README.zh.md)

Run from the SDK checkout with installed Objective-C and Objective-C++ selections, a matching `u2ros` VM and the installed WAT tool. The output directory must be empty. All compiler and VM temporary files go into the chosen work area.

The runner verifies the VM commit, source tree and executable SHA-256 before building cases. Pass `--vm-receipt /path/to/receipt.json` for a separate build. When mounting the suite separately, pass the reviewed `runtime-qualification.json` through `--vm-target`.

```sh
python3 -B src/qualification/objc/matrix.py \
  --objc-sdk "$OBJC_SDK" --objcpp-sdk "$OBJCPP_SDK" \
  --vm "$U2ROS" --wrwat "$WRWAT" --work "$PWD/.tmp/objc-library-matrix" --jobs 4
```

Repeat `--case` and `--profile` to select individual inputs, for example `--case chromium-swizzler --profile wasm64-wasip1-threads-eh-mte`. Each invocation records commands, tool and artifact hashes, stdout, stderr and per-engine verdicts. `inputs.json` identifies the exact build inputs. `results.jsonl` and `summary.json` distinguish guest executions, expected compiler diagnostics and failures.

## Library components

The component cases compile an original upstream implementation with public `wroc` or `wrocxx`, archive the object using the selected SDK's `llvm-ar`, then link a separate client against the archive. The runner checks upstream Git blob IDs and SHA-256 digests, including the bundled license texts. The full revision and repository for each snapshot are in [upstreams.json](upstreams.json).

- GCC `libobjc/Object.m` implements class lookup and identity equality. The client checks both selectors on separate objects and on an inherited implementation. The preprocessor gives the member's root class a private name to allow it to coexist with the installed GNUstep `Object` class. The installed Objective-C headers supply the guest ABI.
- ObjFW `OFCRC32.m` implements the C-callable checksum used by ObjFW archive code. The client checks the standard `123456789` vector, incremental updates, a zero-length update and a binary vector. The two configuration headers in `ports/objfw` select the portable path for this member.
- Chromium `base::apple::ScopedObjCClassSwizzler` uses the Objective-C runtime and C++ scope lifetimes. The client exchanges instance and class methods, calls their original implementations through Chromium's typed template and checks that both destructors restore dispatch. The two headers in `ports/chromium` implement the member's build annotations and debug checks with guest traps. The method exchange, type checks, implementation lookup and lifecycle logic come from Chromium.
- Objective-CPP `NSString+ObjectiveCPP.mm` is a separate dependency probe. The original C++ string category imports Foundation through its upstream umbrella header. The runner records the compiler's `Foundation/Foundation.h` missing-header diagnostic. If an SDK supplies Foundation, the probe records the change as `unexpected-acceptance` for review.

## Runtime and exception cases

The GNUstep libobjc2 tests cover category dispatch, fast retain and release, weak references and retain-count saturation. The three upstream exception programs cover typed catches, cleanup, repeated catches and a rethrow between `.m` and `.mm` translation units. Their original source layout is reproduced next to the installed GNUstep headers in the work area. The additional mixed-language client checks C++ destructors, Objective-C superclass and catch-all matching, C++ integer exceptions, rethrow and `@finally` in both directions.

The default matrix has 160 case/profile combinations. The 112 executable guests produce 224 engine verdicts across INT and AOT. The other combinations check 32 disabled-exception rejections and 16 Foundation diagnostics. Only `executed` rows count toward guest-execution coverage. The WAT owner for each threaded guest uses the imported memory width, minimum and maximum from that guest. VM options and WASIp1 grants come from the common C-family qualification runner.

## Wasmtime comparison for non-MTE profiles

`wasmtime_reference.py` replays one host's original Objective-C matrix on Wasmtime 42.0.1. Its default plan covers ten cases across eight non-MTE profiles. The 56 linked guests have 112 planned INT/AOT comparisons. The remaining 16 EH-disabled cells and eight Foundation probes check the original compiler diagnostics.

Use the network-isolated qualification environment with the original matrix directory, SDK installations and VM build receipt mounted read-only. Keep `objc` and `cfamily` alongside each other under `$QUALIFICATION`. On the replay machine, build the C-family C API host from the pinned release and supply its approved build digest as `$HOST_SHA256`. The reference host and the instruction decoder run natively. The original producer tools and VM may belong to another architecture. [C API archive digest and host build](../cfamily/wasmtime_reference/README.md)

```sh
mkdir -p "$WORK/scratch"
export TMPDIR="$WORK/scratch"
(cd "$QUALIFICATION/cfamily/decoder" &&
  cargo build --offline --locked --release --target-dir "$WORK/decoder-build")
python3 -I -B "$QUALIFICATION/objc/wasmtime_reference.py" \
  --results "$OBJC_MATRIX" --work "$WORK/objc-wasmtime" \
  --host "$QUALIFICATION_HOST" --host-sha256 "$HOST_SHA256" \
  --decoder "$WORK/decoder-build/release/decode-memtag" \
  --vm "$U2ROS" --vm-receipt "$VM_RECEIPT" --vm-target "$VM_TARGET" \
  --objc-sdk "$OBJC_SDK" --objcpp-sdk "$OBJCPP_SDK" --wrwat "$WRWAT"
```

The decoder build uses the SDK checkout's vendored Rust dependencies. An existing native `decode-memtag` can be passed directly. Select an empty reference output directory for each run. Repeat `--case` and `--profile` to replay a subset. When the original matrix used an earlier C-family policy, pass its frozen `sysroot_suite.py` through `--matrix-policy` for the original tool hash check. The active reviewed policy regenerates the INT and AOT command lines, including memory-owner paths, import decisions and grants.

Each row binds the guest bytes to the original module digest, producer commands, Objective-C runtime receipt and archives, VM commit, tree and executable. The driver reads the module's actual import signatures and memory width and decodes its instructions to check the profile. Threaded cells verify the supplied owner's digest, export and exact memory limits. The adapter uses the original bytes with an empty guest environment, zero preopens and EOF on stdin.

`results.jsonl` and the per-cell `result.json` report each engine's exit-code, stdout and stderr comparison separately. `host.log` records entry into `_start` and guest termination. `wasmtime.out` and `wasmtime.err` preserve the raw streams. A `match` requires a successful guest termination, an output accepted by the case, and exact agreement with both successful original engines. This includes byte-for-byte agreement for the GNUstep case that prints a pointer. `dependency-unavailable` and `eh-disabled-rejected` count only as compiler diagnostics. An unsupported import or grant, a missing receipt, a timeout or a difference leaves the affected comparison incomplete and the run exits nonzero. `summary.json` records planned guests, actual starts and terminations, and comparison counts per engine.
