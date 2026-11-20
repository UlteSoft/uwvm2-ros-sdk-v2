"""@file upstream_jvm_libraries.py
@brief Replay pinned fastutil and Kotlin stdlib cases using signed SDK installations.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys
from urllib.request import urlopen

from separate_compilation import cgroup_record

ROOT = Path(__file__).resolve().parents[1]
FASTUTIL = "vigna/fastutil/aa30fa7d93bf06fec45c4f6f572a1f6a38047d9f"
KOTLIN = "JetBrains/kotlin/658a2010b15a22583f9841e1a2d4bddf1baac612"
SOURCES = {
    "fastutil/HashCommon.java": (
        FASTUTIL + "/src/it/unimi/dsi/fastutil/HashCommon.java",
        "8a9970601485fdfa9421af6d1367aa4e011b3798f66b72ebe2879c8b538b6761",
    ),
    "fastutil/HashCommonTest.java": (
        FASTUTIL + "/test/it/unimi/dsi/fastutil/HashCommonTest.java",
        "27a83c85f979a422fe645d7e7b19bf285dacada75405d9c67049c37d3dca9a4e",
    ),
    "kotlin/_Ranges.kt": (
        KOTLIN + "/libraries/stdlib/common/src/generated/_Ranges.kt",
        "030fde4cb2506aca1a721a386d307f9031ecc6282b80d0740ebc0f1d5bb2b659",
    ),
    "kotlin/CoercionTest.kt": (
        KOTLIN + "/libraries/stdlib/test/ranges/CoercionTest.kt",
        "5467f54fb64961fcbac456b53133288276cd5a5230064a1ad50541e5c2ddcda9",
    ),
}
BYTE_LIMIT = 256 * 1024
ABI = [{"module": "uwvm_ros_v2", "name": "abi", "kind": 0, "params": [], "results": ["i32"]}]


def pinned_sources(cache, out, names=SOURCES):
    """Stage exact files. A caller-supplied cache undergoes the same digest verification."""
    sources = {}
    for name in names:
        location, digest = SOURCES[name]
        url = "https://raw.githubusercontent.com/" + location
        if cache:
            with (cache / name).open("rb") as file:
                data = file.read(BYTE_LIMIT + 1)
        else:
            with urlopen(url, timeout=30) as response:
                data = response.read(BYTE_LIMIT + 1)
        if len(data) > BYTE_LIMIT or hashlib.sha256(data).hexdigest() != digest:
            raise ValueError("unexpected pinned source bytes: " + name)
        path = out / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)
        sources[name] = dict(url=url, sha256=digest)
    return sources


def java_sources(upstream):
    """Keep the hash functions and inverse test body verbatim with a local assertion adapter."""
    original = (upstream / "fastutil/HashCommon.java").read_text()
    tests = (upstream / "fastutil/HashCommonTest.java").read_text()
    prefix = original[:original.index("/** Common code for all hash-based classes. */")]
    constants = re.findall(
        r"^\s*private static final (?:int|long) (?:INV_)?(?:INT|LONG)_PHI [^;]+;", original, re.MULTILINE
    )
    methods = re.findall(
        r"^\s*public static (?:int|long) (?:invMix|mix)\([^\n]+\{[\s\S]*?^\s*\}", original, re.MULTILINE
    )
    if len(constants) != 4 or len(methods) != 4:
        raise ValueError("the pinned fastutil declarations differ")
    body = re.search(r"\tpublic void testInverses\(\) \{[\s\S]+?^\t\}", tests, re.MULTILINE)
    if not body:
        raise ValueError("the pinned fastutil test body differs")
    test_header = tests[:tests.index("\t@Test")].replace("import org.junit.Test;\n", "").replace(
        "import static org.junit.Assert.assertTrue;\n", ""
    )
    return {
        "HashCommon.java": prefix + "public class HashCommon {\n" + "\n".join(constants + methods) + "\n}\n",
        "HashCommonTest.java": test_header + body[0] + "\n}\n",
        "Assert.java": """package org.junit;
public final class Assert {
    public static void assertEquals(long expected, long actual) {
        if (expected != actual) throw new AssertionError();
    }
}
""",
        "Main.java": """package example;
import it.unimi.dsi.fastutil.HashCommonTest;
import wros.scene.Scene;
public final class Main {
    public static void main(String[] args) {
        if (Scene.abi() != 2) throw new AssertionError();
        new HashCommonTest().testInverses();
    }
}
""",
    }


def kotlin_sources(upstream):
    """Relocate six primitive stdlib methods and replay their upstream expectations."""
    ranges = (upstream / "kotlin/_Ranges.kt").read_text()
    tests = (upstream / "kotlin/CoercionTest.kt").read_text()
    prefix = tests[:tests.index("package ")]
    methods = re.findall(
        r"^public fun (?:Int|Long|Double)\.coerceAt(?:Least|Most)\([^\n]+\{[\s\S]*?^\}", ranges, re.MULTILINE
    )
    checks = re.findall(
        r"^        expect\(((?:1|5)(?:L|\.0)?)\) \{ ((?:1|5)(?:L|\.0)?\.coerceAt(?:Least|Most)\((?:1|5)(?:L|\.0)?\)) \}",
        tests, re.MULTILINE,
    )
    if len(methods) != 6 or len(checks) != 12:
        raise ValueError("the pinned Kotlin declarations or expectations differ")
    assertions = "\n".join("    check(" + expression + " == " + expected + ")" for expected, expression in checks)
    return {
        "Ranges.kt": prefix + "package example\n\n" + "\n\n".join(methods) + "\n",
        "CoercionTest.kt": prefix + "package example\n\nfun runCoercions() {\n" + assertions + "\n}\n",
        "Main.kt": """@file:JvmName("Main")
