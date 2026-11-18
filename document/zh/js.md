# JavaScript

使用 SDK 安装器按提交选取平台及 `js` 开发包。站点配置使用经验证的 C 工具链和 sysroot。在安装目录中，可调用 `bin/wrjs application.js -o application.wasm --ros-abi --build-receipt`。xmake 使用 `set_language("js")` 和 `add_wros_operations(...)`。安装包内带[可运行的 guard 示例](../../examples/js/body.js)。

例如，以下命令使用完整的 SDK 提交号 REV、安装目录 PREFIX 和本站审核通过的 C 工具链配置 C_SITE。

```sh
python3 install/bootstrap.py --commit "$REV" --platform unitree --language js \
    --prefix "$PREFIX" --site-profile "$C_SITE"
"$PREFIX/$REV/unitree/js/development/bin/wrjs" application.js -o application.wasm --ros-abi --build-receipt
```

编译器将单个 UTF-8 脚本和 QuickJS 一同编译为核心 Wasm 模块，单个脚本最多 1 MiB。目标是 wasm32、Core 3.0、EH、单线程、`-O3 -g`，默认开启严格 MTE。显式使用 `--no-mte` 需要相应的工具链和 sysroot，也可用 `--toolchain DIR --sysroots MANIFEST` 指定。开发流程始终输出 Wasm。当前同步入口不提供 Node.js、模块文件加载或事件循环。

时钟只导入 Preview1 的 `clock_time_get`，按主模块策略授权实时时钟。ROS 接口通过重复的 `--ros-operation 名称` 选择，部署时对每个导入和能力分别授权。选择 `abi` 后可调用 `wros.abi()`。选择 `capability.open` 后，`wros.open(alias)` 成功返回不透明句柄，失败返回状态码。选择 `capability.close` 后，`wros.close(handle)` 返回状态码。其余调用统一使用 `wros[name](handle, requestArrayBuffer, responseCapacity)`。允许空令牌的操作可传 `null`。结果包含数值型 `status`、ArrayBuffer 或 null 型 `data`、BigInt 型 `written`。数据编码沿用通用 ROSv2 协议。每次请求和响应各限 1 MiB，复制后的临时数据会清零；解释器堆限 8 MiB，调用栈预算为 32 KiB。

构建回执记录生成解释器的 C 后端。独立的 JavaScript 回执绑定脚本、解释器源码、选用接口和最终 Wasm 摘要。平台及外置驱动权限由部署方配置。

当前签署的 C 链接器同时导出 `_start` 和名为 `memory` 的应用内存。部署策略应禁止其他模块导入此内存。JS 接口向脚本提供的是对象和有界副本。删去 Wasm 内存导出会改变最终摘要，须经新的生产者或打包签审。
