# JavaScript 工程

使用 `--language js` 安装，并将 `examples/js` 复制到可写工程。`bin/wrjs` 调用随包提供的私有 wasm32 C 后端，将适配后的 QuickJS 和应用模块一起编译成 Core Wasm。二进制安装包含此构建所需的解释器和工具链文件。

```sh
"$UWVM_ROS_SDK_ROOT/bin/wrjs" main.mjs --ros-operation abi -o guest.wasm
xmake build
xmake test -j1
```

从 `uwrosv2/capability` 等模块导入 `wr_abi` 等函数。使用 `--ros-operation` 逐项选择宿主操作，Xmake 中使用 `add_wros_operations`。i64 参数使用 `bigint`。传递原始地址时，保留提供存储的 `ArrayBuffer`，通过 `uwrosv2/memory` 中的 `addressOf` 取得带标签的地址。QuickJS 使用 WASIp1 实时时钟，示例在本地测试配置中显式声明 `"realtime-clock"`。

将 `examples/<platform>/js` 复制到自己的目录即可运行所选平台的离线解码器。例如 ABB 示例从 `uwrosv2/platform/abb/observation` 导入函数，并传入 `Uint8Array`。该 Xmake 工程无需声明 ROS 宿主操作。可用 `--module sub/math.mjs=path/to/math.mjs` 添加依赖，再用相对虚拟路径导入。Xmake 中用 `add_files` 声明文件，用 `set_wros_entry` 指定应用入口。[安装与 Xmake](../install-xmake.md)
