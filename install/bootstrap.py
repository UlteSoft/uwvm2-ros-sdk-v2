#!/usr/bin/env python3
"""Install a language/platform selection from an immutable WROS SDK commit."""
import argparse
import hashlib
import http.client
import json
import os
from pathlib import Path, PurePosixPath
import re
import shutil
import ssl
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.request

REPO = "UlteSoft/uwvm2-ros-sdk-v2"
MAX_METADATA = 2 * 1024 * 1024
MAX_FILE = 128 * 1024 * 1024
MAX_TOTAL = 1024 * 1024 * 1024

def name(value):
    if not re.fullmatch(r"[a-z0-9][a-z0-9_-]{0,95}", value):
        raise ValueError("invalid selection name")
    return value

def relative(value):
    if not isinstance(value,str) or not re.fullmatch(r"[A-Za-z0-9_+./-]{1,256}",value):
        raise ValueError("invalid repository path")
    path=PurePosixPath(value)
    if path.is_absolute() or str(path)!=value or any(x in ("..",".git",".tmp") for x in path.parts) or not path.parts:
        raise ValueError("unsafe repository path")
    return value

class DirectHTTPS(urllib.request.HTTPRedirectHandler):
    def redirect_request(self,*args):
        raise ValueError("unexpected repository redirect")

class Source:
    def __init__(self,commit,local=None):
        if not re.fullmatch("[0-9a-f]{40}",commit):
            raise ValueError("--commit requires a full lowercase Git commit ID")
        self.commit=commit
        self.local=local
        self.requested=[]
        self.http=urllib.request.build_opener(DirectHTTPS())
        if local:
            actual=subprocess.check_output(["git","-C",str(local),"cat-file","-t",commit],text=True).strip()
            if actual!="commit":raise ValueError("selected object is not a commit")

    def read(self,path,limit):
        path=relative(path)
        self.requested.append(path)
        if self.local:
            cmd=["git","-C",str(self.local),"cat-file"]
            key=self.commit+":"+path
            size=int(subprocess.check_output([*cmd,"-s",key]))
            if size>limit:raise ValueError("repository file exceeds bound: "+path)
            data=subprocess.check_output([*cmd,"blob",key])
        else:
            url="https://raw.githubusercontent.com/"+REPO+"/"+self.commit+"/"+path
            for attempt in range(3):
                try:
                    with self.http.open(url, timeout=60) as response:
                        data=response.read(limit+1)
                    break
                except (OSError, http.client.IncompleteRead) as error:
                    cause = error.reason if isinstance(error, urllib.error.URLError) else error
                    transient = isinstance(cause, (TimeoutError, ConnectionError, http.client.IncompleteRead, ssl.SSLEOFError))
                    if isinstance(error, urllib.error.HTTPError):
                        transient = error.code in (408, 429, 500, 502, 503, 504)
                        error.close()
                    if not transient or attempt == 2:
                        raise ValueError(f"could not retrieve {path}: {error}") from error
                    time.sleep(2**attempt)
                    self.requested.append(path)
        if len(data)>limit:raise ValueError("repository file exceeds bound: "+path)
        return data

def selection(source,platform,language,options):
    with tempfile.TemporaryDirectory() as scratch:
        hook=Path(scratch)/"revision.py"
        hook.write_bytes(source.read("install/revision.py",MAX_METADATA))
        # The operator explicitly selects and trusts the official SDK commit.
        # This hook supplies package names. Only the fixed bootstrap installs files.
        argv=[sys.executable,"-I","-B",str(hook),platform,language,*options]
        result=subprocess.run(argv,cwd=scratch,capture_output=True,timeout=20)
        if result.returncode:raise ValueError(result.stderr.decode(errors="replace").strip())
        if len(result.stdout)>MAX_METADATA:raise ValueError("oversized revision response")
        return json.loads(result.stdout)

def configure_site(directory, language, data):
    config = directory / "share/qualification/site-profile.json"
    if (config.parent / "local-trust.json").exists():
        raise ValueError("existing operator trust configuration differs; select a fresh prefix")
    check = ("import sys; from pathlib import Path; root=Path(sys.argv[1]); "
             "sys.path.insert(0,str(root/'install')); from qualification import check_site; "
             "print(check_site(sys.stdin.buffer.read(),root,sys.argv[2]))")
    command = (["-c", check, str(directory), "c" if language in ("js", "typescript") else language] if language not in ("nim", "objectc", "d", "tinygo", "rs", "go")
               else [str(directory / "language" / ("rust" if language == "rs" else language) / "check_site.py")])
    if language in ("java", "kotlin"):
        command = [str(directory / "language/jvm/release.py"), language]
    result = subprocess.run([sys.executable, "-I", "-B", *command],
                            input=data, capture_output=True, timeout=120)
    if result.returncode:
        details = result.stderr.decode(errors="replace").strip().splitlines()
        raise ValueError("site verification failed: " + (details[-1] if details else str(result.returncode)))
    # Publish a complete file only if the selection has no prior site profile.
    with tempfile.NamedTemporaryFile(dir=config.parent) as staged:
        staged.write(data)
        staged.flush()
        try:
            os.link(staged.name, config)
        except FileExistsError:
            if config.is_symlink() or not config.is_file() or config.stat().st_size != len(data) or config.read_bytes() != data:
                raise ValueError("existing site profile differs; select a fresh prefix")
    return result.stdout.decode().strip()


