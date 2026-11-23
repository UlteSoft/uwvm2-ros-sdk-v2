"""Exercise every emitted import and both capability paths under INT and AOT."""
import hashlib
import json
import os
from pathlib import Path
import shlex
import subprocess

WORK = Path("/work")
OUT = WORK / "out"
TABLES = json.loads((OUT / "import-tables.json").read_text())
VM = Path(os.environ["WROS_VM"])
CONTRACT = json.loads((WORK / "src/abi/contract.json").read_text())
REPORT = {
    "binding_commit": (WORK / "binding-commit").read_text().strip(),
    "contract_sha256": hashlib.sha256((WORK / "src/abi/contract.json").read_bytes()).hexdigest(),
    "vm_sha256": hashlib.file_digest(VM.open("rb"), "sha256").hexdigest(),
    "cases": [],
}
logs = OUT / "runtime"
logs.mkdir(exist_ok=True)
BIND_SCENE = ["--ros-scene-create", "robot", "--ros-scene-bind", "robot", "main"]


def expose(names, state):
    return [flag for name in names for flag in ["--ros-scene-interface", "robot", name, state]]


def grant(alias, actions):
    return ["--ros-scene-grant", "robot", alias, "guard", alias, "local", ",".join(actions)]


def run(lang, engine, mode, guest, flags, success=True, diagnostic=None):
    name = f"{lang}-{engine}-{mode}"
    stdout = logs / (name + ".stdout")
    stderr = logs / (name + ".stderr")
    wasm = OUT / lang / (guest + ".wasm")
    argv = [str(VM), "--runtime-" + engine, "--wasm-set-main-module-name", "main", *flags,
            "--run", str(wasm)]
    print(shlex.join(argv), flush=True)
    with stdout.open("wb") as out, stderr.open("wb") as err:
        result = subprocess.run(argv, stdout=out, stderr=err, timeout=45)
    actual_stderr = stderr.read_text(errors="replace")
    passed = (result.returncode == 0) == success and (diagnostic is None or diagnostic in actual_stderr)
    REPORT["cases"].append({
        "name": name,
        "expected_return": "0" if success else "nonzero",
        "expected_diagnostic": diagnostic,
        "returncode": result.returncode,
        "passed": passed,
        "guest_sha256": TABLES[lang][guest]["sha256"],
        "argv": argv,
        "stdout": str(stdout.relative_to(WORK)),
        "stderr": str(stderr.relative_to(WORK)),
    })
    (OUT / "runtime-results.json").write_text(json.dumps(REPORT, indent=2) + "\n")
    print(f"{'PASS' if passed else 'FAIL'} {name} exit={result.returncode}", flush=True)
    if not passed:
        print(actual_stderr[-3500:], flush=True)


def main():
    all_ops = [op["name"] for op in CONTRACT["operations"]]
    for lang, table in TABLES.items():
        guard_names = [entry["name"] for entry in table["guard"]["imports"]]
        full_grant = grant("signal", ["guard.create", "guard.trigger", "guard.take", "resource.close"])
        narrow_grant = grant("narrow", ["guard.create", "resource.close"])
        index = str(table["abi"]["entry_local_index"])
        for engine in ("int", "aot"):
            run(lang, engine, "abi-allow-returns-2", "abi", [
                *BIND_SCENE, *expose(["abi"], "allow"), "--wasm-set-start-func", index, "2",
            ])
            run(lang, engine, "abi-deny-returns-13", "abi", [
                *BIND_SCENE, *expose(["abi"], "deny"), "--wasm-set-start-func", index, "13",
            ])
            run(lang, engine, "abi-default-hidden", "abi", [
                "--wasm-set-start-func", index, "2",
            ], success=False, diagnostic="scene interface is hidden")
            run(lang, engine, "typed-guard-and-capability", "guard", [
                *BIND_SCENE, *expose(guard_names, "allow"), *full_grant, *narrow_grant,
            ])
            run(lang, engine, "all-163-deny-returns-13", "all", [
                *BIND_SCENE, *expose(all_ops, "deny"),
            ])
    assert all(case["passed"] for case in REPORT["cases"])


if __name__ == "__main__":
    main()
