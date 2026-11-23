# Objective-C

wroc 使用安装所得的 GNUstep 和 WROS 头文件，将 .m 编译为 Core Wasm。默认配置为 wasm32、EH、WasmMTE、单线程。可用 --target wasm64、--threads、--no-mte 和 --no-eh 选择已安装的配置。当前源码和本地编译器候选在启用 EH 时通过 GNUstep libobjc2 与 libc++abi 展开标准 Wasm 异常。Linux x86_64 候选已在 `uwvm2-ros` 的 INT 和 AOT 中实测。五宿主及 GitHub 安装进度见[逐项验收记录](../../qualification/objc-library-matrix.json)。

```sh
"$UWVM_ROS_SDK_ROOT/bin/wroc" --platform generic --reactor --export _start main.m -o scene.wasm
```