def install(source,platform,language,prefix,options,plan=False,site_profile=None):
    platform,language=name(platform),name(language)
    selected=selection(source,platform,language,options)
    if "help" in selected:return selected
    variant=name(selected["variant"])
    site_data = None
    if site_profile is not None:
        if plan or variant != "development" or language not in ("java", "kotlin", "c", "cpp", "fortran", "js", "typescript", "lua", "nim", "objectc", "d", "tinygo", "rs", "go"):
            raise ValueError("--site-profile requires a supported language development installation")
        if not site_profile.is_file():
            raise ValueError("site profile must be an explicit local file")
        with site_profile.open("rb") as stream:
            site_data = stream.read(32769)
        if len(site_data) > 32768:
            raise ValueError("site profile exceeds 32 KiB")
    packages=selected["packages"]
    if not isinstance(packages,list) or not 0<len(packages)<=64:raise ValueError("invalid package selection")
    files={}; total=0
    for package in dict.fromkeys(packages):
        manifest=json.loads(source.read("install/packages/"+relative(package)+".json",MAX_METADATA))
        for row in manifest["files"]:
            target=relative(row["path"]);size=row["bytes"];digest=row["sha256"];mode=row["mode"]
            if not re.fullmatch("[0-9a-f]{64}",digest) or type(size)!=int or not 0<=size<=MAX_FILE or mode not in (420,493):
                raise ValueError("invalid package member: "+target)
            if target in files:
                if files[target]!=row:raise ValueError("conflicting package member: "+target)
                continue
            total+=size
            if len(files)>=8192 or total>MAX_TOTAL:raise ValueError("selection exceeds install budget")
            files[target]=row
    result={"commit":source.commit,"platform":platform,"language":language,"variant":variant,
            "packages":packages,"files":len(files),"bytes":total}
    if plan:return result
    root=prefix.resolve();dest=root/source.commit/platform/language/variant
    dest.parent.mkdir(parents=True,exist_ok=True)
    cache=root/".objects";cache.mkdir(exist_ok=True)
    def verify(path,row):
        if not path.is_file() or path.is_symlink() or path.stat().st_size!=row["bytes"]:return False
        with path.open("rb") as stream:return hashlib.file_digest(stream,"sha256").hexdigest()==row["sha256"]
    def installed():
        return all(verify(dest/path,row) and (dest/path).stat().st_mode&0o777==row["mode"] for path,row in files.items())
    if dest.exists():
        if not installed():raise ValueError("existing selection differs: "+str(dest))
        if site_data is not None:
            result["site_release_sha256"] = configure_site(dest, language, site_data)
        return {**result,"directory":str(dest),"reused":True}
    with tempfile.TemporaryDirectory(dir=dest.parent) as scratch:
        tree=Path(scratch)/"tree";tree.mkdir()
        for path,row in files.items():
            obj=cache/row["sha256"]
            if obj.exists():
                if not verify(obj,row):raise ValueError("cached digest mismatch: "+path)
            else:
                data=source.read(path,row["bytes"])
                if len(data)!=row["bytes"] or hashlib.sha256(data).hexdigest()!=row["sha256"]:
                    raise ValueError("download digest mismatch: "+path)
                staged=Path(scratch)/"object";staged.write_bytes(data);os.replace(staged,obj)
            target=tree/path;target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(obj,target)
            if not verify(target,row):raise ValueError("staging verification failed: "+path)
            target.chmod(row["mode"])
        if site_data is not None:
            result["site_release_sha256"] = configure_site(tree, language, site_data)
        try:tree.rename(dest)
        except OSError:
            if not dest.exists() or not installed():raise
            if site_data is not None:
                result["site_release_sha256"] = configure_site(dest, language, site_data)
    return {**result,"directory":str(dest),"reused":False}

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("action",choices=["plan","install","revision-help"])
    p.add_argument("--commit",required=True)
    p.add_argument("--platform",required=True)
    p.add_argument("--language",required=True)
    p.add_argument("--prefix",type=Path,default=Path.home()/".local/share/wros-sdk")
    p.add_argument("--local-repository",type=Path,help="read exact Git objects from this trusted local repository")
    p.add_argument("--site-profile", type=Path, help="use an explicitly trusted local development site profile")
    args,extra=sys.argv[1:],[]
    if "--" in args:
        pos=args.index("--");args,extra=args[:pos],args[pos+1:]
    a=p.parse_args(args)
    try:
        if a.site_profile is not None and a.action != "install":
            raise ValueError("--site-profile is an install option")
        source=Source(a.commit,a.local_repository)
        if a.action=="revision-help":print(selection(source,name(a.platform),name(a.language),["--revision-help"])["help"]);return
        result=install(source,a.platform,a.language,a.prefix,extra,a.action=="plan",a.site_profile)
        print(json.dumps({**result,"requested_paths":source.requested},indent=2))
    except (ValueError,OSError,KeyError,subprocess.SubprocessError) as exc:p.exit(1,f"installation failed: {exc}\n")

if __name__=="__main__":main()
