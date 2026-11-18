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
