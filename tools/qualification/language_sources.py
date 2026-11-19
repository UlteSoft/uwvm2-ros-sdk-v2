"""Check release provenance of the compiler and interpreter inputs in one complete SDK checkout."""
import argparse
import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def read(path):
    return json.loads(path.read_bytes())


def check_component(root, component):
    checks = component["checks"]
    if not checks:
        return ["site binary and official release have not been bound"]
    errors = []
    for check in checks:
        p = root / check["path"]
        try:
            if "keys" in check:
                value = read(p)
                for key in check["keys"]:
                    value = value[key]
                passed = type(value) is type(check["equals"]) and value == check["equals"]
            else:
                with p.open("rb") as stream:
                    passed = hashlib.file_digest(stream, "sha256").hexdigest() == check["sha256"]
            if not passed:
                errors.append("release identity differs in " + check["path"])
        except (OSError, KeyError, ValueError, TypeError):
            errors.append("missing or invalid release input " + check["path"])
    return errors


def audit(root, scope=None):
    evidence = read(root / "share/qualification/language-source-releases.json")
    inventory = read(root / "share/targets.json")["languages"]
    if scope and scope not in inventory:
        raise ValueError("unregistered language: " + scope)
    failures = {}
    rows = []
    for name in ([scope] if scope else inventory):
        metadata = read(root / "share/language" / (name + ".json"))
        if not metadata["development_package"]:
            status = "no-development-package"
            details = []
        elif name in evidence["separate_review"]:
            status = "separate-managed-review"
            details = []
        elif name not in evidence["languages"]:
            status = "missing-source-review"
            details = []
        else:
            details = []
            for cid in evidence["languages"][name]["components"]:
                if cid not in failures:
                    c = evidence["components"][cid]
                    failures[cid] = check_component(root, c)
                details.extend(f"{cid}: {m}" for m in failures[cid])
            if name in ("java", "kotlin"):
                jars = read(root / "language" / name / "host-inputs.json")["files"]
                for jar in (r for r in jars if r["path"].startswith("compiler-jars/")):
                    if evidence["maven_sha256"].get(jar.get("source")) != jar["sha256"]:
                        details.append("unreviewed Maven artifact " + jar["path"])
            status = "unverified-source" if details else "verified-source-inputs"
        rows.append({"language": name, "status": status, "details": details})
    return rows


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--sdk-root", type=Path, default=ROOT)
    parser.add_argument("--language")
    parser.add_argument("--require", action="store_true", help="fail if any selected source input lacks release evidence")
    args = parser.parse_args()
    try:
        rows = audit(args.sdk_root.resolve(), args.language)
    except (OSError, KeyError, ValueError) as error:
        parser.exit(1, "source review failed: " + str(error) + "\n")
    print(json.dumps({"scope": "source inputs", "languages": rows}, indent=2))
    return int(args.require and any(r["status"] != "verified-source-inputs" for r in rows))


if __name__ == "__main__":
    raise SystemExit(main())
