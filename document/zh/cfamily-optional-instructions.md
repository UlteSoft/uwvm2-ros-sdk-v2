# C 系列 SDK 的 Wasm 可选指令

安装后的 `wrc`、`wrcc`、`wroc` 和 `wrocxx` 接受两组独立开关。Core 3.0 默认同时启用两组。同一组多次指定时，最后一个开关生效。

- `-msimd128` 启用 SIMD128。`-mno-simd128` 同时关闭当前翻译单元的普通 SIMD 和 relaxed SIMD，允许编译器用标量指令实现本可向量化的运算。
- `-mbulk-memory-opt` 允许 LLVM 生成 `memory.copy` 和 `memory.fill`。指定 `-mno-bulk-memory-opt` 后，LLVM 将内存 intrinsic（包括聚合对象复制）降为标量读写或 libc 调用。十六种来宾配置的 WASIp1 运行库、编译器内建库和 GNUstep 归档均按标量基线构建。
- 随 SDK 发行的 libc 提供 `memcpy`、`memmove` 和 `memset` 的弱定义。写入前先检查完整线性内存范围。启用 MTE 时还用带原标签的指针逐粒度检查。 `memmove` 根据去标签后的地址选择搬移方向。应用的强定义优先生效。
- 线程 ABI 保留 `memory.init`、`data.drop` 与 TLS 所需的完整 bulk-memory 特性。关闭复制与填充指令后，LLD 在初始化线程原有的临界区内调用隐藏的标量 libc 函数清零被动 BSS，待内存映像就绪后再唤醒等待线程。
- 四个前端的 `--build-receipt` 都会将应用设置及实际传入 Clang 的覆盖参数写入 `optional_isa`。单独编译的对象会记录显式关闭的指令族。常规链接可以继续使用旧对象，关闭指令族的链接要求应用对象也按该限制编译。严格内存认证对应其原有代码生成设置。

例如，使用标量向量运算和原生 bulk 复制编译 Wasm64 C++ 应用。

```sh
/sdk/cpp/bin/wrcc --target wasm64 --core 3.0 --no-threads --no-mte --no-eh \
  -O3 -mno-simd128 -mbulk-memory-opt --build-receipt example.cpp -o example.wasm
```

## 验收最终模块

完整矩阵包含四种语言、指针位宽/MTE/线程/EH 的 16 档组合，以及 SIMD 和 bulk 的四组开关，共 256 个模块。u2ros INT 和 LLVM AOT 分别运行每个成功链接和解码的文件。遇到指令残留时仍保留两引擎的实际运行结果。VM 二进制与构建收据必须匹配指定的提交及源码树。

```sh
cargo build --release --locked --offline --manifest-path src/qualification/cfamily/decoder/Cargo.toml
python3 src/qualification/cfamily/optional_isa_suite.py \
  --cc-sdk /sdk/c --cxx-sdk /sdk/cpp --objc-sdk /sdk/objc --objcpp-sdk /sdk/objcpp \
  --vm /opt/tools/bin/uwvm2-ros \
  --decoder src/qualification/cfamily/decoder/target/release/decode-memtag \
  --work /work/isa-matrix --seed 0x12345678 --jobs 4
```

增加 `--language objc --profile wasm32-wasip1-threads-noeh-mte --simd off --bulk on` 只跑一格，此时只需指定 Objective-C 的 SDK 根目录。每次运行使用独立空目录。测试其他版本的 VM 时，用 `--vm-target` 指向含已选定 `vm_commit` 和 `vm_tree` 的 JSON，用 `--vm-receipt` 指向对应可执行文件的构建收据。

程序在堆上分配数据，计算 64 个无符号整数通道、填充一段内存，随后分别向高地址、低地址进行重叠搬移，最后进行零长度搬移。Objective-C 执行类方法消息，Objective-C++ 同时实例化 C++ 模板。四档指令设置使用相同的运算源码与输入。固定用例包括零、一、最高位和全一位模式。`--random-cases` 设置额外随机用例数，默认四个。省略 `--seed` 将自动选种，并在 `inputs.json` 记录。

独立的 Python 参考实现把种子、全部通道、无符号累加结果及每次操作后的完整 64 字节缓冲区写入 `expected.bin`。两引擎均须逐字节匹配。出现差异时记录首个不匹配字节的位置。

解码器从函数体及常量表达式逐条读取真实指令。向量实现须在指定内核中出现并行算术；标量路径须出现普通读写；两个内存内核须符合所选复制和填充设置。解码器分别统计 SIMD、relaxed SIMD、`memory.copy`、`memory.fill`、其他 bulk、线程和 MTE 指令。线程启动可能需要 `memory.init`、`data.drop` 和原子操作。最终模块在任意函数出现已关闭的 SIMD 或复制/填充指令都判该格失败，`result.json` 记录函数名与数量。检查覆盖分配器、语言运行时和链接器生成的启动函数。线程的内存提供模块只包含内存定义和导出，没有代码段。

每格保留模块、构建收据、解码清单、完整命令参数、INT/AOT 的原始标准输出与错误输出。`summary.json` 分别给出各格判定和引擎执行统计。全部所选格及两种引擎通过时进程返回零。

## 复现 x86_64 公开安装

在验收 namespace 内的空项目目录执行以下命令。每个安装回执的 directory 字段给出该语言实际安装的位置。此次验收使用空 HOME，父、子 cgroup 各设 64 GiB 和零 swap，临时文件写入项目盘。安装结束后，测试在仅有回环接口的网络 namespace 中运行。

```sh
SDK_COMMIT=38023bff47eb545815bdc7e272fc24c44901686d
mkdir -p .tmp/sdk-install
export TMPDIR="$PWD/.tmp/sdk-install"
curl -fL --retry 3 "https://raw.githubusercontent.com/UlteSoft/uwvm2-ros-sdk-v2/$SDK_COMMIT/install.py" -o install.py
for language in c cpp objc objcpp
do
  python3 -I -B install.py install --commit "$SDK_COMMIT" --language "$language" --platform generic --mode binary --prefix "$PWD/sdk" > "$language.install.json" || exit 1
done
```

本轮验收目标是使用 WASIp1 的 Core Wasm 模块。语言运行时必需的特性作为前置条件。例如，依赖 WasmGC 的 Java 或 C# 后端只在开启 WasmGC 时验收。Component Model、WASIp2、WASIp3 和 ROS 集成属于本轮范围之外。
