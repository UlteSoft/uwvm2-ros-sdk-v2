"""@brief Replay the pinned Fortran stdlib trapezoid assertions on native and Wasm targets."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import resource
import subprocess
import sys
import urllib.request


UPSTREAM = "0ede3015ba4c7f945e1daa6b1fc504c0fbf1236f"
FILES = {
    "include/common.fypp": "df99b7452d6ba20f5f263dcade5c1b19d0d07398cc54064e2e4d4f309d75a589",
    "src/core/stdlib_kinds.fypp": "952c1813326a412a6e7a8d50c85031859f826f593c3ca5153c8b98b2ecbb19d4",
    "src/quadrature/stdlib_quadrature.fypp": "5f67dfbd91bd7c698e33b33cd2e33eeaf006b915d15745e16ab8f07a942a123e",
    "src/quadrature/stdlib_quadrature_trapz.fypp": "9d3faf640edc2d1899e29cfac8410c56c03eb252e0a09230c04db37d02e72ba7",
    "test/quadrature/test_trapz.fypp": "8192615cba1d2de9e729e0cf93a6bbab01bc7a8f9745de2aa7c7e75e8dbea1b2",
    "LICENSE": "d04c7ac7af8eb6b9d57f57765560dddc779a7e0f01c96fae178e7a35988b0a68",
}
UNITS = ("stdlib_kinds", "stdlib_quadrature", "stdlib_quadrature_trapz", "test_trapz")


def sha(path):
    """@brief Hash a full compiler, test input, receipt or emitted guest."""
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def inputs(directory, fetch):
    """@brief Acquire or verify only the fixed upstream files, including their license."""
    for name, digest in FILES.items():
        path = directory / Path(name).name
        if fetch and not path.exists():
            url = f"https://raw.githubusercontent.com/fortran-lang/stdlib/{UPSTREAM}/{name}"
            with urllib.request.urlopen(url, timeout=20) as response:
                data = response.read((1 << 20) + 1)
            if len(data) > (1 << 20) or hashlib.sha256(data).hexdigest() != digest:
                raise ValueError(f"unexpected upstream bytes for {name}")
            path.write_bytes(data)
        if sha(path) != digest:
            raise ValueError(f"upstream bytes differ for {name}")


def adapt_tests(source, output):
    """@brief Retain the 20 upstream predicates and replace only test reporting.
    @details The floating point inputs, calls and predicate text remain from
    upstream. Replace the test-drive error object with a numeric ERROR STOP.
    """
    checks, units = [], []
    for family in ("trapz", "trapz_weights", "trapz_zero"):
        for kind in ("sp", "dp"):
            name = f"test_{family}_{kind}"
            match = re.search(rf"subroutine {name}\(error\)\n(.*?)end subroutine {name}", source, re.S)
            if not match:
                raise ValueError(f"missing upstream test {name}")
            body, declarations = re.subn(
                r"(?mi)^\s*type\(error_type\), allocatable, intent\(out\) :: error\s*\n", "\n", match[1])

            def adapt(predicate):
                expression = predicate[1]
                checks.append({"test": name, "expression": expression})
                return f"if (.not. ({expression})) error stop {40 + len(checks)}"

            body, count = re.subn(r"call check\(error, (.+)\)$", adapt, body, flags=re.M)
            if declarations != 1 or count != (2 if family == "trapz_weights" else 4):
                raise ValueError(f"unexpected upstream test-drive interface for {name}")
            units.append((name, body))
    output.write_text(
        "program upstream_checks\nuse stdlib_kinds, only: sp,dp\n"
        "use stdlib_quadrature, only: trapz, trapz_weights\nimplicit none\n"
        + "\n".join(f"call {name}()" for name, _ in units)
        + "\ncontains\n"
        + "".join(f"subroutine {name}()\n{body}end subroutine {name}\n" for name, body in units)
        + "end program\n")
    return checks


def guest_assertions(build, out):
    """@brief Give the numerical fixture a guest-local failure path."""
    interface = """implicit none
