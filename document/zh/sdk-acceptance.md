# SDK 语言与平台验收

[English](../en/sdk-acceptance.md)

每种语言先执行独立验收，成功后再运行该语言的已安装平台工程。指定产物可单独验证。选定修订包含 WAT 配置夹具时，WAT 语言验收会额外执行一次 Core 3.0、共享内存、WasmMTE 和真实子线程的联合测试。缺少联合夹具的语言记录为 `joint_profile.outcome = not_exercised`。`all_joint_profiles_passed` 要求每个所选语言都有实际联合验证结果。

从源码检出目录运行，确保本地已有指定的 Git 提交，并通过指定的 64 GiB、零 swap 测试 cgroup。编译与 VM 测试串行执行。结果记录所选 SDK 提交、cgroup、测试脚本摘要以及 Xmake 和 VM 的身份。

~~~sh
$GATE python3 -B tests/sdk_acceptance.py \
  --commit "$SDK_COMMIT" --language wat --language as \
  --platform unitree --platform universal_robots \
  --platform-case migration --vm "$VM" --xmake "$XMAKE" \
  --output .tmp/sdk-acceptance
~~~

重复语言与平台参数可以选定子集。省略其中一个参数时，对应维度选择所有已登记值。每种语言先在选中的第一个平台构建和执行通用示例，也可用 --contract-platform 指定。第二层默认在每个所选组合运行扩展和迁移项目，重复 --platform-case 可以指定类别。用 --plan 查看选项和已知前置条件，无需启动构建或执行任务。

可选的 --inputs 文件采用 wros-sdk-acceptance-inputs-v1 格式。路径可为相对于该文件的路径或绝对路径。平台专用配置覆盖该语言的默认配置。有签名的站点使用 SDK 安装器本来就会校验的配置。C#、F# 和 Visual Basic 使用各语言准备命令生成的 managed_host 与对应 Wasm LLVM 的 managed_toolchain。AssemblyScript、标准 Go 和 WAT 随包提供工具，可以直接验收。

支持显式工具路径的编译器可用 toolchain 和 sysroots 指定 Wasm LLVM 目录与匹配的 sysroot 清单。编译器仍会执行自身的配置和准入校验。

~~~json
{
  "schema": "wros-sdk-acceptance-inputs-v1",
  "profiles": {
    "c": {"site": "wasm32-c-site.json"},
    "unitree/c": {"target": "wasm64", "site": "wasm64-c-site.json"}
  },
  "artifacts": {}
}
~~~

验收外部提供的 core Wasm 时，在 artifacts 中按平台/语言/类别登记，例如 unitree/wat/migration。填写 file 与小写 SHA-256 字段 sha256。可选的 profile 字段包括 address_bits、wasm_version、threads、mte 和 exceptions，默认选择 wasm32、Core 3.0、单线程、MTE、无 EH。queries 是可选的本地只读授权清单，默认留空。测试先核对摘要和 SDK 导入策略，再用两种 VM 引擎执行指定字节。该用例提供指定产物的执行证据。编译器和厂商驱动仍需各自的源码测试。

结果保存在带格式版本的 results.json 中，包含三类状态。

- executable 记录两种引擎的执行结果及 Wasm 摘要。
- blocked 记录缺失的前置条件、测试失败或产物被拒。
- not_exercised 记录缺少示例或仅生成计划。

普通运行只在所选行均为 executable 时返回零。输出目录保留测试日志与子验收记录，每个用例结束后会清理临时安装文件和构建中间产物。扩展测试验证 SDK 的本机认证权限边界，官方仿真和实体厂商驱动由单独的测试覆盖。

## 平台物理仿真

`tests/mujoco_matrix.py` 按平台安装指定语言的签名 SDK，并校验模型清单摘要。
每行用 MuJoCo 原生运行结果比对来宾驱动的 128 步轨迹，还在解释器和 AOT 中
检查超范围命令是否推进零步，以及驱动崩溃时来宾是否能识别状态。

矩阵每行指定 `platform`、`language`、`address_bits`、`model`、
`model_sha256`、`assets` 和 `site`。路径相对于矩阵文件。
可选的 `compiled_model_mib` 默认 64 MiB，最大 512 MiB。
输出保留编译模型摘要、场景日志和每行回执。GPU 专用运行时与实体设备联锁需单独验收。

```sh
"$GATE" /usr/bin/python3 -B tests/mujoco_matrix.py --commit "$SDK_COMMIT" \
  --plan "$PLAN" --runtime "$WROS_VM" --vm-source "$VM_SOURCE" \
  --mujoco "$MUJOCO" --openssl-root "$OPENSSL_ROOT" --output "$OUTPUT"
```

## 上游 C 库测试

上游复验使用 GitHub 固定提交的库源码和原测试实现。结果记录原生对照、
严格 `wrc` 构建凭据、访客导入、反汇编确认的 WasmMTE 指令，以及两种 VM
引擎的结果。把上游源码放在本地测试工作区的独立目录，并通过共用的
64 GiB 测试入口执行。

