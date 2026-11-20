# base-x、abbrev 与 mitt 上游库测试

测试用固定 SDK 提交 `63b57f8b3debfe14cabd5af05de2ffbee22a0314` 安装
QuickJS 和 mruby 路径。需要匹配 VM 的签名 C 站点，配置为 wasm32
Core 3.0、EH、单线程、严格 MTE 和 `-O3 -g`。编译及解释器记录会核对
实际执行的 Wasm 摘要。

- **base-x 5.0.1** 保留 ESM 实现、测试体和原始向量。适配层替换模块导入并
  提供用到的断言方法，共检查 254 组测试和 256 条断言，覆盖 121 个有效
  向量和 9 个无效向量。同一脚本在 Node.js 和 Wasm QuickJS 中执行。
  [上游源码](https://github.com/cryptocoinjs/base-x/tree/b7b0cec52bf60d993957902e8e7c96906ac39c7c)
- **abbrev 0.1.2** 保留原版两个测试方法和 6 个相等断言。移植版用字符串切片
  判断字面前缀，并拒绝其他有值的过滤器类型。原实现和移植实现均先用本机
  Ruby 跑相同断言，随后在 Wasm mruby 中运行移植实现。
  [上游源码](https://github.com/ruby/abbrev/tree/b362e8e3b92c48a9e8f34fc0f782d3396858db1f)

按英文版命令获取固定归档，在现有 64 GiB cgroup 门控内运行，并指定新的
`.tmp` 输出目录。QuickJS 只导入一个只读时钟，mruby 导入表为空。
两个产物分别在解释器和 AOT 中启用同步 MTE。结果记录输入源码、编译器、
VM、Wasm 和每个执行阶段的状态。

## TypeScript

`mitt` 3.0.1 测试保留原始实现、全部 19 个运行时测试体和包含 10 条
`@ts-expect-error` 的类型测试。适配只把测试导入映射到本地模块，并实现
测试使用的断言和调用记录方法。运行时必须完成 43 条断言。
[上游源码](https://github.com/developit/mitt/tree/b240473b5707857ba2c6a8e6d707c28d1e39da49)

按英文版命令下载固定归档，通过签名 C 站点安装同一 SDK。使用 SDK 中的
TypeScript 5.9.3 执行严格类型检查。独立 Node.js 对照所用的 JavaScript
摘要必须与 `wrts` 打包进 QuickJS 的 JavaScript 一致。两个 Wasm 引擎均
启用同步 MTE，模块只导入一个只读时钟。

## AssemblyScript

标量数学库测试复用 AssemblyScript 0.28.20 的 `imul` 和 `clz32` 共 28
条原始断言。测试核对编译器携带的 `math.ts` 与上游文件一致，并以三级优化和
调试名称构建。编译器选用上游完整的浮点转整数路径。两个 VM 引擎运行无导入、
无线性内存的 wasm32 产物。Node.js 再用 ECMAScript Math 比对 4,100 个固定和
随机生成的标量结果。
[上游断言](https://github.com/AssemblyScript/assemblyscript/blob/b6bda05c29c9eb7d07d7f6cb2703508483b30493/tests/compiler/std/math.ts)

按英文版命令获取归档和选择性安装 SDK。将完整提交 ID 传给 `--commit`，并在
同一 64 GiB 门控内运行。

[English](README.md)
