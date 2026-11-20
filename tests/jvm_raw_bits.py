"""@file jvm_raw_bits.py
@brief Check the signed JVM raw float/double admission and exact runtime bits.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys

from separate_compilation import cgroup_record

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "install"))
from imports import inspect
from upstream_jvm_libraries import pinned_sources


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for key in ("repository", "site", "vm", "output"):
        parser.add_argument("--" + key, required=True, type=lambda path: Path(path).resolve())
    parser.add_argument("--commit", required=True)
    parser.add_argument("--sources", type=Path)
    args = parser.parse_args()
    out = args.output
    cgroup = cgroup_record()
    out.mkdir(mode=0o700)
    env = {key: value for key, value in os.environ.items() if not key.startswith(("WROS_", "UWVM_", "XMAKE_"))}
    env.update(PATH="/usr/bin:/bin", WROS_VM=str(args.vm), TMPDIR=str(out), PYTHONDONTWRITEBYTECODE="1")
    report = dict(complete=False, commit=args.commit, steps={}, cgroup=cgroup,
                  raw_cases=dict(float=11, double=11),
                  vm_sha256=hashlib.sha256(args.vm.read_bytes()).hexdigest())

    def save():
        (out / "results.json").write_text(json.dumps(report, indent=2) + "\n")

    def run(name, command, *, denial=None, environment=env):
        argv = list(map(str, command))
        result = subprocess.run(argv, cwd=out, env=environment, capture_output=True, timeout=350)
        log = result.stdout + result.stderr
        (out / (name + ".log")).write_bytes(log)
        passed = result.returncode == 0 if denial is None else result.returncode != 0 and denial in log
        report["steps"][name] = dict(exit=result.returncode, expected_denial=denial is not None,
                                     passed=passed, log_sha256=hashlib.sha256(log).hexdigest())
        save()
        if not passed:
            raise RuntimeError(name + ": " + log[-2200:].decode(errors="replace"))
        print(name, "passed", flush=True)
        return result.stdout

    report["sources"] = pinned_sources(args.sources, out / "sources", ("fastutil/HashCommon.java",))
    installation = json.loads(run("install", [
        sys.executable, "-I", "-B", ROOT / "install/bootstrap.py", "install",
        "--commit", args.commit, "--local-repository", args.repository, "--platform", "unitree",
        "--language", "java", "--prefix", out / "sdk", "--site-profile", args.site,
    ]))
    sdk = Path(installation["directory"])
    toolchain = Path(json.loads(args.site.read_bytes())["toolchain"])
    bundle = (toolchain / "libexec/wros/jvm/java").resolve(strict=True)
    native_env = env | {"LD_LIBRARY_PATH": os.pathsep.join(str(bundle / name) for name in
        ("lib/host-runtime", "jdk21/lib/server", "jdk21/lib"))}
    native = out / "native"
    native.mkdir()
    fixture = ROOT / "tests/jvm_raw_bits/RawBits.java"
    report["fixture_sha256"] = hashlib.sha256(fixture.read_bytes()).hexdigest()
    java = [bundle / "jdk21/bin/java", "-Xint", "-XX:-CreateCoredumpOnCrash"]
    run("native-javac", [*java, "-m", "jdk.compiler/com.sun.tools.javac.Main", "-proc:none", "-g",
                        "-d", native, fixture], environment=native_env)
    run("native-run", [*java, "-cp", native, "example.RawBits"], environment=native_env)

    guest = out / "raw.wasm"
    wrjava = sdk / "bin/wrjava"
    run("wasm-build", [wrjava, "--main-class", "example.RawBits", fixture,
                      "--work", out / "compiler", "-o", guest])
    product = guest.read_bytes()
    if inspect(product):
        raise ValueError("the raw-bit guest requires no host imports")
    report["guest_sha256"] = hashlib.sha256(product).hexdigest()
    run("wasm-disassembly", [toolchain / "bin/llvm-objdump", "-d", guest])
    runner = [sys.executable, "-B", sdk / "tools/xmake/run_guest.py", guest, "wasm32", "3.0", "single",
              "--exceptions", "eh", "--check-tags"]
    for engine in ("int", "aot"):
        run("wasm-" + engine, [*runner, "--engine", engine])

    for owner, method, signature, value in (
        ("Float", "floatToIntBits", "(F)I", "0.0f"), ("Double", "doubleToLongBits", "(D)J", "0.0")
    ):
        source = out / "Reject.java"
        source.write_text("public class Reject { public static void main(String[] args) { "
                          + owner + "." + method + "(" + value + "); } }\n")
        denied = f"unsupported synchronous JVM feature: java/lang/{owner}.{method}{signature}".encode()
        run("deny-" + owner, [wrjava, "--main-class", "Reject", source, "-o", out / "rejected.wasm"], denial=denied)
        if (out / "rejected.wasm").exists():
            raise ValueError("denied code produced a Wasm file")

    original = out / "sources/fastutil/HashCommon.java"
    probe = out / "Probe.java"
    probe.write_text("""import it.unimi.dsi.fastutil.HashCommon;
public class Probe {
    public static void main(String[] args) {
        if (HashCommon.float2int(-0.0f) != 0x80000000 || HashCommon.double2int(-0.0) != 0x80000000)
            throw new AssertionError();
    }
}
""")
    # The release checks every method of the unmodified class. Its other
    # JDK dependencies remain outside the synchronous producer contract.
    run("deny-full-fastutil", [wrjava, "--main-class", "Probe", original, probe, "-o", out / "full.wasm"],
        denial=b"unsupported synchronous JVM feature: java/lang/Integer.numberOfLeadingZeros(I)I")
    report["complete"] = True
    save()


if __name__ == "__main__":
    main()
