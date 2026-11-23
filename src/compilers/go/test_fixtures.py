"""Remove upstream private-key test vectors while preserving surrounding source."""
import hashlib
import json
from pathlib import Path
import re

PEM = re.compile(rb"-----BEGIN ((?:[A-Z0-9 ]+ )?(?:TESTING KEY|TEST KEY|PRIVATE KEY))-----.*?-----END \1-----", re.S)
REDACTION = b"Upstream private-key test fixture omitted from this SDK distribution."


def sanitize(data):
    return PEM.sub(REDACTION, data)


def import_sources(original, destination):
    inventory = {}
    for entry in sorted((original / "src").rglob("*")):
        if not entry.is_file() or entry.suffix not in (".go", ".pem", ".txt"):
            continue
        data = entry.read_bytes()
        blocks = list(PEM.finditer(data))
        if not blocks:
            continue
        name = entry.relative_to(original).as_posix()
        target = destination / name
        unchanged = hashlib.sha256(data).hexdigest()
        omit = entry.suffix == ".pem" and PEM.fullmatch(data.strip()) is not None
        if omit:
            target.unlink(missing_ok=True)
        else:
            target.write_bytes(sanitize(data))
        inventory[name] = {"upstream_sha256": unchanged, "action": "omit" if omit else "redact-pem-blocks",
                           "pem_sha256": [hashlib.sha256(m[0]).hexdigest() for m in blocks]}
    return inventory


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("original", type=Path)
    parser.add_argument("destination", type=Path)
    opts = parser.parse_args()
    records = import_sources(opts.original, opts.destination)
    (opts.destination.parent / "test-fixtures.json").write_text(json.dumps(records, indent=2, sort_keys=True) + "\n")
