"""Read ROS package identity and dependency declarations without running package code."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from xml.etree.ElementTree import TreeBuilder
from xml.parsers import expat

MAX_MANIFEST = 1 << 20
DEPENDS = frozenset(("depend", "build_depend", "build_export_depend", "buildtool_depend",
                     "buildtool_export_depend", "exec_depend", "run_depend", "test_depend",
                     "doc_depend", "group_depend", "member_of_group", "conflict", "replace",
                     "rosdep"))


def read_xml(raw):
    """Parse a bounded manifest. External entities, document types and includes are never loaded."""
    if len(raw) > MAX_MANIFEST:
        raise ValueError("manifest exceeds the size limit")
    builder = TreeBuilder()
    parser = expat.ParserCreate()
    count = depth = 0

    def start(name, attrs):
        nonlocal count, depth
        count += 1
        depth += 1
        if depth > 64 or count > 16384:
            raise ValueError("manifest exceeds XML structural limits")
        builder.start(name, attrs)

    def end(name):
        nonlocal depth
        builder.end(name)
        depth -= 1

    def refuse(*unused):
        raise ValueError("document types and external entities are unsupported")

    parser.StartElementHandler = start
    parser.EndElementHandler = end
    parser.CharacterDataHandler = builder.data
    parser.StartDoctypeDeclHandler = parser.ExternalEntityRefHandler = refuse
    try:
        parser.Parse(raw, True)
    except expat.ExpatError as exc:
        raise ValueError(f"invalid XML: {exc}") from exc
    return builder.close()


class NonPackageDocument(ValueError):
    """A recognized source asset whose filename also occurs in ROS package discovery."""


def describe(raw, filename, directory_name=None):
    root = read_xml(raw)
    child_tags = {child.tag for child in root}
    if root.tag == "model" and {"name", "sdf"} <= child_tags:
        raise NonPackageDocument("Gazebo model description")
    if root.tag == "launch" and "node" in child_tags:
        raise NonPackageDocument("ROS launch description")
    if root.tag == "Package" and {"DisplayName", "Version", "ReleaseDate"} <= child_tags:
        raise NonPackageDocument("Qt Installer Framework component")
    if root.tag != "package" or filename not in ("manifest.xml", "package.xml"):
        raise ValueError("expected a ROS package manifest")
    legacy = filename == "manifest.xml"
    names = root.findall("name")
    if len(names) > 1 or (names and list(names[0])):
        raise ValueError("ambiguous package identity")
    name = (names[0].text or "").strip() if names else ""
    origin = "manifest"
    if legacy and not name and directory_name:
        name, origin = directory_name, "rosbuild-directory"
    if not name or any(c.isspace() or c in "/\\\x00" for c in name) or name in (".", ".."):
        raise ValueError("missing or invalid package name")
    versions = root.findall("version")
    if len(versions) > 1:
        raise ValueError("ambiguous package version")
    version = (versions[0].text or "").strip() if versions else None
    dependencies = []
    for elem in root:
        if elem.tag not in DEPENDS:
            continue
        value = (elem.text or "").strip()
        attrs = dict(elem.attrib)
        if legacy and elem.tag == "depend":
            value = attrs.pop("package", value)
        if legacy and elem.tag == "rosdep":
            value = attrs.pop("name", value)
        if not value or list(elem):
            raise ValueError("invalid dependency declaration: " + elem.tag)
        dependencies.append({"kind": elem.tag, "name": value, "attributes": attrs})
    exports = [dict(tag=e.tag, value=(e.text or "").strip(), attributes=dict(e.attrib))
               for block in root.findall("export") for e in block]
    return dict(name=name, name_origin=origin, format="rosbuild" if legacy else root.get("format", "1"),
                version=version, dependencies=dependencies, exports=exports,
                sha256=hashlib.sha256(raw).hexdigest())


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("manifest", type=Path)
    args = parser.parse_args()
    try:
        with args.manifest.open("rb") as stream:
            result = describe(stream.read(MAX_MANIFEST + 1), args.manifest.name, args.manifest.parent.resolve().name)
    except (OSError, ValueError) as exc:
        parser.exit(1, f"{exc}\n")
    print(json.dumps(result, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