package example
import wros.scene.Scene
fun main(args: Array<String>) {
    check(args.isEmpty() && Scene.abi() == 2)
    runCoercions()
}
""",
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--commit", required=True)
    for arg in ("repository", "vm", "xmake", "java-site", "kotlin-site", "output"):
        parser.add_argument("--" + arg, required=True, type=lambda path: Path(path).resolve())
    parser.add_argument("--sources", type=Path, help="use the four digest-checked local files instead of downloading")
    args = parser.parse_args()
    cgroup = cgroup_record()
    out = args.output
    out.mkdir(mode=0o700)
    sys.path.insert(0, str(ROOT / "install"))
    from imports import inspect

    env = {key: value for key, value in os.environ.items() if not key.startswith(("WROS_", "UWVM_", "XMAKE_"))}
    env.update(PATH="/usr/bin:/bin", WROS_VM=str(args.vm), TMPDIR=str(out),
               XMAKE_GLOBALDIR=str(out / "xmake-global"), XMAKE_STATS="false", PYTHONDONTWRITEBYTECODE="1")
    report = dict(complete=False, commit=args.commit, platform="unitree", cgroup=cgroup,
                  profile="wasm32/Core3.0/single/EH/MTE/sync/-O3/-g",
                  vm_sha256=hashlib.sha256(args.vm.read_bytes()).hexdigest(),
                  sources=pinned_sources(args.sources, out / "sources"), steps={}, products={})

    def save():
        temporary = out / "results.part"
        temporary.write_text(json.dumps(report, indent=2) + "\n")
        temporary.replace(out / "results.json")

    def run(name, command, *, cwd=out, denial=None):
        result = subprocess.run(list(map(str, command)), cwd=cwd, env=env, capture_output=True, timeout=350)
        log = result.stdout + result.stderr
        (out / (name + ".log")).write_bytes(log)
        passed = result.returncode == 0 if denial is None else result.returncode != 0 and denial in log
        report["steps"][name] = dict(exit=result.returncode, expected_denial=denial is not None,
                                     passed=passed, log_sha256=hashlib.sha256(log).hexdigest())
        save()
        if not passed:
            raise RuntimeError(name + ": " + log[-1800:].decode(errors="replace"))
        print(name, "passed", flush=True)
        return result.stdout

    def check_wasm(name, wasm, import_rows):
        product = wasm.read_bytes()
        if inspect(product) != import_rows:
            raise ValueError("unexpected guest imports: " + name)
        report["products"][name] = dict(sha256=hashlib.sha256(product).hexdigest(), bytes=len(product), imports=import_rows)
        save()

    def execute(language, compiler, suffix, site, sources):
        selected = json.loads(run(language + "-install", [
            sys.executable, "-I", "-B", ROOT / "install/bootstrap.py", "install",
            "--commit", args.commit, "--local-repository", args.repository, "--platform", "unitree",
            "--language", language, "--prefix", out / "install", "--site-profile", site,
        ]))
        sdk = Path(selected["directory"])
        env["UWVM_ROS_SDK_ROOT"] = str(sdk)
        project = out / language
        project.mkdir()
        files = []
        for name, body in sources.items():
            path = project / name
            path.write_text(body)
            files.append(path)
        guest = project / "direct.wasm"
        run(language + "-direct", [sdk / "bin" / compiler, "--main-class", "example.Main",
            "--ros-operation", "abi", *files, "--work", out / (language + "-compiler"), "-o", guest])
        check_wasm(language + "-direct", guest, ABI)
        direct = [sys.executable, "-B", sdk / "tools/xmake/run_guest.py", guest,
                  "wasm32", "3.0", "single", "--exceptions", "eh", "--check-tags"]
        for engine in ("int", "aot"):
            run(language + "-" + engine + "-allowed", [*direct, "--engine", engine, "--queries", "abi"])
            run(language + "-" + engine + "-hidden", [*direct, "--engine", engine],
                denial=b"ROS scene interface is hidden")
        template = (sdk / "examples/platform/unitree/common" / language / "xmake.lua").read_text()
        needle = 'add_files("Main.' + suffix + '")'
        if needle not in template:
            raise ValueError("installed Xmake example lacks its language source")
        (project / "xmake.lua").write_text(template.replace(needle, 'add_files("*.' + suffix + '")'))
        run(language + "-xmake-configure", [args.xmake, "f", "-c", "-y", "-a", "wasm32"], cwd=project)
        run(language + "-xmake-build", [args.xmake, "build", "-j1", "common"], cwd=project)
        built, = (project / "build").rglob("common.wasm")
        check_wasm(language + "-xmake", built, ABI)
        run(language + "-xmake-test", [args.xmake, "test", "-j1"], cwd=project)

    save()
    execute("java", "wrjava", "java", args.java_site, java_sources(out / "sources"))
    execute("kotlin", "wrkt", "kt", args.kotlin_site, kotlin_sources(out / "sources"))
    report["complete"] = True
    save()


if __name__ == "__main__":
    main()
