"""Pinned inputs, independent expected outputs and build evidence for the execution matrix."""
from dataclasses import dataclass
from functools import cache
import hashlib
import itertools
import json
from pathlib import Path
import re
import struct

from optional_isa_suite import ISA_KEYS, LANGUAGES, PROFILE_KEYS, fields, memory_owner
from sysroot_suite import SHARED_MEMORY_PAGES, capture, digest, vm_elf_host

HERE = Path(__file__).resolve().parent
CFAMILY = HERE.parent
OBJC = CFAMILY.parent / "objc"
ROOT = CFAMILY.parents[2]


@dataclass(frozen=True)
class Workload:
    name: str
    project: str
    units: tuple
    includes: tuple = ()
    defines: tuple = ()
    client: str = ""
    preamble: str = ""


WORKLOADS = {
    "c": Workload("lz4", "lz4", (HERE / "lz4.c", CFAMILY / "upstream/lz4/lib/lz4.c"),
                  (CFAMILY / "upstream/lz4/lib",)),
    "cpp": Workload("parse", "fast_float", (HERE / "workloads.cpp",),
                    (CFAMILY / "upstream/fast_float/include",), ("BENCH_PARSE", "BENCH_EXECUTION_MATRIX")),
    "objc": Workload("gcc-object", "gcc", (HERE / "gcc-object.m", OBJC / "upstream/gcc/libobjc/Object.m"),
                     defines=("Object=QualificationGCCObject",), client="gcc-object.m", preamble="gcc-libobjc-object-ok\n"),
    "objcpp": Workload("chromium-swizzler", "chromium",
                       (HERE / "chromium-swizzler.mm", OBJC / "upstream/chromium/base/apple/scoped_objc_class_swizzler.mm"),
                       (OBJC / "upstream/chromium", OBJC / "ports/chromium"), client="chromium-swizzler.mm",
                       preamble="chromium-scoped-objc-swizzler-ok\n"),
}


def require(condition, message):
    if not condition:
        raise ValueError(message)


def public_inputs(language):
    workload = WORKLOADS[language]
    if workload.client:
        directory, manifest = OBJC, OBJC / "upstreams.json"
        record = json.loads(manifest.read_bytes())[workload.project]
        pins = {name: info["git_blob"] for name, info in record["files"].items()}
        revision = record["revision"]
    else:
        directory, manifest = CFAMILY, CFAMILY / "external-libraries.json"
        record = json.loads(manifest.read_bytes())["upstreams"][workload.project]
        pins, revision = record["git_blobs"], record["commit"]
    paths = {HERE / "guest.h", *workload.units}
    if workload.client:
        paths.add(OBJC / "clients" / workload.client)
    if language == "objcpp":
        paths.update((OBJC / "ports/chromium").rglob("*.h"))
    for name, expected in pins.items():
        path = directory / "upstream" / workload.project / name
        data = path.read_bytes()
        require(hashlib.sha1(f"blob {len(data)}\0".encode() + data).hexdigest() == expected,
                f"upstream Git blob mismatch for {path}")
        paths.add(path)
    return {"workload": workload.name, "upstream": record["repository"], "commit": revision,
            "manifest_sha256": digest(manifest), "files": {str(p.relative_to(ROOT)): digest(p) for p in sorted(paths)}}


def hash_words(words):
    value = 14695981039346656037
    for word in words:
        value = ((value ^ word) * 1099511628211) & 0xffffffffffffffff
    return value


