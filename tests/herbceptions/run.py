"""Check genuine Herbceptions across separate translation units and the final wrcc runtime."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys

HERE = Path(__file__).resolve().parent
SDK = HERE.parents[1]
sys.path.insert(0, str(SDK / "tests"))
from separate_compilation import cgroup_record
sys.path.insert(0, str(SDK / "install"))
from guest_profile import Profile
from imports import inspect


def sha(path):
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_subparsers(dest="mode", required=True)
    native = mode.add_parser("upstream", help="language reference on its native target and Wasm target parser checks")
    native.add_argument("--clang", required=True, type=Path)
    wasm = mode.add_parser("wrcc", help="compile two sealed Wasm objects with the selected SDK and run on both VM engines")
    wasm.add_argument("--wrcc", type=Path, required=True)
    wasm.add_argument("--vm", type=Path, required=True)
    wasm.add_argument("--feature-flag", default="--herbceptions",
                      help="option enabling the SDK's Herbceptions route, or 'default' for an implicit route")
    wasm.add_argument("--disabled-flag", default="--no-herbceptions", help="SDK option selecting conventional C++")
    wasm.add_argument("--compiler-arg", action="append", default=[],
                      help="additional reviewed site/compiler option; use --compiler-arg=VALUE")
    wasm.add_argument("--toolchain", type=Path)
    wasm.add_argument("--sysroots", type=Path, action="append", default=[])
    wasm.add_argument("--candidate-mte", action="store_true", help="explicitly exercise an unsigned candidate backend")
    wasm.add_argument("--profile", choices=("wasm32-noeh", "wasm32-eh", "wasm64-noeh", "wasm64-eh"),
                      action="append", required=True, help="repeat for each installed compiler and sysroot profile")
    for cmd in (native, wasm):
        cmd.add_argument("--output", required=True, type=Path, help="new results directory")
    opt = parser.parse_args()
    gate = cgroup_record()
    out = opt.output.resolve()
    out.mkdir(parents=True, exist_ok=False)
    report = dict(complete=False, mode=opt.mode, cgroup=gate, cases=[], artifacts={}, inputs={})
    for path in (*HERE.glob("*.cpp"), HERE/"policy.hpp", Path(__file__)):
        report["inputs"][str(path.resolve())] = sha(path)
    def save():
        (out/"results.json").write_text(json.dumps(report, indent=2) + "\n")

    def run(label, command, diagnostic=None):
        cmd = list(map(str, command))
        process = subprocess.run(cmd, capture_output=True, timeout=200, cwd=out)
        log = process.stdout + process.stderr
        (out/(label+".log")).write_bytes(log)
        passed = process.returncode == 0 if diagnostic is None else process.returncode != 0 and diagnostic.lower() in log.lower()
        report["cases"].append(dict(name=label, argv=cmd, exit=process.returncode, expected_success=diagnostic is None, passed=passed))
        save()
        if not passed:
            raise RuntimeError(label + ": " + log.decode(errors="replace")[-1500:])
        return log

    save()
    negative = (("unhandled", b"must be handled"), ("invalid_error", b"must be trivially copyable"))
    if opt.mode == "upstream":
        clang = opt.clang.absolute()
        report["inputs"][str(clang)] = sha(clang)
        common = [clang, "-std=c++20", "-fherbceptions", "-O3", "-g", "-Werror"]
        for eh in (False, True):
            name = "eh" if eh else "noeh"
            flags = ["-fexceptions","-DFIXTURE_EXPECT_EH"] if eh else ["-fno-exceptions"]
            for target in ("wasm32", "wasm64"):
                # Target parsing is a separate check. This mode does not build or execute a Wasm module.
                for source in ("application", "provider"):
                    run(target+"-"+name+"-parse-"+source, [*common, *flags, "--target="+target+"-unknown-wasip1",
                        "-DFIXTURE_WASM_PARSE", "-DFIXTURE_WIDTH="+target[4:], "-fsyntax-only", HERE/(source+".cpp")])
            objects = []
            for source in ("application", "provider"):
                obj = out/(name+"-"+source+".o")
                run(name+"-compile-"+source, [*common, *flags, "-DFIXTURE_NATIVE", "-c", HERE/(source+".cpp"), "-o", obj])
                objects.append(obj)
            exe = out/("native-"+name)
            run(name+"-link", [clang, *objects, "-lstdc++", "-o", exe])
            run(name+"-execute", [exe])
            report["artifacts"][exe.name] = sha(exe)
            for source, msg in negative:
                run(name+"-reject-"+source, [*common, *flags, "-fsyntax-only", HERE/(source+".cpp")], msg)
            if not eh:
                run("noeh-reject-standard", [*common, *flags, "-fsyntax-only", HERE/"standard_throw.cpp"], b"exceptions disabled")
    else:
        wrcc, vm = opt.wrcc.resolve(strict=True), opt.vm.resolve(strict=True)
        report["inputs"].update({str(wrcc):sha(wrcc), str(vm):sha(vm)})
        report["candidate_mte"] = opt.candidate_mte
        enabled = [] if opt.feature_flag == "default" else [opt.feature_flag]
        selected = list(opt.compiler_arg)
        if opt.toolchain:
            selected += ["--toolchain", opt.toolchain.resolve(strict=True)]
        for sysroots in opt.sysroots:
            selected += ["--sysroots", sysroots.resolve(strict=True)]
        for name in dict.fromkeys(opt.profile):
            target, mode_name = name.split("-")
            bits, eh = int(target[4:]), mode_name == "eh"
            options = [*selected, "--target", target, "--core", "3.0", "--eh" if eh else "--no-eh",
                     "--legacy-mte" if opt.candidate_mte else "--mte", "-O3", "-g", "--std", "c++20",
                     "-D", "FIXTURE_WIDTH="+str(bits)]
            if eh:
                options += ["-D","FIXTURE_EXPECT_EH"]
            flags = [wrcc, *enabled, *options]
            conventional = [wrcc, opt.disabled_flag, *options]
            ordinary = out/(name+"-conventional.wasm")
            run(name+"-compile-conventional", [*conventional, "--reactor", "--export", "_start", HERE/"ordinary.cpp", "-o", ordinary])
            off = out/(name+"-disabled-extension.o")
            run(name+"-reject-disabled-extension", [*conventional, "-c", HERE/"provider.cpp", "-o", off],
                b"the selected frontend must implement Herbceptions")
            if off.exists():
                raise RuntimeError("disabled Herbceptions compilation published an object")
            domain = out/(name+"-standard-domain.wasm")
            # The upstream standard-domain headers require C++23 constexpr rules.
            library_flags = list(flags)
            library_flags[library_flags.index("--std") + 1] = "c++23"
            run(name+"-compile-standard-domain", [*library_flags, "--reactor", "--export", "_start", HERE/"standard_domain.cpp", "-o", domain])
            if inspect(domain.read_bytes()):
                raise ValueError("standard error domain unexpectedly requires a host import")
            report["artifacts"][domain.name] = sha(domain)
            legacy = out/(name+"-legacy-domain.wasm")
            legacy_link = [*flags, "--reactor", "--export", "_start", HERE/"legacy_domain.cpp", "-o", legacy]
            if eh:
                run(name+"-compile-legacy-domain", legacy_link)
                if inspect(legacy.read_bytes()):
                    raise ValueError("legacy exception bridge unexpectedly requires a host import")
                report["artifacts"][legacy.name] = sha(legacy)
            else:
                run(name+"-reject-legacy-domain", legacy_link, b"undefined symbol: __cxa_error_domain_itanium_exception_ptr")
                if legacy.exists():
                    raise RuntimeError("no-EH sysroot published an unresolved legacy exception bridge")
            objects = []
            for source in ("application","provider"):
                obj = out/(name+"-"+source+".o")
                run(name+"-compile-"+source, [*flags, "-c", HERE/(source+".cpp"), "-o", obj])
                objects.append(obj)
            guest = out/(name+".wasm")
            run(name+"-link", [*flags, "--reactor", "--export", "_start", *objects, "-o", guest])
            surface = inspect(guest.read_bytes())
            if surface:
                raise RuntimeError("guest unexpectedly requires a host import: " + str(surface))
            report["artifacts"][guest.name] = sha(guest)
            for engine in ("int", "aot"):
                base = [vm, *Profile(address_bits=bits, exceptions=mode_name).uwvm_feature_flags(),
                        "--debug-fault-action", "exit", "--runtime-"+engine, "--runtime-compile-threads", "0",
                        "--runtime-llvm-jit-cache-path", "disable", "--runtime-memtag-mode", "sync"]
                run(name+"-"+engine+"-conventional", [*base, "--run", ordinary])
                run(name+"-"+engine+"-standard-domain", [*base, "--run", domain])
                if eh:
                    run(name+"-"+engine+"-legacy-domain", [*base, "--run", legacy])
                run(name+"-"+engine+"-active", [*base, "--run", guest])
                run(name+"-"+engine+"-disabled-control", [*base, "--runtime-disable-memtag", "--run", guest], b"unreachable")
            for source, msg in negative + (() if eh else (("standard_throw",b"exceptions disabled"),)):
                output = out/(name+"-"+source+".o")
                output.write_bytes(b"keep previous artifact")
                run(name+"-reject-"+source, [*flags, "-c", HERE/(source+".cpp"), "-o", output], msg)
                if output.read_bytes() != b"keep previous artifact":
                    raise RuntimeError("failed compilation replaced a prior artifact")
    report["complete"] = True
    save()


if __name__ == "__main__":
    main()
