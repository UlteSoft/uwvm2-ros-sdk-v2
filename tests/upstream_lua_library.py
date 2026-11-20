"""@file upstream_lua_library.py
@brief Replay the pinned json.lua suite in the installed Wasm Lua interpreter.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import resource
import subprocess
import sys

REVISION = "d1e3b0f5d0f3d3493c7dadd0bb54135507fcebd7"
INPUTS = {
    "json.lua": "b13df59b32c77db3bec7a1619280ea77ee5014e715ccffaa4876d857e3e9ab87",
    "test/test.lua": "8995a30213d9755043318593416d559615d5950fbb4bff24a255f1431f85770d",
}


def digest(data):
    """@brief Identify the exact tested input bytes."""
    return hashlib.sha256(data).hexdigest()


def pinned_source(root, name):
    """@brief Load only the expected bounded upstream file."""
    with (root / name).open("rb") as stream:
        data = stream.read(32769)
    if len(data) > 32768 or digest(data) != INPUTS[name]:
        raise ValueError(f"unexpected upstream input: {name}")
    return data.decode("utf-8")


def application(source, tests):
    """@brief Replace the file loader and pass/fail reports with an in-guest test runner."""
    end = tests.index("\n\nlocal function equal")
    if not tests.startswith('\nlocal json = loadfile("../json.lua")()\n'):
        raise ValueError("unexpected original harness")
    return "\n".join((r"""
local json = (function()
""", source, r"""
end)()
local fmt = string.format
local check = assert
local groups, assertions = 0, 0
local function assert(value, message)
  check(value, message)
  assertions = assertions + 1
  return value
end
local function test(name, func)
  local success, failure = pcall(func)
  check(success, name .. ": " .. tostring(failure))
  groups = groups + 1
end
""", tests[end:], "check(groups == 14 and assertions == 74)\n"))


def main():
    """@brief Verify the native reference and execute both VM engines with an empty import table."""
    parser = argparse.ArgumentParser(description=__doc__)
    for key in ("sdk", "source", "site", "vm", "output"):
        parser.add_argument("--" + key, type=Path, required=True)
    parser.add_argument("--commit", required=True)
    args = parser.parse_args()
    sdk, root, site, vm, output = (p.resolve() for p in
                                     (args.sdk, args.source, args.site, args.vm, args.output))
    sys.path.insert(0, str(sdk / "tests"))
    from separate_compilation import Profile, cgroup_record, inspect, sha

    state = dict(complete=False, upstream_commit=REVISION, sdk_commit=args.commit, input_sha256=INPUTS,
                 cgroup=cgroup_record(), vm_sha256=sha(vm), site_sha256=sha(site), cases=[])
    resource.setrlimit(resource.RLIMIT_CORE, (0, 0))
    output.mkdir(parents=True, exist_ok=False)
    env = {key: value for key, value in os.environ.items()
           if not key.startswith(("UWVM_", "WROS_", "LUA_", "XMAKE_"))}
    env.update(PATH="/usr/bin:/bin", TMPDIR=str(output), LC_ALL="C")

    def run(label, argv, cwd=output):
        log = output / (label + ".log")
        with log.open("xb") as stream:
            process = subprocess.run(list(map(str, argv)), cwd=cwd, env=env, stdout=stream,
                                     stderr=subprocess.STDOUT, timeout=300)
        state["cases"].append(dict(name=label, exit=process.returncode, log_sha256=sha(log)))
        (output / "results.json").write_text(json.dumps(state, indent=2) + "\n")
        process.check_returncode()
        return log.read_text()

    source = pinned_source(root, "json.lua")
    tests = pinned_source(root, "test/test.lua")
    original = run("native-original", ["/usr/bin/lua5.4", "test.lua"], root / "test")
    seen = re.findall(r"^\[pass\] (.+)$", original, re.MULTILINE)
    expected = re.findall(r'^test\("([^"]+)", function\(\)', tests, re.MULTILINE)
    if len(expected) != 14 or seen != expected or "[fail]" in original:
        raise ValueError("native upstream suite did not pass every active test")
    program = output / "json-suite.lua"
    program.write_text(application(source, tests))
    run("native-adapted", ["/usr/bin/lua5.4", program])

    result = run("install", [sys.executable, "-I", "-B", sdk / "install/bootstrap.py", "install",
                              "--local-repository", sdk, "--commit", args.commit, "--platform", "unitree",
                              "--language", "lua", "--prefix", output / "installed",
                              "--site-profile", site, "--", "--component", "development"])
    installation = json.loads(result)
    if installation["commit"] != args.commit:
        raise ValueError("unexpected installed revision")
    frontend = Path(installation["directory"]) / "bin/wrlua"
    app = output / "json-suite.wasm"
    run("wrlua", [frontend, "--guest-seed", "7", program, "-o", app, "--build-receipt"])
    imports = inspect(app.read_bytes())
    receipt = json.loads(app.with_suffix(".wasm.wros-build.json").read_text())
    if (imports or receipt["mode"] != "strict" or receipt["vm_sha256"] != state["vm_sha256"]
            or receipt["settings"] != {"optimization": "3", "debug": True}
            or not receipt["profile"]["mte"] or receipt["profile"]["threads"]):
        raise ValueError("unexpected SDK build profile or host imports")
    state.update(groups=seen, assertions=74, wasm_sha256=sha(app), build=receipt, imports=imports)
    for engine in ("int", "aot"):
        run(engine, [vm, *Profile(32, mte=True, exceptions="eh").uwvm_feature_flags(), "--runtime-" + engine,
                     "--runtime-compile-threads", "0", "--runtime-llvm-jit-cache-path", "disable", "--run", app])
    for name in INPUTS:
        pinned_source(root, name)
    state["complete"] = True
    (output / "results.json").write_text(json.dumps(state, indent=2) + "\n")


if __name__ == "__main__":
    main()