@cache
def expected(language):
    if language == "c":
        data = (i % 71 + block + ((i >> 8) & 15) for block in range(16) for i in range(16384))
        count, checksum = 32 * 16 * 16384, hash_words(data)
    elif language == "cpp":
        # The decimal oracle uses CPython's correctly rounded double conversion.
        decimals = ("1024", "-10.00099999999999", "3.141592653589793", "3.141592653589793238462643383",
                    "0.84551240822557006", "9.999999999999998", "1000000000000000128", "-123456789.1234567",
                    "1.7976931348623157e308", "2.2250738585072014e-308", "4.9406564584124654e-324", "0.00001376",
                    "1e-24", "7.128274632e30", "993721e+12", "3.731389e-47")
        bits = [struct.unpack("<Q", struct.pack("<d", float(s)))[0] for s in decimals]
        seed, chunk = 0xc001d00d, []
        for _ in range(16384):
            seed ^= (seed << 13) & 0xffffffff
            seed ^= seed >> 17
            seed ^= (seed << 5) & 0xffffffff
            chunk.append(bits[seed % len(bits)])
        count, checksum = 16 * len(chunk), hash_words(itertools.chain.from_iterable(itertools.repeat(chunk, 16)))
    elif language == "objc":
        count = 65536
        checksum = (2 + 5) * (count // 2)
    else:
        count = 4096
        checksum = sum(3 * (i % 32) + 2 * ((i % 32) + 7) for i in range(count))
    return {"language": language, "workload": WORKLOADS[language].name, "items": count, "checksum": f"{checksum:016x}"}


def sdk_identity(sdk, language):
    name = LANGUAGES[language][1]
    driver = sdk / "bin" / name
    selection = sdk / "selection.json"
    config = json.loads(selection.read_bytes())
    frontend_hash = digest(driver)
    require(config["language"] == language and config["mode"] == "binary" and config["platform"] == "generic"
            and re.fullmatch("[0-9a-f]{40}", config["commit"]), f"expected installed generic binary {language} SDK: {sdk}")
    require(config["files"]["bin/" + name]["sha256"] == frontend_hash and config["host"] == vm_elf_host(driver),
            f"frontend differs from installed binary SDK receipt: {driver}")
    return {"root": str(sdk), "selection_sha256": digest(selection), "commit": config["commit"], "host": config["host"],
            "frontend_sha256": frontend_hash, "imports_reader_sha256": digest(sdk / "install/imports.py"),
            "artifact_reader_sha256": digest(sdk / "install/artifacts.py")}


def build(args, row, out, target, simd, inspect, uleb):
    language = row["language"]
    sdk, workload = args.sdks[language], WORKLOADS[language]
    _, driver, _, standard = LANGUAGES[language]
    guest = out / "guest.wasm"
    command = [sdk / "bin" / driver, "--target", f"wasm{target.bits}", "--core", "3.0", "--std", standard,
               "-O3", "--build-receipt", "--mte" if target.mte else "--no-mte", "--eh" if target.eh else "--no-eh",
               "--threads" if target.threads else "--no-threads", "-msimd128" if simd else "-mno-simd128"]
    if target.threads:
        command += ["--shared-memory-pages", str(SHARED_MEMORY_PAGES)]
    for inc in workload.includes:
        command += ["-I", inc]
    defines = workload.defines + (("EXECUTION_TAGGED",) if target.mte else ())
    for define in defines:
        command += ["-D", define]
    command += [*workload.units, "-o", guest]
    record = row["build"] = capture(command, out, "compile", args.compile_timeout)
    require(record.get("returncode") == 0, "SDK build failed or timed out; see compile.err")
    receipt_path = guest.with_suffix(".wasm.wros-build.json")
    receipt = json.loads(receipt_path.read_bytes())
    profile = receipt["profile"]
    wanted = {"address_bits": target.bits, "wasm_version": "3.0", "threads": target.threads, "mte": target.mte,
              "exceptions": "eh" if target.eh else "noeh",
              "abi": "wasi_snapshot_preview1" if target.bits == 32 else "uwvm-preview1-memory64-extension"}
    guest_hash = digest(guest)
    require(receipt["language"] == language and receipt["artifact_sha256"] == guest_hash and
            receipt["compiler_sha256"] == args.sdk_receipts[language]["frontend_sha256"] and
            all(profile.get(k) == v for k, v in wanted.items()) and
            all(receipt["optional_isa"].get(k) is simd for k in ("simd128", "relaxed_simd")),
            "SDK receipt differs from requested compiler, profile or artifact")
    row.update(wasm_sha256=guest_hash, receipt_sha256=digest(receipt_path), sdk_profile=profile,
               optional_isa=receipt["optional_isa"], sysroot_sha256=receipt["sysroot_sha256"])
    if "objc_runtime_sha256" in receipt:
        row["objc_runtime_sha256"] = receipt["objc_runtime_sha256"]
    widths = []
    row["imports"] = imports = inspect(guest.read_bytes(), memory_types=widths, memory_limits=True)
    require(widths == [target.bits], f"unexpected linear memory widths {widths}")
    wasi = [i for i in imports if i["module"] == "wasi_snapshot_preview1"]
    require(all(i["kind"] == 0 and i["name"].endswith("_wasm64") == (target.bits == 64) for i in wasi)
            and any(i["name"].removesuffix("_wasm64") == "clock_time_get" for i in wasi), "incorrect guest clock or ABI")
    owner = memory_owner(out, target, imports, uleb) if target.threads else None
    if owner:
        row["owner_sha256"] = digest(owner)
    else:
        require(all(i["kind"] != 2 for i in imports), "private guest imports memory")
    record = row["decode"] = capture([args.decoder, guest], out, "decode", args.compile_timeout)
    require(record.get("returncode") == 0, "linked instruction decoding failed; see decode.err")
    with (out / "decode.out").open() as stream:
        header = stream.readline().rstrip("\n")
    require(header.startswith(f"MODULE {guest} "), "decoder reported a different module")
    row["opcodes"] = counts = fields(header, PROFILE_KEYS | ISA_KEYS)
    require(counts["bodies"] > 0 and bool(counts["memtag_total"]) == target.mte and
            counts["shared_memories"] == int(target.threads) and
            (target.threads or not (counts["threads_total"] or counts["thread_spawn_imports"])) and
            (target.eh or not (counts["eh_total"] or counts["tags"])) and
            (simd or not (counts["simd_total"] or counts["relaxed_simd_total"])), "linked opcodes contradict profile")
    return guest, owner
