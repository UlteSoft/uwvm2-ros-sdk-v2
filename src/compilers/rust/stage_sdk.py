"""Stage one checkout's Rust guest support beside a freshly built native compiler."""
import argparse
import json
import os
from pathlib import Path
import shutil
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "install"))
import install as installer


def stage(sdk, platform):
    sdk = sdk.resolve(strict=True)
    if not (sdk / "bin/wrrs").is_file() or not (sdk / "bin/rustc").is_file():
        raise ValueError("provide the --prefix produced by rebuild.py")
    receipt = sdk / "selection.json"
    if receipt.exists():
        raise ValueError("the destination already contains an SDK selection")
    manifest = json.loads((ROOT / "bin/packages/linux-x86_64/manifest.json").read_bytes())
    entry = manifest["selections"]["rust"]
    mapping = {**entry["support_map"], "src/xmake": "tools/xmake", "src/examples/rust": "examples/rust"}
    roots = [*entry["support_roots"], *installer.binding_roots(platform, "rust"), "src/xmake", "src/examples/rust"]
    if platform != "generic":
        example = f"src/examples/{platform}/rust"
        roots.append(example)
        mapping[example] = f"examples/{platform}/rust"
    for root in roots:
        source = ROOT / root
        target = sdk / mapping.get(root, root)
        if source.is_dir():
            shutil.copytree(source, target, dirs_exist_ok=True)
        else:
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(source, target)
    with tempfile.TemporaryDirectory(dir=sdk) as temporary:
        work = Path(temporary)
        for package, (metadata, destinations) in installer.native_packages(manifest, entry["host_tools"]).items():
            archive = work / Path(package).name
            shutil.copyfile(ROOT / package, archive)
            executable = work / metadata["member"]
            installer.unpack_executable(archive, metadata, executable)
            for dest in destinations:
                target = sdk / dest
                target.parent.mkdir(parents=True, exist_ok=True)
                staged = work / "installation"
                os.link(executable, staged)
                os.replace(staged, target)
    receipt.write_text(json.dumps({"schema": 1, "platform": platform, "language": "rust",
                                   "mode": "local-build"}, indent=2) + "\n")


if __name__ == "__main__":
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument("--sdk", required=True, type=Path)
    cli.add_argument("--platform", required=True, choices=installer.PLATFORMS)
    try:
        args = cli.parse_args()
        stage(args.sdk, args.platform)
    except (OSError, ValueError, KeyError) as error:
        sys.exit(f"Rust SDK staging failed: {error}")
