# Upstream base-x and abbrev tests

This replay installs the exact SDK revision
`63b57f8b3debfe14cabd5af05de2ffbee22a0314` for QuickJS and mruby. It uses an
authenticated wasm32 Core 3.0 C site configured for EH, one thread, strict MTE,
and `-O3 -g`. The build and interpreter receipts must identify the exact
guest module and VM.

- **base-x 5.0.1** uses the original ESM implementation, test bodies, and
  fixture JSON. The adapter replaces module imports and supplies the assertion
  methods called by the tests. It checks all 254 test groups and 256 assertions,
  covering 121 valid and 9 invalid vectors, return types, and input forms. The
  same assembled script runs under Node.js and under QuickJS in Wasm.
  [Upstream source](https://github.com/cryptocoinjs/base-x/tree/b7b0cec52bf60d993957902e8e7c96906ac39c7c)
- **abbrev 0.1.2** keeps both original test methods and all six equality checks.
  The guest source uses string slicing for literal prefixes, and rejects other
  truthy filter types. The same assertions run against both the original
  and adapted implementation in native Ruby before the adapted source runs
  in mruby in Wasm.
  [Upstream source](https://github.com/ruby/abbrev/tree/b362e8e3b92c48a9e8f34fc0f782d3396858db1f)

Fetch the pinned archives below. The test checks their SHA-256 values before
reading the original library and test sources.

```sh
curl --fail --location \
    https://codeload.github.com/cryptocoinjs/base-x/tar.gz/b7b0cec52bf60d993957902e8e7c96906ac39c7c \
    --output .tmp/base-x-5.0.1.tar.gz
curl --fail --location \
    https://codeload.github.com/ruby/abbrev/tar.gz/b362e8e3b92c48a9e8f34fc0f782d3396858db1f \
    --output .tmp/abbrev-0.1.2.tar.gz

PATH_TO_GATE /usr/bin/python3 -B tests/script-libraries/upstream_libraries.py \
    --sdk PATH_TO_SDK_REPOSITORY \
    --site PATH_TO_SIGNED_C_SITE \
    --vm PATH_TO_MATCHING_VM \
    --basex .tmp/base-x-5.0.1.tar.gz \
    --abbrev .tmp/abbrev-0.1.2.tar.gz \
    --output .tmp/script-library-tests
```

Use an unused output directory and the existing 64 GiB cgroup gate. By
default the tool runs both suites serially. Add `--language js` or
`--language ruby` to select one. The QuickJS guest has one read-only clock
import. The mruby guest has an empty import table. Each module runs under
the interpreter and AOT with synchronous tag checks. Receipts identify
the archive, source, compiler, VM and Wasm digests and record failures at
the stage that reported them.

[简体中文](README.zh-CN.md)
