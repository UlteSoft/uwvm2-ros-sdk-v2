"""Measure trusted local candidate inputs before running independent release tests."""
import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "install"))
from guest_profile import Profile
from qualification import EXTERNAL, measure_inputs


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--language", choices=sorted(EXTERNAL), required=True)
    p.add_argument("--toolchain", required=True, type=Path)
    p.add_argument("--sysroots", required=True, type=Path, action="append")
    p.add_argument("--target", choices=("wasm32", "wasm64"), default="wasm32")
    p.add_argument("--core", choices=("mvp", "3.0"), default="3.0")
    p.add_argument("--eh", action=argparse.BooleanOptionalAction, default=None)
    p.add_argument("--threads", action="store_true")
    p.add_argument("-O", choices=list("0123sz"), required=True)
    p.add_argument("-g", action="store_true")
    for name in sorted(set.union(*EXTERNAL.values())):
        p.add_argument("--" + name.replace("_", "-"), type=Path)
    args = p.parse_args()
    eh = (args.core != "mvp" and args.language != "rs") if args.eh is None else args.eh
    target = Profile(int(args.target[4:]), "1.0" if args.core == "mvp" else "3.0", args.threads, True,
                     "eh" if eh else "noeh")
    extra = {name: getattr(args, name) for name in EXTERNAL[args.language]}
    if any(value is None for value in extra.values()):
        p.error("required build inputs: " + ", ".join(sorted(EXTERNAL[args.language])))
    record = dict(status="unreviewed-candidate", language=args.language, profile=target.to_dict(),
                  settings={"optimization":args.O, "debug":args.g}, inputs=measure_inputs(args.language,args,target,extra))
    print(json.dumps(record, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
