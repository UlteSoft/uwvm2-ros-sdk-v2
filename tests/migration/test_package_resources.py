"""Regression tests for the public resource lock, pack and manifest commands."""
import hashlib
import io
import json
import os
from pathlib import Path
import struct
import subprocess
import sys
import tempfile
import unittest

TOOLS = Path(__file__).resolve().parents[2] / "tools/migration"
sys.path.insert(0, str(TOOLS))
from package_manifest import describe, NonPackageDocument
from package_resources import collect, parts, write_pack

XML = b'<package format="3"><name>arm</name><version>1.0.0</version><depend condition="$ROS_VERSION == 2" version_gte="1.0">tf</depend></package>'


class PackageResources(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.tmp = Path(tmp.name)
        self.root = self.tmp / "source"
        self.root.mkdir()
        (self.root / "package.xml").write_bytes(XML)
        self.resource = self.root / "arm 1.urdf"
        self.resource.write_bytes(b"payload\0")
        self.uri = "package://arm/arm%201.urdf"

    def command(self, *args):
        return subprocess.run([sys.executable, "-B", str(TOOLS / "package_resources.py"), *args],
                              cwd=self.tmp, capture_output=True)

    def test_exact_lock_and_failed_update(self):
        common = ["--package-root", str(self.root)]
        create = ["lock", *common, "--uri", self.uri, "--output", "lock"]
        pack = ["pack", *common, "--lock", "lock", "--output", "data"]
        self.assertEqual(self.command(*create).returncode, 0)
        original = (self.tmp / "lock").read_bytes()
        locked = json.loads(original)
        self.assertEqual(locked, [dict(uri=self.uri, sha256=hashlib.sha256(self.resource.read_bytes()).hexdigest(),
                                       manifest_sha256=hashlib.sha256(XML).hexdigest())])
        self.assertEqual(self.command(*pack).returncode, 0)
        data = (self.tmp / "data").read_bytes()
        self.assertEqual(struct.unpack_from("<8sIIIIII", data),
                         (b"WROSRES\0", 1, 32, 32, len(self.uri), 32 + len(self.uri), 8))
        self.assertEqual(data[32:], self.uri.encode() + b"payload\0")
        (self.root / "package.xml").write_bytes(XML + b" ")
        self.assertNotEqual(self.command(*pack).returncode, 0)
        (self.root / "package.xml").write_bytes(XML)
        self.resource.write_bytes(b"changed")
        self.assertNotEqual(self.command(*pack).returncode, 0)
        self.resource.write_bytes(b"payload\0")
        (self.tmp / "lock").write_bytes(original.replace(b'"uri":', b'"uri":"x","uri":'))
        self.assertNotEqual(self.command(*pack).returncode, 0)
        self.assertEqual((self.tmp / "data").read_bytes(), data)

    def test_exact_uri_and_rank(self):
        for value in ["file://x", "package://arm/..", "package://arm/a%2Fb", "package://arm/%2e%2e",
                      "package://arm/arm 1.urdf", "package://arm//name", "package://arm/d%00",
                      "package://arm/%FF", "package://arm/a?b", "package://arm/dir%5Cfile"]:
            with self.subTest(value=value), self.assertRaises(ValueError):
                parts(value)
        self.assertEqual(parts("package://arm/%E8%BD%B4"), ("arm", ["轴"]))
        for roots, entries in [([self.root] * 2, [self.uri]), ([self.root], [self.uri] * 2),
                               ([self.root], ["package://foreign/arm"])]:
            with self.assertRaises(ValueError):
                collect(roots, entries, False)
        (self.root / "zero").touch()
        rows = collect([self.root], ["package://arm/zero", self.uri], False)
        self.assertEqual([entry["uri"] for entry, _ in rows], [self.uri, "package://arm/zero"])
        self.assertEqual(rows[1][1], b"")

    def test_links_and_non_regular(self):
        (self.tmp / "outside").mkdir()
        (self.tmp / "outside/secret").write_bytes(b"other")
        (self.root / "subdir").symlink_to(self.tmp / "outside", target_is_directory=True)
        (self.root / "link").symlink_to(self.tmp / "outside/secret")
        os.mkfifo(self.root / "fifo")
        for relative in ["subdir/secret", "link", "fifo"]:
            with self.subTest(relative=relative), self.assertRaises((OSError, ValueError)):
                collect([self.root], ["package://arm/" + relative], False)
        link = self.tmp / "linked-root"
        link.symlink_to(self.root, target_is_directory=True)
        with self.assertRaises(OSError):
            collect([link], [self.uri], False)

    def test_manifest(self):
        self.assertEqual(describe(XML, "package.xml")["dependencies"], [
            dict(kind="depend", name="tf", attributes={"condition": "$ROS_VERSION == 2", "version_gte": "1.0"})])
        legacy = b'<package><depend package="geometry"/></package>'
        self.assertEqual(describe(legacy, "manifest.xml", "arm")["name"], "arm")
        with self.assertRaises(NonPackageDocument):
            describe(b"<model><name>lamp</name><sdf>lamp.sdf</sdf></model>", "manifest.xml", "arm")
        for raw in [b'<!DOCTYPE package SYSTEM "local"><package/>',
                    b"<package><name>arm</name><name>leg</name></package>",
                    b"<package><name>arm</name><depend/></package>"]:
            with self.assertRaises(ValueError):
                describe(raw, "package.xml")


if __name__ == "__main__":
    unittest.main()
