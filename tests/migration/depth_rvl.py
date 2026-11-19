"""Check RVL depth frames from the ROS source inventory against independent wire vectors."""
import argparse
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import resource
import subprocess
import sys

from upstream_cpp import Profile, SourceArchive, cgroup_record, inspect, put, save, sha

SOURCE = PurePosixPath("src/rvl_codec.cpp")
PACKAGE = "compressed_depth_image_transport"
FIXTURE = Path(__file__).with_suffix(".cpp")


def rvl_words(depths):
    """Encode zero and nonzero run lengths and zigzag deltas in 8-nibble words."""
    digits = []

    def write(value):
        while value >= 8:
            digits.append(8 + value % 8)
            value //= 8
        digits.append(value)

    previous = 0
    cursor = 0
    while cursor < len(depths):
        start = cursor
        while cursor < len(depths) and depths[cursor] == 0:
            cursor += 1
        write(cursor - start)
        start = cursor
        while cursor < len(depths) and depths[cursor] != 0:
            cursor += 1
        write(cursor - start)
        for value in depths[start:cursor]:
            diff = value - previous
            write(2 * diff if diff >= 0 else -2 * diff - 1)
            previous = value
    digits.extend([0] * (-len(digits) % 8))
    return [int("".join(format(n, "x") for n in digits[i:i + 8]), 16)
            for i in range(0, len(digits), 8)]


def vectors():
    # Independent format anchors: one zero run, one value and both delta signs.
    assert rvl_words([0]) == [0x10000000]
    assert rvl_words([1]) == [0x01200000]
    assert rvl_words([2, 1]) == [0x02410000]
    frames = {"empty": [], "all_zero": [0] * 512, "constant": [1900] * 512,
              "delta_extremes": [1, 65535, 1, 2, 65534, 6, 0, 1],
              "nibble_boundaries": [0] * 7 + [2] * 8 + [0] * 63 + [512] * 64 + [4096] * 65,
              "depth_scan": [(0 if (i % 53 < 16) else 350 + (i * 7) % 1873) for i in range(1024)]}
    code = ["#pragma once"]
    for name, frame in frames.items():
        words = rvl_words(frame)
        code.append("static constexpr unsigned short " + name + "_pixels[] = {" +
                    ", ".join(map(str, frame or [0])) + "};")
        code.append("static constexpr unsigned int " + name + "_words[] = {" +
                    ", ".join(hex(word) + "u" for word in words or [0]) + "};")
    code.append("static constexpr Frame frames[] = {")
    for name, frame in frames.items():
        code.append(f"    {{{name}_pixels, {len(frame)}, {name}_words, {len(rvl_words(frame))}}},")
    code.append("};")
    return "\n".join(code) + "\n", list(frames)


def run(folder, name, argv, expect=0):
    command = list(map(str, argv))
    with (folder / (name + ".log")).open("xb") as log:
        result = subprocess.run(command, cwd=folder, stdout=log, stderr=subprocess.STDOUT, timeout=120)
    if expect is None:
        if result.returncode == 0:
            raise ValueError(f"{name} accepted the altered reference")
    elif result.returncode != expect:
        raise ValueError(f"{name} exited {result.returncode}, see {folder}/{name}.log")
    return result.returncode


