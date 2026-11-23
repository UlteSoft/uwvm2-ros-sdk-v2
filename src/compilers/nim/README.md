# Nim compiler sources

[中文](README.zh.md)

The private frontend runs Nim's C backend on the user's project. It selects the WebAssembly target's native integer and pointer widths and emits a list of generated C translation units. The SDK's Wasm compiler must compile and link those units with the guest runtime. The source tree contains the compiler, standard library, release dependencies and the 191 generated C units used by the official Linux x86-64 bootstrap. [Source revisions and modifications](upstream.json) · [Original file digests](release-files.sha256) · [Target selection](upstream/compiler/wrnim_lower.nim)

To build the host frontend with a native C compiler, run from the SDK checkout. The writable work directory holds the bootstrap and Nim cache.

```sh
mkdir -p .tmp/nim-host
cp -a src/compilers/nim/upstream/. .tmp/nim-host/
cd .tmp/nim-host
mkdir -p bin work
export TMPDIR="$PWD/work"
export TEMP="$TMPDIR" TMP="$TMPDIR"
sh build.sh
bin/nim c --skipUserCfg --skipParentCfg --threads:off -d:release -d:leanCompiler -d:nimcore \
  --lib:"$PWD/lib" --nimcache:"$PWD/work/nimcache" --out:"$PWD/bin/wrnim-lower" compiler/wrnim_lower.nim
```

Only the Linux amd64 C bootstrap identified by the official build script is included. The source manifest distinguishes Git-matched files from generated and bundled files verified against the official release archive. The guest entry calls NimMain. The panic handler traps inside the guest. The public compiler, ABI bindings, WasmMTE policy and external-project execution still need independent qualification. [Entry](runtime/entry.c) · [Panic handler](runtime/panicoverride.nim)
