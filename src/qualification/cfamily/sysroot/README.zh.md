# SDK sysroot 资格测试用例

[English](README.md)

测试程序为每个 SDK 用例记录源码 SHA-256、用例类别及关联的上游路径。原始上游程序各有独立条目和运行结果。[用例清单与上游版本](../cases.json)

可重复传入 `--case` 指定清单中的完整源码路径，用 `--profile` 选择一个或多个配置。所选用例在两个引擎上全部通过时，程序退出 0。退出 77 表示未完成的用例均命中已知的上游限制。`floatuntisf` 测试要求 80 位 long double，在这些目标上输出精确的 `skipped\n`。命名信号量测试需要 `sem_unlink`，链接器须仅报告这一个未定义符号。出现其他失败或未决结果时退出 1。汇总分别统计原始构建结果、引擎结果和每个源码与配置组合的验收结果。

上游读锁测试最多调用四次 `sleep(1)`。wasi-libc 为每次调用提交一个相对的 `CLOCK_REALTIME` 定时器订阅。该用例获得 `realtime-timer` 权限，允许调用导入的 `poll_oneoff` 接口，每次限一个订阅，共限四次调用。退出 0 时还须核对上游成功输出，并确认轮询过程中没有权限或配额拒绝。该程序未同步对共享标志的轮询，并限定了等待次数。在 QEMU 上同样保留这一条件。未决结果计为验收失败。[wasi-libc sleep](../../../compilers/cc/wasi-libc/libc-bottom-half/cloudlibc/src/libc/unistd/sleep.c) · [定时器订阅](../../../compilers/cc/wasi-libc/libc-bottom-half/cloudlibc/src/libc/time/clock_nanosleep.c)

对于开启线程及 MemTag 的四种 `find.pass.cpp` 配置，x86_64 和 i686 的 AOT 重定位条目上限按宿主和配置分别指定。将各目标文件的实测条目数增加 1%，再向上取整到 1,024 的倍数。SDK `03a3904` 的四个 x86_64 目标文件相较先前测量增加了 26 至 112 个条目。若上限高于默认的 65,536 个条目，虚拟机要求每个获准条目在每子线程 512 MiB 的代码预算中至少占 512 字节。其他宿主在取得实测值前使用虚拟机的默认上限。[用例预算](../cases.json)

* `search_lsearch_full_width.c` 移植自 libc-test 的 `18e28496adee3d84fefdda6efcb9c5b8996a2398` 版本。它保留上游的十个初始键、查询命中和未命中、插入重复键以及末尾追加新键的检查。包括空字符串在内，每个键都占满 80 字节的记录。用例先用非零字节填充目标表，再逐项核对每次追加的全部 80 字节。比较函数使用 `lfind` 和 `lsearch` 要求的签名。适用于全部十六档。[上游测试](../upstream/libc-test/src/functional/search_lsearch.c) · [许可证](../upstream/libc-test/COPYRIGHT)
* `sem_getvalue_unnamed.c` 补充 wasi-libc 的 `2e6fb9d8ee0cdf9e431fbcabe8af3115de000a13` 版本所收录的 Open POSIX 用例。上游 `sem_getvalue` 用例创建命名信号量并调用 `sem_unlink`。SDK 用例将进程内的匿名信号量初始化为 1，检查取走一个令牌前后的计数，再等待执行 `sem_post` 的子线程结束并核对计数。每项操作成功才会通过。适用于开启线程的八档。[上游 sem_getvalue 测试](../../../compilers/cc/wasi-libc/test/open-posix-test-suite/conformance/interfaces/sem_getvalue/1-1.c) · [上游 sem_init 测试](../../../compilers/cc/wasi-libc/test/open-posix-test-suite/conformance/interfaces/sem_init/1-1.c)
* `pthread_rwlock_init_join.c` 补充同一 wasi-libc 版本所收录的 Open POSIX 读锁用例。上游程序轮询与子线程共享的状态标志。SDK 用例初始化锁属性与读写锁，用 `pthread_join` 等待获取并释放读锁的子线程结束，再确认主线程能够获取写锁。适用于开启线程的八档。[上游 pthread_rwlock_init 测试](../../../compilers/cc/wasi-libc/test/open-posix-test-suite/conformance/interfaces/pthread_rwlock_init/1-1.c)