interface
  subroutine wros_test_failed(code) bind(c)
    use iso_c_binding, only: c_int
    integer(c_int), value :: code
  end subroutine
end interface
"""
    staged = build.copy()
    for index, count in ((1, 1), (len(build) - 1, 20)):
        source = build[index]
        text, replaced = re.subn(r"error stop (\d+)", r"call wros_test_failed(\1)", source.read_text())
        if replaced != count or text.count("implicit none\n") != 1:
            raise ValueError("unexpected assertion report structure")
        staged[index] = out / ("guest-" + source.name)
        staged[index].write_text(text.replace("implicit none\n", interface, 1))
    failure = out / "guest-failure.c"
    failure.write_text("void wros_test_failed(int code) { (void)code; __builtin_trap(); }\n")
    negative = out / "guest-checks-negative.f90"
    checks = staged[-1].read_text()
    if checks.count("ans = 128.0_sp") != 1:
        raise ValueError("expected one false-assertion control")
    negative.write_text(checks.replace("ans = 128.0_sp", "ans = 129.0_sp", 1))
    return staged, failure, negative


def main():
    """@brief Replay native, strict site, and explicit untagged paths under the test gate."""
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("repository", "output", "native", "fypp"):
        parser.add_argument("--" + name, required=True, type=Path)
    for name in ("inputs", "vm", "toolchain", "sysroots", "site-profile", "fypp-module-dir"):
        parser.add_argument("--" + name, type=Path)
    parser.add_argument("--commit", required=True)
    parser.add_argument("--fetch", action="store_true", help="fetch only the six reviewed upstream files")
    parser.add_argument("--native-arg", action="append", default=[], help="explicit native compiler option")
    parser.add_argument("--plain", action="store_true", help="also exercise explicit --no-mte and --no-eh")
    parser.add_argument("--guest-assertion-traps", action="store_true",
                        help="replace fixture-only ERROR STOP reporting with a guest-local trap")
    args = parser.parse_args()
    if not re.fullmatch(r"[0-9a-f]{40}", args.commit):
        parser.error("supply the exact SDK commit")
    if not args.fetch and args.inputs is None:
        parser.error("supply --inputs or use --fetch")
    if (args.plain or args.site_profile) and args.vm is None:
        parser.error("guest execution needs an explicit --vm")
    if args.plain and (args.toolchain is None or args.sysroots is None):
        parser.error("--plain needs an explicit toolchain and a matching untagged sysroot")
    if args.guest_assertion_traps and not (args.plain or args.site_profile):
        parser.error("--guest-assertion-traps requires a guest execution route")
    out = args.output.resolve()
    if ".tmp" not in out.parts:
        parser.error("choose a fresh output within .tmp")
    membership = Path("/proc/self/cgroup").read_text().strip().split("::", 1)[1]
    cgroup = Path("/sys/fs/cgroup" + membership)
    if ((cgroup / "memory.max").read_text().strip() != "68719476736"
            or (cgroup / "memory.swap.max").read_text().strip() != "0"):
        parser.error("run through the existing 64 GiB test gate with zero swap")
    resource.setrlimit(resource.RLIMIT_CORE, (0, 0))
    out.mkdir(mode=0o700)
    source = args.inputs.resolve() if args.inputs else out / "upstream"
    source.mkdir(parents=True, exist_ok=True)
    native = args.native.resolve()
    fypp = args.fypp.resolve()
    repo = args.repository.resolve(strict=True)
    env = dict(os.environ, PATH="/usr/bin:/bin", TMPDIR=str(out), PYTHONDONTWRITEBYTECODE="1")
    report = dict(complete=False, cgroup=membership,
                  memory_events_before=(cgroup / "memory.events").read_text(),
                  sdk_commit=args.commit, upstream_commit=UPSTREAM, upstream_files=FILES,
                  commands=[], routes={})
    report["external_files"] = {str(path.resolve()): sha(path) if path.is_file() else None
                                for path in (args.site_profile, args.sysroots, args.vm)
                                if path is not None}

    def save():
        (out / "results.json").write_text(json.dumps(report, indent=2) + "\n")

    def run(label, argv, environ=env, timeout=120):
        command = list(map(str, argv))
        try:
            result = subprocess.run(command, cwd=out, env=environ, check=False,
                                    capture_output=True, timeout=timeout)
            status, stdout, stderr = result.returncode, result.stdout, result.stderr
        except subprocess.TimeoutExpired as error:
            status, stdout, stderr = None, error.stdout or b"", error.stderr or b""
        (out / (label + ".stdout")).write_bytes(stdout)
        (out / (label + ".stderr")).write_bytes(stderr)
        report["commands"].append(
            dict(name=label, argv=command, status=status, stdout_sha256=hashlib.sha256(stdout).hexdigest(),
                 stderr_sha256=hashlib.sha256(stderr).hexdigest()))
        save()
        print(label, status, flush=True)
        return status

    inputs(source, args.fetch)
    for unit in UNITS:
        fypp_env = env if args.fypp_module_dir is None else dict(
            env, PYTHONPATH=str(args.fypp_module_dir.resolve()))
        if run("fypp-" + unit, [sys.executable, fypp, "-D", "PROJECT_VERSION_MAJOR=0",
                                "-D", "PROJECT_VERSION_MINOR=8", "-D", "PROJECT_VERSION_PATCH=1",
                                "-I", source, source / (unit + ".fypp"), out / (unit + ".f90")],
               fypp_env) != 0:
            return 1
    boundary = out / "stdlib_error.f90"
    boundary.write_text(
        "module stdlib_error\nimplicit none\ncontains\nsubroutine check(ok,message)\n"
        "logical,intent(in)::ok\ncharacter(len=*),intent(in)::message\n"
        "if (.not. ok) error stop 75\nend subroutine\nend module\n")
    checks = out / "checks.f90"
    report["assertions"] = adapt_tests((out / "test_trapz.f90").read_text(), checks)
    build = [out / "stdlib_kinds.f90", boundary, out / "stdlib_quadrature.f90",
             out / "stdlib_quadrature_trapz.f90", checks]
    report["inputs"] = {str(p): sha(p) for p in (Path(__file__), native, fypp, *build)}
    native_guest = out / "native-checks"
    if run("native-version", [native, "--version"]) != 0:
        return 1
    if run("native-compile", [native, *args.native_arg, "-O3", "-g", *build, "-o", native_guest]) != 0:
        return 1
    if run("native-assertions", [native_guest]) != 0:
        return 1
    report["routes"]["native"] = {"status": "passed", "assertions": len(report["assertions"])}
    report["inputs"][str(native_guest)] = sha(native_guest)
    save()

    guest_sources, failure, negative = build, None, None
    if args.guest_assertion_traps:
        guest_sources, failure, negative = guest_assertions(build, out)
        report["inputs"].update({str(p): sha(p) for p in (*guest_sources, failure, negative)})

    for route in ("strict", "plain"):
        selected = args.site_profile is not None if route == "strict" else args.plain
        status = {"status": "unrequested"}
        report["routes"][route] = status
        if not selected:
            continue
        status.update(status="blocked", phase="install")
        install = [sys.executable, "-I", "-B", repo / "install/bootstrap.py", "install",
                   "--commit", args.commit, "--local-repository", repo, "--platform", "unitree",
                   "--language", "fortran", "--prefix", out / (route + "-sdk")]
        if route == "strict":
            install += ["--site-profile", args.site_profile.resolve()]
        if run(route + "-install", install) != 0:
            continue
        sdk = Path(json.loads((out / (route + "-install.stdout")).read_bytes())["directory"])
        vm = args.vm.resolve()
        image = out / (route + ".wasm")
        flags = ["--target", "wasm32", "-O3", "-g", "--build-receipt"]
        runtime_flags = ["--wasm-feature-wasm3"]
        if route == "plain":
            flags += ["--toolchain", args.toolchain.resolve(), "--sysroots", args.sysroots.resolve(),
                      "--no-mte", "--no-eh"]
        else:
            runtime_flags += ["--runtime-memtag-mode", "sync"]
        link = []
        if failure:
            obj = out / (route + "-guest-failure.o")
            status.update(phase="fixture-compile")
            cc_flags = [flag for flag in flags if flag != "--build-receipt"]
            if run(route + "-fixture-compile", [sdk / "bin/wrc", *cc_flags, "-c", failure, "-o", obj]) != 0:
                continue
            link = ["--link-object", obj]
        status.update(phase="compile")
        if run(route + "-compile", [sdk / "bin/wrf", *flags, *link, *guest_sources, "-o", image]) != 0:
            continue
        receipt = Path(str(image) + ".wros-build.json")
        report["inputs"].update({str(p): sha(p) for p in (image, receipt, vm)})
        mode = json.loads(receipt.read_bytes())
        if mode["mode"] != ("strict" if route == "strict" else "off"):
            raise ValueError("unexpected guest build policy")
        if route == "strict":
            status.update(phase="artifact-admission")
            if run("strict-artifact-admission",
                   [sys.executable, sdk / "install/qualification.py", "--artifact", image, "--receipt", receipt,
                    "--vm", vm, "--approved-receipt-sha256", sha(receipt)]) != 0:
                continue
        for engine in ("int", "aot"):
            status.update(phase=engine)
            if run(route + "-" + engine, [vm, *runtime_flags, "--runtime-" + engine,
                   "--runtime-compile-threads", "0", "--runtime-llvm-jit-cache-path", "disable",
                   "--run", image]) != 0:
                break
        else:
            status.update(status="passed", assertions=len(report["assertions"]))
            del status["phase"]
        if negative and status["status"] == "passed":
            from importlib.util import module_from_spec, spec_from_file_location

            spec = spec_from_file_location("wros_imports", sdk / "install/imports.py")
            imports = module_from_spec(spec)
            spec.loader.exec_module(imports)
            if imports.inspect(image.read_bytes()):
                raise ValueError("expected an import-free numerical guest")
            status["guest_imports"] = []
            neg_image = out / (route + "-negative.wasm")
            status.update(status="blocked", phase="negative-compile")
            if run(route + "-negative-compile", [sdk / "bin/wrf", *flags, *link,
                                              *guest_sources[:-1], negative, "-o", neg_image]) != 0:
                continue
            neg_receipt = Path(str(neg_image) + ".wros-build.json")
            report["inputs"].update({str(p): sha(p) for p in (neg_image, neg_receipt)})
            if mode["mode"] == "strict":
                status.update(phase="negative-artifact-admission")
                if run("strict-negative-artifact-admission",
                       [sys.executable, sdk / "install/qualification.py", "--artifact", neg_image,
                        "--receipt", neg_receipt, "--vm", vm, "--approved-receipt-sha256", sha(neg_receipt)]) != 0:
                    continue
            for engine in ("int", "aot"):
                label = route + "-negative-" + engine
                status.update(phase=label)
                code = run(label, [vm, *runtime_flags, "--runtime-" + engine,
                                   "--runtime-compile-threads", "0", "--runtime-llvm-jit-cache-path",
                                   "disable", "--run", neg_image])
                if not code or b"unreachable" not in (out / (label + ".stderr")).read_bytes():
                    break
            else:
                status.update(status="passed", false_assertion_traps=2)
                del status["phase"]
        save()
    report["memory_events_after"] = (cgroup / "memory.events").read_text()
    report["complete"] = all(row["status"] != "blocked" for row in report["routes"].values())
    save()
    return 0 if report["complete"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
