# 选择内存标记配置

`wrc`、`wrcc`、`wrf`、`wrlua`、`wrrs` 和 `wrtg` 使用同一份发布验收索引。默认模式要求编译器、目标库、语言运行库、VM 和优化设置均与已审阅的组合一致。两个存活的独立受管对象，其实际存储区间相隔不超过 64 字节时，必须拥有不同的非零标签。发布验收涵盖自动存储、静态存储及所支持的分配路径。线程配置还须提供线程局部存储与并发测试的证据。

| 编译器选项 | xmake 字段 | 构建行为 |
| --- | --- | --- |
| 默认或 `--mte` | `mte=true` | 拒绝未登记或内容已变更的发布组合。 |
| `--legacy-mte` | `mte="legacy"` | 发出警告，使用所选带标记的 sysroot 构建。旧分配器可能为邻近对象分配相同标签。 |
| `--no-mte` | `mte=false` | 使用显式关闭插桩的 sysroot。 |

安装包的 `share/qualification/memory-neighbors.json` 列出已通过审阅的组合。现场可按下文的 WSEA 流程补充本机验收组合。严格模式只接受与受信记录匹配的构建。源码属性可局部修改插桩。若对象可完全保留在寄存器中，编译器无需为其分配内存。编译器也可使用静态证明消除检查。因此应用生成了多少条标记指令无法判断发布组合是否合格。

## 验收工具链

按提交锁定完整 SDK，从可信来源取得编译器与 sysroot。每条发布记录绑定编译器、链接器、归档工具、已校验的 sysroot 文件清单、SDK 前端和该语言的构建输入。Rust 与 TinyGo 还绑定用于构建 IR 标记工具的 LLVM 开发文件，并校验宿主工具组件清单。记录包含 VM 摘要及栈、静态布局、堆、语言、解释执行、AOT 执行的独立测试报告摘要。构建宿主和宿主系统库属于信任边界。

维护者可以在源码仓库用 `tools/wasm/memtag/measure_release.py` 计算可信候选工具链的输入摘要。例如传入 `--language c --target wasm32 -O3 -g --toolchain PREFIX --sysroots FILE`。工具输出待审阅的输入清单。加入发布索引之前，使用回归套件的 `--candidate-mte` 测试选项生成独立证据。逐项审阅测试条件、二进制身份、结果与变更的源码。向索引登记某个组合需要独立审批。

Lua 解释器本身编为 Wasm，Lua 堆通过所选 libc 分配。TinyGo 使用独立垃圾收集器，需要单独验证分配与回收。现有 Rust 配置重新编译 `core` 和编译器内建库，支持 `no_std`。应用自建内存池及对象内部的子对象需要单独审阅。数值 Fortran 覆盖实际链接的运行库子集。通用描述符运行库、新分配器和新语言均需补充相应证据。

## 审阅应用

添加 `--build-receipt`，即可生成 `OUTPUT.wros-build.json`，记录产物摘要、构建配置、模式与范围。Rust 和 TinyGo 会列出前端观察到的局部关闭插桩声明。其他前端记录 `not-enumerated`，需要通过源码审阅补足。批准应用前应审阅自建内存池、局部关闭声明、unsafe 代码、输入对象和构建环境。可重定位对象中的构建说明用于检查输入一致性，不承担签名职责。

将批准的收据摘要保存于独立可信的已签名部署清单。部署前同时核对最终模块与实际 VM，通过以下命令验证。

```sh
python3 install/qualification.py --artifact body.wasm --receipt body.wasm.wros-build.json \
  --vm /opt/wros/uwvm2-ros --approved-receipt-sha256 "$approved_digest"
```

审批绑定这份模块、收据和 VM。应用更新可以继续使用原先已审阅的工具链，产物需要按新摘要审阅。应运行已经校验的不可变文件，并启用部署策略要求的运行时检查。关闭运行时检查后，VM 无法执行相邻对象标签约束。

## 在本机验收 C、C++ 与 Lua

