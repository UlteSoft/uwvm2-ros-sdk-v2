"""Verify selective retrieval and atomic publication using only committed Git objects."""
import io,json,hashlib,sys,subprocess,tempfile,unittest
import ssl
import urllib.error
from unittest.mock import patch
from pathlib import Path
root=Path(__file__).resolve().parents[1];sys.path.insert(0,str(root/"install"))
from bootstrap import Source,install
class Installer(unittest.TestCase):
    def setUp(self):
        tmp=root/".tmp";tmp.mkdir(exist_ok=True);self.tmp=tempfile.TemporaryDirectory(dir=tmp)
        self.prefix=Path(self.tmp.name); self.commit=subprocess.check_output(["git","-C",str(root),"rev-parse","HEAD"],text=True).strip()
    def tearDown(self):self.tmp.cleanup()
    def test_http_retry_keeps_the_pinned_selection(self):
        path = "install/revision.py"
        for failure in (TimeoutError(), urllib.error.URLError(ssl.SSLEOFError())):
            with self.subTest(error=repr(failure)):
                source = Source(self.commit)
                with patch.object(source.http, "open", side_effect=[failure, io.BytesIO(b"abc")]) as opened, \
                     patch("bootstrap.time.sleep"):
                    self.assertEqual(source.read(path, 3), b"abc")
                self.assertEqual(source.requested, [path, path])
                self.assertEqual(opened.call_args_list[0], opened.call_args_list[1])

    def test_http_refusals_and_retry_bound(self):
        failures = [(TimeoutError(), 3),
                    (urllib.error.HTTPError("", 403, "Forbidden", {}, None), 1),
                    (urllib.error.URLError(ssl.SSLCertVerificationError()), 1)]
        for failure, attempts in failures:
            with self.subTest(error=type(failure).__name__):
                source = Source(self.commit)
                with patch.object(source.http, "open", side_effect=failure) as opened, patch("bootstrap.time.sleep"):
                    with self.assertRaisesRegex(ValueError, "could not retrieve install/revision.py"):
                        source.read("install/revision.py", 8)
                self.assertEqual(opened.call_count, attempts)

    def test_explicit_site_refusal_is_atomic(self):
        profile = self.prefix / "site.json"
        profile.write_text("{}")
        source = Source(self.commit, root)
        with self.assertRaisesRegex(ValueError, "site verification failed"):
            install(source, "unitree", "c", self.prefix, [], site_profile=profile)
        with self.assertRaisesRegex(ValueError, "site verification failed"):
            install(source, "unitree", "fortran", self.prefix, [], site_profile=profile)
        self.assertFalse((self.prefix / self.commit / "unitree/fortran/development").exists())
        destination = self.prefix / self.commit / "unitree/c/development"
        self.assertFalse(destination.exists())
        install(source, "unitree", "c", self.prefix, [])
        with self.assertRaisesRegex(ValueError, "site verification failed"):
            install(source, "unitree", "c", self.prefix, [], site_profile=profile)
        self.assertFalse((destination / "share/qualification/site-profile.json").exists())
        self.assertTrue(install(source, "unitree", "c", self.prefix, [])["reused"])
        with self.assertRaisesRegex(ValueError, "development installation"):
            install(source, "unitree", "c", self.prefix, ["--component", "protocol"], site_profile=profile)

    def test_public_executable_names(self):
        from revision import COMPILER_COMMANDS

        names = set(COMPILER_COMMANDS.values())
        self.assertNotIn("wrar", names)
        for name in names:
            self.assertRegex(name, r"\Awr[a-z][a-z0-9]*\Z")
        tree = subprocess.check_output(
            ["git", "-C", str(root), "ls-tree", "-z", self.commit + ":bin"]
        )
        for entry in tree.rstrip(b"\0").split(b"\0"):
            attributes, path = entry.split(b"\t", 1)
            with self.subTest(path=path):
                mode, kind, _ = attributes.split()
                self.assertEqual((mode, kind), (b"100755", b"blob"))
                self.assertIn(path.decode("ascii"), names | {"wrar"})

    def test_installed_compiler_command_names(self):
        from revision import COMPILER_COMMANDS, DEVELOPMENT, LANGUAGES

        self.assertEqual(set(COMPILER_COMMANDS), set(LANGUAGES) - {"c_ffi_bridge"})
        self.assertEqual(len(COMPILER_COMMANDS), len(set(COMPILER_COMMANDS.values())))
        self.assertEqual([COMPILER_COMMANDS[k] for k in ("java", "csharp", "kotlin")],
                         ["wrjava", "wrcs", "wrkt"])
        for language in (*DEVELOPMENT, "java", "kotlin"):
            with self.subTest(language=language):
                options = [] if language in DEVELOPMENT else ["--component", "synchronous-aot"]
                installed = install(Source(self.commit, root), "unitree", language, self.prefix, options)
                directory = Path(installed["directory"])
                command = COMPILER_COMMANDS[language]
                metadata = json.loads((directory / "share/language" / (language + ".json")).read_text())
                self.assertEqual(metadata["command_name"], command)
                adapter = (directory / "language" / language / "xmake/adapter.lua").read_text()
                self.assertIn('program = "' + command + '"', adapter)
                help_text = subprocess.check_output([directory / "bin" / command, "--help"], text=True)
                self.assertIn("usage: " + command + " ", help_text)
                self.assertLessEqual({p.name for p in (directory / "bin").iterdir()},
                                     {command, "wrar", "wrc", "wrcc"})

    def test_shared_compiler_source_selection(self):
        for language in ("c", "cpp", "fortran", "lua", "objectc", "rs", "tinygo", "nim"):
            with self.subTest(language=language):
                source = Source(self.commit, root)
                plan = install(source, "kuka", language, self.prefix, ["--component", "compiler-source"], plan=True)
                self.assertIn("compiler-source", plan["packages"])
                self.assertEqual([p for p in plan["packages"] if p.startswith("languages/")],
                                 ["languages/" + language])
                self.assertTrue(all(p.startswith("install/") for p in source.requested))
    def test_selective_and_retry(self):
        source=Source(self.commit,root)
        plan=install(source,"unitree","c",self.prefix,[],True)
        self.assertTrue(all(p.startswith("install/") for p in source.requested))
        source.requested.clear();res=install(source,"unitree","c",self.prefix,[])
        self.assertEqual(res["files"],plan["files"]);self.assertTrue((Path(res["directory"])/"bin/wrc").is_file())
        self.assertFalse(any("franka" in p or "bin/wrcc" in p or "third-parties" in p for p in source.requested))
        source.requested.clear();self.assertTrue(install(source,"unitree","c",self.prefix,[])["reused"])
        self.assertTrue(all(p.startswith("install/") for p in source.requested))
    def test_digest_failure_no_partial_install(self):
        class Changed(Source):
            def read(self,path,limit):
                result=super().read(path,limit)
                return b"changed" if path=="bin/wrc" else result
        with self.assertRaisesRegex(ValueError,"digest mismatch"):
            install(Changed(self.commit,root),"unitree","c",self.prefix,[])
        self.assertFalse((self.prefix/self.commit/"unitree/c/development").exists())
    def test_incomplete_language_denied(self):
        with self.assertRaisesRegex(ValueError,"has not been published"):
            install(Source(self.commit,root),"unitree","c_ffi_bridge",self.prefix,[])
    def test_no_mutable_refs(self):
        with self.assertRaises(ValueError):Source("main",root)
    def test_cpp_selection_builds_c_dependencies(self):
        source=Source(self.commit,root)
        result=install(source,"unitree","cpp",self.prefix,[])
        installed=Path(result["directory"])
        for name in ("wrc","wrcc","wrar"):
            self.assertTrue((installed/"bin"/name).is_file())
        self.assertFalse(any("third-parties" in p or "platform/franka" in p for p in source.requested))
if __name__=="__main__":unittest.main()
