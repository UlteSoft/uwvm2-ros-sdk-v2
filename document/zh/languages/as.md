# AssemblyScript 工程

使用 `--language as` 安装。SDK 自带 Linux x64 版 Node.js 22.22.3，默认路径是 `share/toolchains/node/bin/node`。需要改用同一发行二进制的其他副本时，可将 `WROS_NODE` 指向该文件。`bin/wras` 会核对宿主程序及配套的 AssemblyScript 0.28.20、Binaryen 和 long 包。将 `examples/as` 复制到可写目录即可使用标量示例。

```sh
"$UWVM_ROS_SDK_ROOT/bin/wras" main.ts --ros-abi -g -o guest.wasm
xmake build
xmake test -j1
```

可从 `./uwrosv2/<domain>` 导入标量 ABI 函数。`include/u2rosv2/universal/as/uwrosv2` 中的声明说明了 VM 注册的 163 个导入。标量前端生成没有线性内存的 wasm32 程序，入口为用户定义的 `_start(): void`，可选的宿主导入为 `abi`。

专用平台工程位于 `examples/<platform>/as`。使用 `wras main.ts --ros-driver -o guest.wasm` 编译，也可直接运行工程的 Xmake 命令。工程使用 `set_wros_profile({as_driver = true})` 启用有界暂存区，可通过 `./wros` 写入 512 字节的请求缓冲区。平台模块还可读取上一次成功的驱动回复。附带样本可离线运行。使用真实驱动的应用可重复指定 `--ros-operation`，核对产物的导入集合。

原始导入模块逐项说明 VM 契约。链接和执行的验证记录按提交区分。[安装与 Xmake](../install-xmake.md)
