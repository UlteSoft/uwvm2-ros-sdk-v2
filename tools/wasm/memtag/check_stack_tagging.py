"""Check Wasm stack-tagging IR, instruction selection and object emission."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import tempfile
from check_owner_assembly import check as check_owner_assembly


def digest(path):
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def check(tool_bin, source, work):
    """Use only this producer's tools and this prepared LLVM source."""
    work.mkdir(parents=True, exist_ok=True)
    report = work / "results.json"
    result = dict(complete=False, fixtures={}, tools={}, cases=[])

    def save():
        with tempfile.NamedTemporaryFile(mode="w", dir=work, delete=False) as stream:
            partial = Path(stream.name)
            json.dump(result, stream, indent=2)
            stream.write("\n")
        os.replace(partial, report)

    save()
    llc, filecheck = tool_bin / "llc", tool_bin / "FileCheck"
    test_dir = source / "llvm/test/CodeGen/WebAssembly"
    fixtures = [test_dir / (base + ".ll") for base in
                ("memtag-addr32", "memtag-addr64")]
    addr32, addr64 = fixtures
    inventory = json.loads((source.parent / "source-inventory.json").read_text())
    hashes = result["fixtures"]
    for path in fixtures:
        key = path.relative_to(source).as_posix()
        hashes[key] = digest(path)
        if inventory[key].get("sha256") != hashes[key]:
            raise ValueError("prepared LLVM regression fixture has changed: " + key)
    zero = Path(__file__).resolve().with_name("memtag-adjacent-zero.ll")
    hashes[zero.name] = digest(zero)
    generations = zero.with_name("memtag-lifetime-generations.ll")
    hashes[generations.name] = digest(generations)
    attributes = zero.with_name("memtag-source-attributes.c")
    hashes[attributes.name] = digest(attributes)
    owner = zero.with_name("memtag-stack-owner.ll")
    dynamic = zero.with_name("memtag-unsupported-dynamic.ll")
    unwinding = zero.with_name("memtag-unsupported-unwind.ll")
    for path in (owner, dynamic, unwinding):
        hashes[path.name] = digest(path)
    result["tools"] = {name: digest(tool_bin / name) for name in ("clang", "clang++", "llc", "FileCheck", "llvm-mc")}

    def run(bits, name, fixture, flags, suffix, prefix=None, driver=None):
        """Fail independently on the producer, empty output, object header, or FileCheck."""
        stem = f"wasm{bits}-{name}"
        product = work / (stem + suffix)
        product.unlink(missing_ok=True)
        if driver is None:
            args = [str(llc), f"-mtriple=wasm{bits}-unknown-unknown", "-verify-each"]
        else:
            args = [str(tool_bin / driver), "--no-default-config", f"--target=wasm{bits}-unknown-unknown"]
        args.extend([*flags, str(fixture), "-o", str(product)])
        case = dict(name=stem, producer=args, passed=False)
        result["cases"].append(case)
        save()
        proc = subprocess.run(args, capture_output=True, timeout=120)
        case["producer_exit"] = proc.returncode
        errors = work / (stem + ".producer.log")
        errors.write_bytes(proc.stderr)
        if proc.returncode or not product.is_file() or product.stat().st_size == 0:
            save()
            raise RuntimeError(f"{stem}: no successful producer output. See {errors}")
        if prefix:
            args = [str(filecheck), str(fixture), "--check-prefix=" + prefix, "--input-file=" + str(product)]
            case["filecheck"] = args
            proc = subprocess.run(args, capture_output=True, timeout=120)
            case["filecheck_exit"] = proc.returncode
            errors = work / (stem + ".filecheck.log")
            errors.write_bytes(proc.stderr)
            if proc.returncode:
                save()
                raise RuntimeError(f"{stem}: FileCheck failed. See {errors}")
        else:
            with product.open("rb") as stream:
                if stream.read(8) != b"\0asm\1\0\0\0":
                    save()
                    raise RuntimeError(f"{stem}: wrong Wasm object header")
        case.update(passed=True, output_sha256=digest(product))
        save()

    def reject(bits, fixture):
        name = f"wasm{bits}-{fixture.stem}"
        product = work / (name + ".o")
        product.unlink(missing_ok=True)
        args = [str(llc), f"-mtriple=wasm{bits}-unknown-unknown", "-mattr=+memtag",
                "-verify-each", "-filetype=obj", str(fixture), "-o", str(product)]
        proc = subprocess.run(args, capture_output=True, timeout=120)
        (work / (name + ".producer.log")).write_bytes(proc.stderr)
        diagnostic = ("statically bounded" if fixture == dynamic else "non-local exit").encode()
        passed = proc.returncode != 0 and b"strict WasmMTE" in proc.stderr and diagnostic in proc.stderr
        result["cases"].append(dict(name=name, producer=args, producer_exit=proc.returncode, passed=passed))
        save()
        if not passed:
            raise RuntimeError(name + " did not produce the required unsupported-storage diagnostic")

    save()
    result["cases"].extend(check_owner_assembly(tool_bin / "llvm-mc", work / "owner-assembly"))
    save()
    for bits, address in ((32, addr32), (64, addr64)):
        stop = "-stop-after=wasm-stack-tagging"
        features = "-mattr=+memtag,+atomics,+bulk-memory"
        run(bits, "generations", generations, [features, stop], ".mir", "CHECK")
        run(bits, "owners", owner, [features, stop], ".mir", "CHECK")
        run(bits, "owner-object", owner, [features, "-filetype=obj"], ".o")
        for fixture in (dynamic, unwinding):
            reject(bits, fixture)
        run(bits, "zero", zero, [features, stop], ".mir", "CHECK")
        run(bits, "zero-unfused", zero, [features, "-wasm-memtag-fuse-zero-init=false", stop], ".mir", "UNFUSED")
        run(bits, "zero-assembly", zero, [features, "-asm-verbose=false"], ".s", "ASM")
        run(bits, "address-assembly", address, ["-asm-verbose=false"], ".s", "CHECK")
        for language, driver in (("c", "clang"), ("c++", "clang++")):
            for mode, flag in (("ON", "-fsanitize=memtag"), ("OFF", "-fno-sanitize=memtag")):
                run(bits, f"attributes-{driver}-{mode.lower()}", attributes,
                    ["-x", language, "-O3", "-g", "-S", flag], ".s", mode, driver)
    result["complete"] = True
    save()
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    for option in ("tool-bin", "source", "work"):
        parser.add_argument("--" + option, type=Path, required=True)
    options = parser.parse_args()
    result = check(options.tool_bin.resolve(), options.source.resolve(), options.work.resolve())
    print(f"{len(result['cases'])} checks passed. See {options.work / 'results.json'}")
