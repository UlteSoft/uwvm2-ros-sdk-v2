# WROS SDK 开发指南

## 按 commit 安装

使用 Python 3.11 或更高版本。REV 必须是可信的 40 位小写 Git commit。固定入口可用于后来遵循同一安装协议的版本。用普通开发用户执行脚本。


新机器上只需获取首次提交的安装入口文件。将 `REV` 设为要安装的完整提交 ID。这个脚本可独立运行。

```sh
curl --fail --silent --show-error --output bootstrap.py \
  https://raw.githubusercontent.com/UlteSoft/uwvm2-ros-sdk-v2/cf09b4b30e3801deb73c012957b9f1c5f1196289/install/bootstrap.py
printf '%s  %s\n' e93d8e7c2fe733d8c33ca09c5dfee38d5047b0c11ba0524b5b2d8fecb36f1f29 bootstrap.py | sha256sum --check -
python3 bootstrap.py revision-help --commit "$REV" --language cpp --platform unitree
```

```sh
python3 install/bootstrap.py plan --commit "$REV" --language cpp --platform unitree
python3 install/bootstrap.py install --commit "$REV" --language cpp --platform unitree --prefix "$SDK_HOME"
python3 install/bootstrap.py revision-help --commit "$REV" --language cpp --platform unitree
```

固定命令为 `plan`、`install` 和 `revision-help`。后续版本的参数放在 `--` 后面。指定 `--local-repository` 可以离线读取本地 Git 对象。引导器先读取所选 commit 的 Python 脚本和必要的小清单，再逐文件校验大小和 SHA-256。所有成员校验通过才发布安装目录。相同摘要的文件可以复用，输出的 requested_paths 可用于核对传输范围。版本脚本是所选提交中的可执行代码。

`--component protocol` 安装通用协议及指定平台的来源记录。`--component compiler-source` 安装 C/C++ 编译器及 sysroot 的固定源码和补丁。常规开发安装只取对应开发文件。

已有编译环境时，可使用 `-- --component bindings` 单独安装所选语言的原始声明、许可证以及所选语言和平台的元数据。C 和 C++ 共用头文件，本修订还提供 Rust 和 AssemblyScript 的声明。此模式仅请求这些文件。首个 commit 的安装入口也可通过 `revision-help` 发现新选项。

### 修订脚本和文件清单格式

固定入口为所选提交中的 `install/revision.py`。安装器通过 Python 隔离模式执行该脚本，依次传入平台名、语言名以及分隔符 `--` 后的扩展参数。`revision-help` 传入 `--revision-help`，读取含 `help` 字符串的 JSON 对象。正常选择时，脚本向标准输出写入一个 JSON 对象，例如

```json
{"variant":"bindings","packages":["platforms/unitree","metadata/cpp","license","bindings/c"]}
```

每个包名对应同一提交下的 `install/packages/<包名>.json`。清单的 `files` 数组逐项声明仓内相对路径、字节数 `bytes`、小写 SHA-256 和十进制 POSIX 权限 `mode`（420 或 493）。多个包引用同一路径时，元数据必须一致。单次选择最多 64 个包、8,192 个不同文件，单个文件上限 128 MiB，载荷总上限 1 GiB。安装目录为 `<prefix>/<commit>/<平台>/<语言>/<variant>`，同时通过结果字段 `directory` 返回。后续修订应保持首版基础命令和上述脚本格式。仓库中的 `tests/install_protocol_matrix.py` 从指定提交的 Git 对象执行安装，逐个核对所有已登记语言与平台组合的实际文件集合。

## 编译程序

`wrc` 用于 C，`wrcc` 用于 C++。PRODUCER 指向支持 WasmMTE 的专用编译器目录，RECEIPT 指向与这个编译器摘要匹配的 sysroot 构建记录。编译器和基础库的源码构建入口位于 `tools/wasm/memtag`。

```sh
bin/wrcc --toolchain "$PRODUCER" --sysroots "$RECEIPT" --reactor --export _start -O3 -g -o body.wasm body.cpp
```

默认 wasm32、Core 3.0、MTE、标准 Wasm EH，线程默认关闭。使用 `-pthread`、`--target wasm64`、`--no-mte`、`--no-eh`、`--core mvp` 选择对应配置。依赖 pthread 的构建须传递线程选项。地址宽度、线程、MTE 和异常模式各自决定可使用的 sysroot。链接后检查实际导入名和签名，拒绝通用 POSIX 套接字。允许有限的 WASIp1 环境变量和退出操作。运行权限另由 VM 控制。

C/C++ 使用 `<wros/scene.h>`，Rust 和 AssemblyScript 的底层声明位于 `language/`。底层声明对应本次 VM 登记的 163 项操作。29 个旧语言标识、32 个平台标识及其来源属于迁移清单。其他编译器、高层绑定、各厂商实机和旧 ROS 源码兼容层的验收需有各自的构建与执行记录。

## 厂商接入

SDK 的登记范围可扩展到国内和国际厂商。纯算法留在 Wasm，设备访问交给加密连接的隔离驱动。只有通用权限难以表达、且需要宿主执行的约束才进入 VM 平台扩展。上层拉取器按授权从厂商入口获取原厂文件，部署器只读取本地文件并验证摘要。协议来源、物理仿真和实体设备验收分别登记。
