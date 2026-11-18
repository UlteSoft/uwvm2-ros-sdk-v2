"""Verify selective retrieval and atomic publication using only committed Git objects."""
import json,hashlib,sys,subprocess,tempfile,unittest
from pathlib import Path
root=Path(__file__).resolve().parents[1];sys.path.insert(0,str(root/"install"))
from bootstrap import Source,install
class Installer(unittest.TestCase):
    def setUp(self):
        tmp=root/".tmp";tmp.mkdir(exist_ok=True);self.tmp=tempfile.TemporaryDirectory(dir=tmp)
        self.prefix=Path(self.tmp.name); self.commit=subprocess.check_output(["git","-C",str(root),"rev-parse","HEAD"],text=True).strip()
    def tearDown(self):self.tmp.cleanup()
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
            install(Source(self.commit,root),"unitree","java",self.prefix,[])
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
