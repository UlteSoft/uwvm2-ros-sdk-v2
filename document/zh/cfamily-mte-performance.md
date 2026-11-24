# 复测 WasmMTE 线性访存内核

用二进制安装的 C SDK 一次编译四个 Wasm 模块，再将同一套产物交给各宿主 ABI 的 VM。公开记录中的 x86_64 和 i686 在 x86 硬件上运行，AArch64、ARM EABI 和 ARM 硬浮点在系统级 QEMU TCG 中运行。记录给出了 VM 与编译器版本、模块摘要、各配置的迭代次数及配对计时。[五宿主实测记录](../qualification/cfamily-mte-performance.json) · [内核与原生参考程序](../../src/qualification/cfamily/mte_performance_sources) · [English](../en/cfamily-mte-performance.md)

在当前 SDK 源码目录运行以下命令，传入 C 的安装前缀和对应宿主的 VM 可执行文件。每条命令都会在项目盘上新建工作目录。Linux 环境需要 Python 3.11 或更新版本、支持用户命名空间的 Bubblewrap、systemd 用户作用域和 cgroup v2。编译阶段还需要本机的 `/usr/bin/gcc`。验收使用的父级 `wrosvendor.slice` 应配置为 `MemoryMax=64G`、`MemorySwapMax=0`、`memory.oom.group=0`。启动器创建相同内存与交换空间上限、启用整组 OOM 终止的子作用域，核对两级限制、私有命名空间、只读临时目录和项目盘上的可写目录后再开始编译或计时。[隔离启动器](../../src/qualification/isolated.py)

```sh
runner=src/qualification/cfamily/mte_performance.py
python3 -I -B "$runner" build --cc-sdk /path/to/installed/c --work .tmp/mte-build
python3 -I -B "$runner" run --programs .tmp/mte-build/fixtures \
  --vm /path/to/uwvm2-ros --work .tmp/mte-run
```

在其他宿主上复测时复制整个 `fixtures` 目录。运行公开记录所用的 i686 VM，需要系统提供 32 位 ELF 加载器 `/lib/ld-linux.so.2`，并在系统库路径中提供 `libatomic.so.1` 等 32 位共享库。可使用原生 i386 系统，也可使用支持 32 位程序且具备这些库的 x86_64 系统。Debian 的 `libc6:i386` 和 `libatomic1:i386` 分别提供加载器和 libatomic。

追加 `--width 32 --engine int --iterations 8388608` 可选取公开记录中的 x86_64、wasm32、INT 配置。默认覆盖两个位宽和两个引擎，按五轮配对采样，绑定当前允许的第一个 CPU。可用 `--cpu N` 指定其他 CPU。自动标定以软件标签检查耗时 320 ms 为目标，选取 2 的幂次迭代次数。系统级 QEMU 来宾可用 `--emulated` 启用较短的标定探针。在支持 MTE 的 AArch64 Linux 上加 `--hardware`，即可同时测量同步硬件与软件标签检查。独立于计时的探针用 `strace` 核实 VM 成功设置了带标签的内存映射和同步标签控制，可用 `--strace /path/to/strace` 指定跟踪程序。每个配置的跟踪文件与 `summary.json` 保存在同一目录，摘要中的 `hardware_probe` 记录文件名和 SHA-256。

来宾时钟覆盖数组初始化及访存循环。每轮循环在 4 KiB 数组中对一个 32 位元素各读写一次。每次执行均核对原生参考程序独立算出的校验和，以及预期的零或非零标签。`summary.json` 中的比值取同一轮的完整内核耗时相除，两个分母分别为普通模块及关闭运行时检查的同一份带标签模块。三个分位点依次为含端点的第一四分位数、中位数和第三四分位数。每轮还保留四分之一长度和零次循环对照、来宾耗时与宿主进程耗时。摘要标明传入的 VM 和所测模块是否与公开记录的哈希相符。[复测程序](../../src/qualification/cfamily/mte_performance.py)
