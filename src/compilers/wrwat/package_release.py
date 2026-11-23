"""Package wrwat and regenerate the WAT release record and language selection for one Linux ABI."""
import argparse
import fcntl
import hashlib
import json
import lzma
import os
from pathlib import Path
import re
import runpy
import subprocess
import tempfile


HERE = Path(__file__).resolve().parent
SDK = HERE.parents[2]
BUILD = runpy.run_path(str(HERE / "rebuild.py"))
PACKER = BUILD["PACKER"]
INSTALLER = BUILD["INSTALLER"]
SOURCE_LOCK = "src/compilers/wrwat/release/linux-x86_64.json"


def inspect_program(tool, host, bootstrap):
    """Check the output ABI and link mode, then read the compiler identities from the ELF."""
    INSTALLER["require_host"](tool, host)
    details = subprocess.check_output(["/usr/bin/readelf", "-lW", "-p", ".comment", "-A", tool],
                                      env={"LC_ALL": "C", "PATH": "/usr/bin:/bin"}, text=True)
    entry = re.search(r"^Entry point (0x[0-9a-f]+)$", details, re.MULTILINE)
    loads = [line.split() for line in details.splitlines() if line.lstrip().startswith("LOAD ")]
    if not entry or not any("E" in "".join(segment[6:-1])
                            and int(segment[2], 16) <= int(entry[1], 16) < int(segment[2], 16) + int(segment[4], 16)
                            for segment in loads):
        raise ValueError(f"{tool} has no entry point in an executable load segment")
    if "target_std" in bootstrap and re.search(r"^\s*(INTERP|DYNAMIC)\s", details, re.MULTILINE):
        raise ValueError(f"expected a statically linked {bootstrap['target']} ELF")
    if host in ("linux-arm", "linux-armhf"):
        required = (["Tag_CPU_arch: v5TE"] if host == "linux-arm" else
                    ["Tag_CPU_arch: v7", "Tag_FP_arch: VFPv3-D16", "Tag_ABI_VFP_args: VFP registers"])
        attributes = {line.strip() for line in details.splitlines()}
        if not set(required) <= attributes:
            raise ValueError(f"unexpected {host} ARM attributes in {tool}")
    comments = set(re.findall(r"^\s*\[\s*[0-9a-f]+\]\s+(.+)$", details, re.MULTILINE))
    rust = bootstrap["components"]["rustc"]["package_version"]
    linkers = [comment.removeprefix("Linker: ") for comment in comments if comment.startswith("Linker: ")]
    if "rustc version " + rust not in comments or len(linkers) != 1:
        raise ValueError(f"{tool} lacks the release rustc and LLD identities")
    return "rustc " + rust, BUILD["check_linker"](linkers[0])


def encode_json(path, data):
    path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")


def package_release(tool, host, root):
    bootstrap = BUILD["bootstrap_lock"](host)
    rustc, linker = inspect_program(tool, host, bootstrap)
    original = json.loads((SDK / SOURCE_LOCK).read_bytes())
    upstream = json.loads((HERE / "UPSTREAM.json").read_bytes())
    relative = Path("bin/packages") / host
    dest = root / relative
    dest.mkdir(parents=True, exist_ok=True)
    package_path = relative / "wrwat/wrwat.tar.xz"
    lock_path = Path(SOURCE_LOCK).with_name(host + ".json")
    manifest_path = dest / "manifest.json"
    template = json.loads((SDK / "bin/packages/linux-x86_64/manifest.json").read_bytes())["selections"]["wat"]
    if host != BUILD["GNU_X86_64"]:
        template["support_roots"][template["support_roots"].index(SOURCE_LOCK)] = lock_path.as_posix()
        template["support_map"][lock_path.as_posix()] = template["support_map"].pop(SOURCE_LOCK)
        template["source_roots"].append(bootstrap["target_std"]["path"])
    scratch = root / ".tmp"
    scratch.mkdir(exist_ok=True)
    with tempfile.TemporaryDirectory(dir=scratch, prefix="wrwat-package-") as temporary:
        stage = Path(temporary)
        archive = stage / "wrwat.tar.xz"
        package = PACKER["package"](tool, "wrwat", archive, host=host)
        package["path"] = package_path.as_posix()
        if host != BUILD["GNU_X86_64"]:
            with lzma.open(archive, "rb") as tar:
                package["tar_sha256"] = hashlib.file_digest(tar, "sha256").hexdigest()
                package["tar_bytes"] = tar.tell()
        if host == "linux-armhf":
            package["required_hwcap"] = ["vfp", "vfpv3"]
        release = dict(wasm_tools_commit=upstream["upstream"]["commit"],
                       wasmparser_memtag_commit=upstream["reader_fork"]["commit"], rustc=rustc,
                       wire=original["wire"], binary_bytes=package["bytes"], binary_sha256=package["sha256"],
                       host=host, executable="bin/wrwat", source_root="src/compilers/wrwat",
                       package=package["path"], compressed_sha256=package["compressed_sha256"],
                       compressed_bytes=package["compressed_bytes"], package_member="wrwat")
        if host != BUILD["GNU_X86_64"]:
            release.update(rust_target=bootstrap["target"], rustc_commit=bootstrap["rust_commit"],
                           cargo=bootstrap["cargo"], linker=linker)
        encode_json(stage / "release.json", release)

        # A fresh host starts with WAT. Existing manifests can also contain other language selections.
        directory_fd = os.open(dest, os.O_RDONLY | os.O_DIRECTORY)
        try:
            fcntl.flock(directory_fd, fcntl.LOCK_EX)
            manifest = (json.loads(manifest_path.read_bytes()) if manifest_path.exists() else
                        dict(schema=1, host=host, packages={}, selections={}))
            if manifest["schema"] != 1 or manifest["host"] != host:
                raise ValueError(f"unexpected host package manifest: {manifest_path}")
            manifest["packages"]["wrwat"] = package
            manifest["selections"]["wat"] = template
            encode_json(stage / "manifest.json", manifest)
            (root / package_path).parent.mkdir(parents=True, exist_ok=True)
            (root / lock_path).parent.mkdir(parents=True, exist_ok=True)
            os.replace(archive, root / package_path)
            os.replace(stage / "release.json", root / lock_path)
            os.replace(stage / "manifest.json", manifest_path)
        finally:
            os.close(directory_fd)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--host", choices=INSTALLER["HOSTS"], required=True)
    parser.add_argument("--executable", type=Path, required=True)
    parser.add_argument("--output-root", type=Path, default=SDK, help="SDK tree to write (default: this checkout)")
    args = parser.parse_args()
    package_release(args.executable, args.host, args.output_root.resolve())


if __name__ == "__main__":
    main()
