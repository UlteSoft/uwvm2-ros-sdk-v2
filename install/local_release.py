"""Read local memory-profile attestations signed under the operator's WSEA policy."""
import hashlib
import json
import os
from pathlib import Path
import stat
import subprocess
import tempfile

from artifacts import MAGIC, sections, uleb, unique_object


SECTION = "wros.sdk.memory.release"
CONFIG = Path("share/qualification/local-trust.json")
LIMIT = 1024 * 1024


def read_file(path, limit):
    # Reject special files before reading. O_NONBLOCK also handles an unexpected FIFO.
    fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK | os.O_CLOEXEC)
    with os.fdopen(fd, "rb") as f:
        info = os.fstat(f.fileno())
        if not stat.S_ISREG(info.st_mode) or info.st_size > limit:
            raise ValueError("local release needs a bounded regular file")
        data = f.read(limit + 1)
        if len(data) > limit or len(data) != info.st_size:
            raise ValueError("local release changed while reading")
    return data


def encode(rows):
    name = SECTION.encode()
    if not isinstance(rows, list) or not 1 <= len(rows) <= 32:
        raise ValueError("a qualification bundle contains 1 to 32 release rows")
    data = json.dumps({"format": "wros-local-memory-releases", "routes": rows}, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()
    body = uleb(len(name)) + name + data
    if len(body) > LIMIT // 2:
        raise ValueError("release statement exceeds the size limit")
    return MAGIC + b"\0" + uleb(len(body)) + body


def decode(module):
    parsed = list(sections(module))
    if [name for _, _, name, _ in parsed] != [SECTION, "uwvm.wsea.v2"]:
        raise ValueError("expected one signed, data-only local memory release")
    reader = parsed[0][3]
    bundle = json.loads(bytes(reader.data[reader.position:]), object_pairs_hook=unique_object)
    if (not isinstance(bundle, dict) or set(bundle) != {"format", "routes"} or
            bundle["format"] != "wros-local-memory-releases" or not isinstance(bundle["routes"], list) or
            not 1 <= len(bundle["routes"]) <= 32):
        raise ValueError("unexpected local release bundle")
    return bundle["routes"]


def releases(sdk):
    # The installed SDK and its local trust configuration are provisioned by the
    # operator. No project path, environment override or incoming signing key.
    try:
        config = json.loads(read_file(sdk / CONFIG, 32768), object_pairs_hook=unique_object)
    except FileNotFoundError:
        return []
    if not isinstance(config, dict) or set(config) != {"verifier", "verifier_sha256", "policy", "statement", "statement_sha256"}:
        raise ValueError("invalid operator WSEA configuration")
    if not all(isinstance(config[key], str) and Path(config[key]).is_absolute() for key in ("verifier", "policy", "statement")):
        raise ValueError("operator WSEA configuration requires absolute paths")
    policy = read_file(config["policy"], LIMIT)
    module_ids = [line.split(b"|", 1)[0] for line in policy.splitlines() if line.startswith(b"module=")]
    if module_ids != [b"module=wros.sdk.memory.release"]:
        raise ValueError("WSEA policy must authorize only the dedicated local qualification module")
    # Execute the very file that was hashed. The verifier is an operator-trusted
    # native Linux prerequisite, independent of the target compiler and Wasm.
    fd = os.open(config["verifier"], os.O_RDONLY | os.O_NOFOLLOW | os.O_CLOEXEC | os.O_NONBLOCK)
    with os.fdopen(fd, "rb") as executable:
        if not stat.S_ISREG(os.fstat(fd).st_mode) or hashlib.file_digest(executable, "sha256").hexdigest() != config["verifier_sha256"]:
            raise ValueError("local wasm-cosign verifier identity changed")
        verified = Path("/proc/self/fd") / str(fd)
        module = read_file(config["statement"], LIMIT)
        if hashlib.sha256(module).hexdigest() != config["statement_sha256"]:
            raise ValueError("signed qualification bundle differs from the operator-approved release")
        with tempfile.TemporaryDirectory(prefix="wros-local-release-") as scratch:
            snapshot = Path(scratch) / "release.wasm"
            snapshot.write_bytes(module)
            child = subprocess.run([verified, "wasm", "secure", "verify", snapshot, "--policy", config["policy"]],
                                   env={}, stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL,
                                   stderr=subprocess.DEVNULL, pass_fds=(fd,), timeout=20)
        if child.returncode or read_file(config["policy"], LIMIT) != policy:
            raise ValueError("wasm-cosign rejected the local qualification statement or its policy changed")
    return decode(module)
