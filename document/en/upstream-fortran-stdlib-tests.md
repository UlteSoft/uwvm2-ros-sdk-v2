# Fortran stdlib trapezoid qualification

The replay checks the trapezoid integration routines from Fortran-lang stdlib v0.8.1 at commit `0ede3015ba4c7f945e1daa6b1fc504c0fbf1236f`. It verifies the upstream inputs and license against fixed SHA-256 digests. The upstream Fypp templates produce the library and six FP32 and FP64 tests. Their 20 original predicates cover constant and irregular spacing, quadrature weights, and empty or singleton ranges. The adapter replaces test-drive error reporting with a numeric `ERROR STOP` and preserves the library's argument-size check. [Release](https://github.com/fortran-lang/stdlib/releases/tag/v0.8.1) · [Upstream tests](https://github.com/fortran-lang/stdlib/blob/0ede3015ba4c7f945e1daa6b1fc504c0fbf1236f/test/quadrature/test_trapz.fypp)

Run through your existing 64 GiB test gate with zero swap. Set `SDK_REPOSITORY` and `SDK_COMMIT` to the SDK checkout and full commit under test. Supply local GFortran and Fypp paths. `--fetch` retrieves the five reviewed source and template files and their license. For offline replay, pass `--inputs` with those six files staged by basename.

```sh
"$WROS_TEST_GATE" python3 -B tests/fortran_stdlib_upstream.py \
  --repository "$SDK_REPOSITORY" --commit "$SDK_COMMIT" \
  --native "$(command -v gfortran)" --fypp "$(command -v fypp)" \
  --fetch --output "$PWD/.tmp/stdlib-trapz-native"
```

Add `--site-profile "$SITE" --vm "$VM"` to exercise the normal signed `wrf` route. The site must supply matching reviewed Fortran, C, and C++ releases for the requested wasm32 debug build and VM. To exercise the explicit untagged, no-EH control, add `--plain --toolchain "$TOOLCHAIN" --sysroots "$PLAIN_SYSROOTS" --vm "$VM"`. Each selected route builds at `-O3 -g` and runs both VM engines if admission and linking succeed. Use a fresh output directory for each invocation.

The exit status is nonzero if a requested route fails. `results.json` records each route and the stage it reached, and the neighboring logs retain the actual compiler or deployment diagnostic. For SDK `63b57f8`, the original predicates passed with GFortran 15.2.0. The supplied C-only signed site rejected Fortran at installation. The untagged control reached the C++ Flang runtime build and stopped because the Herbceptions producer and its matching C++ sysroot were missing. A separate static-library probe built the original kernels into a sealed archive and reached the linker. Its array assignments still required the pinned Flang descriptor runtime symbols `_FortranAAssign` and `_FortranAAssignTemporary`. Guest execution remains unverified for this library configuration. [Flang assignment implementation](https://github.com/llvm/llvm-project/blob/392dfff97d29b59d77e5cac6d4b6ef2585fe7117/flang-rt/lib/runtime/assign.cpp)
