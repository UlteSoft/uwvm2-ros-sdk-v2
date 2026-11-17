"""Exercise one unchanged bootstrap against two different committed selection hooks."""
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]


class RevisionCompatibility(unittest.TestCase):
    def test_revision_option_and_cross_commit_payload_reuse(self):
        scratch = ROOT / ".tmp"
        scratch.mkdir(exist_ok=True)
        with tempfile.TemporaryDirectory(dir=scratch) as directory:
            repo = Path(directory) / "repo"
            repo.mkdir()
            subprocess.run(["git", "init", "-q", repo], check=True)
            prefix = Path(directory) / "installed"
            bootstrap = ROOT / "install/bootstrap.py"

            def put(name, body):
                path = repo / name
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(body)

            def package(key, path, body):
                put(path, body)
                row = dict(path=path, bytes=len(body), mode=0o644, sha256=hashlib.sha256(body).hexdigest())
                put("install/packages/" + key + ".json", json.dumps({"files": [row]}).encode())

            def commit(label):
                subprocess.run(["git", "-C", repo, "add", "."], check=True)
                subprocess.run(["git", "-C", repo, "-c", "user.name=Fixture", "-c",
                                "user.email=fixture@example.invalid", "commit", "-qm", label], check=True)
                return subprocess.check_output(["git", "-C", repo, "rev-parse", "HEAD"], text=True).strip()

            def run(action, revision, *extensions):
                args = [sys.executable, "-I", "-B", bootstrap, action, "--commit", revision,
                        "--language", "c", "--platform", "unitree", "--prefix", prefix,
                        "--local-repository", repo]
                return subprocess.check_output(args + (["--", *extensions] if extensions else []), text=True)

            package("shared", "LICENSE", b"common licence")
            put("install/revision.py", b'import json\nprint(json.dumps(dict(variant="base",packages=["shared"])))\n')
            first = commit("Initial selection")
            install_a = json.loads(run("install", first))
            self.assertIn("LICENSE", install_a["requested_paths"])

            package("extension", "include/extra.h", b"/* new declaration */\n")
            put("install/revision.py", b"""import json, sys
if "--revision-help" in sys.argv:
    print(json.dumps({"help": "--extra-header"}))
elif "--extra-header" in sys.argv:
    print(json.dumps({"variant": "extra", "packages": ["shared", "extension"]}))
else:
    print(json.dumps({"variant": "base", "packages": ["shared"]}))
""")
            second = commit("Publish a revision-specific header")
            self.assertIn("--extra-header", run("revision-help", second))
            install_b = json.loads(run("install", second, "--extra-header"))
            self.assertEqual(install_b["requested_paths"], ["install/revision.py", "install/packages/shared.json",
                             "install/packages/extension.json", "include/extra.h"])
            self.assertTrue((Path(install_b["directory"]) / "include/extra.h").is_file())
            self.assertFalse((Path(install_a["directory"]) / "include/extra.h").exists())
            self.assertTrue(json.loads(run("install", first))["reused"])


if __name__ == "__main__":
    unittest.main()
