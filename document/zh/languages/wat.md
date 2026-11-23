# WebAssembly 文本工程

使用 `--language wat` 安装。复制安装目录中的 `examples/wat`，按照[安装指南](../install-xmake.md)设置环境，然后执行 `xmake build` 和 `xmake test -j1`。工程显式声明导入 `uwvm_ros_v2.abi`，并在 VM 中检查实际返回值。

```sh
"$UWVM_ROS_SDK_ROOT/bin/wrwat" main.wat --target wasm32 --core 3.0 \
    --mte --eh --ros-operation abi -o guest.wasm
```

每个 `--ros-operation` 声明一个导入，其签名须与安装的契约一致。WAT 在模块中定义内存位宽。此汇编器的 `--target wasm64` 开启 memory64 验证，`--target wasm32` 关闭该特性。`-g` 生成调试信息，`--build-receipt` 输出编译记录。源码安装包含可编辑的 `src/compilers/wrwat`、Cargo 锁、依赖源码和重建脚本。

`include/u2rosv2/universal/wat/uwrosv2` 提供 38 个按域划分的模块和汇总文件 `scene.wat`。将需要的导入复制到自己的模块中，VM 即可识别调用方及其线性内存。每个导入的注释都给出操作语义、调用权限、具名参数、记录布局、内存生存期和不同返回状态下的输出行为。专用平台解码模块位于 `include/u2rosv2/platform/<platform>/wat`，可运行的工程位于 `examples/<platform>/wat`。
