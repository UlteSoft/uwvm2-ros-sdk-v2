# Nim 编译器源码

[English](README.md)

专用前端在用户工程上运行 Nim 的 C 后端。它按 WebAssembly 目标选择整数和指针位宽，并给出生成的 C 翻译单元。SDK 的 Wasm 编译器需要编译这些文件并链接 guest 运行时。目录含编译器、标准库、发行依赖，以及官方 Linux x86-64 引导脚本使用的 191 个 C 翻译单元。[版本与修改](upstream.json) · [官方文件摘要](release-files.sha256) · [目标选择](upstream/compiler/wrnim_lower.nim)

使用宿主 C 编译器构建前端时，在 SDK 源码根目录执行。引导工具和 Nim 缓存写入项目盘工作目录。

```sh
mkdir -p .tmp/nim-host
cp -a src/compilers/nim/upstream/. .tmp/nim-host/
cd .tmp/nim-host
mkdir -p bin work
export TMPDIR="$PWD/work"
export TEMP="$TMPDIR" TMP="$TMPDIR"
sh build.sh
bin/nim c --skipUserCfg --skipParentCfg --threads:off -d:release -d:leanCompiler -d:nimcore \
  --lib:"$PWD/lib" --nimcache:"$PWD/work/nimcache" --out:"$PWD/bin/wrnim-lower" compiler/wrnim_lower.nim
```

C 引导源码按官方脚本的 Linux amd64 分支选取。清单区分能逐项匹配 Git 的文件，以及按官方发行包验证的生成文件和打包依赖。guest 入口调用 NimMain，panic 处理函数在 guest 内执行 trap。公开编译器、ABI 绑定、WasmMTE 策略和外部工程运行仍待独立验收。[入口](runtime/entry.c) · [panic 处理](runtime/panicoverride.nim)
