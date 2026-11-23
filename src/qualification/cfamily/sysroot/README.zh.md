# SDK sysroot 资格测试用例

[English](README.md)

测试程序为每个 SDK 用例记录源码 SHA-256、用例类别及关联的上游路径。原始上游程序各有独立条目和运行结果。[用例清单与上游版本](../cases.json)

* `search_lsearch_full_width.c` 移植自 libc-test 的 `18e28496adee3d84fefdda6efcb9c5b8996a2398` 版本。它保留上游的十个初始键、查询命中和未命中、插入重复键以及末尾追加新键的检查。包括空字符串在内，每个键都占满 80 字节的记录。用例先用非零字节填充目标表，再逐项核对每次追加的全部 80 字节。比较函数使用 `lfind` 和 `lsearch` 要求的签名。适用于全部十六档。[上游测试](../upstream/libc-test/src/functional/search_lsearch.c) · [许可证](../upstream/libc-test/COPYRIGHT)
* `sem_getvalue_unnamed.c` 补充 wasi-libc 的 `2e6fb9d8ee0cdf9e431fbcabe8af3115de000a13` 版本所收录的 Open POSIX 用例。上游 `sem_getvalue` 用例创建命名信号量并调用 `sem_unlink`。SDK 用例将进程内的匿名信号量初始化为 1，检查取走一个令牌前后的计数，再等待执行 `sem_post` 的子线程结束并核对计数。每项操作成功才会通过。适用于开启线程的八档。[上游 sem_getvalue 测试](../../../compilers/cc/wasi-libc/test/open-posix-test-suite/conformance/interfaces/sem_getvalue/1-1.c) · [上游 sem_init 测试](../../../compilers/cc/wasi-libc/test/open-posix-test-suite/conformance/interfaces/sem_init/1-1.c)
* `pthread_rwlock_init_join.c` 补充同一 wasi-libc 版本所收录的 Open POSIX 读锁用例。上游程序轮询与子线程共享的状态标志。SDK 用例初始化锁属性与读写锁，用 `pthread_join` 等待获取并释放读锁的子线程结束，再确认主线程能够获取写锁。适用于开启线程的八档。[上游 pthread_rwlock_init 测试](../../../compilers/cc/wasi-libc/test/open-posix-test-suite/conformance/interfaces/pthread_rwlock_init/1-1.c)
