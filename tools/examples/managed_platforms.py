"""@file managed_platforms.py
@brief Publish editable managed Wasm projects for an exact platform and language.
"""
from argparse import ArgumentParser
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
LANGUAGES = {"csharp": ("C#", "cs"), "vbnet": ("Visual Basic", "vb"), "fsharp": ("F#", "fs")}


def project(platform, language, area):
    """@brief Copy the original managed source into its standalone Xmake project."""
    title, suffix = LANGUAGES[language]
    driver = area == "extension"
    entry = "Driver" if driver else "GoalStatus"
    file = entry + "." + suffix
    src = ROOT / "examples/shared" / area / language / file
    task = "check both driver permission gates" if driver else "interpret ROS 1 action statuses"
    operation = "driver.connect" if driver else "abi"
    fixture = 'set_wros_test_policy("platform-driver-denial")' if driver else 'set_wros_test_queries("abi")'
    xmake = f"""-- @file xmake.lua
-- @brief Build the {title} project and {task} in both VM engines.
set_project("{platform}-{area}-{language}")
includes(path.join(os.getenv("UWVM_ROS_SDK_ROOT"), "tools/xmake/ros.lua"))

target("{entry.lower()}")
    set_kind("binary")
    set_language("{language}")
    set_ros_platform("{platform}")
    set_optimize("fastest")
    set_symbols("debug")
    add_wros_exports("{entry}.Start")
    add_wros_operations("{operation}")
    add_files("{file}")
    {fixture}
    add_wros_tests("int", "aot")
target_end()
"""
    return {file: src.read_bytes(), "xmake.lua": xmake.encode()}


def main():
    parser = ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    registry = json.loads((ROOT / "share/targets.json").read_bytes())
    for platform in sorted(registry["platforms"]):
        for language in LANGUAGES:
            for area in ("extension", "migration"):
                if language == "fsharp" and area == "migration":
                    continue
                dest = ROOT / "examples/platform" / platform / area / language
                for name, data in project(platform, language, area).items():
                    p = dest / name
                    if p.is_file() and p.read_bytes() == data:
                        continue
                    if args.check:
                        parser.error("missing or changed managed example: " + str(p))
                    dest.mkdir(parents=True, exist_ok=True)
                    p.write_bytes(data)


if __name__ == "__main__":
    main()
