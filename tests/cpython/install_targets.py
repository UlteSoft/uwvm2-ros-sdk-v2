"""@file install_targets.py
@brief Exercise one-width downloads and signed toolchain admission through the fixed public installer.
"""
import argparse
import json
from pathlib import Path
import subprocess
import sys


def main():
    """@brief Install both widths separately and reject conflicting choices and mismatched signed sites."""
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("sdk", "site32", "site64", "output"):
        parser.add_argument("--" + name, required=True, type=Path)
    args = parser.parse_args()
    sdk = args.sdk.resolve()
    root = args.output.resolve()
    root.mkdir()
    revision = subprocess.check_output(["git", "-C", sdk, "rev-parse", "HEAD"], text=True).strip()
    base = ["--local-repository", str(sdk), "--commit", revision, "--platform", "unitree", "--language", "py"]
    records = []

    def check(label, action, options, expected=None):
        command = [sys.executable, str(sdk / "install/bootstrap.py"), action, *base, *map(str, options)]
        process = subprocess.run(command, capture_output=True, text=True, timeout=180)
        (root / (label + ".stdout")).write_text(process.stdout)
        (root / (label + ".stderr")).write_text(process.stderr)
        if expected is None:
            if process.returncode:
                raise ValueError(label + ": " + process.stderr)
        elif process.returncode == 0 or expected not in process.stderr:
            raise ValueError(label + ": expected rejection: " + process.stderr)
        records.append(dict(label=label, exit=process.returncode))
        return json.loads(process.stdout) if expected is None else None

    sites = {32: args.site32.resolve(), 64: args.site64.resolve()}
    for bits, other_bits in ((32, 64), (64, 32)):
        width, other = "wasm" + str(bits), "wasm" + str(other_bits)
        switch = [] if bits == 32 else ["--", "--python-target", width]
        plan = check(width + "-plan", "plan", switch)
        assert "python-runtime/" + width in plan["packages"]
        assert "python-runtime/" + other not in plan["packages"]
        installed = check(width + "-install", "install", ["--site-profile", sites[bits], "--prefix", root / width, *switch])
        requests = [path for path in installed["requested_paths"] if path.startswith("third-parties/cpython-runtime/")]
        assert len(requests) == 2 and all(Path(p).name.startswith(width + "-") for p in requests)
        path = Path(installed["directory"]) / "third-parties/cpython-runtime"
        assert {p.name for p in path.iterdir()} == {Path(p).name for p in requests}
        wrong_prefix = root / ("mismatch-" + width)
        check(width + "-mismatch", "install", ["--site-profile", sites[other_bits], "--prefix", wrong_prefix, *switch],
              "width differs from selected signed C site")
        assert not (wrong_prefix / revision / "unitree/py/development").exists()
    check("both-widths", "plan", ["--", "--python-target", "wasm32", "--python-target", "wasm64"],
          "select one --python-target")
    check("existing-width", "install", ["--prefix", root / "wasm32", "--", "--python-target", "wasm64"],
          "existing selection differs")
    (root / "results.json").write_text(json.dumps(dict(sdk_commit=revision, cases=records), indent=2) + "\n")


if __name__ == "__main__":
    main()
