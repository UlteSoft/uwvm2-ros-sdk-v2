"""Validate supplied producer checkouts with more than one locked source patch."""
import hashlib
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools/wasm/memtag"))
from build_sysroots import source_tree


class CheckoutTests(unittest.TestCase):
    def test_ordered_patches_and_unrecorded_files(self):
        with tempfile.TemporaryDirectory(dir=ROOT / ".tmp") as temporary:
            work = Path(temporary)
            source = work / "checkout"
            source.mkdir()

            def git(*args):
                return subprocess.check_output(["git", "-c", "user.name=SDK", "-c", "user.email=sdk@localhost",
                                                *args], cwd=source)

            git("init", "-q")
            existing, added = source / "existing", source / "added"
            existing.write_text("one\n")
            git("add", "existing")
            git("commit", "-qm", "release")
            entry = dict(revision=git("rev-parse", "HEAD").decode().strip(), patches=[])
            existing.write_text("two\n")
            first = git("diff", "HEAD")
            git("add", "existing")
            existing.write_text("three\n")
            added.write_text("recorded\n")
            git("add", "-N", "added")
            for i, data in enumerate((first, git("diff"))):
                patch = work / f"{i}.patch"
                patch.write_bytes(data)
                entry["patches"].append(dict(path=str(patch), sha256=hashlib.sha256(data).hexdigest()))
            index = source / ".git/index"
            before = index.read_bytes()
            self.assertEqual(source_tree(entry, source, work, None), source)
            added.write_text("other\n")
            with self.assertRaises(subprocess.CalledProcessError):
                source_tree(entry, source, work, None)
            added.write_text("recorded\n")
            extra = source / "unexpected"
            extra.touch()
            with self.assertRaisesRegex(ValueError, "unrecorded files"):
                source_tree(entry, source, work, None)
            extra.unlink()
            entry["patches"][0]["sha256"] = "incorrect"
            with self.assertRaisesRegex(ValueError, "hash mismatch"):
                source_tree(entry, source, work, None)
            self.assertEqual(index.read_bytes(), before)


if __name__ == "__main__":
    unittest.main()
