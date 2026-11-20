# Fortran stdlib 梯形积分验收

本回放覆盖 Fortran-lang stdlib v0.8.1 的梯形积分，固定提交 `0ede3015ba4c7f945e1daa6b1fc504c0fbf1236f`，并按 SHA-256 校验上游文件与许可证。用上游 Fypp 模板生成库与六个 FP32、FP64 测试。20 个原始断言覆盖等距采样、不规则采样、积分权重以及空数组和单元素数组。适配器以带数字状态的 `ERROR STOP` 替换 test-drive 的错误报告，并保留库的参数长度检查。 [正式发布](https://github.com/fortran-lang/stdlib/releases/tag/v0.8.1) · [上游测试](https://github.com/fortran-lang/stdlib/blob/0ede3015ba4c7f945e1daa6b1fc504c0fbf1236f/test/quadrature/test_trapz.fypp)

通过现有的 64 GiB、零 swap 测试门禁执行。将 `SDK_REPOSITORY` 和 `SDK_COMMIT` 设置为待验收的 SDK 检出路径和完整提交号，另需本地 GFortran 与 Fypp。`--fetch` 只下载五份固定源码和模板及其许可证。离线回放时，把六个文件按原文件名放在同一目录，再以 `--inputs` 指定该目录。

```sh
"$WROS_TEST_GATE" python3 -B tests/fortran_stdlib_upstream.py \
  --repository "$SDK_REPOSITORY" --commit "$SDK_COMMIT" \
  --native "$(command -v gfortran)" --fypp "$(command -v fypp)" \
  --fetch --output "$PWD/.tmp/stdlib-trapz-native"
```

追加 `--plain --guest-assertion-traps --toolchain "$TOOLCHAIN" --sysroots "$PLAIN_SYSROOTS" --vm "$VM"` 可回放显式关闭 MTE 和 EH 的构建。需要带 libc++ 的匹配 sysroot、固定版本的 Flang 和 Wasm IR 助手。固定的 Fortran 运行库使用该 sysroot 对应的 C++ 编译器和库。发布 Wasm 前，已安装的 `wrf` 会校验 sysroot、检查各对象的构建配置并审计最终导入。

来宾测试用 trap 报告失败，保留 20 条数值断言和参数长度检查。回放要求 Wasm 零导入，并验证故意改错的断言在两个引擎中都触发 trap。Fortran 计算运行库尚未实现带外部 I/O 与进程退出语义的通用 `ERROR STOP`。

追加 `--site-profile "$SITE" --vm "$VM"` 可验收签名发布的准入和编译。站点必须提供与 wasm32 调试构建和 VM 匹配的 Fortran、C 和 C++ 资格记录。两种模式都使用 `-O3 -g`。无 MTE 回放已通过原生、解释器和 AOT。仅含 C 凭据的站点会在准入阶段被拒绝，本用例仍需匹配的签名站点复验。每次回放使用新输出目录，路线失败时返回非零状态。回执和同目录日志记录实际构建输入、退出码和诊断。
