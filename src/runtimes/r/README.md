# GNU R 4.5.1

[简体中文](README.zh.md)

The tree contains the evaluator, base library sources, math code and Unix platform sources from the CRAN release. Two retained changes apply to the release without modifying their original context. The WASI configure path handles the missing dynamic-loader variable and skips the libcurl probe. Rmath.h also supports C translation units on a target without working log1p.

The standalone runtime Wasm, installable language entry point and external guest project still require qualification. [Upstream identity, licenses and changes](upstream.json) · [Original release file digests](upstream.sha256)
