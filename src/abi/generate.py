#!/usr/bin/env python3
"""Regenerate the guest APIs offline or refresh their source-pinned contract with --vm."""
import argparse
import json
import sys
from pathlib import Path

sys.dont_write_bytecode = True

from extract import extract
from render import MARKER, ROOT_C, ROOT_CPP, ROOT_RS, render

ROOT = Path(__file__).resolve().parents[2]
CONTRACT = Path("src/abi/contract.json")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--vm", type=Path, help="read an uwvm2-ros source tree and check its actual import registrations")
    parser.add_argument("--check", action="store_true", help="report drift without writing any files")
    args = parser.parse_args()
    contract = extract(args.vm) if args.vm else json.loads((ROOT / CONTRACT).read_text())
    files = render(contract)
    if args.vm:
        files[CONTRACT] = json.dumps(contract, indent=2, ensure_ascii=False) + "\n"
    changed = []
    for path, contents in files.items():
        dest = ROOT / path
        if dest.is_file() and dest.read_text() == contents:
            continue
        changed.append(str(path))
        if not args.check:
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_text(contents)
    for public in (ROOT_C, ROOT_CPP, ROOT_RS):
        for dest in (ROOT / public).glob("*"):
            if dest.is_file() and dest.relative_to(ROOT) not in files:
                with dest.open() as stream:
                    if MARKER not in stream.readline():
                        continue
                changed.append(str(dest.relative_to(ROOT)))
                if not args.check:
                    dest.unlink()
    if args.check and changed:
        parser.exit(1, "Bindings differ:\n" + "\n".join(changed) + "\n")
    print(f"{contract['module']}: {len(contract['operations'])} registered imports, {len(changed)} changed files")


if __name__ == "__main__":
    main()
