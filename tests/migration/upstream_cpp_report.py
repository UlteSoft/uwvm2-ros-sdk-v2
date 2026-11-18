"""Verify execution receipts and distinguish upstream tests from locally corrected tests."""
import argparse
from collections import Counter, defaultdict
import hashlib
import json
from pathlib import Path
import xml.etree.ElementTree as ET

from upstream_cpp import sha


def read(path):
    return json.loads(path.read_bytes())


def require(condition, message):
    if not condition:
        raise ValueError(message)


def generate(receipt):
    data = read(receipt)
    require(data["complete"], "incomplete inventory traversal")
    by_package = defaultdict(Counter)
    sources = {}
    instance_count = Counter()
    rows = data["unique_suites"]
    for variant in data["variants"]:
        package = variant["package"]
        stats = by_package[package]
        stats["snapshots"] += 1
        stats["unselected_cpp_file_instances"] += len(variant["unselected_cpp_tests"])
        for unit, entry in variant["units"].items():
            if entry["status"] == "absent":
                stats["absent_unit_instances"] += 1
                continue
            key = entry["closure"]
            expected = hashlib.sha256(json.dumps(entry["sources"], sort_keys=True).encode()).hexdigest()
            require(key == expected, "invalid source digest set " + key)
            require(rows[key]["unit"] == unit and rows[key]["package"] == package, "mismatched unit " + key)
            sources[key] = entry["sources"]
            instance_count[key] += 1
            stats["present_unit_instances"] += 1
    require(set(rows) == set(sources), "orphan or missing source closure")
    stages = ("oracle-compile", "oracle-run", "native-trace-compile", "native-trace-run", "wrcc", "vm-int", "vm-aot")
    corrections = {}
    profiles = set()
    tools = {}
    failed = []
    for key, row in rows.items():
        folder = receipt.parent / key
        stats = by_package[row["package"]]
        if not row["passed"]:
            stats["failed_distinct_units"] += 1
            failed.append({"closure": key, "error": row["error"]})
            continue
        for name in stages:
            require(read(folder / (name + ".command.json")).get("exit") == 0, "missing successful stage " + name)
        build = read(folder / "tests.wasm.wros-build.json")
        require(build["artifact_sha256"] == row["guest_sha256"] == sha(folder / "tests.wasm"), "guest hash " + key)
        require(build["settings"] == {"optimization": "3", "debug": True}, "unexpected compiler options")
        require(build["profile"]["mte"] and row["imports"] == [], "MTE or import policy " + key)
        require(row["int"] and row["aot"] and row["native_googletest"], "missing run " + key)
        mode = "legacy" if data["legacy_mte"] else "strict"
        require(mode == build["mode"], "incorrect evidence mode " + key)
        if mode == "strict":
            require(build["vm_sha256"] == data["vm_sha256"], "wrong strict VM " + key)
            require(read(folder / "strict-artifact.command.json").get("exit") == 0, "strict validation " + key)
        profiles.add(build["mode"])
        args = read(folder / "wrcc.command.json")["argv"]
        tool_dir = Path(args[args.index("--toolchain") + 1]) / "bin"
        for path in (Path(args[1]), tool_dir / "clang++", tool_dir / "wasm-ld"):
            identity = str(path.resolve())
            if identity not in tools:
                tools[identity] = sha(path)
        cases = row["observed_assertions"]
        lines = (folder / "native-trace-run.stdout").read_text().splitlines()
        observed = {n: [int(c), int(t)] for n, c, t in (line.split() for line in lines)}
        require(observed == cases and set(row["tests"]) == set(cases), "native trace mismatch " + key)
        xml_cases = ET.parse(folder / "oracle.xml").findall(".//testcase")
        actual = [c.get("classname") + "." + c.get("name") for c in xml_cases]
        require(sorted(actual) == sorted(cases) and all(c.get("status") == "run" and c.find("failure") is None
                                                        for c in xml_cases), "native GoogleTest results " + key)
        change = row.get("test_only_adaptation")
        label = "adapted" if change else "unmodified"
        stats[label + "_distinct_units"] += 1
        stats[label + "_unit_instances"] += instance_count[key]
        for path, upstream_hash in sources[key].items():
            wanted = change["sha256"] if change and path == row["unit"] else upstream_hash
            require(sha(folder / path) == wanted, "source mismatch " + str(folder / path))
        changed_name = None
        if change:
            # This verifier accepts the one reviewed edit only. An additional
            # adaptation must identify its own test body independently.
            changed_name = "VelocityIteratorTest.test_cranky"
            require(row["unit"] == "test/velocity_iterator_test.cpp" and changed_name in cases and
                    change["assertions_removed"] == 0, "unrecognised adaptation")
            original = sources[key][row["unit"]]
            correction = corrections.setdefault(original, {
                "case": changed_name, "upstream_test_sha256": original, "tested_test_sha256": change["sha256"],
                "raw_qualification": change["raw_qualification"], "reason": change["reason"],
                "unchanged_predicates": True, "qualified_after_adaptation_in_closures": []})
            require(correction["tested_test_sha256"] == change["sha256"], "different correction for same test")
            correction["qualified_after_adaptation_in_closures"].append(key)
        for name, (count, trace) in cases.items():
            require(count > 0 and 0 <= trace < 2**64, "empty or invalid assertion trace " + name)
            form = "adapted" if name == changed_name else "unmodified"
            stats[form + "_case_executions_per_engine"] += 1
            stats[form + "_assertions_per_engine"] += count
    return dict(receipt_sha256=sha(receipt), archive_snapshots=len(data["variants"]),
                distinct_source_closures=len(rows), profiles=sorted(profiles), tool_sha256=tools,
                per_package={p: dict(s) for p, s in sorted(by_package.items())},
                totals=dict(sum(by_package.values(), Counter())), corrections=list(corrections.values()),
                failed=failed, all_present_suites_passed=not failed,
                count_basis="Each distinct translation unit and package-local include closure runs once per engine. "
                            "Archive instance counts include repeated source closures. Corrections identify the edited "
                            "test body for each affected closure. Unselected files were not executed.")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("receipt", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    if ".tmp" not in args.output.resolve().parts:
        parser.error("place output beneath a .tmp directory")
    result = generate(args.receipt.resolve())
    with args.output.open("x") as target:
        json.dump(result, target, indent=2)
        target.write("\n")


if __name__ == "__main__":
    main()
