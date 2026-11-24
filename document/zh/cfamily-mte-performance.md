# 复测 WasmMTE 线性访存内核

用二进制安装的 C SDK 一次编译四个 Wasm 模块，再将同一套产物交给各宿主 ABI 的 VM。公开记录中的 x86_64 和 i686 在 x86 硬件上运行，AArch64、ARM EABI 和 ARM 硬浮点在系统级 QEMU TCG 中运行。记录给出了 VM 与编译器版本、模块摘要、各配置的迭代次数及配对计时。[五宿主实测记录](../qualification/cfamily-mte-performance.json) · [内核与原生参考程序](../../src/qualification/cfamily/mte_performance_sources) · [English](../en/cfamily-mte-performance.md)

在当前 SDK 源码目录运行以下命令，传入 C 的安装前缀和对应宿主的 VM 可执行文件。每条命令都会在项目盘上新建工作目录。Linux 环境需要 `/usr/bin/python3`（Python 3.11 或更新版本）、支持用户命名空间的 Bubblewrap、systemd 用户作用域和 cgroup v2。编译阶段还需要本机的 `/usr/bin/gcc`。验收使用的父级 `wrosvendor.slice` 应配置为 `MemoryMax=64G`、`MemorySwapMax=0`、`memory.oom.group=0`。启动器创建相同内存与交换空间上限、启用整组 OOM 终止的子作用域，核对两级限制、私有命名空间、只读临时目录和项目盘上的可写目录后再开始编译或计时。[隔离启动器](../../src/qualification/isolated.py)

```sh
runner=src/qualification/cfamily/mte_performance.py
/usr/bin/python3 -I -B "$runner" build --cc-sdk /path/to/installed/c --work .tmp/mte-build
/usr/bin/python3 -I -B "$runner" run --programs .tmp/mte-build/fixtures \
  --vm /path/to/uwvm2-ros --work .tmp/mte-run
```

在其他宿主上复测时复制整个 `fixtures` 目录。运行公开记录所用的 i686 VM，需要系统提供 32 位 ELF 加载器 `/lib/ld-linux.so.2`，并在系统库路径中提供 `libatomic.so.1` 等 32 位共享库。可使用原生 i386 系统，也可使用支持 32 位程序且具备这些库的 x86_64 系统。Debian 的 `libc6:i386` 和 `libatomic1:i386` 分别提供加载器和 libatomic。

在支持 i686 原生执行的 x86_64 Linux 宿主上，一条命令即可测量两种 VM ABI。程序先核对 ELF 位宽和机器类型，再将 x86_64、i686 依次绑定到同一逻辑 CPU，在各自的离线命名空间中运行。两次测量共用前面编译的四个模块，每个 VM 都用 INT 和 AOT 运行两种来宾位宽。

```sh
/usr/bin/python3 -I -B "$runner" x86-matrix --programs .tmp/mte-build/fixtures \
  --vm-x86_64 /path/to/x86_64/uwvm2-ros --vm-i686 /path/to/i686/uwvm2-ros \
  --work .tmp/mte-x86
```

若宿主缺少 i386 版 `libatomic.so.1`，可追加 `--i686-libatomic /path/to/extracted/libatomic.so.1`，使用本地从 Debian `libatomic1:i386` 软件包解出的库。程序将该文件只读挂载到 i686 命名空间，并为 i686 VM 进程设置库搜索路径。`--cpu`、`--repeats` 和 `--iterations` 同时作用于两种 ABI。八种配置全部成功后，`.tmp/mte-x86/matrix.json` 会记录 CPU、内核、VM 与各输入文件的哈希，以及每种配置的两组配对耗时比。原始样本分别保存在 `x86_64/summary.json` 与 `i686/summary.json`，总表给出两个文件的路径和 SHA-256。

追加 `--width 32 --engine int --iterations 8388608` 可选取公开记录中的 x86_64、wasm32、INT 配置。默认覆盖两个位宽和两个引擎，按五轮配对采样，绑定当前允许的第一个 CPU。可用 `--cpu N` 指定其他 CPU。自动标定以软件标签检查耗时 320 ms 为目标，选取 2 的幂次迭代次数。系统级 QEMU 来宾可用 `--emulated` 启用较短的标定探针。在支持 MTE 的 AArch64 Linux 上加 `--hardware`，即可同时测量同步硬件与软件标签检查。独立于计时的探针用 `strace` 核实 VM 成功设置了带标签的内存映射和同步标签控制，可用 `--strace /path/to/strace` 指定跟踪程序。每个配置的跟踪文件与 `summary.json` 保存在同一目录，摘要中的 `hardware_probe` 记录文件名和 SHA-256。