```sh
mkdir -p "$SOURCES"
git clone --depth 1 --branch 6.7.3 https://github.com/ros2/rcutils.git "$SOURCES/rcutils"
git clone --depth 1 --branch v1.7.19 https://github.com/DaveGamble/cJSON.git "$SOURCES/cjson"
git clone --depth 1 --branch v1.3.2 https://github.com/madler/zlib.git "$SOURCES/zlib"
"$GATE" /usr/bin/python3 -B tests/upstream_c_libraries.py \
  --sdk "$PWD" --sources "$SOURCES" --commit "$SDK_COMMIT" \
  --site "$SIGNED_C_SITE" --vm "$WROS_VM" --output "$OUTPUT"
```

C 本地签名配置须授权 wasm32 Core 3.0、标准 EH、`-O3 -g` 和 MTE。
可用 `--case` 重跑单项。适配层保留 rcutils 字节数组的上游断言并禁用
标准错误输出，在访客内丢弃 cJSON 的 Unity 日志并核对原始测试计数，同时用 zlib
上游的 `Z_SOLO` 配置执行其官方样例。运行权限只包含声明的只读时钟。
cJSON 语料测试把上游 JSON 输入和期望输出按原字节嵌入访客。
gzip 文件读取和其他 ROS 中间件仍需单独移植验收。

静态归档复验使用上一步的输出，逐个编译 zlib 的八个源文件，用 SDK 的
`wrar` 打包，然后重新链接和执行同一个上游测试。

```sh
"$GATE" /usr/bin/python3 -B tests/upstream_zlib_archive.py "$PWD" "$OUTPUT" \
  "$SOURCES/zlib" "$SIGNED_C_SITE" "$WROS_VM" "$ARCHIVE_OUTPUT"
```

## 上游 Go 和 Python 库

用已签名的 wasm32 TinyGo EH 和 MTE 配置复验 `xxHash` v2.3.0。
访客适配层保留上游功能测试和断言，包括 `TestAll` 的 148 个子用例。
上游对宿主分配次数的测量在原生对照中运行。

```sh
git clone --depth 1 --branch v2.3.0 https://github.com/cespare/xxhash.git "$SOURCES/xxhash"
"$GATE" /usr/bin/python3 -B tests/upstream_go_libraries.py --sdk "$PWD" \
  --source "$SOURCES/xxhash" --commit "$SDK_COMMIT" --site "$SIGNED_TINYGO_SITE" \
  --vm "$WROS_VM" --output "$GO_OUTPUT"
```

CPython 复验采用 ROS `angles` 的原始 unittest 方法和 PyPA `packaging`
的版本用例。 [Python 复验说明](../../tests/cpython/upstream-libraries.zh-CN.md)。

## 上游 Rust 与解释器库

ArrayVec 0.7.7 复验需要已签名的 Rust wasm32 Core 3.0 配置，采用单线程、
无 EH 和 `-O3 -g`。原生对照关闭库的默认特性，运行上游集成测试。访客
运行 26 个原测试，覆盖内联向量、UTF-8 字符串、容量检查、迭代、区间移除
和析构。测试入口使用 `core`，断言失败触发 Wasm trap。依赖宿主服务、
标准库堆对象和异常展开的用例只在原生对照中运行。

```sh
git clone --depth 1 --branch 0.7.7 https://github.com/bluss/arrayvec.git "$SOURCES/arrayvec"
"$GATE" /usr/bin/python3 -B tests/upstream_rust_libraries.py --sdk "$PWD" \
  --source "$SOURCES/arrayvec" --commit "$SDK_COMMIT" --site "$SIGNED_RUST_SITE" \
  --rustroot "$RUST_ROOT" --vm "$WROS_VM" --output "$RUST_OUTPUT"
```

如果要对照显式关闭 MTE 的配置，把 `--site` 换成
`--toolchain "$WROS_LLVM" --plain-sysroots "$PLAIN_NOEH_SYSROOT"`，并选择新的
输出目录。严格配置会记录反汇编确认的托管栈操作、签名绑定的 VM 和两个引擎的结果。

QuickJS 和 mruby 复验独立记录源码提交及适配范围。
[解释器库复验说明](../../tests/script-libraries/README.zh-CN.md)。

### Lua JSON 库

先在原生 Lua 5.4 上运行 json.lua 0.1.2 的上游测试，再用已安装的
Wasm Lua 解释器构建同一套测试。库实现和 14 组启用的测试函数保持原样。
测试入口把库嵌入程序，替代文件加载，并在任意一条断言失败时使测试失败，
共核对 74 条断言。

~~~sh
git clone --depth 1 --branch v0.1.2 https://github.com/rxi/json.lua.git "$SOURCES/json.lua"
"$GATE" /usr/bin/python3 -B tests/upstream_lua_library.py --sdk "$PWD" \
  --source "$SOURCES/json.lua" --commit "$SDK_COMMIT" --site "$SIGNED_LUA_SITE" \
  --vm "$WROS_VM" --output "$LUA_OUTPUT"
~~~

签名站点选用 wasm32 Core 3.0、EH、MTE 和 -O3 -g。测试程序使用固定的公开
种子，无宿主导入，在解释器和 AOT 中分别运行。上游禁用的严格解码测试仍保持
禁用。
