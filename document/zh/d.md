# D BetterC

Linux x86-64 站点支持单线程 Wasm32、Core 3、EH 与 WasmMTE。应用提供一个 D 源文件，实现 `extern(C) nothrow @nogc uint wros_main()`，成功时返回零。SDK 提供入口、ROSv2 的 D 声明及 C 绑定。LDC BetterC 先生成带调试信息的未优化 LLVM IR，再由 SDK LLVM 工具标记，交给经签署的 C 后端用 `-O3 -g` 编译链接。

```sh
python3 install/bootstrap.py install --commit "$SDK_COMMIT" --platform unitree --language d --site-profile "$SITE" --prefix "$PREFIX"
"$SDK/bin/wrd" "$SDK/examples/d/body.d" -o body.wasm --build-receipt
"$SDK/bin/wrd" verify --artifact body.wasm --receipt body.wasm.wros-build.json --vm "$VM" --approved-receipt-sha256 "$RECEIPT_SHA256"
```

将 SDK 设为安装结果中的目录。Xmake 示例通过 `UWVM_ROS_SDK_ROOT` 找到安装目录。验证端应独立取得可信的构建收据摘要。D 专用收据绑定其签署资格、C 后端资格与 VM。

站点工具链放置 `bin/wros-ldc2`、带构建收据的 `bin/wros-flang-mte`，以及匹配版本的 D 导入目录 `share/wros/betterc/imports`（含 `object.d`）。资格记录逐项绑定 Linux ELF 加载器、LDC 与标记工具加载的共享库、D 源码导入树和 SDK 代码。构建使用固定的 LDC 配置。

管理员可用 `tests/d_bindings/qualify_site.py --measure-host --toolchain "$TOOLCHAIN"` 审核宿主输入。随后提供已审核的摘要、已签署的 C 站点和匹配 VM，运行资格程序以核对 D 声明，编译含固定数组、指针运算及 ABI 查询的客体，在两种引擎上验证权限拒绝和授权。程序生成候选声明，须经管理员独立审核、按 WSEA 资格策略签署后才能安装。当前资格覆盖此 BetterC 链路与测例；完整 DRuntime、Phobos 运行时、Wasm64 和多线程 D 不在范围内。