来宾时钟覆盖数组初始化及访存循环。每轮循环在 4 KiB 数组中对一个 32 位元素各读写一次。每次执行均核对原生参考程序独立算出的校验和，以及预期的零或非零标签。`summary.json` 中的比值取同一轮的完整内核耗时相除，两个分母分别为普通模块及关闭运行时检查的同一份带标签模块。三个分位点依次为含端点的第一四分位数、中位数和第三四分位数。每轮还保留四分之一长度和零次循环对照、来宾耗时与宿主进程耗时。摘要标明传入的 VM 和所测模块是否与公开记录的哈希相符。[复测程序](../../src/qualification/cfamily/mte_performance.py)

## x86 原生计时与 VTune 热点

对于这个 4 KiB 内核，在两种来宾位宽下，开启软件标签检查后 INT 的耗时增幅均大于 AOT。以同一份带标签模块关闭检查时的耗时为基准，公开的配对计时显示，x86_64 上 wasm32、wasm64 的 INT 耗时比中位数依次为 1.84、1.78，AOT 为 1.42、1.52。i686 上对应的 INT 比值为 3.56、3.14，AOT 为 1.91、1.96。[来宾配对计时](../qualification/cfamily-mte-performance.json)

VTune 在同一台 Core i9-14900HX 上对发布版 VM `d46186fca2dc` 的全部 16 种组合进行了采样。每次运行的校验和都与原生参考程序一致，开启软件检查时分配标签非零，关闭时为零。将原始指令地址按 VM 进程和逻辑 CPU 6 过滤后，四组开启检查的 INT 运行中，各有 49%–52% 的分布式周期样本落在标签处理函数内。x86_64 上集中在带缓存的标量访存函数，i686 上则分布在访问策略、来宾访存及指令分派函数。关闭检查的四组中，样本最多的都是解释器的加载或存储函数。另一次使用带调试符号的 x86_64 VM（SHA-256 前缀 `7fa4df1e1920`）采样时，wasm32 INT 有 44 个样本命中 `shadow.h` 第 207 行读取影子标签字节的指令。该可执行文件中，`movzx r14d, byte ptr [r12+r13]` 的地址是 `0x1e0c0a0`。[对应版本的标签读取源码](https://github.com/UlteSoft/uwvm2-ros/blob/d46186fca2dc60eebc71fdf4bf1c78ab32b9cb91/src/uwvm2/extension/memtag/shadow.h#L207) · [VTune 实测记录](../qualification/cfamily-mte-vtune.json)

AOT 的 MCJIT 符号地址范围表明，开启检查时 88%–91% 的样本落在编译后的来宾内核，关闭时为 92%–95%。这两组占比都包含循环运算和数据读写。wasm32 INT 开启检查时，VTune 将 x86_64 性能核 22.9% 的流水线槽位归为前端受限，i686 上为 1.8%。四组 wasm32 INT 访存报告中，DRAM 停顿占性能核时钟周期的 0.0%–0.5%。CPU 6 与 SMT 兄弟线程 CPU 7 共享物理核，uncore 带宽统计包含系统中的其他流量。无驱动采样无法定位到具体缓存行，参考周期事件 `CPU_CLK_UNHALTED.REF_TSC` 在多次运行中仅覆盖部分时段。物理 Arm 芯片的 MTE 性能需要在相应硬件上测量。

仅修改标签扫描的候选提交 `5cafd78f1897` 未合入。独立 A/B 计时覆盖八种开启软件检查的配置，每种有 16 对样本。各配置耗时变化中位数的 97.87% 符号检验区间均包含零。

## VM f3cfe4477ad0 的原生 x86 复测

x86_64 和 i686 均实测了 INT、AOT 与两种 Wasm ABI。两台宿主 ABI 使用同一套由已安装 wrc 编出的客体。在 x86_64 AOT 上，4 KiB 循环开启软件检查后，wasm32 和 wasm64 的来宾耗时分别为关闭检查时的 1.29 倍和 1.50 倍。cJSON 1.7.18 对应为 27.47 倍和 17.17 倍，在 i686 AOT 上为 19.07 倍和 17.65 倍。该负载轮流解析四份短文档、查询字段、计算校验和，并释放解析结果。记录包含配对四分位数、零文档冷启动对照、编译命令和客体摘要。VTune 将 x86_64 wasm32 AOT 开启检查时的 67.7% 稳态周期样本定位到分配元数据维护及分配生命周期调用。[实测记录](../qualification/cfamily-mte-native-x86.json) · [负载源码](../../src/qualification/cfamily/mte_performance_sources/cjson/library.c)
