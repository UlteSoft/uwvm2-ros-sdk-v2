# 编译器与解释器的发行来源

在完整 SDK 检出目录中运行以下命令，可以离线核对所有语言的源码来源。
对单个语言运行时可指定 `--language js --require`，来源验证失败会返回非零退出码。
工具按上游正式发行记录核对 SDK 使用的源码锁、归档和宿主文件清单。

```sh
python3 tools/qualification/language_sources.py
```

| 语言 | 上游来源和验证范围 |
| --- | --- |
| C、C++、Fortran | 通用锁指向 LLVM 23.1.5 正式发行提交。WASI SDK 34 的子模块指向对应的 wasi-libc。使用某个编译器仍需核对构建与二进制收据，包括 C++ 的稳定版 Herbceptions 回移植。 |
| Java、Kotlin | TeaVM 0.13.1 与正式发行提交一致。Kotlin 编译器为 2.1.20，宿主清单绑定 Ubuntu OpenJDK 21.0.10+7。两份语言清单共有 36 个不同 Maven 构件，已逐项与 Maven Central 核对 SHA-256。 |
| JavaScript、Lua | QuickJS 原始分发版本为 2026-06-04。运行 `python3 third-parties/quickjs/verify_release.py` 可从该归档重放 SDK 的实际改动。Lua 5.4.9 源码归档与上游公布摘要一致。 |
| Nim、Rust | Nim 2.2.4 源码与官方分发归档匹配。Rust 1.98.0 源码归档与稳定频道清单匹配。 |
| TinyGo | 已核对的宿主清单对应 TinyGo 0.38.0 和 Go 1.24.2。独立的 Go 前端单列。 |
| D | LDC 1.41.0 有正式版本。现场资格还需将实际可执行文件和 BetterC 导入文件关联至该版本。 |
| Objective-C | GNUstep 正式发行的 libobjc2 2.3 对应 e877e782，SDK 旧基线 a21ae931 没有发行标签，两个提交已经分叉。检查器要求正式发行归档。 |
| C#、Visual Basic | 两种语言共用的托管编译器宿主另行核查。 |

缺少开发包的语言在报告中单列。升级工具链需更新上游来源证明并重新验收构建结果。
此项核对只覆盖编译输入来源。执行配置、MTE、签名、仿真和平台能力各有独立验收。
机器可读记录包含各上游发行链接。[发行证据](../../share/qualification/language-source-releases.json)
