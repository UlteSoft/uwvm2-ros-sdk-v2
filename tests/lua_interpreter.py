"""Compile Lua 5.4 as a Wasm guest and exercise its imports, limits and error path."""
import argparse
import json
import os
import resource
import subprocess
import sys
from pathlib import Path

from separate_compilation import Profile, cgroup_record, inspect, sha, candidate_arguments, candidate_command

ROOT = Path(__file__).resolve().parents[1]
LIBRARIES = """
local values = {4,1,8}
table.sort(values)
assert(table.concat(values, ",") == "1,4,8")
assert(not pcall(function() error("expected") end))
assert(math.sqrt(9) == 3 and utf8.len("机器人") == 3)
assert(not io and not os and not package and not dofile and not load and not debug)
local co = coroutine.create(function() coroutine.yield(42) end)
local ok, value = coroutine.resume(co)
assert(ok and value == 42)
-- An allocation larger than the Lua-state budget must be catchable. The
-- allocator and interpreter must remain usable after Lua's emergency GC.
assert(not pcall(string.rep, "x", 20 * 1024 * 1024))
assert(string.rep("x", 5) == "xxxxx")
for _, mode in ipairs({"incremental", "generational"}) do
    collectgarbage(mode)
    local retained = {}
    for cycle = 1, 4 do
        for i = 1, 80 do
            retained[i] = {n = i, bytes = string.rep(string.char(i), 11 + i)}
        end
        for i = 2, 80, 2 do retained[i] = nil end
        collectgarbage("collect")
        for i = 1, 80, 2 do
            assert(retained[i].n == i and retained[i].bytes:byte(11 + i) == i)
        end
    end
end
"""


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("toolchain", "sysroots", "runtime", "output"):
        parser.add_argument("--" + name, type=Path, required=True)
    parser.add_argument("--address-bits", type=int, nargs="+", choices=(32, 64), default=(32, 64))
    parser.add_argument("--frontend-root", type=Path, default=ROOT)
    parser.add_argument("--no-mte", action="store_true", help="build and run the entire Lua interpreter without WasmMTE")
    candidate_arguments(parser)
    args = parser.parse_args()
    front, tc, sr, vm, work = (path.resolve() for path in
        (args.frontend_root, args.toolchain, args.sysroots, args.runtime, args.output))
    result = dict(complete=False, mte=not args.no_mte, cases=[], modules={}, cgroup=cgroup_record())
    work.mkdir(parents=True, exist_ok=False)
    tmp = work / "tmp"
    tmp.mkdir()
    os.environ["TMPDIR"] = str(tmp)
    resource.setrlimit(resource.RLIMIT_CORE, (0, 0))
    inputs = (front / "bin/wrlua", front / "bin/wrcc", front / "language/lua/entry.cpp",
              front / "third-parties/lua/lua-5.4.9.tar.gz", front / "install/frontend.py",
              front / "install/compiler.py", sr, vm, tc / "bin/clang", tc / "bin/wasm-ld",
              Path(__file__), front / "examples/lua/body.lua")
    result["inputs"] = {str(p): sha(p) for p in inputs}

    def save():
        (work / "results.json").write_text(json.dumps(result, indent=2) + "\n")

    def run(label, argv, diagnostic=None):
        command = candidate_command(argv, args.candidate_mte)
        proc = subprocess.run(command, cwd=work, capture_output=True, timeout=150)
        (work / (label + ".stderr")).write_bytes(proc.stderr)
        result["cases"].append(dict(name=label, argv=command, exit=proc.returncode, expected_success=diagnostic is None))
        save()
        if diagnostic is None:
            proc.check_returncode()
        elif proc.returncode == 0 or diagnostic not in proc.stderr:
            raise RuntimeError(label + ": " + proc.stderr.decode(errors="replace")[-1500:])
        print(label, flush=True)

    for bits in dict.fromkeys(args.address_bits):
        clock = "clock_time_get" + ("_wasm64" if bits == 64 else "")
        compiler = [sys.executable, front / "bin/wrlua", "--toolchain", tc, "--sysroots", sr,
                    "--target", f"wasm{bits}"]
        if args.no_mte:
            compiler.append("--no-mte")
        for mode in ("permitted", "standalone", "guest-only", "ros-only", "syntax-error"):
            seeded = mode in ("guest-only", "ros-only")
            ros = mode in ("permitted", "ros-only")
            label = f"{mode}{bits}"
            body = work / (label + ".lua")
            text = (front / "examples/lua/body.lua").read_text()
            body.write_text((text if ros else "assert(wros == nil)\n") +
                            LIBRARIES if mode != "syntax-error" else "local incomplete =")
            if seeded:
                with body.open("a") as stream:
                    stream.write("\nlocal a,b=math.randomseed(); assert(a==4294967295 and b==0)\n")
            app = work / (label + ".wasm")
            build = [*compiler, body, "-o", app]
            if ros:
                build += ["--ros-abi"]
            if seeded:
                build += ["--guest-seed", "4294967295"]
            run(label + "-compile", build)
            imports = inspect(app.read_bytes())
            expected = set() if seeded else {("wasi_snapshot_preview1", clock)}
            if ros:
                expected.add(("uwvm_ros_v2", "abi"))
            if {(r["module"], r["name"]) for r in imports} != expected:
                raise RuntimeError(f"unexpected final import set: {imports}")
            result["modules"][app.name] = {"sha256": sha(app), "imports": imports}
            for engine in ("int", "aot"):
                base = [vm, *Profile(bits).uwvm_feature_flags(), "--runtime-" + engine,
                        "--runtime-compile-threads", "0", "--runtime-llvm-jit-cache-path", "disable",
                        "--wasm-set-main-module-name", "main"]
                if not seeded:
                    base += ["--wasip1-single-create", "main", "--wasip1-single-enable",
                             "main", "--wasip1-single-interface", "main", clock, "allow"]
                if args.no_mte:
                    base.append("--wasm-feature-disable-memtag-extension")
                granted = base.copy() if seeded else [*base, "--wasip1-single-grant", "main", "realtime-clock"]
                if ros:
                    bound = ["--ros-scene-create", "robot", "--ros-scene-bind", "robot", "main",
                             "--ros-scene-interface", "robot", "abi", "allow"]
                    run(label + "-abi-denied-" + engine, [*granted, "--run", app], b"ROS scene interface is hidden")
                    granted += bound
                if mode == "standalone":
                    # Seed/pivot clock queries may be refused by the VM; the guest can still compute.
                    run(label + "-clock-denied-" + engine, [*base, "--run", app])
                run(label + "-" + engine, [*granted, "--run", app],
                    b"unreachable" if mode == "syntax-error" else None)
            saved = sha(app)
            broken = work / "bytecode.luac"
            broken.write_bytes(b"\x1bLua")
            run(label + "-binary-refused", [*compiler, broken, "-o", app], b"Lua text")
            if sha(app) != saved:
                raise RuntimeError("invalid input replaced an existing module")

    if any(sha(Path(p)) != digest for p, digest in result["inputs"].items()):
        raise RuntimeError("test inputs changed during qualification")
    result["complete"] = True
    save()


if __name__ == "__main__":
    main()
