"""Produce the unsigned WSEA statement for two measured synchronous JVM routes."""
import argparse
import json
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "language/jvm"))
import release


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for key in ("toolchain", "sysroots", "vm", "c-release", "output"):
        parser.add_argument("--" + key, required=True, type=lambda path: Path(path).resolve())
    parser.add_argument("--approved-c-release-sha256", required=True, help="canonical SHA-256 of the reviewed C release row")
    args = parser.parse_args()
    args.output.mkdir(exist_ok=False, parents=True)
    parent = release.qualification.read_json(args.c_release, 4 << 20)
    if (release.canon(parent) != args.approved_c_release_sha256
            or parent.get("vm_sha256") != release.digest(args.vm)):
        parser.error("the C release or VM differs from the approved source")
    def measure(lang):
        inputs = release.measure(args.toolchain, [args.sysroots], lang)
        release.c_parent([parent], args.approved_c_release_sha256, inputs["backend"])
        return inputs

    before = {lang:measure(lang) for lang in release.COMMANDS}
    proof = args.output / "ownership"
    subprocess.run([sys.executable, "-B", ROOT / "tests/jvm_memory_neighbors.py",
        "--toolchain", args.toolchain, "--sysroots", args.sysroots, "--runtime", args.vm,
        "--java-bundle", release.bundle_at(args.toolchain, "java"), "--kotlin-bundle", release.bundle_at(args.toolchain, "kotlin"),
        "--output", proof], check=True)
    report = release.qualification.read_json(proof / "results.json", 4 << 20)
    if not report["complete"] or report["failures"]:
        raise ValueError("incomplete synchronous JVM ownership run")
    rows = [parent]
    for lang in release.COMMANDS:
        inputs = measure(lang)
        if inputs != before[lang]:
            raise ValueError("JVM inputs changed during qualification")
        cases = {r["name"].removeprefix(lang + "-"):release.canon(r) for r in report["steps"]
                 if r["name"].startswith(lang + "-") and r["passed"]}
        if cases.keys() != release.CASES:
            raise ValueError("the ownership run did not cover every required case")
        row = dict(format=release.FORMAT, language=lang, profile=release.PROFILE.to_dict(), settings=release.SETTINGS,
                   inputs=inputs, c_release_sha256=args.approved_c_release_sha256, vm_sha256=parent["vm_sha256"],
                   evidence=cases, ownership_report_sha256=release.digest(proof / "results.json"))
        (args.output / (lang + ".json")).write_text(json.dumps(row, indent=2) + "\n")
        rows.append(row)
    if release.digest(args.vm) != parent["vm_sha256"]:
        raise ValueError("qualification VM changed")
    (args.output / "releases.wasm").write_bytes(release.local_release.encode(rows))


if __name__ == "__main__":
    main()
