"""Install wrcs at a pinned SDK commit, build user C# inputs, and test the actual exports in both VM engines."""
import argparse
import json
import os
from pathlib import Path
import resource
import shutil
import subprocess
import sys

from separate_compilation import cgroup_record, Profile, sha

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "install"))
from bootstrap import install, Source
from artifacts import sections
from imports import inspect


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for key in ("repository", "dotnet", "mono-compiler", "toolchain", "vm", "xmake", "output"):
        parser.add_argument("--" + key, type=Path, required=True)
    parser.add_argument("--sysroots", type=Path, help="matching wasm32/EH/MTE receipt to exercise mixed C#/C Xmake linking")
    parser.add_argument("--commit", required=True)
    args = parser.parse_args()
    resource.setrlimit(resource.RLIMIT_CORE, (0, 0))
    out = args.output.resolve()
    out.mkdir(parents=True, exist_ok=False)
    (out / "tmp").mkdir()
    os.environ["TMPDIR"] = str(out / "tmp")
    report = {"complete": False, "cgroup": cgroup_record(), "commit": args.commit, "cases": [], "modules": {}}

    def save():
        (out / "results.json").write_text(json.dumps(report, indent=2) + "\n")

    save()
    source = Source(args.commit, args.repository.resolve())
    try:
        install(source, "unitree", "c", out / "install", ["--component", "numeric-aot"], plan=True)
    except ValueError:
        report["cases"].append({"name": "refuse-c", "result": "correct refusal"})
    else:
        raise ValueError("unexpected numeric AOT admission for C")
    result = install(source, "unitree", "csharp", out / "install", [])
    sdk = Path(result["directory"])
    adapters = {p for p in source.requested if p.endswith("/adapter.lua") or p.endswith("/platform.lua")}
    expected_adapters = {"language/csharp/xmake/adapter.lua", "platform/unitree/xmake/platform.lua"}
    if adapters != expected_adapters or "bin/wrcs" not in source.requested:
        raise ValueError("C# installation contains incorrect adapters")
    report["selection"] = result
    project = out / "project"
    shutil.copytree(sdk / "examples/csharp/numeric-aot", project)
    tool = args.toolchain.resolve()
    env = dict(os.environ, PATH="/usr/bin:/bin", PYTHONDONTWRITEBYTECODE="1",
               UWVM_ROS_SDK_ROOT=str(sdk), WROS_PLATFORM="unitree",
               WROS_TOOLCHAIN=str(tool), WROS_DOTNET=str(args.dotnet.resolve()),
               WROS_MONO=str(args.mono_compiler.resolve()), XMAKE_GLOBALDIR=str(out / "xmake"))
    cli = [sdk / "bin/wrcs", "--toolchain", tool, "--dotnet", args.dotnet.resolve(),
           "--mono-compiler", args.mono_compiler.resolve()]

    def run(name, argv, refusal=None, *, cwd=None):
        cmd = list(map(str, argv))
        raw = subprocess.run(cmd, env=env, cwd=cwd or project, stdout=subprocess.PIPE,
                             stderr=subprocess.STDOUT, timeout=180)
        (out / (name + ".log")).write_bytes(raw.stdout)
        report["cases"].append({"name": name, "exit": raw.returncode, "argv": cmd})
        save()
        if refusal:
            if raw.returncode == 0 or refusal not in raw.stdout:
                raise RuntimeError("missing expected refusal: " + name)
        elif raw.returncode:
            raise RuntimeError(name + ": " + raw.stdout.decode(errors="replace")[-2200:])

    xmake = args.xmake.resolve()
    for language, variant, message in (("java", "numeric-aot", b"synchronous-aot component for java"),
                                       ("csharp", "protocol", b"numeric-aot component for csharp")):
        renamed = out / "renamed" / args.commit / "unitree" / language / variant
        shutil.copytree(sdk, renamed)
        env["UWVM_ROS_SDK_ROOT"] = str(renamed)
        run("reject-mislabeled-" + language, [xmake, "f", "-c", "-y", "-a", "wasm32"], message)
    env["UWVM_ROS_SDK_ROOT"] = str(sdk)
    run("configure", [xmake, "f", "-c", "-y", "-a", "wasm32"])
    run("build-installed-example", [xmake, "-j1", "filter"])
    example, = (project / "build").rglob("filter.wasm")
    sample = project / "Filter.cs"
    if args.sysroots:
        # Two explicit installations from the same commit; C# never sees a driver.
        c_sdk = Path(install(source, "unitree", "c", out / "install", [])["directory"])
        env.update(WROS_C_BODY=str(c_sdk), WROS_SYSROOTS=str(args.sysroots.resolve()))
        (project / "body.c").write_text("extern int evaluate(int); void _start(void) {"
            "for (int n=-80;n<=80;++n) if (evaluate(n)!=7*n-3) __builtin_trap(); }")
        with (project / "xmake.lua").open("a") as script:
            script.write("""
target("scalar")
    set_kind("static")
    set_language("csharp")
    set_ros_platform("unitree")
    set_wros_profile({mte = "legacy"})
    set_optimize("fastest")
    set_symbols("debug")
    add_wros_exports("Filter.Scale")
    add_files("Filter.cs")
target_end()
target("body")
    set_kind("binary")
    set_language("c")
    set_wros_sdk(os.getenv("WROS_C_BODY"))
    set_ros_platform("unitree")
    set_wros_profile({mte = "legacy"})
    set_optimize("fastest")
    set_symbols("debug")
    add_deps("scalar")
    add_files("body.c")
target_end()
""")
        run("mixed-configure", [xmake, "f", "-c", "-y", "-a", "wasm32"])
        run("mixed-build", [xmake, "-j1", "body"])
        mixed, = (project / "build").rglob("body.wasm")
        if inspect(mixed.read_bytes()):
            raise ValueError("mixed no-authority kernel requested a host import")
        for engine in ("int", "aot"):
            run("mixed-" + engine, [args.vm.resolve(), *Profile().uwvm_feature_flags(),
                "--runtime-" + engine, "--runtime-compile-threads", "0", "--runtime-memtag-mode", "sync", "--run", mixed])
        obj = out / "unreviewed.o"
        run("object-needs-sysroot", [*cli, "--legacy-mte", "-c", "--entry", "Filter.Scale", sample, "-o", obj],
            b"use -c and --sysroots together")
        run("signed-object-denial", [*cli, "--mte", "-c", "--sysroots", args.sysroots.resolve(),
            "--entry", "Filter.Scale", sample, "-o", obj], b"no signed strict C# release")
        if obj.exists():
            raise ValueError("refused build published an SDK object")
    cli_out = out / "project.wasm"
    for label, flags, refusal in (
        ("wasip2", ["--target", "wasm32-wasip2"], b"invalid choice"),
        ("wasip3", ["--target", "wasm32-wasip3"], b"invalid choice"),
        ("component", ["--component-model"], b"unrecognized arguments"),
        ("native", ["--target", "x86_64-linux"], b"invalid choice"),
    ):
        run(label, [*cli, *flags, "--entry", "Filter.Scale", sample, "-o", cli_out], refusal)

    run("strict-explicit", [*cli, "--mte", "--entry", "Filter.Scale", sample, "-o", cli_out])
    for scalar in (example, cli_out):
        data = scalar.read_bytes()
        if [data[start] for start, _, _, _ in sections(data) if data[start]] != [1, 3, 7, 10]:
            raise ValueError("strict C# kernel exposes guest resources or has additional sections")
    # A distinct user source exercises the compiler, not just the packaged example.
    body = project / "Track.cs"
    body.write_text("""public static class Track {
    public static unsafe int Tags(int n) {
        long a = n, b = n + 1;
        return (int)(((nuint)(&a) >> 28) | (((nuint)(&b) >> 28) << 4));
    }
    public static int Sum(int x) { int y = 0; for (int i = 0; i < 5; i++) y += x ^ i; return y; }
    public static int Array(int n) { int[] a = new int[4]; a[0] = n; return a[0] + a.Length; }
    public static long Wide(int n) => n;
}""")
    cli_out.write_bytes(b"original")
    run("strict-address-taken", [*cli, "--entry", "Track.Tags", body, "-o", cli_out], b"C# scalar proof rejects")
    if cli_out.read_bytes() != b"original":
        raise ValueError("failed scalar proof replaced an existing output")
    (out / "observe.c").write_text("""
__attribute__((import_module("component"), import_name("evaluate"))) extern int evaluate(int);
void _start(void) {
    for (int i = -80; i <= 80; ++i) {
        int out = evaluate(i);
#if MODE == 0
        if (out != i*7-3) __builtin_trap();
#elif MODE == 1
        int lo = out & 15, hi = out >> 4;
        if (lo <= 0 || hi <= 0 || hi >= 16 || lo == hi) __builtin_trap();
#elif MODE == 2
        if (out != 0) __builtin_trap();
#else
        int expected = 0; for (int k=0;k<5;k++) expected += i ^ k;
        if (out != expected) __builtin_trap();
#endif
    }
}
""")
    modules = [example]
    for name, entry, mode in (("tags", "Track.Tags", "--legacy-mte"), ("plain", "Track.Tags", "--no-mte"),
                              ("loop", "Track.Sum", "--mte")):
        path = out / (name + ".wasm")
        run("compile-" + name, [*cli, mode, "--entry", entry, body, "-o", path])
        modules.append(path)
    for mode, path in enumerate(modules):
        data = path.read_bytes()
        if inspect(data):
            raise ValueError("numeric module contains imports")
        exports = []
        for start, _, _, stream in sections(data):
            if data[start] == 7:
                exports.extend((stream.name(), stream.byte(), stream.uint()) for _ in range(stream.count()))
                stream.end()
        if len(exports) != 1 or exports[0][:2] != ("evaluate", 0):
            raise ValueError("numeric module unexpectedly exposes memory or another export")
        report["modules"][path.name] = sha(path)
        observer = out / ("observer-" + str(mode) + ".wasm")
        run("observer-" + str(mode), [tool / "bin/clang", "--no-default-config", "--target=wasm32-wasip1",
            "-O3", "-g", "-nostdlib", "-ffreestanding", "-DMODE=" + str(mode), out / "observe.c",
            "-Wl,--no-entry,--export=_start", "-o", observer])
        for engine in ("int", "aot"):
            run(path.stem + "-" + engine, [args.vm.resolve(), *Profile().uwvm_feature_flags(), "--runtime-" + engine,
                "--runtime-compile-threads", "0", "--runtime-llvm-jit-cache-path", "disable",
                "--runtime-memtag-mode", "sync", *(["--runtime-disable-memtag"] if mode == 2 else []),
                "--wasm-preload-library", path, "component", "--run", observer])

    # Exercise a C#-authored entry at the application boundary, with the real
    # SDK-managed declaration and policy compiled from the installed example.
    scene_project = out / "scene-project"
    shutil.copytree(sdk / "examples/csharp/scene-abi", scene_project)
    run("scene-xmake-config", [xmake, "f", "-c", "-y", "-a", "wasm32"], cwd=scene_project)
    run("scene-xmake-build", [xmake, "-j1", "robot"], cwd=scene_project)
    application, = (scene_project / "build").rglob("robot.wasm")
    def scene_shape(path):
        data = path.read_bytes()
        standard = [data[start] for start, _, _, _ in sections(data) if data[start]]
        expected = [{"module": "uwvm_ros_v2", "name": "abi", "kind": 0, "params": [], "results": ["i32"]}]
        if standard != [1, 2, 3, 7, 10] or inspect(data) != expected:
            raise ValueError("C# scene entry has an unexpected type or authority")
        export, = (stream for start, _, _, stream in sections(data) if data[start] == 7)
        if export.count() != 1 or (export.name(), export.byte(), export.uint()) != ("_start", 0, 2):
            raise ValueError("C# scene program exports more than its startup function")
        export.end()
    scene_shape(application)
    for engine in ("int", "aot"):
        command = [args.vm.resolve(), *Profile().uwvm_feature_flags(), "--debug-fault-action", "exit",
                   "--runtime-" + engine, "--runtime-compile-threads", "0", "--runtime-llvm-jit-cache-path", "disable",
                   "--wasm-set-main-module-name", "main"]
        run("scene-hidden-" + engine, [*command, "--run", application], b"ROS scene interface is hidden")
        binding = ["--ros-scene-create", "robot", "--ros-scene-bind", "robot", "main",
                   "--ros-scene-interface", "robot", "abi"]
        run("scene-denied-" + engine, [*command, *binding, "deny", "--run", application], b"unreachable")
        run("scene-abi-" + engine, [*command, *binding, "allow", "--run", application])
    report["modules"]["robot.wasm"] = sha(application)
    scene_source = (scene_project / "Robot.cs").read_text()
    changed = out / "Changed.cs"
    changed.write_text(scene_source.replace("major == 2", "major == 3"))
    scene_cli = [*cli, "--scene-entry", "Robot.Start", changed, "-o", cli_out]
    run("scene-compile-other-policy", scene_cli)
    scene_shape(cli_out)
    for engine in ("int", "aot"):
        run("scene-reject-major-" + engine, [args.vm.resolve(), *Profile().uwvm_feature_flags(),
            "--runtime-" + engine, "--runtime-compile-threads", "0", "--debug-fault-action", "exit",
            "--wasm-set-main-module-name", "main", "--ros-scene-create", "robot", "--ros-scene-bind", "robot", "main",
            "--ros-scene-interface", "robot", "abi", "allow", "--run", cli_out], b"unreachable")
    cli_out.write_bytes(b"original")
    for label, code in (
        ("no-query", scene_source.replace("Scene.Abi()", "2")),
        ("extra-query", scene_source.replace("Scene.Abi()", "Scene.Abi() + Scene.Abi()")),
        ("shadow-query", scene_source.replace("using Wros;", "public static class Scene { public static int Abi() => 2; }")),
    ):
        changed.write_text(code)
        run("scene-refuse-" + label, scene_cli, b"scene entry must return")
        if cli_out.read_bytes() != b"original":
            raise ValueError("rejected scene entry replaced its output")

    cli_out.write_bytes(b"original")
    for name, entry, diagnostic in (("array", "Track.Array", b"unsupported numeric IL"),
                                    ("signature", "Track.Wide", b"taking one int"),
                                    ("missing", "Track.None", b"entry method was not found")):
        run(name, [*cli, "--legacy-mte", "--entry", entry, body, "-o", cli_out], diagnostic)
    body.write_text("public static class Track { static Track() {} public static int Sum(int n) => n; }")
    run("initializer", [*cli, "--legacy-mte", "--entry", "Track.Sum", body, "-o", cli_out], b"initializer needs the CLR")
    body.write_text("""using System.Runtime.CompilerServices;
public static class Track {
    [MethodImpl(MethodImplOptions.Synchronized)] public static int Sum(int n) => n + 1;
}""")
    run("synchronized", [*cli, "--legacy-mte", "--entry", "Track.Sum", body, "-o", cli_out], b"method flags need the CLR")
    body.write_text("""public static class Track {
    public static int Helper(int n) => n + 1;
    public static int Sum(int n) => Helper(n);
}""")
    run("managed-call", [*cli, "--legacy-mte", "--entry", "Track.Sum", body, "-o", cli_out], b"unsupported numeric IL operation: call")
    body.write_text("""using System.Runtime.InteropServices;
public static class Track {
    [DllImport("device")] public static extern int Native(int n);
    public static int Sum(int n) => Native(n);
}""")
    run("pinvoke", [*cli, "--legacy-mte", "--entry", "Track.Sum", body, "-o", cli_out], b"DllImportAttribute' could not be found")
    if cli_out.read_bytes() != b"original":
        raise ValueError("rejected input modified existing output")
    report["complete"] = True
    save()


if __name__ == "__main__":
    main()