def execute(folder, files, sdk, vm, native, vector_header):
    folder.mkdir()
    for path, data in files.items():
        put(folder, path, data)
    header, = [str(path.relative_to("include")) for path in files if path.parts[0] == "include"]
    (folder / "vectors.h").write_text(vector_header)
    put(folder, "driver.cpp", FIXTURE.read_bytes().replace(b'"rvl_header"', json.dumps(header).encode()))
    recorded = {}
    for negative in (False, True):
        label = "changed-reference" if negative else "reference"
        # Use the same source on native and Wasm. Only the negative test changes
        # one expected word after the encoder returns.
        (folder / "expected.h").write_text(f"#define ALTER_EXPECTATION {int(negative)}\n")
        guest = folder / (label + ".wasm")
        oracle = folder / ("native-" + label)
        sources = [folder / SOURCE, folder / "driver.cpp"]
        run(folder, label + "-compile-native", [native, "-std=c++20", "-O3", "-g", "-Wall", "-Wextra",
                                               "-I", folder / "include", *sources, "-o", oracle])
        code = run(folder, label + "-native", [oracle], 17 if negative else 0)
        run(folder, label + "-wrcc", [sdk / "bin/wrcc", "--target", "wasm32", "--std", "c++20",
            "-O3", "-g", "--reactor", "--export", "_start", "-I", folder / "include",
            "--build-receipt", *sources, "-o", guest])
        receipt = Path(str(guest) + ".wros-build.json")
        info = json.loads(receipt.read_bytes())
        if info["mode"] != "strict" or inspect(guest.read_bytes()):
            raise ValueError("expected a strict build with zero Wasm host imports")
        run(folder, label + "-verify", [sys.executable, "-B", sdk / "install/qualification.py",
            "--vm", vm, "--artifact", guest, "--receipt", receipt, "--approved-receipt-sha256", sha(receipt)])
        engines = {}
        for engine in ("int", "aot"):
            name = label + "-" + engine
            rc = run(folder, name, [vm, *Profile().uwvm_feature_flags(), "--debug-fault-action", "exit",
                       "--runtime-" + engine, "--runtime-compile-threads", "0",
                       "--runtime-llvm-jit-cache-path", "disable", "--run", guest], None if negative else 0)
            if negative and "unreachable" not in (folder / (name + ".log")).read_text(errors="replace").lower():
                raise ValueError(f"{name} failed without the expected guest trap")
            engines[engine] = rc
        recorded[label] = dict(nativeExit=code, vmExits=engines, hostImports=[], wasmSha256=sha(guest),
                               strictBuildReceiptSha256=sha(receipt))
    return recorded


def main():
    p = argparse.ArgumentParser(description=__doc__)
    for key in ("corpus", "sdk", "vm", "output"):
        p.add_argument("--" + key, type=lambda s: Path(s).resolve(), required=True)
    p.add_argument("--native-cxx", type=lambda s: Path(s).resolve(), default=Path("/usr/bin/g++"))
    args = p.parse_args()
    group = cgroup_record()
    if ".tmp" not in args.output.parts:
        p.error("choose a fresh output directory under .tmp")
    args.output.mkdir(mode=0o700, parents=True, exist_ok=False)
    os.environ["TMPDIR"] = str(args.output)
    resource.setrlimit(resource.RLIMIT_CORE, (0, 0))
    inventory = args.corpus / "linux-five-capability-inventory/packages.json"
    row, = [r for r in json.loads(inventory.read_bytes()) if r["name"] == PACKAGE]
    header, frames = vectors()
    result = dict(complete=False, package=PACKAGE, scope="valid locally owned RVL depth payloads",
                  frames=frames, inventorySha256=sha(inventory), cgroup=group, vmSha256=sha(args.vm),
                  nativeCompilerSha256=sha(args.native_cxx), fixtureSha256=sha(FIXTURE),
                  runnerSha256=sha(Path(__file__)), snapshots=[], variants={})
    target = args.output / "results.json"
    save(target, result)
    for entry in row["instances"]:
        archive = SourceArchive(args.corpus, entry)
        try:
            obs = dict(sourceId=entry["source_id"], archiveSha256=entry["archive_sha256"],
                       manifest=entry["manifest"])
            result["snapshots"].append(obs)
            if SOURCE not in archive.files:
                obs["status"] = "rvl-source-absent"
            else:
                files = archive.closure(SOURCE)
                pins = {str(path): hashlib.sha256(data).hexdigest() for path, data in files.items()}
                key = hashlib.sha256(json.dumps(pins, sort_keys=True).encode()).hexdigest()
                if key not in result["variants"]:
                    cases = execute(args.output / key, files, args.sdk, args.vm, args.native_cxx, header)
                    result["variants"][key] = dict(sources=pins, runs=cases)
                obs.update(status="matched-qualified-source", variant=key)
        finally:
            archive.tar.close()
            save(target, result)
    if not result["variants"]:
        raise ValueError("no RVL implementation was tested")
    result["complete"] = True
    save(target, result)


if __name__ == "__main__":
    main()
