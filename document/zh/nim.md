# Nim 应用开发

SDK 的 Nim 2.2.4 专用前端按所选 Wasm 目标的内存布局生成 C，由 WROS Clang 将应用、运行库及 ARC 分配编入同一个核心模块。VM 通过 `_start` 运行程序。当前支持单线程 ARC 和 Nim 自身的 goto 异常处理。EH 选项决定所链接的 sysroot ABI。

选择登记了 Nim 的平台（如 `unitree`），安装时选 `compiler-source` 可获取专用前端的固定版本源码。使用受信任的宿主 Nim 编译器构建这个前端。Nim 宏在开发机编译期间求值，编译完成的客体在 VM 内运行。

```sh
python3 language/nim/build_producer.py --bootstrap /usr/bin/nim --output /absolute/build/wrnim-lower
bin/wrnim app.nim --producer /absolute/build/wrnim-lower --toolchain "$WROS_TOOLCHAIN" \
  --sysroots "$WROS_SYSROOTS" --target wasm32 -O3 -g -o app.wasm
```

默认使用经过审核的 MTE 配置。显式使用 `--legacy-mte` 可以测试待审核的带标签配置。`--no-mte` 需要匹配的无标签 sysroot。生成 wasm64 时同时指定 `--target wasm64` 和对应的 sysroot。使用 Xmake 时设置 `WROS_NIM_PRODUCER` 并指定一个入口文件，其他模块从入口导入。

`import wros_scene` 提供通用 ROSv2 接口。参数使用固定宽度整数，通过 `wrAddress` 提交客体地址并指定线性内存索引。每项宿主操作仍由 VM 单独授权。可使用 `examples/nim/body.nim` 验证编译和 ROSv2 ABI 查询。SDK 拒绝 WASI Preview 2/3、组件模型接口，以及 Nim 构建清单中的外部原生对象和链接依赖。厂商原生驱动由部署器在 VM 进程外管理。

站点管理员将已审核的 Nim 编译前端放在 `TOOLCHAIN/bin/wrnim-lower`。安装时通过 `--site-profile FILE` 指定配置。安装后执行 `bin/wrnim app.nim -o app.wasm --build-receipt` 即可使用已审核的编译器和 sysroot。xmake 项目读取同一份安装配置。

## 在 UWVM 中调试应用

编译时传入 `-g`，或在 Xmake 中使用 `set_symbols("debug")`。Nim 的 C 后端生成源码行号指令，Clang 将行号写入 Wasm 的 DWARF。可以在原始 `.nim` 文件的可执行行设置断点。调试器使用另一份源码时，通过 DAP 的 `sourceMap` 将记录中的绝对路径映射到本地路径。

使用 `-O3` 时，调试器在优化后保留的位置之间单步。列号和变量表示来自生成的 C。局部变量可能被重命名或优化掉。Nim 自身的运行时栈跟踪和行跟踪保持关闭。

签名发布会校验编译驱动。升级驱动后，先用确切的 SDK 与前端重新验收，再签署相应的发布声明。
