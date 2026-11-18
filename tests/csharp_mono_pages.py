"""Build the pinned Mono WASI page manager and exercise it on real bounded Wasm memories."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import resource
import subprocess
import sys
import tarfile


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("toolchain", "sysroots", "runtime", "output"):
        parser.add_argument("--" + name, type=Path, required=True)
    args = parser.parse_args()
    sdk = Path(__file__).resolve().parents[1]
    sys.path[:0] = [str(sdk / "tests"), str(sdk / "install")]
    from compiler import compiler_environment, make_command
    from frontend import audit
    from guest_profile import Profile
    from imports import inspect
    from memtag_performance import exported_index
    from separate_compilation import cgroup_record, sha

    group = cgroup_record()
    work = args.output.resolve()
    work.mkdir(parents=True, exist_ok=False)
    resource.setrlimit(resource.RLIMIT_CORE, (0, 0))
    tool = args.toolchain.resolve()
    roots = args.sysroots.resolve()
    runtime = args.runtime.resolve()
    environment = dict(compiler_environment(tool), TMPDIR=str(work))
    profile = Profile(32)
    upstream = sdk / "third-parties/mono-pages"
    archive = upstream / "mono-pages.tar.xz"
    patch = upstream / "wasi-page-budget.patch"
    fixtures = sdk / "tests/csharp"
    settings = fixtures / "mono-pages.cmake"
    owners = fixtures / "mono-page-owners.c"
    quota = fixtures / "mono-page-quota.c"
    inputs = [Path(__file__), archive, patch, settings, owners, quota, roots, runtime,
              tool / "bin/clang", tool / "bin/wasm-ld"]
    report = dict(complete=False, cgroup=group,
                  scope="Single-thread wasm32/EH Mono page manager and VM memory owners. "
                        "No managed heap tracing, CLR startup or user C# package.",
                  inputs={str(path): sha(path) for path in inputs}, steps=[], modules={})

    def save():
        (work / "results.json").write_text(json.dumps(report, indent=2) + "\n")

    def run(name, argv, cwd=work):
        command = list(map(str, argv))
        result = subprocess.run(command, cwd=cwd, env=environment, capture_output=True, timeout=120)
        (work / (name + ".log")).write_bytes(result.stdout + result.stderr)
        report["steps"].append(dict(name=name, argv=command, exit=result.returncode))
        save()
        result.check_returncode()

    if sha(archive) != "fb336d94f589ad4a5a2b3b074ce485bac3694c458261ad8581ff30bf1881312c":
        raise ValueError("pinned Mono input archive differs")
    source = work / "source"
    source.mkdir()
    with tarfile.open(archive, "r:xz") as source_archive:
        for member in source_archive:
            relative = Path(member.name)
            if not member.isfile() or relative.is_absolute() or ".." in relative.parts:
                raise ValueError("unexpected Mono source member")
            target = source / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            with target.open("xb") as dest:
                dest.write(source_archive.extractfile(member).read())

    mono = source / "src/mono"
    unit = mono / "mono/utils/mono-wasm-pagemgr.c"
    headers = work / "include"
    headers.mkdir()
    run("configure", ["/usr/bin/cmake", "-Dsource=" + str(source), "-Doutput=" + str(headers), "-P", settings])
    cflags = ["-O3", "-g", "-std=gnu11", "-DNDEBUG", "-DHOST_WASI", "-DHAVE_CONFIG_H",
              "-D_WASI_EMULATED_SIGNAL", "-D_THREAD_SAFE"]
    for directory in [headers, mono, mono / "mono/eglib", source / "src/native",
                      source / "src/native/public", mono / "wasi/mono-include"]:
        cflags += ["-I", str(directory)]

    def compile_unit(label):
        target = work / (label + ".o")
        command, selection = make_command(tool, [roots], profile, "c", [*cflags, "-c", str(unit), "-o", str(target)], True)
        report["sysroot_closure"] = selection["closure_sha256"]
        run(label, command)
        return target

    def exercise(label, native_object, fixture, flags):
        module = work / (label + ".wasm")
        link, _ = make_command(tool, [roots], profile, "c", [
            "-O3", "-g", "-nostartfiles", "-Wl,--no-entry,--export=check_pages",
            *flags, str(native_object), str(fixture), "-o", str(module)])
        run(label + "-link", link)
        payload = module.read_bytes()
        audit(payload, profile)
        if inspect(payload):
            raise ValueError("unexpected host import in Mono page manager test")
        report["modules"][label] = sha(module)
        entry = str(exported_index(module, "check_pages"))
        for engine in ("int", "aot"):
            for enabled in (True, False):
                name = label + "-" + engine + ("-tagged" if enabled else "-plain")
                run(name, [runtime, *profile.uwvm_feature_flags(),
                           *([] if enabled else ["--runtime-disable-memtag"]),
                           "--runtime-" + engine, "--runtime-compile-threads", "0",
                           "--runtime-llvm-jit-cache-path", "disable", "--runtime-memtag-mode", "sync",
                           "--wasm-set-start-func", entry, str(int(enabled)), "--run", module])

    save()
    reference = compile_unit("upstream")
    exercise("upstream-ownership", reference, owners, [])
    run("apply-budget-fix", ["/usr/bin/patch", "--batch", "--fuzz=0", "-p1", "-i", patch], source)
    if sha(unit) != "3a5a63a61613723a667828428d7bdaf9615ab25264084d507d1ce3ad91ed337c":
        raise ValueError("reviewed Mono page manager source differs")
    corrected = compile_unit("bounded")
    exercise("bounded-ownership", corrected, owners, [])
    exercise("fixed-budget", corrected, quota, ["-DNO_ROOM", "-Wl,--initial-memory=262144,--max-memory=262144"])
    exercise("two-spare-pages", corrected, quota, ["-Wl,--initial-memory=262144,--max-memory=393216"])
    report["complete"] = True
    save()


if __name__ == "__main__":
    main()
