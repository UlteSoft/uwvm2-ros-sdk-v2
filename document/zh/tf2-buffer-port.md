# 将 Jazzy tf2 BufferCore 移植到 Wasm

按固定 SDK 提交安装 C++ 迁移组件，准备本地 ROS Jazzy 的 geometry2 源码和
同一发行版生成的 C++ 消息头。工具先验证本次适配涉及的三个上游文件的摘要，
再创建输出目录。

```sh
python3 -I install/bootstrap.py install --commit "$SDK_COMMIT" --platform unitree \
  --language cpp --prefix "$SDK_PREFIX" -- --component migration
migration="$SDK_PREFIX/$SDK_COMMIT/unitree/cpp/migration"
python3 -I "$migration/tools/migration/tf2_buffer_port.py" \
  --tf2-source "$GEOMETRY2/tf2" --ros-prefix "$JAZZY_PREFIX" \
  --execution single-executor --output "$BUILD/tf2-port"
```

所有翻译单元都应优先包含 `$BUILD/tf2-port/include`。从
`$BUILD/tf2-port/port.json` 读取 BufferCore 翻译单元的位置，结合上游的
cache、static_cache、time 及 rcutils 依赖进行编译。使用 C++ 开发组件的
`wrcc`，选择经签名的 wasm32、Core 3.0、MTE 和 EH 配置。单执行器要求
独立的非共享线性内存，同一模块的调用必须串行，部署时应确保其他模块无法
读写它的私有内存。使用多线程时选择 `--execution threaded`，并向具有对应
签名配置的 `wrcc` 传入 `-pthread`。

两种模式都保留 Jazzy 原有的 UTF-16 YAML 输出，包括对 NUL 字符的处理和非
ASCII 码元的转义。单执行器保留上游的每一处持锁范围，重复获取同一把锁会抛出
C++ 异常，异常展开会释放锁。编译器启用原子指令或 pthread 时，该适配头会报错。
多线程模式保留原版 BufferCore 翻译单元及其所有互斥锁。

测试覆盖动静坐标边组合、插值、断开坐标树、前后外推、缓存淘汰、清空及 UTF-16
序列化。单执行器 Wasm 已在解释器和 AOT 上运行，链接的四个 Preview1 接口全部
按模块设为拒绝。原生多线程测试使用两个读线程和一个写线程。已测试站点只提供
无线程配置的签名资格记录。Wasm 并发、DDS 接收及实时调度仍需分别验证。