现场可以使用已有的 wasm-cosign WSEA 信任策略，授权从源码构建的工具链。每次验收选择一种语言的无线程配置。验收默认的 WebAssembly 3.0 配置时，选择开启 EH 的 sysroot，给验收脚本传入 `--eh`。两种 VM 引擎都会实际执行 C++ 析构、重抛，以及异常路径上的内存归还。选择 C 或 C++ 时传入 `--language c` 或 `--language cpp`。验收无 EH 的 sysroot 时，省略该选项，编译应用时使用 `wrc --no-eh`。

1. 使用已经独立审核、工作树干净的 SDK 提交，按照源锁重建编译器与 sysroot。独立核对 VM、新构建的 sysroots.json 的 SHA-256，以及生产工具指纹。工具指纹计算方法为先对 `clang`、`wasm-ld`、`llc`、`llvm-objdump`、`llvm-ar`、`FileCheck` 六个程序分别计算小写 SHA-256，再将名称和摘要构成的对象按键排序、用无空白 JSON 编码，最后对编码计算 SHA-256。构建主机、引导工具和 SDK 源码属于信任边界。
2. 在关闭交换空间的 64 GiB cgroup 中运行验收，明确选择用户编译时需要的地址宽度、优化级别及调试符号。验收会实际运行栈生命周期、全局指针、嵌套聚合中的指针、堆分配器、libc 的测试，并分别运行解释器与 AOT。输出目录须为新目录。

```sh
python3 -I -B tools/wasm/memtag/qualify_local_c.py --sdk-commit "$SDK_COMMIT" \
  --approved-producer-sha256 "$PRODUCER_SHA256" --approved-vm-sha256 "$VM_SHA256" \
  --approved-sysroots-sha256 "$SYSROOTS_SHA256" \
  --toolchain "$TOOLCHAIN" --sysroots "$SYSROOT_JSON" --runtime "$VM" \
  --target wasm32 --eh -O2 --output .tmp/site-c
```

Lua 安装需要分别以 `--language cpp --eh -O3 -g` 和 `--language lua --eh -O3 -g` 验收同一地址宽度，并将两条记录合并签名。Lua 前端调用 C++ 前端编译锁定的完整解释器。语言测试既覆盖默认读取时钟的模式，也覆盖仅依赖 guest 种子的模式，并实际测试各模式的 ROS 权限开放及拒绝。

3. 管理员逐项审阅输出目录内的测试记录，使用专门的验收密钥和仅包含 `wros.sdk.memory.release` 这个模块 ID 的 WSEA 策略，通过 `wasm secure sign` 签署 `.tmp/site-c/unsigned.wasm`。若要同时批准多个配置，先用 `tools/wasm/memtag/bundle_local_releases.py --output unsigned.wasm --release-json A/release.json --release-json B/release.json` 合并已审阅的记录，再统一签名。每次变更授权集合都递增 WSEA 模块版本，验签程序会读取 WSEA 的策略与回滚状态。受保护配置还固定已批准签名文件的摘要；更新时先将文件保存在新路径，再原子替换配置中的路径与摘要。此 Wasm 只携带验收声明。由管理员保管签名模块、验签程序和策略。
4. 在**已安装且受信的 SDK** 内创建 `share/qualification/local-trust.json`。填写绝对路径与独立审核过的验签程序摘要。若现场将应用开发员与验收签署者分权，应用开发员对 SDK 和这些配置只能有读取权限。

```json
{
  "verifier": "/opt/wros/bin/cosign",
  "verifier_sha256": "<已审核的 wasm-cosign 程序 SHA-256>",
  "policy": "/etc/wros/qualification.policy",
  "statement": "/var/lib/wros/qualification/site-releases.wasm",
  "statement_sha256": "<批准的已签名验收集合 SHA-256>"
}
```

使用 `wrc --toolchain ... --sysroots ... app.c -o app.wasm` 构建符合已批准配置的任意 C 应用。SDK 对签名声明的私有副本验签，重新核对工具链身份。应用源代码可正常修改；签名被篡改、证书被吊销、未配置可信来源、工具链被替换，均无法取得严格资格。现场批准工具链和验收证据后，部署阶段仍须另外批准成品与权限。
