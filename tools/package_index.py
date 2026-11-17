"""Create content-addressed file lists used by this SDK commit."""
import hashlib,json
from pathlib import Path
root=Path(__file__).resolve().parents[1]

def write(path,value):
    p=root/path;p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(value,indent=2)+"\n")

def package(name, paths):
    entries=[]
    for path in sorted(set(paths)):
        p=root/path
        if not p.is_file() or p.is_symlink():raise ValueError(path)
        with p.open("rb") as f:digest=hashlib.file_digest(f,"sha256").hexdigest()
        entries.append({"path":path,"bytes":p.stat().st_size,"mode":493 if path.startswith("bin/") else 420,"sha256":digest})
    write("install/packages/"+name+".json",{"files":entries})

def main():
    registry=json.loads((root/"share/targets.json").read_text())
    package("license", ["LICENSE"])
    for language, path in {"c": "include/wros/scene.h", "rs": "language/rust/scene.rs", "as": "language/assemblyscript/scene.ts"}.items():
        package("bindings/" + language, [path])
    package("protocol",["share/abi/ros.json","LICENSE"])
    for platform in registry["platforms"]:
        package("platforms/"+platform,["platform/"+platform+"/sources.json"])
    for language in registry["languages"]:
        meta="share/language/"+language+".json"
        write(meta,{"id":language,"development_package":language in ("c","cpp","rs","as")})
        package("metadata/"+language,[meta])
    package("languages/c",["bin/wrc","include/wros/scene.h"])
    package("languages/cpp",["bin/wrcc","include/wros/scene.h"])
    package("languages/rs",["language/rust/scene.rs"])
    package("languages/as",["language/assemblyscript/scene.ts"])
    package("frontend",["install/"+filename for filename in ["frontend.py","imports.py","guest_profile.py","compiler.py"]])
    package("compiler-source",[p.relative_to(root).as_posix() for top in ("tools/wasm/memtag","third-parties/sources")
                               for p in (root/top).rglob("*") if p.is_file() and "__pycache__" not in p.parts])

if __name__=="__main__":main()
