# C++ 工程

使用 `--language cpp` 安装，按照[安装指南](../install-xmake.md)设置 `UWVM_ROS_SDK_ROOT` 和 `WROS_VM`。原生驱动 `wrcc` 会查找已安装的 C++ 头文件和所选平台的公共头文件。复制 `examples/cpp` 后，可在工程目录编译 ABI 版本查询示例。

```sh
"$UWVM_ROS_SDK_ROOT/bin/wrcc" --reactor --export _start --std c++20 main.cpp -o guest.wasm
```

`--std` 支持 `c++98`、`c++03`、`c++11`、`c++14`、`c++17`、`c++20`、`c++23` 与 `c++26`。Xmake 使用相同的值，例如 `set_wros_profile({std = "c++98"})`。每个域都有独立头文件，也可以通过 `<uwrosv2/scene.hpp>` 引入全部接口。调用通过状态码或 `result<uint64_t>` 这类类型化结果报告错误。同时使用两种语言接口时，把 C 安装目录下的 `include/u2rosv2/universal/c` 加入 C++ 工程的 include 路径。C 与 C++ 头文件在 C++98/03 下以 `throw()` 声明调用，从 C++11 起使用 `noexcept`。随包配置启用 Wasm EH 与 Herbceptions，Xmake 可通过 `eh` 和 `herbceptions` 分别选择。

SDK 的 `include/sysroot/c++/` 中可直接查看 libc++ 的 `vector`、`string` 等头文件，以及 Herbceptions 的 `herbceptions/error`。代码可照常引用 `<vector>` 或 `<herbceptions/error>`。驱动为所选线程模型配置 libc++。

C++ 与 C 共用带标签的指针减法和按字节相减的内建函数。[WasmMTE 指针相减](c.md#wasmmte-指针相减)

## 管理能力与资源的生存期

能力句柄代表部署为某个别名授权的一组操作。通过该能力创建的 guard、timer、clock 或 waitset 各有独立的资源句柄。`<uwrosv2/owner.hpp>` 提供两种不可复制的所有者。下面的 C++98 函数打开配置好的别名、创建 guard，并触发一次。

```cpp
#include <uwrosv2/guard.hpp>

uint32_t notify() UWROSV2_CPP_NOEXCEPT {
    uwrosv2::capability_owner grant;
    uint32_t code = grant.open("signal");
    if (code) return code;

    uwrosv2::resource_owner guard;
    code = uwrosv2::guard::create(grant.get(), guard);
    if (code) return code;
    return uwrosv2::guard::trigger(grant.get(), guard.get());
}
```

先声明能力，再声明借用它的资源。接管资源所使用的能力需要具有该资源的 `resource.close` 权限。离开作用域时，每个资源通过原能力调用 `resource.close`，最后由能力所有者调用 `capability.close`。`get()` 返回借用的身份，可在所有者持有期间传给其他接口。如果某个资源需要离开当前作用域，先结束其他借用，再调用 `resource.take_capability(grant)`。该资源将接管两个句柄，按先资源、后能力的顺序关闭。

显式调用 `close()` 可获得 VM 状态码，并在所有者仍存活时重试。如果资源已成功关闭而能力关闭失败，重试只关闭能力。析构会尝试完成剩余清理，并忽略返回状态。对已清空的所有者调用 `close()` 返回成功。

所有标准都支持 `source.transfer_to(destination)`、`swap` 与 `release`。移交会先关闭目标已有的资源。如果目标正拥有传入资源所借用的能力，就会为传入的资源保留该能力。如果这一步失败，来源继续持有原句柄，目标保留尚未完成的清理责任。C++11 起还支持移动构造与移动赋值。调用者需要获知目标清理状态时使用 `transfer_to`。能力的 `release()` 返回原始能力句柄。资源的 `release()` 返回能力、资源以及 `owns_capability` 标志，可交给空所有者的 `adopt` 接手。

## 运行所有权示例

将随包工程复制到可写目录。它让两个 guard 共享一个能力，在局部作用域结束时释放第一个 guard，再将另一个 guard 连同能力移交给调用者。启动脚本会为本地场景准备 `signal` 别名和示例使用的六个导入。

```sh
cp -R "$UWVM_ROS_SDK_ROOT/examples/cpp/raii" scoped-guard
cd scoped-guard
"$UWVM_ROS_SDK_ROOT/bin/wrcc" --std c++98 --reactor --export _start main.cpp -o guard.wasm
sh run.sh guard.wasm int
sh run.sh guard.wasm aot
```

两种引擎执行成功时均返回退出码零。工程内也提供 `xmake.lua`，可执行 `xmake build`。另一个项目 `examples/cpp/migration/angles` 展示从独立 guest 使用 ROS angles 库。
