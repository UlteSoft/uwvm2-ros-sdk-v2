"""Pack operator-reviewed release rows into one unsigned, rollback-versioned WSEA payload."""
import argparse
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "install"))
from local_release import encode
from qualification import complete_release, LANGUAGES, read_json


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--release-json", type=Path, required=True, action="append")
    p.add_argument("--output", type=Path, required=True)
    a = p.parse_args()
    if len(a.release_json) > 32:
        p.error("at most 32 reviewed profiles fit in one local release")
    rows = []
    identities = set()
    for path in a.release_json:
        row = read_json(path, 128 * 1024)
        if not isinstance(row, dict) or row.get("language") not in LANGUAGES or not complete_release(row):
            p.error("invalid release shape in " + str(path))
        settings = row["settings"]
        identity = row["language"], row["profile"]["triple"], row["profile"]["wasm_version"], row["profile"]["exceptions"], settings["optimization"], settings["debug"]
        if identity in identities:
            p.error("select one reviewed candidate per build profile")
        identities.add(identity)
        rows.append(row)
    payload = encode(rows)
    with a.output.open("xb") as out:
        out.write(payload)


if __name__ == "__main__":
    main()
