"""Index the official GNU Rust build tools and musl target libraries in the SDK checkout."""
import argparse
import hashlib
import json
from pathlib import Path
import tarfile
import tomllib


HERE = Path(__file__).resolve().parent
SDK = HERE.parents[2]
TARGETS = {
    "linux-i686": ("i686-unknown-linux-gnu", "i686-unknown-linux-musl"),
    "linux-aarch64": ("aarch64-unknown-linux-gnu", "aarch64-unknown-linux-musl"),
    "linux-arm": ("arm-unknown-linux-gnueabi", "armv5te-unknown-linux-musleabi"),
    "linux-armhf": ("armv7-unknown-linux-gnueabihf", "armv7-unknown-linux-musleabihf"),
}


def component(manifest, archives, package, triple, version):
    release = manifest["pkg"][package]
    upstream = release["target"][triple]
    stem = f"{package}-{version}-{triple}"
    archive = archives / (stem + ".tar.xz")
    if not upstream["available"] or upstream["xz_url"].rsplit("/", 1)[1] != archive.name:
        raise ValueError(f"missing upstream release for {archive.name}")
    with archive.open("rb") as stream:
        digest = hashlib.file_digest(stream, "sha256").hexdigest()
    if digest != upstream["xz_hash"]:
        raise ValueError(f"Rust release manifest checksum mismatch for {archive.name}")

    rustlib = f"lib/rustlib/{triple}/"
    member_root = f"rust-std-{triple}" if package == "rust-std" else package
    prefix = f"{stem}/{member_root}/"
    rustc_files = {"bin/rustc", rustlib + "bin/rust-lld", rustlib + "bin/gcc-ld/ld.lld"}
    files = {}
    with tarfile.open(archive, "r|xz") as tar:
        for member in tar:
            if not member.name.startswith(prefix) or not member.isreg():
                continue
            path = member.name[len(prefix):]
            if package == "rustc":
                keep = path in rustc_files or path.startswith("lib/") and path.count("/") == 1
            elif package == "cargo":
                keep = path == "bin/cargo"
            else:
                keep = path.startswith(rustlib + "lib/")
            if keep:
                if member.mode not in (0o644, 0o755) or path in files:
                    raise ValueError(f"unexpected archive member {member.name}")
                with tar.extractfile(member) as stream:
                    checksum = hashlib.file_digest(stream, "sha256").hexdigest()
                files[path] = dict(bytes=member.size, sha256=checksum, mode=f"{member.mode:04o}")
    if not files or package == "rustc" and not {"bin/rustc", rustlib + "bin/rust-lld"} <= files.keys():
        raise ValueError(f"missing build tools in {archive.name}")
    return dict(package_version=release["version"], url=upstream["xz_url"],
                compressed_bytes=archive.stat().st_size, compressed_sha256=digest, member_prefix=prefix,
                files=dict(sorted(files.items())))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("manifest", type=Path, help="official dated channel manifest pinned in bootstrap.json")
    parser.add_argument("--host", choices=TARGETS, required=True)
    parser.add_argument("--archives", type=Path, required=True, help="directory of official Rust archives")
    args = parser.parse_args()
    base = json.loads((HERE / "bootstrap.json").read_bytes())
    raw = args.manifest.read_bytes()
    if hashlib.sha256(raw).hexdigest() != base["release_manifest"]["sha256"]:
        raise ValueError("expected the official channel manifest identified in bootstrap.json")
    manifest = tomllib.loads(raw.decode("utf-8"))
    host, target = TARGETS[args.host]
    lock = {k: base[k] for k in ("rust_release", "rust_commit", "cargo", "release_manifest")}
    lock.update(host=host, target=target,
                target_has_official_host_tools=all(manifest["pkg"][p]["target"].get(target, {}).get("available")
                                                   for p in ("rustc", "cargo")),
                components={p: component(manifest, args.archives, p, host, base["rust_release"])
                            for p in ("rustc", "cargo", "rust-std")},
                target_std=component(manifest, args.archives, "rust-std", target, base["rust_release"]))
    dest = HERE / "bootstrap" / (args.host + ".json")
    dest.parent.mkdir(exist_ok=True)
    dest.write_text(json.dumps(lock, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
