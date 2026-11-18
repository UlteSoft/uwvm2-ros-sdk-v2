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
    parser.add_argument("--commit", required=True)
    args = parser.parse_args()
    resource.setrlimit(resource.RLIMIT_CORE, (0, 0))
    out = args.output.resolve()
    out.mkdir(parents=True, exist_ok=False)
    report = {"complete": False, "cgroup": cgroup_record(), "commit": args.commit, "cases": [], "modules": {}}

    def save():
        (out / "results.json").write_text(json.dumps(report, indent=2) + "\n")

    save()
    source = Source(args.commit, args.repository.resolve())
    for language, flags in (("csharp", []), ("c", ["--component", "numeric-aot"])):
        try:
            install(source, "unitree", language, out / "install", flags, plan=True)
        except ValueError:
            report["cases"].append({"name": "refuse-" + language, "result": "correct refusal"})
        else:
            raise ValueError("unexpected component admission")
    result = install(source, "unitree", "csharp", out / "install", ["--component", "numeric-aot"])
    sdk = Path(result["directory"])
    adapters = {p for p in source.requested if p.endswith("/adapter.lua") or p.endswith("/platform.lua")}
    expected_adapters = {"language/csharp/xmake/adapter.lua", "platform/unitree/xmake/platform.lua"}
    if adapters != expected_adapters or "bin/wrcs" not in source.requested:
        raise ValueError("C# installation contains incorrect adapters")
    report["selection"] = result
    project = out / "project"
    shutil.copytree(sdk / "examples/csharp/numeric-aot", project)
    tool = args.toolchain.resolve()
    env = dict(os.environ, UWVM_ROS_SDK_ROOT=str(sdk), WROS_PLATFORM="unitree",
               WROS_TOOLCHAIN=str(tool), WROS_DOTNET=str(args.dotnet.resolve()),
               WROS_MONO=str(args.mono_compiler.resolve()), XMAKE_GLOBALDIR=str(out / "xmake"))
    cli = [sdk / "bin/wrcs", "--toolchain", tool, "--dotnet", args.dotnet.resolve(),
           "--mono-compiler", args.mono_compiler.resolve()]

    def run(name, argv, refusal=None):
        cmd = list(map(str, argv))
        raw = subprocess.run(cmd, env=env, cwd=project, stdout=subprocess.PIPE,
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
    run("configure", [xmake, "f", "-c", "-y", "-a", "wasm32"])
    run("build-installed-example", [xmake, "-j1", "filter"])
    example, = (project / "build").rglob("filter.wasm")
    sample = project / "Filter.cs"
    cli_out = out / "project.wasm"
    for label, flags, refusal in (
        ("default-strict", [], b"no signed strict"), ("strict", ["--mte"], b"no signed strict"),
        ("wasip2", ["--target", "wasm32-wasip2"], b"invalid choice"),
        ("wasip3", ["--target", "wasm32-wasip3"], b"invalid choice"),
        ("component", ["--component-model"], b"unrecognized arguments"),
        ("native", ["--target", "x86_64-linux"], b"invalid choice"),
    ):
        run(label, [*cli, *flags, "--entry", "Filter.Scale", sample, "-o", cli_out], refusal)

    # A distinct user source exercises the compiler, not just the packaged example.
    body = project / "Track.cs"
    body.write_text("""public static class Track {
    public static unsafe int Tags(int n) {
        long a = n, b = n + 1;
        return (int)(((nuint)&a >> 28) | (((nuint)&b >> 28) << 4));
    }
    public static int Sum(int x) { int y = 0; for (int i = 0; i < 5; i++) y += x ^ i; return y; }
    public static int Array(int n) { int[] a = new int[4]; a[0] = n; return a[0] + a.Length; }
    public static long Wide(int n) => n;
}""")
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
                              ("loop", "Track.Sum", "--legacy-mte")):
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

    cli_out.write_bytes(b"original")
    for name, entry, diagnostic in (("array", "Track.Array", b"unsupported numeric IL"),
                                    ("signature", "Track.Wide", b"taking one int"),
                                    ("missing", "Track.None", b"entry method was not found")):
        run(name, [*cli, "--legacy-mte", "--entry", entry, body, "-o", cli_out], diagnostic)
    body.write_text("public static class Track { static Track() {} public static int Sum(int n) => n; }")
    run("initializer", [*cli, "--legacy-mte", "--entry", "Track.Sum", body, "-o", cli_out], b"initializer needs the CLR")
    body.write_text("""using System.Runtime.InteropServices;
public static class Track {
    [DllImport("device")] public static extern int Native(int n);
    public static int Sum(int n) => Native(n);
}""")
    run("pinvoke", [*cli, "--legacy-mte", "--entry", "Track.Sum", body, "-o", cli_out], b"unsupported numeric IL")
    if cli_out.read_bytes() != b"original":
        raise ValueError("rejected input modified existing output")
    report["complete"] = True
    save()


if __name__ == "__main__":
    main()
