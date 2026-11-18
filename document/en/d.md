# D BetterC

The Linux x86-64 site builds one D application for single-threaded wasm32 Core 3 with EH and WasmMTE. Implement `extern(C) nothrow @nogc uint wros_main()` and return zero on success. The SDK supplies the C entry point and the generated D declarations and C bridge for the ROSv2 imports. The qualified path uses LDC BetterC to produce unoptimized LLVM IR with debug information, applies the SDK LLVM marker, then compiles and links with the signed C backend using `-O3 -g`. The installed driver accepts D source.

```sh
python3 install/bootstrap.py install --commit "$SDK_COMMIT" --platform unitree --language d --site-profile "$SITE" --prefix "$PREFIX"
"$SDK/bin/wrd" "$SDK/examples/d/body.d" -o body.wasm --build-receipt
"$SDK/bin/wrd" verify --artifact body.wasm --receipt body.wasm.wros-build.json --vm "$VM" --approved-receipt-sha256 "$RECEIPT_SHA256"
```

Set `SDK` to the installed directory. The included Xmake project uses `UWVM_ROS_SDK_ROOT` to locate it. Supply the approved receipt hash independently to the D verifier. The D-specific receipt records the D row, its signed C backend qualification, and the VM identity.

The site toolchain contains `bin/wros-ldc2`, `bin/wros-flang-mte` with its marker receipt, and `share/wros/betterc/imports` with matching D frontend sources including `object.d`. Its native GNU ELF loader and individually hashed LDC and marker shared libraries must match the site's inventory. The driver passes its own LDC configuration and an explicit D import tree.

Run `tests/d_bindings/qualify_site.py --measure-host --toolchain "$TOOLCHAIN"` to inspect the host identities. With the reviewed host digest, signed C site and matching VM, the script's qualification mode checks the declarations, builds a weighted fixed-array and pointer example, and executes its ROS ABI grant and denial on both engines. It emits an unsigned candidate statement. The site operator reviews and signs it under the dedicated WSEA qualification policy before installing. This evidence covers that BetterC route and these probes. Full DRuntime, Phobos runtime linkage, memory64 and threaded D applications are outside this profile.
