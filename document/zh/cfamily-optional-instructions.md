# C 系列 SDK 的 Wasm 可选指令

安装后的 `wrc`、`wrcc`、`wroc` 和 `wrocxx` 接受两组独立开关。Core 3.0 默认同时启用两组。同一组多次指定时，最后一个开关生效。

- `-msimd128` 启用 SIMD128。`-mno-simd128` 同时关闭当前翻译单元的普通 SIMD 和 relaxed SIMD，允许编译器用标量指令实现本可向量化的运算。
- `-mbulk-memory-opt` 允许 LLVM 生成 `memory.copy` 和 `memory.fill`。`-mno-bulk-memory-opt` 为普通 `memcpy`、`memmove` 和 `memset` 选择标量实现。最终链接时驱动加入用字节读写实现的 guest 弱定义，应用自己的强定义优先。
- 非线程目标关闭复制优化时也关闭 LLVM 隐含此优化的完整 bulk-memory 目标特性。WASIp1 线程目标依赖完整特性初始化 TLS 和共享内存。驱动为线程保留该特性，并关闭 Clang 对上述三个内存函数的内建识别。显式 intrinsic、编译器产生的聚合复制、已编译的库及链接器生成的启动代码均可能带入可选指令。指针宽度、MTE、EH 由各自配置选择。
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

解码器从函数体及常量表达式逐条读取真实指令。向量实现须在指定内核中出现并行算术；标量路径须出现普通读写；两个内存内核须符合所选复制和填充设置。解码器分别统计 SIMD、relaxed SIMD、`memory.copy`、`memory.fill`、其他 bulk、线程和 MTE 指令。线程启动可能需要 `memory.init`、`data.drop` 和原子操作。最终模块在任意函数出现已关闭的 SIMD 或复制/填充指令都判该格失败，`result.json` 记录函数名与数量。堆管理可能带入预编译 libc 的指令，LLD 也可能为共享内存的 BSS 初始化生成 `memory.fill`。线程的内存提供模块只包含内存定义和导出，没有代码段。

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
