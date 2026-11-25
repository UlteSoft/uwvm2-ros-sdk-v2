"""Launch the same SDK module on engines with compatible host and guest ABIs."""
from pathlib import Path
import re
import shutil
from types import SimpleNamespace

from sysroot_suite import capture, digest, runtime_args, vm_elf_host
from wasmtime_reference import adapter
from workloads import WORKLOADS, require

NATIVE_WASMTIME = {"linux-x86_64": "x86_64-unknown-linux-gnu", "linux-aarch64": "aarch64-unknown-linux-gnu"}
EXTERNAL = ("wasmtime-host", "wasmtime-cli", "wavm")
# The x86_64 static C API executable in the published C++ execution receipt
# predates the explicit backend marker. Its exact binary has native Cranelift provenance.
PUBLISHED_X86_CAPI = "bc2bf09adb4ed875e3f887c9be63e1033440b35153f54169472d19cbe2257dd5"


def references(args, directory):
    tools = {}
    for name in EXTERNAL:
        option = getattr(args, name.replace("-", "_"))
        default = {"wasmtime-host": "qualification-host", "wasmtime-cli": "wasmtime", "wavm": "wavm"}[name]
        path = option or shutil.which(default)
        info = tools[name] = {}
        if path is None:
            info["reason"] = f"supply --{name} or install {default} on PATH"
            continue
        path = Path(path).resolve()
        info["path"] = str(path)
        try:
            info.update(elf_host=vm_elf_host(path), sha256=digest(path))
            if info["elf_host"] != args.host:
                info["reason"] = f"reference ELF is {info['elf_host']}, selected VM ELF is {args.host}"
                continue
            if name == "wavm":
                info["backend"] = "WAVM LLVM JIT with checked software MTE and WROS allocation ownership"
                if args.host not in NATIVE_WASMTIME:
                    info["reason"] = "the adapted mt-2 ownership runtime requires a 64-bit host"
                    continue
                info["probe"] = capture([path, "help", "run"], directory, name + "-features", args.run_timeout)
                help_text = (directory / (name + "-features.out")).read_text(errors="replace")
                features = set(re.findall(r"^  ([a-z0-9-]+)\s", help_text, re.M))
                info["features"] = sorted(features)
                if info["probe"].get("returncode") != 0 or not {"memtag-soft-debug", "wros-ownership"} <= features:
                    info["reason"] = "WAVM run help does not advertise the checked WROS ownership port"
                    continue
                info["version_probe"] = capture([path, "version"], directory, "wavm-version", args.run_timeout)
                version = (directory / "wavm-version.out").read_text(errors="replace")
                info["version"] = version.splitlines()[0] if version else ""
                info["static"] = bool(re.search(r"^WAVM_ENABLE_STATIC_LINKING:\s+true$", version, re.M))
                if not info["static"] and shutil.which("ldd"):
                    info["library_probe"] = capture(["ldd", path], directory, "wavm-libraries", args.run_timeout)
                    listing = (directory / "wavm-libraries.out").read_text(errors="replace")
                    match = re.search(r"^\s*libWAVM\.so[\w.]*\s+=>\s+(/.+?)\s+\(0x[0-9a-f]+\)", listing, re.M)
                    if match:
                        library = Path(match[1]).resolve()
                        require(vm_elf_host(library) == args.host, "loaded WAVM library and VM ELF differ")
                        info["library"] = {"path": str(library), "sha256": digest(library)}
            else:
                info["backend"] = ("native Cranelift requested" if args.host in NATIVE_WASMTIME
                                   else "Pulley/32-bit correctness probe")
                if name == "wasmtime-cli":
                    info["probe"] = capture([path, "--version"], directory, name + "-version", args.run_timeout)
                    info["version"] = (directory / (name + "-version.out")).read_text(errors="replace").strip()
                    if (info["probe"].get("returncode") != 0 or not
                            re.fullmatch(r"wasmtime 42\.0\.1 \(6844a83b5[0-9a-f]* [\d-]+\)", info["version"])):
                        info["reason"] = "stock Wasmtime differs from the pinned 42.0.1 release"
        except (ValueError, OSError) as error:
            info["reason"] = str(error)
    return tools


def capability(args, name, target, imports):
    info = args.references[name]
    if name == "wasmtime-cli":
        if target.bits == 64:
            return "stock WASIp1 does not bind the SDK's _wasm64 clock and I/O imports"
        if target.threads:
            return "the SDK command imports shared env.memory from its owner; stock WASIp1 does not supply that owner"
    if name == "wasmtime-host" and any(i["module"] == "wasi" and i["name"] == "thread-spawn" for i in imports):
        return "the reviewed C API adapter supplies shared env.memory and has no wasi.thread-spawn binding"
    if name == "wavm" and target.threads:
        return "the reviewed WAVM ownership port requires private, locally defined linear memory"
    return info.get("reason")


def wros_args(args, name, target, simd, imports, owner, guest):
    engine = "int" if name in ("int", "int-disabled") else "aot"
    argv = runtime_args(args.vm, engine, target, imports, owner, guest, thread_stack_mib=8, thread_storage_mib=64)
    if engine == "aot":
        argv[argv.index("--runtime-llvm-jit-policy") + 1] = "balanced"
    flags = ["--log-color", "disable"]
    if not simd:
        flags += ["--wasm-feature-disable-simd", "--wasm-feature-disable-relaxed-simd"]
    if target.mte:
        pos = argv.index("--runtime-memtag-mode")
        if name in ("int-disabled", "aot-disabled"):
            argv[pos:pos + 2] = ["--runtime-disable-memtag"]
        else:
            flags += ["--runtime-memtag-backend", "software", "--runtime-memtag-action", "crash"]
    argv[argv.index("--run"):argv.index("--run")] = flags
    return argv


