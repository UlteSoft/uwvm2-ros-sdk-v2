"""Run the C-family Wasmtime adapter and compare the saved INT and AOT observations."""
import re
import subprocess

from sysroot_suite import digest, runtime_args

WASMTIME_VERSION = "42.0.1"
WASMTIME_COMMIT = "6844a83b530f86ad13a65175282fe2dbcd33cad1"


def require(condition, message):
    if not condition:
        raise ValueError(message)


def checked_hash(path, expected):
    actual = digest(path)
    require(actual == expected, f"SHA-256 mismatch for {path}")
    return actual


def recorded_policy(row, target, case, vm_witness=None):
    owner = row["memory_owner"]["argv"][-1] if target.threads else None
    guest = row["compile"]["argv"][-1]
    for engine in ("int", "aot"):
        recorded = row["runs"][engine]["argv"]
        expected = runtime_args(vm_witness or recorded[0], engine, target, row["imports"], owner, guest, case=case)
        expected[0] = recorded[0]
        require(recorded == expected, f"recorded {engine} arguments differ from the suite profile")
    options = []
    for i, flag in enumerate(recorded):
        if flag == "--wasip1-single-interface":
            options.append(f"{recorded[i + 3]}={recorded[i + 2]}")
        elif flag == "--wasip1-single-grant":
            options.append("grant=" + recorded[i + 2])
    if "grant=args" in options:
        # The suite leaves main's argv at its default: the exact --run tail.
        # The replay may mount guest.wasm under a different absolute path.
        require(recorded[-2:] == ["--run", guest] and guest.startswith("/")
                and not {"--wasip1-single-force-args", "--wasip1-single-set-argv0"}.intersection(recorded),
                "unsupported producer guest argument profile")
        options.append("guest-argv0=" + recorded[-1])
    return options


def run_host(args, target, guest, owner, policy, out):
    report = out / "host.log"
    argv = [str(args.host), str(target.bits), "eh" if target.eh else "noeh",
            str(guest), str(owner) if owner else "-", str(report), *policy]
    result = {"argv": argv}
    with (out / "stdout").open("xb") as stdout, (out / "stderr").open("xb") as stderr:
        try:
            proc = subprocess.run(argv, stdin=subprocess.DEVNULL, stdout=stdout, stderr=stderr,
                                  timeout=args.timeout)
            result["host_returncode"] = proc.returncode
        except subprocess.TimeoutExpired:
            result["timeout_seconds"] = args.timeout
    lines = report.read_text(errors="replace").splitlines() if report.exists() else []
    result["stdout_sha256"] = digest(out / "stdout")
    result["stderr_sha256"] = digest(out / "stderr")
    result["host_log_sha256"] = digest(report) if report.exists() else None
    result["start_invoked"] = "invoke _start" in lines
    end = re.fullmatch(r"end (returned|proc_exit) ([0-9]+)", lines[-1]) if lines else None
    heading = ["wasmtime-c-api " + WASMTIME_VERSION, "memory " + ("env.memory" if owner else "caller.memory")]
    if result.get("host_returncode") == 0 and lines[:2] == heading and result["start_invoked"] and end:
        result["termination"], result["guest_exit_code"] = end.group(1), int(end.group(2))
    elif "timeout_seconds" in result:
        result["termination"] = "timeout"
    else:
        result["detail"] = lines[-1] if lines else "missing host log"
        result["termination"] = "execution-error" if result["start_invoked"] else "setup-or-instantiation-error"
    return result


def saved_engines(row, original):
    observations = {}
    for engine in ("int", "aot"):
        saved = row["runs"][engine]
        fields = {"returncode": saved.get("returncode"), "saved_suite_status": saved["status"], "comparison": "unavailable"}
        if "timeout_seconds" in saved:
            fields["timeout_seconds"] = saved["timeout_seconds"]
        for name, suffix in (("stdout", ".out"), ("stderr", ".err")):
            key = name + "_sha256"
            fields[key] = digest(original / (engine + suffix))
            if key in saved:
                require(fields[key] == saved[key], f"original {engine} {name} digest differs")
        observations[engine] = fields
    return observations


def compare_engines(observations, result):
    guest_code = result.get("guest_exit_code")
    for fields in observations.values():
        code = fields["returncode"]
        if guest_code is None or type(code) is not int or code < 0 or "timeout_seconds" in fields:
            continue
        fields["exit_equal"] = code == guest_code
        fields["stdout_equal"] = fields["stdout_sha256"] == result["stdout_sha256"]
        fields["stderr_equal"] = fields["stderr_sha256"] == result["stderr_sha256"]
        agrees = fields["exit_equal"] and fields["stdout_equal"] and fields["stderr_equal"]
        fields["comparison"] = "match" if agrees else "difference"
    return observations
