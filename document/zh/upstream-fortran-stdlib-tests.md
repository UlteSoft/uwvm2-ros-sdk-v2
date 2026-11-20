# Fortran stdlib 梯形积分验收

本回放覆盖 Fortran-lang stdlib v0.8.1 的梯形积分，固定提交 `0ede3015ba4c7f945e1daa6b1fc504c0fbf1236f`，并按 SHA-256 校验上游文件与许可证。用上游 Fypp 模板生成库与六个 FP32、FP64 测试。20 个原始断言覆盖等距采样、不规则采样、积分权重以及空数组和单元素数组。适配器以带数字状态的 `ERROR STOP` 替换 test-drive 的错误报告，并保留库的参数长度检查。 [正式发布](https://github.com/fortran-lang/stdlib/releases/tag/v0.8.1) · [上游测试](https://github.com/fortran-lang/stdlib/blob/0ede3015ba4c7f945e1daa6b1fc504c0fbf1236f/test/quadrature/test_trapz.fypp)

通过现有的 64 GiB、零 swap 测试门禁执行。将 `SDK_REPOSITORY` 和 `SDK_COMMIT` 设置为待验收的 SDK 检出路径和完整提交号，另需本地 GFortran 与 Fypp。`--fetch` 只下载五份固定源码和模板及其许可证。离线回放时，把六个文件按原文件名放在同一目录，再以 `--inputs` 指定该目录。

```sh
"$WROS_TEST_GATE" python3 -B tests/fortran_stdlib_upstream.py \
  --repository "$SDK_REPOSITORY" --commit "$SDK_COMMIT" \
  --native "$(command -v gfortran)" --fypp "$(command -v fypp)" \
  --fetch --output "$PWD/.tmp/stdlib-trapz-native"
```

追加 `--site-profile "$SITE" --vm "$VM"` 可测试正式签名 `wrf` 路径。站点需要提供适配 wasm32 调试构建与该 VM 的 Fortran、C 和 C++ 资格记录。追加 `--plain --toolchain "$TOOLCHAIN" --sysroots "$PLAIN_SYSROOTS" --vm "$VM"` 可测试显式关闭 MTE 和 EH 的对照路径。两条路线均以 `-O3 -g` 构建，准入和链接通过后运行 INT 与 AOT。每次回放使用独立输出目录。

请求的路线失败时，脚本返回非零状态。`results.json` 记录各路线到达的阶段，同目录日志保留编译器或准入工具的实际诊断。SDK `63b57f8` 上的原始断言已通过原生 GFortran 15.2.0 验证。仅含 C 资格的签名站点在安装阶段拒绝了 Fortran。关闭 MTE 的对照构建到达 Flang C++ 运行库，但缺少 Herbceptions 生成工具与匹配 C++ sysroot。单独的静态库试验已生成封装归档，链接阶段仍需要固定版本 Flang 描述符运行库提供 `_FortranAAssign` 和 `_FortranAAssignTemporary`。该库配置的 Wasm 执行尚未验证。 [Flang 数组赋值实现](https://github.com/llvm/llvm-project/blob/392dfff97d29b59d77e5cac6d4b6ef2585fe7117/flang-rt/lib/runtime/assign.cpp)
