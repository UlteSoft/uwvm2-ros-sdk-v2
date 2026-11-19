"""Check release identity and reporting for published and metadata-only languages."""
import json
from pathlib import Path
import runpy
import tempfile
import unittest


SDK = Path(__file__).resolve().parents[1]
tools = runpy.run_path(str(SDK / "tools/qualification/language_sources.py"))


class LanguageReleaseTests(unittest.TestCase):
    def test_unpublished_selection_has_no_producer(self):
        self.assertEqual(tools["audit"](SDK, "go")[0]["status"], "no-development-package")

    def test_version_string_is_insufficient(self):
        with tempfile.TemporaryDirectory() as work:
            root = Path(work)
            (root / "producer.json").write_text(json.dumps({"version": "2.3", "revision": "unreleased"}))
            checks = [{"path": "producer.json", "keys": ["revision"], "equals": "official-commit"}]
            self.assertTrue(tools["check_component"](root, {"checks": checks}))

    def test_unbound_site_fails_closed(self):
        self.assertTrue(tools["check_component"](SDK, {"checks": []}))


if __name__ == "__main__":
    unittest.main()
