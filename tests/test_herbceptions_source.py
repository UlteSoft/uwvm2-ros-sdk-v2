"""Check failure handling without compiling LLVM or unpacking a full source tree."""
from pathlib import Path
import runpy
import shutil
import tempfile
import unittest


SDK = Path(__file__).resolve().parents[1]
SOURCE = runpy.run_path(str(SDK / "tools/wasm/herbceptions/recover_source.py"))


class HerbceptionsSourceTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.sdk = Path(self.temp.name) / "sdk"
        self.output = Path(self.temp.name) / "recovered"
        vendor = Path("third-parties/sources") / SOURCE["DELTA"]
        self.vendor = self.sdk / vendor
        self.vendor.mkdir(parents=True)
        shutil.copyfile(SDK / vendor / "source.json", self.vendor / "source.json")

    def test_descriptor_is_pinned(self):
        with (self.vendor / "source.json").open("ab") as stream:
            stream.write(b" ")
        with self.assertRaisesRegex(ValueError, "descriptor hash"):
            SOURCE["recover"](self.output, self.sdk)
        self.assertFalse(self.output.exists())

    def test_existing_destination_is_preserved(self):
        self.output.mkdir()
        sentinel = self.output / "local-file"
        sentinel.write_bytes(b"owned by the caller")
        with self.assertRaises(FileExistsError):
            SOURCE["recover"](self.output, self.sdk)
        self.assertEqual(sentinel.read_bytes(), b"owned by the caller")

    def test_corrupt_delta_is_rejected_before_extraction(self):
        (self.vendor / "part-000").write_bytes(b"truncated")
        with self.assertRaisesRegex(ValueError, "delta chunk hash"):
            SOURCE["recover"](self.output, self.sdk)
        self.assertEqual(sorted(p.name for p in self.sdk.parent.iterdir()), ["sdk"])


if __name__ == "__main__":
    unittest.main()
