"""@file noetic_costmap_ruby.py
@brief Compare the installed Ruby migration example with the pinned Noetic index method.
"""
import argparse
import json
from pathlib import Path
import subprocess
import sys

from noetic_costmap_fortran import HEADER_SHA256, MASK, inputs, write_reference

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from separate_compilation import Profile, cgroup_record, inspect, sha


def main():
    """@brief Execute the original C++ and both VM engines on the same unsigned bit patterns."""
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("sdk", "vm", "noetic-header", "cxx", "output"):
        parser.add_argument("--" + name, type=Path, required=True)
    parser.add_argument("--target", choices=("wasm32", "wasm64"), default="wasm32")
    args = parser.parse_args()
    group = cgroup_record()
    sdk, vm, output = args.sdk.resolve(strict=True), args.vm.resolve(strict=True), args.output.resolve()
    platform = sdk.parents[1].name
    if sdk.parent.name != "ruby" or sdk.name != "migration":
        parser.error("select an installed platform Ruby migration package")
    output.mkdir(parents=True)
    example = sdk / "examples/platform" / platform / "migration/ruby/body.rb"
    reference_source = write_reference(args.noetic_header.read_bytes(), output)
    reference = output / "noetic"
    subprocess.run([args.cxx.resolve(), "-std=c++17", "-O3", "-g", reference_source, "-o", reference],
                   check=True, timeout=120)
    cases = [tuple(word & MASK for word in triple) for triple in inputs()]
    request = "".join(f"{width} {x} {y}\n" for width, x, y in cases).encode()
    native = subprocess.run([reference], input=request, stdout=subprocess.PIPE, check=True, timeout=30)
    expected = [int(index) for index in native.stdout.split()]
    if len(expected) != len(cases):
        raise ValueError("the native oracle omitted a case")
    records = "".join(f"{x} {y} {width} {index}\n" for (width, x, y), index in zip(cases, expected))
    source = output / "probe.rb"
    source.write_text(example.read_text() + "\nrecords = <<'EXPECTED'\n" + records
                      + "EXPECTED\ncount = 0\nrecords.split(\"\\n\").each do |line|\n"
                      + "  x, y, width, expected = line.split.map { |word| word.to_i }\n"
                      + "  raise 'index differs from Noetic' unless grid_index(x, y, width) == expected\n"
                      + "  count += 1\nend\n"
                      + f"raise 'incomplete oracle replay' unless count == {len(cases)}\n")
    artifact = output / "probe.wasm"
    subprocess.run([sys.executable, "-B", sdk / "bin/wrrb", "--target", args.target,
                    "--build-receipt", source, "-o", artifact], check=True, timeout=240)
    if inspect(artifact.read_bytes()):
        raise ValueError("the costmap arithmetic probe must have zero host imports")
    receipt = {"complete": False, "cases": len(cases), "cgroup": group, "target": args.target,
               "header_sha256": HEADER_SHA256, "vm_sha256": sha(vm), "example_sha256": sha(example),
               "oracle_sha256": sha(reference), "artifact_sha256": sha(artifact), "engines": {}}
    profile = Profile(int(args.target[4:]))
    result = output / "results.json"
    for engine in ("int", "aot"):
        child = subprocess.run([vm, *profile.uwvm_feature_flags(), "--runtime-" + engine,
                                "--runtime-compile-threads", "0", "--runtime-llvm-jit-policy", "fast-compile",
                                "--runtime-llvm-jit-cache-path", "disable", "--runtime-memtag-mode", "sync",
                                "--debug-fault-action", "exit", "--run", artifact],
                               capture_output=True, timeout=300)
        log = output / (engine + ".log")
        log.write_bytes(child.stdout + child.stderr)
        receipt["engines"][engine] = {"status": child.returncode, "log_sha256": sha(log)}
        result.write_text(json.dumps(receipt, indent=2) + "\n")
        if child.returncode:
            raise RuntimeError(f"the {engine} guest exited with {child.returncode}. See {log}.")
    receipt["complete"] = True
    result.write_text(json.dumps(receipt, indent=2) + "\n")


if __name__ == "__main__":
    main()
