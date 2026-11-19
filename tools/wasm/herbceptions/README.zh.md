# 还原 LLVM Herbceptions 源码

编译器源码包可还原 Herbceptions 提交
`218014296779772a4edbe63eff3fe6fe0ba92390` 的完整源码树。它复用 SDK
已收录的 LLVM 23.1.5 源码归档，以 Git 二进制补丁提供所有差异，保留文件模式、
符号链接、测试和 `libherbceptions` 运行库。该提交的许可证随补丁一同存放于
`third-parties/sources/llvm-herbceptions-21801429/`。

在 SDK 根目录执行下列命令，选择尚不存在的输出目录。Linux 文件系统须支持符号链接
和可执行位，建议预留至少 9 GiB 临时空间。需要 Python 3.11 或更高版本、Git、
GNU tar 和 xz。

```sh
python3 tools/wasm/herbceptions/recover_source.py --output /work/llvm-herbceptions
```

整个过程可离线完成。脚本先校验基础归档和补丁的 SHA-256，再校验最终 Git 树
`69a2c7cbcfb0371010a4b5a02d0f73e14eef23ed`，验证通过后才生成目标目录。
任一校验失败都会终止并清理临时文件。此处还原的上游源码随后交给 SDK 的编译器
构建流程，由该流程应用 Wasm 内存标记补丁并选择 WebAssembly 后端。

[上游提交](https://github.com/trcrsired/llvm-project/commit/218014296779772a4edbe63eff3fe6fe0ba92390)
