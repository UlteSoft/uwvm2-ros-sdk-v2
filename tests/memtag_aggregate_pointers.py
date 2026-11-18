"""Execute optimized aggregate and PHI global pointers on both Wasm widths and engines."""
import argparse
import json
import os
import resource
import subprocess
from pathlib import Path

from separate_compilation import Profile, cgroup_record, sha


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("llc", "linker", "runtime", "output"):
        parser.add_argument("--" + name, required=True, type=Path)
    args = parser.parse_args()
    llc, linker, runtime, output = (x.absolute() for x in (args.llc, args.linker, args.runtime, args.output))
    folder = Path(__file__).resolve().parents[1] / "tools/wasm/memtag"
    fixtures = (("aggregate", folder / "memtag-global-aggregate.ll"), ("phi", folder / "memtag-global-phi.ll"))
    report = dict(complete=False, cgroup=cgroup_record(), cases=[],
                  inputs={str(p): sha(p) for p in (llc, linker, runtime, Path(__file__), *(path for _, path in fixtures))})
    output.mkdir(parents=True, exist_ok=False)
    os.environ["TMPDIR"] = str(output)
    resource.setrlimit(resource.RLIMIT_CORE, (0, 0))

    def save():
        (output / "results.json").write_text(json.dumps(report, indent=2) + "\n")

    def run(name, args):
        cmd = list(map(str, args))
        with (output / (name + ".log")).open("wb") as log:
            proc = subprocess.run(cmd, cwd=output, stdout=log, stderr=subprocess.STDOUT, timeout=120)
        report["cases"].append(dict(name=name, argv=cmd, exit=proc.returncode))
        save()
        proc.check_returncode()

    for name, fixture in fixtures:
        prefix = "" if name == "aggregate" else "phi-"
        for bits in (32, 64):
            triple = f"wasm{bits}-unknown-unknown"
            obj = output / f"{name}{bits}.o"
            guest = output / f"{name}{bits}.wasm"
            run(f"{prefix}object{bits}", [llc, "-O3", "-verify-each", "-verify-machineinstrs", "-mtriple=" + triple,
                                  "-mattr=+memtag,+simd128", "-filetype=obj", fixture, "-o", obj])
            run(f"{prefix}link{bits}", [linker, "-m", f"wasm{bits}", "--no-entry", "--export=_start", obj, "-o", guest])
            report.setdefault("modules", {})[f"{prefix}{bits}"] = sha(guest)
            for engine in ("int", "aot"):
                for mode in ("enabled", "disabled"):
                    run(f"{prefix}{bits}-{engine}-{mode}", [runtime, *Profile(bits).uwvm_feature_flags(),
                         *(["--runtime-disable-memtag"] if mode == "disabled" else []),
                         "--runtime-" + engine, "--runtime-compile-threads", "0",
                         "--runtime-llvm-jit-cache-path", "disable", "--run", guest])
    report["complete"] = True
    save()


if __name__ == "__main__":
    main()
