"""Check that the freestanding Flang fatal numerical diagnostic traps within its guest."""
import argparse
import json
from pathlib import Path
import resource
import subprocess
import sys
from separate_compilation import Profile, cgroup_record, inspect, sha

ROOT = Path(__file__).resolve().parents[1]
PROGRAM = """program invalid_modulus
  use iso_c_binding
  implicit none
  integer(c_int32_t), volatile :: result
  interface
    function runtime_modulo(x,p,file,line) bind(c,name="_FortranAModInteger4")
      import c_int32_t, c_ptr
      integer(c_int32_t), value :: x,p,line
      type(c_ptr), value :: file
      integer(c_int32_t) :: runtime_modulo
    end function
  end interface
  result = runtime_modulo(7,0,c_null_ptr,0)
end program
"""


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("toolchain", "sysroots", "plain-sysroots", "flang", "mte-tool", "runtime", "output"):
        parser.add_argument("--" + name, required=True, type=Path)
    args = parser.parse_args()
    work = args.output.resolve()
    report = dict(complete=False, cgroup=cgroup_record(), modules={}, runs=[])
    work.mkdir(parents=True, exist_ok=False)
    resource.setrlimit(resource.RLIMIT_CORE, (0, 0))
    source = work / "invalid.f90"
    source.write_text(PROGRAM)
    for bits in (32, 64):
        for tagged in (True, False):
            profile = Profile(bits, mte=tagged)
            app = work / (profile.identity + ".wasm")
            build = [sys.executable, ROOT / "bin/wrfortran", "--toolchain", args.toolchain.resolve(),
                     "--sysroots", (args.sysroots if tagged else args.plain_sysroots).resolve(),
                     "--flang", args.flang.resolve(), "--mte-tool", args.mte_tool.resolve(),
                     "--target", f"wasm{bits}", "--mte" if tagged else "--no-mte", "-O3", "-g", source, "-o", app]
            subprocess.run(build, cwd=work, check=True, timeout=180)
            imports = inspect(app.read_bytes())
            if imports:
                raise RuntimeError("freestanding error handling acquired host imports: " + str(imports))
            report["modules"][app.name] = dict(sha256=sha(app), imports=imports)
            for engine in ("int", "aot"):
                cmd = [args.runtime.resolve(), *profile.uwvm_feature_flags(), "--runtime-" + engine,
                       "--runtime-compile-threads", "0", "--runtime-llvm-jit-cache-path", "disable",
                       "--run", app]
                proc = subprocess.run(cmd, cwd=work, capture_output=True, timeout=60)
                (work / (app.name + "." + engine + ".stderr")).write_bytes(proc.stderr)
                if proc.returncode == 0 or b"unreachable" not in proc.stderr:
                    raise RuntimeError("expected guest unreachable trap: " + proc.stderr.decode(errors="replace"))
                report["runs"].append(dict(profile=profile.to_dict(), engine=engine, exit=proc.returncode))
    report["complete"] = True
    (work / "results.json").write_text(json.dumps(report, indent=2) + "\n")


if __name__ == "__main__":
    main()
