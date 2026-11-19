# Recover the LLVM Herbceptions source

The compiler source package includes the complete filesystem tree of the
Herbceptions fork at commit `218014296779772a4edbe63eff3fe6fe0ba92390`.
It shares the SDK's vendored LLVM 23.1.5 archive. A binary Git patch supplies
the differences, including file modes, symlinks, tests and the
`libherbceptions` runtime. The matching upstream license is distributed
beside the patch in `third-parties/sources/llvm-herbceptions-21801429/`.

From the SDK root, choose a fresh output directory on a Linux filesystem that
supports symlinks and executable permissions. Allow at least 9 GiB of working
space. The unpacker uses Python 3.11 or later, Git, GNU tar and xz.

```sh
python3 tools/wasm/herbceptions/recover_source.py --output /work/llvm-herbceptions
```

The command operates offline, verifies the SHA-256 of the base archive and
the patch, and checks the resulting Git tree against
`69a2c7cbcfb0371010a4b5a02d0f73e14eef23ed` before publishing the source.
An error aborts recovery and removes the staging tree. Use the SDK's compiler
build workflow to apply its Wasm memory-tagging patches and select the
WebAssembly backend. The fork tree recovered here is the upstream input to
that workflow.

[Upstream commit](https://github.com/trcrsired/llvm-project/commit/218014296779772a4edbe63eff3fe6fe0ba92390)
