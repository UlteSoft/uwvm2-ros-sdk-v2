"""Exercise Jazzy tf2 BufferCore and its TimeCache with original package sources."""
import argparse
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import resource
import subprocess
import sys
from xml.etree import ElementTree

from upstream_cpp import Profile, SourceArchive, cgroup_record, inspect, put, save, sha

TF2 = "35aa12ef93bbbbbc3a42c705"
RCUTILS = "bc07f0c0c038874d9c7bd440"
WASI = {"clock_time_get": (["i32", "i64", "i32"], ["i32"]),
        "environ_get": (["i32", "i32"], ["i32"]),
        "environ_sizes_get": (["i32", "i32"], ["i32"]), "proc_exit": (["i32"], [])}


def extract(corpus, index, package, source_id, sources, path):
    instance, = [i for i in index[package]["instances"] if i["source_id"] == source_id]
    archive = SourceArchive(corpus, instance)
    try:
        chosen = set(map(PurePosixPath, sources))
        chosen.update(p for p in archive.files if p.parts[0] == "include")
        manifest = archive.read("package.xml")
        for item in sorted(chosen):
            put(path, item, archive.read(item))
        return dict(snapshot=instance, version=ElementTree.fromstring(manifest).findtext("version"),
                    files={str(p): sha(path / p) for p in sorted(chosen)})
    finally:
        archive.tar.close()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("corpus", "sdk", "vm", "ros-prefix", "output"):
        parser.add_argument("--" + name, required=True, type=lambda s: Path(s).resolve())
    parser.add_argument("--layer", required=True, choices=("buffer", "cache"))
    parser.add_argument("--target", required=True, choices=("native", "wasm"))
    a = parser.parse_args()
    group = cgroup_record()
    if ".tmp" not in a.output.parts:
        parser.error("use a fresh directory in a project .tmp")
    a.output.mkdir(mode=0o700, parents=True, exist_ok=False)
    resource.setrlimit(resource.RLIMIT_CORE, (0, 0))
    env = dict(os.environ, TMPDIR=str(a.output), PATH="/usr/bin:/bin", PYTHONDONTWRITEBYTECODE="1")
    report = dict(complete=False, layer=a.layer, target=a.target, cgroup=group, commands=[],
                  runnerSha256=sha(Path(__file__)), vmSha256=sha(a.vm))
    result = a.output / "results.json"

    def step(name, argv):
        argv = list(map(str, argv))
        log = a.output / (name + ".log")
        with log.open("xb") as stream:
            proc = subprocess.run(argv, cwd=a.output, env=env, stdout=stream,
                                  stderr=subprocess.STDOUT, timeout=180)
        report["commands"].append(dict(name=name, exit=proc.returncode, argv=argv, logSha256=sha(log)))
        save(result, report)
        return proc.returncode

    def check(name, argv, expected=0):
        code = step(name, argv)
        if code != expected:
            report["failedStep"] = name
            save(result, report)
            raise RuntimeError(f"{name} exited {code}; see {a.output}/{name}.log")

    inventory = a.corpus / "linux-five-capability-inventory/packages.json"
    index = {r["name"]:r for r in json.loads(inventory.read_bytes())}
    report["inventorySha256"] = sha(inventory)
    src = a.output / "tf2"
    rc = a.output / "rcutils"
    units = ["src/cache.cpp", "src/time.cpp"]
    if a.layer == "buffer":
        units.extend(["src/static_cache.cpp", "src/buffer_core.cpp"])
    c_units = ["src/snprintf.c", "src/strerror.c"]
    report["tf2"] = extract(a.corpus, index, "tf2", TF2, units, src)
    report["rcutils"] = extract(a.corpus, index, "rcutils", RCUTILS, c_units, rc)
    fixture = Path(__file__).with_name("tf2_buffer.cpp" if a.layer == "buffer" else "tf2_time_cache.cpp")
    report["fixtureSha256"] = sha(fixture)
    generated = []
    if a.layer == "buffer":
        # Native ROS message schemas have target-neutral generated C++ headers.
        # Link only the original sources below. Never link the native ROS VM libraries.
        for pkg in ("geometry_msgs", "std_msgs", "builtin_interfaces", "rosidl_runtime_cpp",
                    "rosidl_runtime_c", "rosidl_typesupport_interface", "rcutils", "tf2_msgs"):
            prefix = a.ros_prefix / "include" / pkg
            if not prefix.is_dir():
                raise ValueError("missing ROS header package " + pkg)
            generated.append(prefix)
        mapping = {str(p.relative_to(a.ros_prefix)): sha(p)
                   for d in generated for p in sorted(d.rglob("*")) if p.is_file()}
        save(a.output / "header-inputs.json", mapping)
        report["installedJazzyHeadersSha256"] = sha(a.output / "header-inputs.json")
    includes = [flag for p in [src / "include", rc / "include", *generated] for flag in ("-I", p)]
    flags = ["-D", "RCUTILS_LOG_MIN_SEVERITY=RCUTILS_LOG_MIN_SEVERITY_NONE", *includes]
    save(result, report)
    if a.target == "native":
        # Use the C frontend and XSI strerror_r for the original rcutils C units.
        objects = []
        for unit in c_units:
            obj = a.output / (Path(unit).stem + ".o")
            check("cc-" + obj.stem, ["/usr/bin/gcc", "-std=c11", "-O3", "-g", "-D_POSIX_C_SOURCE=200809L",
                                     *includes, "-c", rc / unit, "-o", obj])
            objects.append(obj)
        for unit in units:
            obj = a.output / (Path(unit).stem + ".o")
            check("cpp-" + obj.stem, ["/usr/bin/g++", "-std=c++20", "-O3", "-g", *flags,
                                      "-c", src / unit, "-o", obj])
            objects.append(obj)
        for negative in (0, 1):
            label = "changed-reference" if negative else "reference"
            binary = a.output / label
            check(label + "-build", ["/usr/bin/g++", "-std=c++20", "-O3", "-g", *flags,
                  f"-DWROS_CHANGED_REFERENCE={negative}", fixture, *objects, "-o", binary])
            check(label + "-run", [binary], 3 if negative else 0)
        report.update(complete=True, nativeCxxSha256=sha(Path("/usr/bin/g++")),
                      nativeCSha256=sha(Path("/usr/bin/gcc")))
        save(result, report)
        return

    # wrcc compiles the dependency as C++. wasi-libc exposes the XSI return
    # type; use the matching upstream branch for this translation unit only.
    xsi = a.output / "rcutils-xsi.cpp"
    xsi.write_text('#if defined(__wasi__)\n#undef _GNU_SOURCE\n#define _POSIX_C_SOURCE 200809L\n'
                   '#endif\n#include "strerror.c"\n')
    report["rcutilsXsiAdapterSha256"] = sha(xsi)
    report["imports"] = {}
    for negative in (0, 1):
        label = "changed-reference" if negative else "reference"
        module = a.output / (label + ".wasm")
        check(label + "-build", [a.sdk / "bin/wrcc", "--std", "c++20", "-O3", "-g", "--target",
              "wasm32", "--reactor", "--export", "_start", "--build-receipt", *flags,
              "-I", rc / "src", "-D", f"WROS_CHANGED_REFERENCE={negative}", fixture,
              *(src / u for u in units), rc / c_units[0], xsi, "-o", module])
        receipt = Path(str(module) + ".wros-build.json")
        if json.loads(receipt.read_bytes())["mode"] != "strict":
            raise ValueError("strict MTE build required")
        check(label + "-verify", [sys.executable, "-B", a.sdk / "install/qualification.py",
              "--vm", a.vm, "--artifact", module, "--receipt", receipt, "--approved-receipt-sha256", sha(receipt)])
        imports = inspect(module.read_bytes())
        policy = ["--wasip1-single-create", "module.wasm", "--wasip1-single-enable", "module.wasm"]
        for imp in imports:
            if (imp["module"] != "wasi_snapshot_preview1" or imp["kind"] != 0 or
                    WASI.get(imp["name"]) != (imp.get("params"), imp.get("results"))):
                raise ValueError("unexpected guest input " + repr(imp))
            policy += ["--wasip1-single-interface", "module.wasm", imp["name"], "deny"]
        report["imports"][label] = dict(imports=imports, policy=policy, guestSha256=sha(module))
        for engine in ("int","aot"):
            name = label + "-" + engine
            cmd = [a.vm, *Profile().uwvm_feature_flags(), "--debug-fault-action", "exit", "--runtime-" + engine,
                   "--runtime-compile-threads", "0", "--runtime-llvm-jit-cache-path", "disable", *policy, "--run", module]
            if negative:
                status = step(name, cmd)
                if status == 0 or "unreachable" not in (a.output / (name + ".log")).read_text().lower():
                    raise ValueError("guest missed the changed reference or failed before the expected trap")
            else:
                check(name, cmd)
    report["complete"] = True
    save(result, report)


if __name__ == "__main__":
    main()
