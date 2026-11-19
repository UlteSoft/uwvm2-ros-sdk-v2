"""Evaluate Go source lines through real Wasm, the secure VM broker and DAP."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys
from textwrap import dedent


def main():
    """@brief Compare two real DAP stops with the compiler's mapped Wasm locations."""
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("sdk", "vm-source", "vm", "output"):
        parser.add_argument("--" + name, type=Path, required=True)
    args = parser.parse_args()
    repo, sdk, vm, out = (path.resolve() for path in
                         (args.vm_source, args.sdk, args.vm, args.output))
    if ".tmp" not in out.parts:
        parser.error("choose a fresh output within a test .tmp directory")
    sys.path[:0] = [str(repo/"test/0084.ros-runtime"), str(repo/"test/0018.debugger"), str(repo/"test/0017.runtime")]
    from run_scene_vm import verify_gate

    verify_gate()
    from run_dap_current_broker import BrokerSession, actual_location
    from run_debug_source_inline_metadata_cli import sections, u32
    from run_debug_source_map_v3_oracle_cli import original_rows

    out.mkdir(mode=0o700)
    source = out/"logic.go"
    source.write_text(dedent("""\
        package robot
        func Start(abi uint32) uint32 {
            adjusted := abi * 7
            if adjusted != 14 {
                return adjusted
            }
            return adjusted - 14
        }
        """))
    wasm = out/"logic.wasm"
    subprocess.run([sdk/"bin/wrgo", source, "-g", "--ros-abi", "--build-receipt", "-o", wasm],
                   check=True, timeout=90)
    subprocess.run(["/usr/bin/wasm-validate", wasm], check=True, timeout=30)
    blob = wasm.read_bytes()
    cursor = 8
    code_begin = code_size = 0
    while cursor < len(blob):
        kind = blob[cursor]
        size, begin = u32(blob, cursor + 1, len(blob))
        if kind == 10:
            code_begin, code_size = begin, size
            break
        cursor = begin + size
    assert code_begin and code_size
    image_sections = sections(wasm)
    for kind, payload in image_sections:
        if kind != 0:
            continue
        size, start = u32(payload, 0, len(payload))
        if payload[start:start+size] == b".debug_source_map":
            source_map = json.loads(payload[start+size:])
            break
    else:
        raise AssertionError("Go compiler source map missing")
    assert source_map["sources"] == [str(source)]
    rows = original_rows(source_map, code_begin, code_size, len(blob))
    assert {row[3] for row in rows} >= {3, 4, 7}, rows

    assert [p for k, p in image_sections if k == 2] == [b"\x01\x0buwvm_ros_v2\x03abi\x00\x00"]
    code, = [p for k, p in image_sections if k == 10]
    count, at = u32(code, 0, len(code))
    expressions = {}
    for index in range(1, count + 1):
        size, body = u32(code, at, len(code))
        end = body + size
        assert end <= len(code)
        groups, expression = u32(code, body, end)
        for _ in range(groups):
            _, expression = u32(code, expression, end)
            assert code[expression] in (0x7f, 0x7e)
            expression += 1
        assert expression < end
        expressions[index] = expression
        at = end
    assert at == len(code)

    argv = ["--runtime-debug", "--debug-permissions", "full", "--runtime-compile-threads", "0",
            "--runtime-llvm-jit-cache-path", "disable", "--ros-scene-create", "robot",
            "--wasm-set-main-module-name", "main", "--ros-scene-bind", "robot", "main",
            "--ros-scene-interface", "robot", "abi", "allow", "--run", str(wasm)]
    result = dict(passed=False, actions=[], cgroup=Path("/proc/self/cgroup").read_text().strip(),
                  inputs={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in [vm, wasm, source]},
                  rows=rows)
    server = BrokerSession(vm, repo/"tools/debug/secure_server.py", repo/"tools/debug/dap_adapter.py", argv, out)
    try:
        client = server.connect("source")
        started = client.evaluate("status")
        assert b"prepared; no Wasm instruction executed" in started, started
        requests = {"source": {"path": str(source)}, "breakpoints": [{"line": 3}]}
        bp = client.request("setBreakpoints", requests)["body"]["breakpoints"]
        result["breakpoints"] = bp
        assert bp[0]["verified"] and bp[0]["line"] == 3, bp
        client.evaluate("continue")
        assert b"stopped: breakpoint" in client.evaluate("wait")

        def current():
            state = actual_location(client)
            pc = expressions[state["function"]] + state["offset"]
            from_map = [row for row in rows if row[0] <= pc < row[1]]
            assert len(from_map) == 1, (from_map, state)
            top = client.request("stackTrace", {"threadId": state["thread"]})["body"]["stackFrames"][0]
            assert top["source"]["path"] == str(source) and top["line"] == from_map[0][3], (from_map, top)
            assert top["column"] == from_map[0][4], (from_map, top)
            result["actions"].append(dict(state=state, frame=top, map_row=from_map[0]))
            return state, top

        state, top = current()
        assert (top["line"], top["column"], top["name"]) == (3, 21, "Start"), top
        client.request("setBreakpoints", {"source": requests["source"], "breakpoints": []})
        client.request("next", {"threadId": state["thread"]})
        next_state, next_frame = current()
        assert next_state["stop"] > state["stop"]
        assert (next_frame["line"], next_frame["column"], next_frame["name"]) == (4, 17, "Start")
        client.evaluate("continue")
        for _ in range(10):
            if any(p.get("event") == "exited" for p in client.events):
                break
            client.absorb(client.next_message())
        assert any(p.get("event") == "exited" and p.get("body", {}).get("exitCode") == 0 for p in client.events)
        result["passed"] = True
    finally:
        try:
            result["cleanup"] = server.close()
        except BaseException:
            result["passed"] = False
            raise
        finally:
            (out/"results.json").write_text(json.dumps(result, indent=2) + "\n")


if __name__ == "__main__":
    main()
