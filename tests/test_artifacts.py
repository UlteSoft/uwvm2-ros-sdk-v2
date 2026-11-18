"""Reject inconsistent or hostile build inputs before invoking a compiler."""
import hashlib
import json
from pathlib import Path
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "install"))
import artifacts as a
from compiler import expand_responses
from frontend import audit
from guest_profile import Profile


def section(kind, data):
    return bytes([kind]) + a.uleb(len(data)) + data


def string(text):
    data = text.encode()
    return a.uleb(len(data)) + data


def imported(name, width):
    types = section(1, bytes([1, 0x60, 2, width, width, 1, 0x7f]))
    imports = section(2, b"\1" + string("wasi_snapshot_preview1") + string(name) + b"\0\0")
    return a.MAGIC + types + imports


class BuildInputTests(unittest.TestCase):
    def setUp(self):
        self.profile = Profile().to_dict()
        self.compiler = "a" * 64
        self.raw = a.MAGIC + section(0, string("linking") + b"\2")
        self.object = a.seal_object(self.raw, self.profile, self.compiler, "c" * 64)

    def test_note_integrity_and_profile(self):
        self.assertEqual(a.check_object(self.object)["object_sha256"], hashlib.sha256(self.raw).hexdigest())
        for data in (self.raw, self.object + b"\0\0", self.object[:-1], self.object.replace(b"linking", b"linkina"),
                     self.object.replace(b'"schema":', b'"schema":"duplicate","schema":')):
            with self.assertRaises(ValueError): a.check_object(data)
        for profile, compiler in ((Profile(64).to_dict(), self.compiler), (self.profile, "b" * 64),
                                  (Profile(mte=False).to_dict(), self.compiler),
                                  (Profile(exceptions="noeh").to_dict(), self.compiler),
                                  (Profile(threads=True).to_dict(), self.compiler)):
            with self.assertRaisesRegex(ValueError, "mismatch"): a.check_object(self.object, profile, compiler)

    def test_mte_and_closure_required(self):
        with self.assertRaisesRegex(ValueError, "WasmMTE"):
            a.seal_object(self.raw, Profile(mte=False).to_dict(), self.compiler, "c" * 64)
        with self.assertRaisesRegex(ValueError, "closure mismatch"):
            a.check_object(self.object, self.profile, self.compiler, "d" * 64)

    def test_archive_envelope(self):
        def member(name, body):
            return name.ljust(16, b" ") + b"0           0     0     644     " + str(len(body)).encode().ljust(10) + b"`\n" + body + (b"\n" if len(body) & 1 else b"")
        valid = b"!<arch>\n" + member(b"u000000.o/", self.object)
        self.assertEqual(a.archive_members(valid), [self.object])
        for data in (b"!<thin>\n", b"!<arch>\n", valid[:-1], valid + b"x",
                     valid + valid[8:], b"!<arch>\n" + member(b"../u.o/", self.object),
                     b"!<arch>\n" + member(b"/0", self.object)):
            with self.assertRaises(ValueError): a.archive_members(data)

    def test_address_specific_imports(self):
        for bits in (32, 64):
            profile = Profile(bits)
            suffix = "_wasm64" if bits == 64 else ""
            width = 0x7e if bits == 64 else 0x7f
            for name in ("environ_get", "environ_sizes_get"):
                audit(imported(name + suffix, width), profile)
                with self.assertRaises(ValueError): audit(imported(name + suffix, width ^ 1), profile)
                with self.assertRaises(ValueError): audit(imported(name + ("" if suffix else "_wasm64"), width), profile)
            for name in ("sock_send", "path_open", "fd_write"):
                with self.assertRaises(ValueError): audit(imported(name + suffix, width), profile)

    def test_response_graph_limits(self):
        (ROOT / ".tmp").mkdir(exist_ok=True)
        with tempfile.TemporaryDirectory(dir=ROOT / ".tmp") as directory:
            work = Path(directory)
            (work / "quoted").write_text('-DNAME="two words" plain.c')
            self.assertEqual(expand_responses(["@quoted"], work), ["-DNAME=two words", "plain.c"])
            (work / "cycle").write_text("@cycle")
            with self.assertRaisesRegex(ValueError, "cyclic"): expand_responses(["@cycle"], work)
            for index in range(17):
                (work / str(index)).write_text("@" + str(index + 1) if index < 16 else "input.c")
            with self.assertRaisesRegex(ValueError, "depth"): expand_responses(["@0"], work)
            (work / "many").write_text("x " * 65537)
            with self.assertRaisesRegex(ValueError, "argument"): expand_responses(["@many"], work)
            (work / "big").write_bytes(b" " * (8 * 1024 * 1024 + 1))
            with self.assertRaisesRegex(ValueError, "byte"): expand_responses(["@big"], work)


if __name__ == "__main__":
    unittest.main()