def wasi_policy(argv):
    policy = []
    for i, token in enumerate(argv):
        if token == "--wasip1-single-interface":
            policy.append(f"{argv[i + 3]}={argv[i + 2]}")
        elif token == "--wasip1-single-grant":
            policy.append("grant=" + argv[i + 2])
    if "grant=args" in policy:
        policy.append("guest-argv0=" + str(argv[-1]))
    return policy


def external_command(args, name, target, simd, guest):
    tool = args.references[name]
    if name == "wavm":
        features = ["wros-ownership", "memtag-soft-debug"]
        if target.bits == 64:
            features.append("memory64")
        if "return-call" in tool["features"]:
            features.append("return-call")
        flags = [token for feature in features for token in ("--enable", feature)]
        return [tool["path"], "run", "--nocache", "--abi=wasi", *flags, guest]
    # The explicit compilation target prevents a Pulley run from being credited as native Cranelift.
    return [tool["path"], "run", "--target", NATIVE_WASMTIME.get(args.host, "pulley32"), "-C", "compiler=cranelift",
            "-C", "parallel-compilation=n", "-O", "opt-level=2", "-W", "memory64=n", "-W", "threads=n",
            "-W", "exceptions=" + ("y" if target.eh else "n"), "-W", "simd=" + ("y" if simd else "n"),
            "-W", "relaxed-simd=" + ("y" if simd else "n"), guest]


def limitation(name, stderr):
    # Only recognized capability diagnostics qualify as unavailable. Traps, wrong results,
    # timeouts and unrelated compilation errors are failures with their original captures.
    patterns = {
        "wavm": r"unknown opcode \(\d+\)|Missing import: [^\n]+|requires (?:the )?[\w'-]+ feature",
        "wasmtime-cli": r"unknown import:?[^\n]+|target '[^']+' is not supported|Support for this target is disabled",
        "wasmtime-host": (r"error native Cranelift target unavailable|"
                          r"error (?:unexpected import|unsupported WASIp1 import|only the denied profile is implemented for) [^\n]+"),
    }
    result = re.search(patterns.get(name, r"(?!)"), stderr, re.I)
    return result and result.group()


def observation(args, row, name, target, simd, guest, owner, directory):
    directory.mkdir(parents=True)
    receipt = {"directory": str(directory.relative_to(args.work)), "engine": name, "wasm_sha256": row["wasm_sha256"]}
    try:
        require(digest(guest) == row["wasm_sha256"] and (not owner or digest(owner) == row["owner_sha256"]),
                "guest or shared owner changed between executions")
        policy_argv = wros_args(args, name, target, simd, row["imports"], owner, guest)
        if name == "wasmtime-host":
            options = SimpleNamespace(host=args.references[name]["path"], timeout=args.run_timeout)
            proc = adapter.run_host(options, target, guest, owner, wasi_policy(policy_argv), directory)
            receipt.update(proc)
            stdout, stderr = directory / "stdout", directory / "stderr"
            report = directory / "host.log"
            detail = report.read_text(errors="replace") if report.is_file() else ""
            code = proc.get("guest_exit_code") if proc.get("host_returncode") == 0 else None
            # Once _start has begun even an adapter error represents an execution failure.
            unsupported = limitation(name, detail) if not proc["start_invoked"] else None
        else:
            argv = external_command(args, name, target, simd, guest) if name in EXTERNAL else policy_argv
            proc = capture(argv, directory, "process", args.run_timeout)
            receipt.update(proc)
            stdout, stderr = directory / "process.out", directory / "process.err"
            detail = stderr.read_text(errors="replace")
            code = proc.get("returncode")
            unsupported = limitation(name, detail) if code is not None and code > 0 else None
        receipt.update(stdout_sha256=digest(stdout), stderr_sha256=digest(stderr))
        if code != 0:
            if unsupported:
                return {**receipt, "status": "unavailable", "reason": unsupported}
            return {**receipt, "status": "failed", "reason": "timeout, trap, nonzero exit or setup failure",
                    "diagnostic": detail[-1500:]}
        expected = row["expected"]
        lead = WORKLOADS[row["language"]].preamble
        label = "{language} workload={workload} items={items} checksum={checksum} ns=".format(**expected)
        pattern = rb"mte=(\d+)\n" + re.escape((lead + label).encode()) + rb"([1-9]\d*)\n"
        match = re.fullmatch(pattern, stdout.read_bytes())
        require(match is not None, "guest stdout differs from the independent oracle or timing protocol")
        tag, ns = map(int, match.groups())
        require((tag != 0) == (target.mte and name not in ("int-disabled", "aot-disabled")),
                "guest tag witness differs from runtime mode")
        if name == "wasmtime-host":
            clocks = re.findall(r"^clock_monotonic_ns (\d+)$", detail, re.M)
            require(any(int(end) - int(start) == ns for start, end in zip(clocks, clocks[1:])),
                    "C API host clock log differs from guest duration")
            marker = f"execution-matrix native-cranelift {NATIVE_WASMTIME.get(args.host)}"
            receipt["native_backend_verified"] = (
                marker in stderr.read_text(errors="replace").splitlines() or
                (args.host == "linux-x86_64" and args.references[name]["sha256"] == PUBLISHED_X86_CAPI))
        return {**receipt, "status": "pass", "guest_ns": ns, "tag": tag, "checksum": expected["checksum"]}
    except (OSError, ValueError, KeyError) as error:
        return {**receipt, "status": "failed", "reason": str(error)}
