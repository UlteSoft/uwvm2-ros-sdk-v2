# TypeScript 工程

使用 `--language typescript` 安装，随后将 `examples/typescript` 复制到可写目录。SDK 默认使用随包提供的 `share/toolchains/node/bin/node`。如需改用固定版本 Node.js 22.22.3 的另一份官方 Linux x64 可执行文件，可将 `WROS_NODE` 指向它。`bin/wrts` 先用固定版本的 TypeScript 5.9.3 按 ES2022 严格模式检查类型，再用 JavaScript 工程使用的私有 QuickJS 后端编译产出的模块。

```sh
"$UWVM_ROS_SDK_ROOT/bin/wrts" main.ts filter.ts --ros-operation abi -o guest.wasm
xmake build
xmake test -j1
```

命令行首先传入入口文件，再列出其他 `.ts` 文件。若项目公共根目录位于入口目录的上层，传入 `--project-root`。在 Xmake 中使用 `add_files("main.ts", "filter.ts")` 声明文件，并用 `set_wros_entry("main.ts")` 指定入口。用 `--ros-operation` 或 `add_wros_operations` 声明宿主导入，类型检查器据此提供 `uwrosv2/<domain>` 中对应的原始函数。i64 参数使用 `bigint`，i32 参数使用 `number`。QuickJS 需要 WASIp1 实时时钟，示例为本地运行声明了这项权限。

专用平台解码示例位于 `examples/<platform>/typescript`。类型声明取自 `include/u2rosv2/platform/<platform>/typescript`，实际解码代码取自同一提交中的 JavaScript 绑定。以 `Uint8Array` 传入平台手册指定格式的记录。[安装与 Xmake](../install-xmake.md)
