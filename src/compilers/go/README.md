# Building and packaging the Go producers

The public CLI and feature descriptions are in document/en/languages/go.md and document/en/languages/tinygo.md. Each upstream.json records the upstream commit and tree, license, and hashes of the local source files copied into the installed frontend. Go's original private PEM test vectors are enumerated in test-fixtures.json. Two standalone PEM files are omitted and 13 mixed test sources keep their surrounding text with the private blocks redacted. Public certificate fixtures retain their original bytes.

The installer fetches the pinned Go and TinyGo host archives from their official distribution URLs. It verifies the publisher archive SHA-256 and extracts the selected frontend, standard-library and target files. The Go source applies the recorded test-fixture exclusions. Source-mode compiler overlays are applied after extraction.

From the checkout, reproduce either input using the original archive in the repository scratch directory.

```sh
python3 -B src/compilers/go/host_package.py go .tmp/go1.24.2.linux-amd64.tar.gz .tmp/host-inputs/go --scratch .tmp/pack
python3 -B src/compilers/go/host_package.py tinygo .tmp/tinygo0.38.0.linux-amd64.tar.gz .tmp/host-inputs/tinygo --scratch .tmp/pack
```

The following release recipes take fresh prefixes. wrgo, asm, compile and link come from the Go source build. wrtg and prepare-ir come from the TinyGo SDK source build. TinyGo binary mode uses the official frontend from the pinned input. Source mode rebuilds that frontend from the SDK's editable TinyGo, Go module and Espressif LLVM 19.1.2 sources. The link backend uses the repository's native Clang and wasm-ld archives. WROS_LLVM_CONFIG may select a matching LLVM 23.1.5 development prefix for the IR reader/writer. The default source recipe builds this dependency from src/compilers/cc/llvm-project. Native products use the single-member USTAR executable package format. The installer reads each language's native.json and admits a complete set for binary installation.

```sh
python3 -I -B src/compilers/go/rebuild.py --language go --mode source --prefix "$PWD/.tmp/release-go" --work "$PWD/.tmp/release-work" --package-dir "$PWD/bin/packages/linux-x86_64/wrgo/go"
python3 -I -B src/compilers/go/rebuild.py --language tinygo --mode source --prefix "$PWD/.tmp/release-tinygo" --work "$PWD/.tmp/release-work" --package-dir "$PWD/bin/packages/linux-x86_64/wrgo/tinygo"
```

For a local qualification build, leave off --package-dir. The installer publishes selected SDKs under PREFIX/COMMIT/PLATFORM/LANGUAGE/MODE. Go lives at libexec/go. TinyGo additionally uses libexec/tinygo and share/toolchains/tinygo-llvm. The user executable is bin/wrgo or bin/wrtg. The native source package defines the products expected from the independent release build. The qualification receipts identify the SDK commit, driver bytes and guest results verified for each public candidate.

## Platform-aware launcher packages

The launcher in `command/main.go` locates its own SDK selection and resolves the universal module and its selected platform module into the guest workspace. The ABB launcher source freeze is `ddf7bf754af8e4c464fb584b71e0fe1f479118a2`. The Go source file has Git blob ID `0b6f9c945057742fbaf3af753b3ff5a0c039c0d7` and SHA-256 `114bbc33f1f8b62c047c91675c852d7b6b8771e01546ad0b7e8ad9174fcabbc8`.

Both Linux x86-64 launchers use Go 1.24.2 from the SDK host archive with SHA-256 `97fe94da1393e25adca8028804e512273c7043b7277ee1c2d200fe670ed4aed3`. The build used an offline mount namespace with a fresh home and cache. Its parent and child cgroups each had a 68,719,476,736-byte memory limit and zero swap. The host command used `GOOS=linux`, `GOARCH=amd64`, `GOAMD64=v1`, `CGO_ENABLED=0`, `-trimpath`, `-buildvcs=false` and linker flags `-buildid= -X main.language=go` or `-buildid= -X main.language=tinygo`. `src/compilers/package_native.py` created each single-member USTAR archive.

- `wrgo` has 3,344,749 ELF bytes, SHA-256 `191ff76fb4ce2de8cf3888c04126fe219e2a74d5867939c48d26c735c10ff2a0`. Its 1,798,956-byte archive has SHA-256 `390ca7a3cebbf2345183a2d810b29dcdfed064abcb0c81bb94a542c081a6be04`. [Go release manifest](../../../bin/packages/linux-x86_64/wrgo/go/native.json)
- `wrtg` has 3,344,749 ELF bytes, SHA-256 `a7f0091b5596a166ba6877ad301db544492c50a0d01f8da337029f66b73e2e66`. Its 1,798,908-byte archive has SHA-256 `a76d6e9b893eadc8b8243355690b2e76c0bb0eaccbf7cd213f8be4c434cf64b0`. [TinyGo release manifest](../../../bin/packages/linux-x86_64/wrgo/tinygo/native.json)
