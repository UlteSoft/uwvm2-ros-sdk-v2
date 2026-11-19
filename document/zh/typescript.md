# 使用 TypeScript 开发 Wasm 应用

在 Linux x86-64 构建机上，按确定的 SDK 提交和目标平台安装。开发包带有微软 TypeScript 5.9.3、ES2022 类型声明、运行编译器的 Node 22.22.3、QuickJS 源码和 WROS 编译入口。安装时使用操作员批准的 C 站点文件，其中记录了编译器、wasm32 EH sysroot、目标 VM 和签名。

~~~sh
python3 install/bootstrap.py install --commit "$SDK_COMMIT" --platform unitree \
  --language typescript --prefix "$PWD/sdk" --site-profile "$C_SITE"
~~~

将安装器输出的目录赋给 UWVM_ROS_SDK_ROOT。下面用于计算传感器采样平方和的示例有两个模块，可以直接编译，也可以用 xmake 构建。

~~~sh
cp -r "$UWVM_ROS_SDK_ROOT/examples/typescript" ./filter
cd filter
"$UWVM_ROS_SDK_ROOT/bin/wrts" main.ts filter.ts --ros-abi --build-receipt -o filter.wasm
xmake f -p wasm-wasip1 -a wasm32 -y
xmake -v filter
WROS_RUN_QUERIES=abi,realtime-clock WROS_VM="$QUALIFIED_VM" xmake test -j1
~~~

第一个源码文件是入口，后面列出相对导入需要的所有源码。多目录工程可以用 --project-root DIR 指定共同根目录。xmake 的 add_files 声明编译输入，set_wros_typescript_entry 选择入口。编译器对这些源码执行严格类型检查，在客户机中使用 ES2022 和 CommonJS 模块初始化语义。缺失源码、裸包名、动态导入和编译器引用指令都会导致编译失败。Node 只在构建机运行编译器。应用和 QuickJS 一起编进同一个 Wasm，部署时由 VM 执行。应用应同步完成工作。

## ROS 调用与授权

使用 --ros-operation NAME 或 xmake 的 add_wros_operations 逐项声明操作。选择 abi 后，类型检查器会提供 wros.abi()。打开资源时得到不透明句柄或数值错误码。数据接口接受句柄或 null、ArrayBuffer 请求和响应容量，返回 status、bigint 类型的 written 以及 ArrayBuffer 或 null 类型的 data。访问未选择的 SDK 操作会在类型检查阶段报错。部署时 VM 独立检查导入策略和资源授权。QuickJS 使用 WASIp1 的 clock_time_get；此示例还需要 realtime-clock 时钟授权和 ROSv2 的 abi 导入许可。

## 编译配置与交付记录

解释器目前的目标为单线程 wasm32、Core 3.0、开启 EH。默认以严格 MTE、-O3 和 -g 编译解释器 C 代码。显式 --no-mte 需要匹配的无标记 sysroot 和工具链。--build-receipt 同时生成 C、QuickJS、TypeScript 三层记录。TypeScript 记录包括每个源码的摘要、入口、编译器身份、ROS 操作，以及生成的 JavaScript 和 Wasm 摘要。部署时可以把它们与二进制一同归档。

[微软 TypeScript 发布记录](https://github.com/microsoft/TypeScript/releases/tag/v5.9.3) · [QuickJS 权限与运行时](js.md) · [xmake 构建参数](xmake.md)
