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
