"""Check sysroot input identity and recovery of an identical rebuilt source directory."""
import hashlib
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT/"tools/wasm/memtag"))
import build_producer
from herbceptions_sysroot import TOOLS, verified_sources, verify_exception_bridge


class SourceTests(unittest.TestCase):
    def setUp(self):
        scratch = ROOT/".tmp"
        scratch.mkdir(exist_ok=True)
        self.tmp = tempfile.TemporaryDirectory(dir=scratch)
        self.addCleanup(self.tmp.cleanup)
        self.work = Path(self.tmp.name)
        self.source = self.work/"source"
        self.source.mkdir()
        (self.source/"runtime.c").write_text("test source\n")
        self.tools = self.work/"toolchain"
        (self.tools/"bin").mkdir(parents=True)
        for name in TOOLS:
            (self.tools/"bin"/name).write_text(name+"\n")
        self.entry = dict(revision="a"*40, tree="b"*40, patches=[])
        self.row = dict(schema="uwvm-memtag-producer-build-v1", producer="herbceptions", source=self.entry,
                        status="built-awaiting-qualification", prepared_source=str(self.source),
                        prepared_inventory_sha256=build_producer.prepared_inventory_digest(build_producer.inventory(self.source)),
                        binaries={n:build_producer.digest(self.tools/"bin"/n) for n in TOOLS})
        self.receipt = self.work/"receipt.json"
        self.save()
        stub = patch.object(build_producer,"herbceptions_entry",return_value=self.entry)
        stub.start()
        self.addCleanup(stub.stop)

    def save(self):
        self.receipt.write_text(json.dumps(self.row))

    def verify(self):
        return verified_sources(self.tools,self.receipt,None,self.work)

    def test_exact_sources_and_tools(self):
        self.assertEqual(self.verify(), (self.source, hashlib.sha256(self.receipt.read_bytes()).hexdigest()))

    def test_source_modified(self):
        (self.source/"runtime.c").write_text("different\n")
        with self.assertRaisesRegex(ValueError,"inventory"):
            self.verify()

    def test_runtime_archiver_modified(self):
        (self.tools/"bin/llvm-ar").write_text("different")
        with self.assertRaisesRegex(ValueError,"llvm-ar"):
            self.verify()

    def test_unfinished_or_wrong_source(self):
        for changes in (dict(status="building"),dict(source=dict(revision="different")),dict(producer="stable")):
            with self.subTest(change=changes):
                receipt=self.row | changes
                self.receipt.write_text(json.dumps(receipt))
                with self.assertRaisesRegex(ValueError,"source-locked"):
                    self.verify()

    def test_missing_tree_recovers_and_rechecks(self):
        self.row["prepared_source"]=str(self.work/"absent")
        self.save()
        with patch.object(build_producer,"prepare_herbceptions",return_value=self.source) as recover:
            self.assertEqual(self.verify()[0], self.source)
            recover.assert_called_once_with(self.work)

    def test_exception_bridge_requires_exactly_one_pair(self):
        triple = "wasm32-wasip1"
        archive = self.work/"lib"/triple/"libc++abi.a"
        archive.parent.mkdir(parents=True)
        archive.write_bytes(b"test archive")
        domain = "00000001 W __cxa_error_domain_itanium_exception_ptr\n"
        cast = "00000002 T __cxa_error_code_itanium_exception_ptr_cast\n"
        for expected, symbols, valid in [
            (True, domain+cast, True), (False, "", True), (True, "", False),
            (True, domain+domain+cast, False), (True, domain, False), (False, domain+cast, False),
        ]:
            with self.subTest(expected=expected,symbols=symbols), patch(
                    "herbceptions_sysroot.subprocess.check_output", return_value=symbols):
                if valid:
                    self.assertEqual(verify_exception_bridge(self.work,triple,self.tools,expected)["enabled"], expected)
                else:
                    with self.assertRaisesRegex(ValueError,"Itanium exception bridge"):
                        verify_exception_bridge(self.work,triple,self.tools,expected)


if __name__ == "__main__":
    unittest.main()
