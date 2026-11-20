# Fortran stdlib trapezoid qualification

The replay checks the trapezoid integration routines from Fortran-lang stdlib v0.8.1 at commit `0ede3015ba4c7f945e1daa6b1fc504c0fbf1236f`. It verifies the upstream inputs and license against fixed SHA-256 digests. The upstream Fypp templates produce the library and six FP32 and FP64 tests. Their 20 original predicates cover constant and irregular spacing, quadrature weights, and empty or singleton ranges. The adapter replaces test-drive error reporting with a numeric `ERROR STOP` and preserves the library's argument-size check. [Release](https://github.com/fortran-lang/stdlib/releases/tag/v0.8.1) · [Upstream tests](https://github.com/fortran-lang/stdlib/blob/0ede3015ba4c7f945e1daa6b1fc504c0fbf1236f/test/quadrature/test_trapz.fypp)

Run through your existing 64 GiB test gate with zero swap. Set `SDK_REPOSITORY` and `SDK_COMMIT` to the SDK checkout and full commit under test. Supply local GFortran and Fypp paths. `--fetch` retrieves the five reviewed source and template files and their license. For offline replay, pass `--inputs` with those six files staged by basename.

```sh
"$WROS_TEST_GATE" python3 -B tests/fortran_stdlib_upstream.py \
  --repository "$SDK_REPOSITORY" --commit "$SDK_COMMIT" \
  --native "$(command -v gfortran)" --fypp "$(command -v fypp)" \
  --fetch --output "$PWD/.tmp/stdlib-trapz-native"
```

To exercise the explicit untagged, no-EH build, add `--plain --guest-assertion-traps --toolchain "$TOOLCHAIN" --sysroots "$PLAIN_SYSROOTS" --vm "$VM"`. Use the pinned Flang, its Wasm IR helper and a matching C++ compiler and sysroot with libc++. The fixed Fortran runtime uses that compiler and sysroot. The installed `wrf` verifies the sysroot, checks each object's build profile and audits the final Wasm imports before publishing it.

The fixture's guest-local failure handler traps and keeps all 20 numerical predicates and the argument-size check intact. The replay requires zero Wasm imports and checks that a deliberately false predicate traps in both engines. The Fortran compute runtime does not implement general `ERROR STOP` or its external I/O and process termination semantics.

Add `--site-profile "$SITE" --vm "$VM"` to test admission and compilation with signed releases. The site requires matching reviewed Fortran, C, and C++ releases for the wasm32 debug build and VM. Both modes use `-O3 -g`. The untagged replay passes natively and in the interpreter and AOT. A C-only signed site is rejected at admission, and a matching signed replay of this fixture is pending. Each invocation requires a fresh output directory and returns a nonzero status for a failed route. The receipt and neighboring logs record exact build inputs, exit statuses and diagnostics.
