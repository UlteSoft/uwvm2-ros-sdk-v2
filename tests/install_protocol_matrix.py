"""Install and inspect every pinned language/platform protocol selection offline."""
import argparse
import json
from pathlib import Path
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "install"))
from bootstrap import MAX_METADATA, Source, install


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--commit", required=True)
    parser.add_argument("--receipt", type=Path, required=True)
    options = parser.parse_args()
    source = Source(options.commit, ROOT)
    registry = json.loads(source.read("share/targets.json", MAX_METADATA))
    scratch = ROOT / ".tmp"
    scratch.mkdir(exist_ok=True)
    results = []
    with tempfile.TemporaryDirectory(dir=scratch) as prefix:
        for platform in registry["platforms"]:
            for language in registry["languages"]:
                source.requested.clear()
                result = install(source, platform, language, Path(prefix), ["--component", "protocol"])
                allowed = {"LICENSE", "share/abi/ros.json", "share/language/" + language + ".json",
                           "platform/" + platform + "/sources.json"}
                directory = Path(result["directory"])
                actual = {p.relative_to(directory).as_posix() for p in directory.rglob("*") if p.is_file()}
                if actual != allowed or any(not (p.startswith("install/") or p in allowed)
                                            for p in source.requested):
                    raise RuntimeError(f"unexpected payload for {platform}/{language}")
                results.append({"platform": platform, "language": language, "requests": list(source.requested)})
    report = {"commit": source.commit, "component": "protocol", "pairs": results}
    with options.receipt.open("x") as output:
        json.dump(report, output, indent=2)
    print(f"Checked {len(results)} installations at {source.commit}")


if __name__ == "__main__":
    main()
