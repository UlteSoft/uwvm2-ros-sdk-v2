"""Replay ROS package URDF and explicit STL dependencies through the official MuJoCo C API."""
import argparse
import collections
import gzip
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
from xml.etree.ElementTree import tostring

SDK = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(SDK / "tools/migration"), str(SDK / "tests")]
from audit_ros_packages import digest, source_manifest
from package_manifest import read_xml
from package_resources import collect, parts, write_pack
from separate_compilation import cgroup_record

# Other XML types can reference plugins, external resources or model preprocessors.
ELEMENTS = set("robot link joint parent child axis limit origin inertial mass inertia visual geometry box sphere cylinder mesh collision material color dynamics safety_controller calibration mimic".split())


def bind_meshes(root, entry, raw, xml):
    nodes = list(xml.iter("mesh"))
    uris = sorted({node.get("filename", "") for node in nodes})
    if not uris:
        return [(entry, raw)], {}, None
    name, _ = parts(entry["uri"])
    for uri in uris:
        if not uri.lower().endswith(".stl") or parts(uri)[0] != name:
            raise ValueError("requires a mesh outside the single-package STL fixture: " + uri)
    rows = collect([root], uris, False)
    # Use paths local to the simulator virtual filesystem. Equal basenames from
    # visual and collision directories may identify different geometry.
    aliases = {e["uri"]: "shape_" + e["sha256"] + ".stl" for e, _ in rows}
    for node in nodes:
        node.set("filename", aliases[node.get("filename")])
    rewritten = tostring(xml, encoding="utf-8")
    sha = hashlib.sha256(rewritten).hexdigest()
    rows.append(({**entry, "sha256": sha}, rewritten))
    rows.sort(key=lambda row: row[0]["uri"])
    # Equal STL bytes need one registration even when two URIs refer to them.
    links = {alias: uri for uri, alias in aliases.items()}
    return rows, links, sha


def replay(tmp, binary, row, files, links):
    if sum(16 + len(e["uri"]) + len(data) for e, data in files) + 16 > 64 * 1024 * 1024:
        raise ValueError("model and its selected meshes exceed the resource budget")
    pack = tmp / "model.pack"
    with pack.open("wb") as target:
        write_pack(target, files)
    cmd = [str(binary), str(pack), row["uri"]]
    for alias, uri in sorted(links.items()):
        cmd.extend([alias, uri])
    result = subprocess.run(cmd, cwd=tmp, capture_output=True, text=True, timeout=30)
    row.update(state="replayed" if result.returncode == 0 else "simulator-rejected",
               exit=result.returncode, details=(result.stdout + result.stderr).strip()[-2048:])


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("corpus", "variants", "mujoco", "include", "cc", "output"):
        parser.add_argument("--" + name, type=lambda s: Path(s).resolve(), required=True)
    args = parser.parse_args()
    group = cgroup_record()
    args.output.mkdir(parents=True, exist_ok=False)
    source = Path(__file__).with_suffix(".c")
    binary = args.output / "probe"
    subprocess.run([args.cc, "-std=c17", "-O3", "-g", "-Wall", "-Wextra", "-Werror",
                    "-I" + str(args.include), "-I" + str(args.mujoco / "include"), source,
                    "-L" + str(args.mujoco / "lib"), "-Wl,-rpath," + str(args.mujoco / "lib"),
                    "-lmujoco", "-lm", "-o", binary], check=True)
    rows = {}
    with gzip.open(args.variants, "rt") as stream, tempfile.TemporaryDirectory(dir=args.output) as tmp:
        for line in stream:
            variant = json.loads(line)
            for entry in variant.get("entries", []):
                uri = entry["uri"]
                if not uri.endswith(".urdf"):
                    continue
                provenance = dict(case=variant["case"], source=variant["source_id"], manifest=variant["manifest"])
                root = source_manifest(args.corpus, variant["source_id"], variant["manifest"]).parent
                raw = collect([root], [entry], True)[0][1]
                row = dict(uri=uri, source_sha256=entry["sha256"])
                try:
                    xml = read_xml(raw)
                except ValueError as exc:
                    row.update(state="invalid-model-xml", detail=str(exc))
                if "state" not in row:
                    tags = {node.tag for node in xml.iter()}
                    if xml.tag != "robot" or not xml.findall("link") or tags - ELEMENTS:
                        row.update(state="requires-different-model-fixture", extra_elements=sorted(tags - ELEMENTS))
                    else:
                        try:
                            files, links, rewritten = bind_meshes(root, entry, raw, xml)
                            row.update(meshes=[e for e, _ in files if e["uri"] != uri], simulator_xml_sha256=rewritten)
                        except (OSError, ValueError) as exc:
                            row.update(state="mesh-review-required", detail=str(exc))
                key = json.dumps(row, sort_keys=True)
                if key in rows:
                    rows[key]["variants"].append(provenance)
                    continue
                rows[key] = row
                row["variants"] = [provenance]
                if "state" not in row:
                    try:
                        replay(Path(tmp), binary, row, files, links)
                    except (ValueError, OSError, subprocess.TimeoutExpired) as exc:
                        row.update(state="simulation-review-required", detail=str(exc))
    counts = collections.Counter(row["state"] for row in rows.values())
    report = dict(cgroup=group, variants_sha256=digest(args.variants), simulator_library_sha256=digest(args.mujoco / "lib/libmujoco.so"),
                  simulator_provenance_sha256=digest(args.mujoco.parent / "provenance.json"), probe_sha256=digest(binary),
                  elements=sorted(ELEMENTS), steps_per_replay=128, counts=dict(counts),
                  scope="Selected original URDF assets and local STL geometry. Only mesh filenames are rewritten for virtual lookup. No vendor controller or hardware.",
                  models=list(rows.values()))
    (args.output / "results.json").write_text(json.dumps(report, indent=2) + "\n")
    print(dict(counts), flush=True)
    return 0 if counts["replayed"] else 1


if __name__ == "__main__":
    sys.exit(main())
