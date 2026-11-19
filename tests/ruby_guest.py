"""@file ruby_guest.py
@brief Exercise the installed mruby compiler and a real VM in both execution engines.
"""
import argparse
import json
from pathlib import Path
import subprocess
import sys

from separate_compilation import Profile, ROOT, cgroup_record, inspect, sha


def main():
    """@brief Check imports, Ruby allocation identities and exception propagation."""
    parser = argparse.ArgumentParser(description=__doc__)
    for path in ("sdk", "vm", "output"):
        parser.add_argument("--" + path, required=True, type=Path)
    parser.add_argument("--bits", type=int, choices=(32, 64), default=32)
    a = parser.parse_args()
    group = cgroup_record()
    out = a.output.resolve()
    out.mkdir(parents=True, exist_ok=False)
    source = out / "application.rb"
    source.write_text(
        f"shift = {28 if a.bits == 32 else 56}\n"
        f"palette = {(1 << (4 if a.bits == 32 else 8)) - 1}\n"
        """
mask = (1 << shift) - 1
objects = (0...512).map { Object.new }
checked = 0
4.times do |epoch|
  ordered = objects.map do |obj|
    id = obj.object_id
    [id & mask, (id >> shift) & palette]
  end.sort { |left, right| left[0] <=> right[0] }
  raise "untagged object" unless ordered.all? { |pair| pair[1] != 0 }
  (1...ordered.length).each do |i|
    left, right = ordered[i - 1], ordered[i]
    raise "overlapping objects" if left[0] == right[0]
    if right[0] - left[0] <= 96
      raise "equal nearby colors" if left[1] == right[1]
      checked += 1
    end
  end
  objects.length.times { |i| objects[i] = nil if i % 2 == epoch % 2 }
  GC.start
  objects.length.times { |i| objects[i] = Object.new if i % 2 == epoch % 2 }
end
raise "insufficient comparison pairs" unless checked >= 128
raise "unexpected ROS ABI" unless WROS.abi == 2
""")
    rejected = out / "exception.rb"
    rejected.write_text("raise 'intentional guest error'\n")
    prefix = [sys.executable, "-B", a.sdk.resolve() / "bin/wrrb", "--target", "wasm" + str(a.bits),
              "--build-receipt"]
    result = dict(complete=False, cgroup=group, vm_sha256=sha(a.vm), width=a.bits, cases=[], modules={})

    def run(label, argv, error=None):
        """@brief Preserve exact exit status and independently match the expected failure."""
        process = subprocess.run(list(map(str, argv)), capture_output=True, timeout=240)
        log = out / (label + ".log")
        log.write_bytes(process.stdout + process.stderr)
        result["cases"].append(dict(name=label, exit=process.returncode, log_sha256=sha(log)))
        (out / "results.json").write_text(json.dumps(result, indent=2) + "\n")
        if (error is None and process.returncode != 0
                or error is not None and (process.returncode == 0 or error not in process.stderr)):
            raise RuntimeError(label + ": " + process.stderr[-1600:].decode(errors="replace"))

    app = out / "application.wasm"
    fail = out / "exception.wasm"
    catalog = json.loads((ROOT / "share/abi/ros.json").read_bytes())["operations"]
    all_ops = out / "catalog.wasm"
    run("compile-application", [*prefix, source, "--ros-abi", "-o", app])
    run("compile-exception", [*prefix, rejected, "-o", fail])
    switches = [value for row in catalog for value in ("--ros-operation", row["name"])]
    run("compile-interface-catalogue", [*prefix, rejected, *switches, "-o", all_ops])
    for wasm, names in ((app, {"abi"}), (fail, set()), (all_ops, {row["name"] for row in catalog})):
        assert sorted((r["module"], r["name"]) for r in inspect(wasm.read_bytes())) == [
            ("uwvm_ros_v2", n) for n in sorted(names)
        ]
        proof = json.loads(wasm.with_suffix(".wasm.wros-build.json").read_bytes())
        assert proof["mode"] == "strict" and proof["artifact_sha256"] == sha(wasm)
        result["modules"][wasm.name] = sha(wasm)
    abi = ["--ros-scene-create", "robot", "--ros-scene-bind", "robot", "main",
           "--ros-scene-interface", "robot", "abi", "allow"]
    for engine in ("int", "aot"):
        vm = [a.vm.resolve(), *Profile(a.bits).uwvm_feature_flags(), "--wasm-set-main-module-name", "main",
              "--runtime-" + engine, "--runtime-compile-threads", "3", "--runtime-llvm-jit-full-policy",
              "legacy-light", "--runtime-llvm-jit-cache-path", "disable", "--runtime-memtag-mode", "sync",
              "--debug-fault-action", "exit"]
        run(engine + "-checked-allocations", [*vm, *abi, "--run", app])
        run(engine + "-hidden-import", [*vm, "--run", app], b"ROS scene interface is hidden")
        run(engine + "-exception", [*vm, "--run", fail], b"unreachable")
    result["complete"] = True
    (out / "results.json").write_text(json.dumps(result, indent=2) + "\n")


if __name__ == "__main__":
    main()
