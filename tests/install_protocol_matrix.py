"""Install and inspect every pinned language/platform protocol selection offline."""
import argparse
import json
import os
import shutil
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
    parser.add_argument("--component", choices=("protocol", "development"), default="protocol")
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
                flags = ["--component", options.component]
                if options.component == "development":
                    descriptor = json.loads(source.read("share/language/" + language + ".json", MAX_METADATA))
                    if not descriptor["development_package"] and "synchronous-aot" in descriptor.get("optional_components", []):
                        flags = ["--component", "synchronous-aot"]
                try:
                    result = install(source, platform, language, Path(prefix), flags)
                except ValueError as error:
                    if (options.component != "development" or descriptor["development_package"] or
                            flags[-1] != "development" or "has not been published" not in str(error)):
                        raise
                    if any(p not in ("install/revision.py", "share/language/" + language + ".json") for p in source.requested):
                        raise ValueError("an unpublished compiler caused a package download")
                    results.append(dict(platform=platform, language=language, status="unpublished"))
                    continue
                directory = Path(result["directory"])
                actual = {p.relative_to(directory).as_posix() for p in directory.rglob("*") if p.is_file()}
                if options.component == "protocol":
                    allowed = {"LICENSE", "share/abi/ros.json", "share/language/" + language + ".json",
                               "platform/" + platform + "/sources.json"}
                    if actual != allowed or any(not (p.startswith("install/") or p in allowed) for p in source.requested):
                        raise RuntimeError(f"unexpected protocol payload for {platform}/{language}")
                else:
                    adapters = {p for p in actual if p.endswith("/xmake/adapter.lua") or p.endswith("/xmake/platform.lua")}
                    if adapters != {f"language/{language}/xmake/adapter.lua", f"platform/{platform}/xmake/platform.lua"}:
                        raise ValueError(f"unexpected development adapters for {platform}/{language}: {adapters}")
                    if not os.access(directory / "bin" / descriptor["command_name"], os.X_OK):
                        raise ValueError(f"missing compiler launcher for {language}")
                results.append(dict(platform=platform, language=language, variant=result["variant"], status="installed",
                                    requests=list(source.requested)))
                # Each selection has been verified. Reuse only the content cache.
                shutil.rmtree(directory)
    report = {"commit": source.commit, "component": options.component, "pairs": results}
    with options.receipt.open("x") as output:
        json.dump(report, output, indent=2)
    print(f"Checked {len(results)} installations at {source.commit}")


if __name__ == "__main__":
    main()
