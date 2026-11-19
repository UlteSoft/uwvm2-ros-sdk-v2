# 使用标准 Go 开发标量控制器

`wrgo` 在 Linux x86-64 主机上使用 Go 1.24.2 官方编译器，对单份 Go 源码做类型检查与优化，然后生成 wasm32 核心模块。支持输入和返回值为 `int32`、`uint32`、`int64`、`uint64`、`bool` 的单返回块纯函数。算术包括加减乘、位运算和整数比较。优化后的操作超出范围时，编译会失败。完整 Go 堆、协程、标准库、初始化、指针、切片、wasm64 与线程仍待实现。

## 安装与构建

将 `REV` 设为完整 SDK 提交哈希，并选择目标平台。以下以 Unitree 为例。

```sh
python3 install/bootstrap.py install --commit "$REV" --platform unitree --language go --prefix "$PWD/sdk"
```

将安装程序打印的目录设置为 `UWVM_ROS_SDK_ROOT`。目录含 `bin/wrgo`、Linux x86-64 主机编译器、Wasm 生成器、示例与 Xmake 适配器。默认安装只选取所需语言和平台，增加 `--component compiler-source` 可取得官方源码、许可证和构建脚本。重建时下载同版官方 Linux x86-64 启动工具链，运行 `language/go/producer/build.py --source <source.tar.gz> --bootstrap <linux-amd64.tar.gz> --output <新目录>`。脚本校验两份归档的固定摘要。[Go 官方发布归档](https://go.dev/dl/#go1.24.2)

```sh
cd "$UWVM_ROS_SDK_ROOT/examples/shared/common/go"
"$UWVM_ROS_SDK_ROOT/bin/wrgo" controller.go -o controller.wasm --build-receipt
xmake f -p wasm-wasip1 -a wasm32
xmake
WROS_VM=/absolute/path/to/uwvm2-ros xmake run
```

编译器导出各个具名标量函数。定义 `func Start() uint32` 作为入口。返回非零值触发 Wasm 陷阱。扩展接入示例通过 `add_wros_operations("abi")` 或 `wrgo --ros-abi` 选择只读导入 `uwvm_ros_v2.abi`，此时 `Start` 的唯一 `uint32` 参数是实际查询结果。VM 另行授权，运行该示例时使用 `WROS_RUN_QUERIES=abi`。这个前置检查只读取父级 ABI，驱动权限和平台子模块状态还需独立检查。

## 内存与权限

MTE 默认开启。每个函数必须通过逐指令允许清单检查，并将原始 SSA 内存标识原样返回。生成器只发布无内存、无读写指令且无间接调用的模块，因此已发布函数能证明可以省略所有 tag。用户显式传 `--no-mte` 后仍执行同样的函数检查。生成物没有 WASI 导入、组件或原生执行入口，也不会回退至系统 Go 编译器。可选构建收据记录输入、编译器和产物摘要、导入与 MTE 设置。

也可以用 `--site-profile <文件>` 传入操作员提供的配置。该配置绑定该标量配置下经过 WSEA 签名的发布声明、编译器、生成器、两个 VM 引擎测试、源码准入和 Xmake 收据。每次编译均重验签名；普通固定提交安装无需站点声明。

迁移示例复现了 Noetic costmap_2d 的无符号网格索引运算，并校验内部单元格、行边界和溢出结果。其覆盖范围是该单项运算。[ROS Noetic Costmap2D::getIndex 源码](https://github.com/ros-planning/navigation/blob/noetic-devel/costmap_2d/include/costmap_2d/costmap_2d.h#L171-L174)
