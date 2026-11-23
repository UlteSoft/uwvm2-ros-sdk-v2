# 用于 WASI 的 Mono

[English](README.md)

本目录的原生源码取自 .NET Runtime v10.0.15，完整 Git 提交为 `a3788b71495457354b64ca8040b6ded5ff6ca4f9`。包括 Mono AOT 编译器与运行时源码、SGen 垃圾收集器、Mono 专用 CoreLib 源码、WASI 平台代码和共用原生头文件。索引逐文件记录所选上游 Git blob。[上游发行版](https://github.com/dotnet/runtime/tree/a3788b71495457354b64ca8040b6ded5ff6ca4f9) · [源码及许可证](upstream.json) · [文件索引](upstream.git-blobs)

在 wasm32 WASI 目标上，移入的 SGen 修改使用 wasi-libc 排序，限制收集器持有堆锁期间的临时存储。这个源文件在正式发行版中与旧补丁的上游基线逐字节相同。C#、F#、Visual Basic 的托管语言编译器、配套的 Mono WASI 构建和安装后的独立工程仍待交付与验收。
