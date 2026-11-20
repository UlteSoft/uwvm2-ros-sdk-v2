# Upstream Python libraries in the Wasm SDK

This replay uses the Python implementation and all seven test methods from
ROS `angles` 1.16.1 at commit `a96224f9ab3ac51fe8fd981c1e1554528dc4345a`.
It also runs 555 version-test invocations from 21 test methods in PyPA
`packaging` 25.0 at commit `f58537628042c7f29780b9d33f31597e7fc9d664`.
The checkout identity and release archive digests are verified before use.
[ROS angles](https://github.com/ros/angles/tree/a96224f9ab3ac51fe8fd981c1e1554528dc4345a).
[PyPA packaging](https://github.com/pypa/packaging/tree/f58537628042c7f29780b9d33f31597e7fc9d664).

Fetch the `angles` checkout and `packaging` archive into a local test directory.
Pass the checked-out tree and the exact GitHub archive to the replay.

```sh
git clone --depth 1 --branch 1.16.1 https://github.com/ros/angles.git .tmp/angles-test-source
curl --fail --location \
  https://codeload.github.com/pypa/packaging/tar.gz/f58537628042c7f29780b9d33f31597e7fc9d664 \
  --output .tmp/packaging-25.0-test.tar.gz

PATH_TO_GATE /usr/bin/python3 -B tests/cpython/upstream_libraries.py \
  --angles .tmp/angles-test-source \
  --packaging .tmp/packaging-25.0-test.tar.gz \
  --cpython third-parties/cpython/Python-3.14.8.tar.xz \
  --sdk PATH_TO_INSTALLED_PY_DEVELOPMENT_SDK \
  --vm PATH_TO_QUALIFIED_UWVM2_ROS \
  --output .tmp/python-upstream
```

Use the existing 64 GiB gate and a fresh output directory. The test requires
the installed wasm32, Core 3.0, single-thread, EH and strict MTE C site at
`-O3 -g`. The installed CPython runtime pack must match that site and VM.
Native reference execution and Wasm execution use the same upstream assertions.
The guest uses the CPython 3.14.8 `unittest.TestCase` and `TestResult`
implementations directly. The packaging adapter replays literal upstream
parameters while retaining the test methods' bodies. The receipt lists five
methods outside this replay, covering extra pytest or pretend behavior and
nonliteral fixture expressions.

The build records the interpreter archive and exact Wasm digest. The import
audit requires the two read-only Preview 1 clock imports. The identical module
runs in UWVM2 interpreter and AOT with synchronous MTE. The test covers the
named pure-Python library behavior. ROS transport, other packaging test files,
memory64, threading and deployment require their own evidence.

[简体中文](upstream-libraries.zh-CN.md)
