"""Select and install Git objects. The public bootstrap supplies the verified repository."""
import argparse
import base64
import hashlib
from functools import lru_cache
import http.client
import json
import lzma
import os
from pathlib import Path, PurePosixPath
import re
import shutil
import subprocess
import sys
import tarfile
import tempfile
import time
import urllib.error
import urllib.parse
import urllib.request


REPO = "UlteSoft/uwvm2-ros-sdk-v2"
INCLUDE = "include/u2rosv2"
LANGUAGES = {"c": "c", "cpp": "c++", "objc": "objc", "objcpp": "objc", "rust": "rust", "wat": "wat", "as": "as", "js": "js", "typescript": "typescript",
             "go": "go", "tinygo": "go", "py": "py", "java": "java"}
SCRIPT_COMMANDS = {"as": "wras", "js": "wrjs", "typescript": "wrts", "py": "wrpy.py"}
C_BACKEND = "libexec/quickjs-c"
PY_BACKEND = "libexec/cpython-c"
JAVA_BACKEND = "libexec/java-c"
JAVA_PLATFORMS = ("generic", "abb")
PY_ENTRY = "src/compilers/py/wrpy.py"
PY_PLATFORMS = ("generic", "unitree")
JS_BACKEND = "libexec/quickjs-modules"
SCRIPT_ENTRY = "src/compilers/script_command.py"
ALIASES = {"objective-c": "objc", "objective-c++": "objcpp", "wroc": "objc", "wrocxx": "objcpp", "python": "py", "c++": "cpp", "rs": "rust", "wrwat": "wat", "assemblyscript": "as", "javascript": "js", "ts": "typescript"}
PLATFORMS = tuple("""generic abb agibot agilex booster boston_dynamics clearpath deep_robotics dobot
doosan elephant fanuc flexiv fourier franka hello_robot kinova kuka leju limx nvidia nvidia-groot
nvidia-isaac-ros nvidia-isaac-sim pal realman robotis ros ros1 ros2 trossen ubtech ufactory
unitree universal_robots wasi yaskawa""".split())
COMMANDS = {"c": "wrc", "cpp": "wrcc", "objc": "wroc", "objcpp": "wrocxx", "wat": "wrwat", "rust": "wrrs", "go": "wrgo", "tinygo": "wrtg", "java": "wrjava"}
GO_COMMANDS = ("go", "tinygo")
GO_PLATFORMS = ("generic", "abb", "franka", "unitree")
ABI = "src/abi/contract.json"
ABI_INSTALLED = "share/abi/ros.json"
CHUNK = 1024 * 1024
MAX_BLOB = 512 * CHUNK
MAX_LFS = 16 * 1024 * CHUNK
HEX = re.compile(r"[0-9a-f]{64}")
LFS = re.compile(rb"version https://git-lfs.github.com/spec/v1\noid sha256:([a-f0-9]{64})\nsize ([0-9]+)\n")


def safe_path(name):
    if not isinstance(name, str):
        raise ValueError("expected a relative repository path")
    path = PurePosixPath(name)
    if (not path.parts or path.is_absolute() or str(path) != name or "\\" in name or ":" in name
            or any(ord(c) < 32 for c in name) or any(p in ("..", ".git", ".tmp") for p in path.parts)):
        raise ValueError(f"invalid repository path: {name!r}")
    return name


def digest(path):
    with path.open("rb") as src:
        return hashlib.file_digest(src, "sha256").hexdigest()


def manifest_file(path, size, expected):
    return (path.is_file() and not path.is_symlink() and path.stat().st_size == size
            and digest(path) == expected)


def github_media_url(url):
    if not isinstance(url, str) or any(ord(char) <= 32 or ord(char) == 127 for char in url):
        raise ValueError("invalid GitHub media URL")
    try:
        target = urllib.parse.urlsplit(url)
        valid = (target.scheme == "https" and target.port in (None, 443) and target.username is None
                 and target.password is None and (target.hostname or "").endswith(".githubusercontent.com"))
    except ValueError:
        valid = False
    if not valid:
        raise ValueError("unexpected GitHub media host")
    return url


class GitHubRedirects(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, url):
        github_media_url(url)
        return super().redirect_request(req, fp, code, msg, headers, url)


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, url):
        return None


def read_github(opener, request, read):
    for attempt in range(3):
        delay = 2 ** attempt
        try:
            with opener.open(request, timeout=60) as response:
                return read(response)
        except urllib.error.HTTPError as error:
            with error:
                if error.code in (403, 429):
                    after = error.headers.get("Retry-After", "")
                    reset = error.headers.get("X-RateLimit-Reset", "")
                    exhausted = error.headers.get("X-RateLimit-Remaining") == "0"
                    waits = []
                    if after.isdecimal():
                        waits.append(int(after))
                    if exhausted and reset.isdecimal():
                        waits.append(int(reset) - int(time.time()) + 1)
                    if waits:
                        delay = max(delay, *waits)
                    elif error.code == 429 or exhausted or b"rate limit" in error.read(1024).lower():
                        delay = 60 * 2 ** attempt
                    else:
                        raise
                    if delay > 60 or attempt == 2:
                        raise OSError(f"GitHub rate limit (HTTP {error.code}), retry in {delay} seconds") from None
                elif error.code not in (408, 500, 502, 503, 504) or attempt == 2:
                    raise
        except (OSError, http.client.HTTPException):
            if attempt == 2:
                raise
        time.sleep(delay)


def read_github_blob(opener, revision, name, oid, read):
    api = f"https://api.github.com/repos/{REPO}"

    def get(url):
        request = urllib.request.Request(url, headers={"Accept": "application/vnd.github.raw+json"})
        return read_github(opener, request, read)

    try:
        return get(f"{api}/git/blobs/{oid}")
    except urllib.error.HTTPError as error:
        if error.code != 404:
            raise
    return get(f"{api}/contents/{urllib.parse.quote(name)}?ref={revision}")


def copy_response(response, output, limit):
    length = response.headers.get("Content-Length")
    if length is not None and not 0 <= int(length) <= limit:
        raise ValueError("oversized GitHub blob response")
    while block := response.read(min(CHUNK, limit + 1 - output.tell())):
        output.write(block)
        if output.tell() > limit:
            raise ValueError("oversized GitHub blob response")
    if length is not None and output.tell() != int(length):
        raise OSError("incomplete GitHub blob response")


def matches_blob(blob, oid, limit):
    size = blob.seek(0, os.SEEK_END)
    if size > limit:
        return False
    blob.seek(0)
    check = hashlib.sha1(f"blob {size}\0".encode())
    while block := blob.read(CHUNK):
        check.update(block)
    return check.hexdigest() == oid


def decode_blob_envelope(wire, output, oid, limit):
    # GitHub's JSON envelope can contain a large, line-wrapped base64 string.
    # Read only its small surrounding metadata into the JSON parser.
    size = wire.seek(0, os.SEEK_END)
    wire.seek(0)
    prefix = wire.read(8192)
    marker = re.search(rb'"content"\s*:\s*"', prefix)
    if not marker:
        raise ValueError("missing GitHub blob content")
    start = marker.end()
    footer_start = wire.seek(max(start, size - 8192))
    footer = wire.read(8192)
    quote = footer.find(b'"')
    if quote < 0:
        raise ValueError("invalid GitHub blob envelope")
    try:
        record = json.loads(prefix[:start] + footer[quote:])
    except (ValueError, RecursionError):
        raise ValueError("invalid GitHub blob envelope") from None
    if (not isinstance(record, dict) or record.get("sha") != oid or record.get("encoding") != "base64"
            or record.get("content") != "" or type(record.get("size")) is not int or not 0 <= record["size"] <= limit):
        raise ValueError("invalid GitHub blob metadata")

    wire.seek(start)
    remaining = footer_start + quote - start
    encoded_size = 4 * ((record["size"] + 2) // 3)
    consumed = 0
    escape = remainder = b""
    while remaining:
        block = wire.read(min(CHUNK, remaining))
        if not block:
            raise ValueError("incomplete GitHub blob content")
        remaining -= len(block)
        block = escape + block
        escape = b"\\" if block.endswith(b"\\") else b""
        if escape:
            block = block[:-1]
        encoded = remainder + block.replace(b"\\n", b"").replace(b"\\r", b"").replace(b"\\/", b"/")
        end = len(encoded) - len(encoded) % 4
        complete = encoded[:end]
        consumed += end
        if consumed > encoded_size or (consumed < encoded_size and b"=" in complete):
            raise ValueError("invalid GitHub base64 content length or padding")
        output.write(base64.b64decode(complete, validate=True))
        remainder = encoded[end:]
        if output.tell() > record["size"]:
            raise ValueError("oversized decoded GitHub blob")
    if escape or remainder or consumed != encoded_size or output.tell() != record["size"]:
        raise ValueError("incomplete decoded GitHub blob")


class GitTree:
    def __init__(self, repository, commit):
        self.repository = Path(repository)
        self.command = ["git", "-C", str(repository)]
        self.commit = commit
        self.media = urllib.request.build_opener(GitHubRedirects())
        self.raw = urllib.request.build_opener(NoRedirect())
        promisor = subprocess.run([*self.command, "config", "--get", "remote.origin.promisor"], capture_output=True)
        self.promisor = promisor.stdout.strip() == b"true"
        if self.promisor:
            if self.git("remote", "get-url", "origin").decode().strip() != f"https://github.com/{REPO}.git":
                raise ValueError("unexpected promisor repository")
            self.no_lazy_fetch = subprocess.run([*self.command, "--no-lazy-fetch", "--version"], capture_output=True).returncode == 0

    def git(self, *args, data=None):
        return subprocess.check_output([*self.command, *args], input=data)

    def files(self, roots):
        roots = sorted(set(map(safe_path, roots)))
        rows = self.git("--literal-pathspecs", "ls-tree", "-rz", self.commit, "--", *roots)
        result = {}
        for row in filter(None, rows.split(b"\0")):
            metadata, filename = row.split(b"\t", 1)
            mode, kind, oid = metadata.decode("ascii").split()
            name = safe_path(filename.decode("utf-8"))
            if kind != "blob" or mode not in ("100644", "100755") or not re.fullmatch(r"[0-9a-f]{40}", oid):
                raise ValueError("selection contains a non-regular Git entry: " + name)
            result[name] = (oid, int(mode, 8) & 0o777)
        for root in roots:
            if root not in result and not any(name.startswith(root + "/") for name in result):
                raise ValueError("release is missing " + root)
        return result

    def contains(self, name):
        return bool(self.git("--literal-pathspecs", "ls-tree", "-z", self.commit, "--", safe_path(name)))

    def json(self, name):
        files = self.files([name])
        self.prefetch(files, limit=4 * CHUNK)
        oid, _ = files[name]
        size = int(self.git("cat-file", "-s", oid))
        if not 0 < size <= 4 * CHUNK:
            raise ValueError("unexpected size for " + name)
        data = self.git("cat-file", "blob", oid)
        if len(data) != size or hashlib.sha1(f"blob {size}\0".encode() + data).hexdigest() != oid:
            raise ValueError("invalid manifest Git object: " + name)
        return json.loads(data)

    def missing(self, selected):
        if self.no_lazy_fetch:
            query = "".join(oid + "\n" for oid in selected).encode("ascii")
            rows = self.git("--no-lazy-fetch", "cat-file", "--batch-check=%(objectname) %(objecttype)", data=query).splitlines()
            if len(rows) != len(selected):
                raise ValueError("incomplete local Git object inventory")
            absent = {}
            for (oid, name), row in zip(selected.items(), rows):
                if row == oid.encode() + b" missing":
                    absent[oid] = name
                elif row != oid.encode() + b" blob":
                    raise ValueError("unexpected local Git object metadata")
            return absent
        # Older Git versions support local-only enumeration but have no --no-lazy-fetch.
        present = set(self.git("cat-file", "--batch-all-objects", "--unordered", "--batch-check=%(objectname)").splitlines())
        return {oid: name for oid, name in selected.items() if oid.encode() not in present}

    def raw_blob(self, name, oid, limit):
        def store(blob):
            blob.seek(0)
            stored = subprocess.check_output([*self.command, "hash-object", "-w", "--stdin"], stdin=blob)
            if stored.strip() != oid.encode():
                raise ValueError("could not store the verified Git blob: " + name)

        def read(response, api=False):
            # GitHub's Git Data API serves blobs up to 100 MiB. Allow room for
            # base64 and JSON line wrapping when a cache returns its default view.
            blob_limit = min(100 * CHUNK, limit) if api else limit
            wire_limit = 2 * blob_limit + 16384 if api else blob_limit
            with tempfile.TemporaryFile(dir=self.repository) as wire:
                copy_response(response, wire, wire_limit)
                if matches_blob(wire, oid, blob_limit):
                    store(wire)
                    return
                if not api:
                    raise ValueError("raw file failed Git blob verification: " + name)
                with tempfile.TemporaryFile(dir=self.repository) as decoded:
                    decode_blob_envelope(wire, decoded, oid, blob_limit)
                    if not matches_blob(decoded, oid, blob_limit):
                        raise ValueError("API response failed Git blob verification: " + name)
                    store(decoded)

        url = f"https://raw.githubusercontent.com/{REPO}/{self.commit}/" + urllib.parse.quote(name)
        try:
            return read_github(self.raw, url, read)
        except (OSError, http.client.HTTPException, ValueError):
            pass

        try:
            read_github_blob(self.raw, self.commit, name, oid, lambda response: read(response, api=True))
        except (OSError, http.client.HTTPException, ValueError) as error:
            raise OSError(f"could not retrieve Git blob {oid} for {name}: {error}") from None

    def fetch_batch(self, selected, limit):
        pending = self.missing(selected)
        for attempt in range(3):
            if not pending:
                return
            wanted = "".join(oid + "\n" for oid in pending).encode("ascii")
            result = subprocess.run([*self.command, "-c", "fetch.negotiationAlgorithm=noop", "fetch", "--quiet",
                                     "--no-tags", "--no-write-fetch-head", "--no-recurse-submodules", "--filter=blob:none",
                                     "--stdin", "origin"], input=wanted, stderr=subprocess.PIPE)
            pending = self.missing(pending)
            if not pending:
                return
            if result.returncode == 0:
                break
            refused = re.search(rb"not our ref ([0-9a-f]{40})\b", result.stderr)
            if refused and (oid := refused[1].decode()) in pending:
                self.raw_blob(pending.pop(oid), oid, limit)
            elif pending and attempt < 2:
                time.sleep(2 ** attempt)
        # An opaque pack failure can cover thousands of healthy blobs. Give smaller
        # groups one bounded series of Git attempts before using per-path HTTP.
        items = list(pending.items())
        if len(items) > 128:
            for start in range(0, len(items), 128):
                self.fetch_batch(dict(items[start:start + 128]), limit)
        else:
            for oid, name in items:
                self.raw_blob(name, oid, limit)

    def prefetch(self, files, limit=MAX_BLOB):
        # A frozen local repository uses only the normal Git materializer.
        if not self.promisor:
            return
        unique = {}
        for name, (oid, _) in files.items():
            unique.setdefault(oid, name)
        objects = sorted(unique.items())
        for start in range(0, len(objects), 8192):
            self.fetch_batch(dict(objects[start:start + 8192]), limit)

    def lfs_download_request(self, expected, size):
        """Ask the same GitHub repository for the basic transfer action for this exact pointer."""
        mime = "application/vnd.git-lfs+json"
        payload = {"operation": "download", "transfers": ["basic"], "objects": [{"oid": expected, "size": size}]}
        batch = urllib.request.Request(f"https://github.com/{REPO}.git/info/lfs/objects/batch",
                                       data=json.dumps(payload).encode(), headers={"Accept": mime, "Content-Type": mime})
        with self.media.open(batch, timeout=60) as response:
            data = response.read(CHUNK + 1)
        if len(data) > CHUNK:
            raise ValueError("oversized GitHub LFS batch response")
        result = json.loads(data)
        objects = result.get("objects") if isinstance(result, dict) else None
        if (not isinstance(objects, list) or len(objects) != 1 or not isinstance(objects[0], dict)
                or objects[0].get("oid") != expected or type(objects[0].get("size")) is not int
                or objects[0]["size"] != size or "error" in objects[0] or result.get("transfer", "basic") != "basic"):
            raise ValueError("GitHub LFS batch did not return the selected object")
        actions = objects[0].get("actions")
        action = actions.get("download") if isinstance(actions, dict) else None
        if not isinstance(action, dict):
            raise ValueError("missing GitHub LFS download action")
        request = urllib.request.Request(github_media_url(action.get("href")))
        headers = action.get("header", {})
        if not isinstance(headers, dict):
            raise ValueError("invalid GitHub LFS action headers")
        for key, value in headers.items():
            if (key.lower() not in ("authorization", "accept") or not isinstance(value, str)
                    or not value.isascii() or any(ord(char) < 32 or ord(char) == 127 for char in value)):
                raise ValueError("unexpected GitHub LFS action header")
            request.add_unredirected_header(key, value)
        return request

    def fetch_lfs(self, name, expected, size, cache):
        if not 0 <= size <= MAX_LFS:
            raise ValueError("LFS object exceeds size limit: " + name)
        cached = cache / expected
        if manifest_file(cached, size, expected):
            return cached
        url = f"https://media.githubusercontent.com/media/{REPO}/{self.commit}/" + urllib.parse.quote(name)
        use_batch = False
        for attempt in range(3):
            try:
                with tempfile.NamedTemporaryFile(dir=cache, delete=False) as output:
                    pending = Path(output.name)
                    try:
                        check = hashlib.sha256()
                        received = 0
                        if not use_batch:
                            try:
                                download = self.media.open(url, timeout=60)
                            except urllib.error.HTTPError as error:
                                if error.code != 404:
                                    raise
                                error.close()
                                use_batch = True
                        if use_batch:
                            download = self.media.open(self.lfs_download_request(expected, size), timeout=60)
                        with download as response:
                            while block := response.read(CHUNK):
                                received += len(block)
                                if received > size:
                                    raise ValueError("oversized Git LFS object: " + name)
                                check.update(block)
                                output.write(block)
                        if received != size or check.hexdigest() != expected:
                            raise ValueError("Git LFS object failed verification: " + name)
                        output.close()
                        os.replace(pending, cached)
                        return cached
                    finally:
                        pending.unlink(missing_ok=True)
            except (OSError, http.client.HTTPException) as error:
                if isinstance(error, urllib.error.HTTPError):
                    retry = error.code in (408, 429, 500, 502, 503, 504)
                    error.close()
                    if not retry:
                        raise OSError(f"GitHub LFS download failed for {name} (HTTP {error.code})") from None
                if attempt == 2:
                    raise OSError(f"GitHub LFS download failed for {name} after 3 attempts") from None
                time.sleep(2 ** attempt)

    def materialize(self, files, destinations, cache):
        self.prefetch(files)
        with subprocess.Popen([*self.command, "cat-file", "--batch"], stdin=subprocess.PIPE,
                              stdout=subprocess.PIPE) as reader:
            try:
                for name, (oid, mode) in sorted(files.items()):
                    output = destinations[name]
                    output.parent.mkdir(parents=True, exist_ok=True)
                    reader.stdin.write(oid.encode() + b"\n")
                    reader.stdin.flush()
                    info = reader.stdout.readline().split()
                    if len(info) != 3 or info[:2] != [oid.encode(), b"blob"]:
                        raise ValueError("Git did not return the selected object for " + name)
                    size = int(info[2])
                    if not 0 <= size <= MAX_BLOB:
                        raise ValueError("oversized Git blob: " + name)
                    check = hashlib.sha1(f"blob {size}\0".encode())
                    remaining = size
                    with output.open("xb") as stream:
                        while remaining:
                            block = reader.stdout.read(min(CHUNK, remaining))
                            if not block:
                                raise ValueError("incomplete Git blob: " + name)
                            check.update(block)
                            stream.write(block)
                            remaining -= len(block)
                    if reader.stdout.read(1) != b"\n" or check.hexdigest() != oid:
                        raise ValueError("Git blob failed verification: " + name)
                    if size < 1024:
                        data = output.read_bytes()
                        if data.startswith(b"version https://git-lfs.github.com/spec/"):
                            match = LFS.fullmatch(data)
                            if not match:
                                raise ValueError("invalid Git LFS pointer: " + name)
                            obj = self.fetch_lfs(name, match[1].decode(), int(match[2]), cache)
                            shutil.copyfile(obj, output)
                    output.chmod(mode)
                reader.stdin.close()
                if reader.stdout.read(1) or reader.wait():
                    raise ValueError("Git failed to complete the selected objects")
            finally:
                if reader.poll() is None:
                    reader.kill()


HOSTS = ("linux-x86_64", "linux-i686", "linux-aarch64", "linux-arm", "linux-armhf")


def elf_host(path):
    """Classify a Linux executable or shared library from its ELF identity."""
    with Path(path).open("rb") as stream:
        header = stream.read(64)
    if (len(header) < 52 or header[:4] != b"\x7fELF" or header[4] not in (1, 2)
            or header[5:7] != b"\x01\x01" or header[7] not in (0, 3)
            or header[16:18] not in (b"\x02\x00", b"\x03\x00") or header[20:24] != b"\x01\x00\x00\x00"):
        raise ValueError(f"expected a little-endian Linux ELF executable or shared library: {path}")
    bits = header[4]
    size, flags_at, ehsize_at = (52, 36, 40) if bits == 1 else (64, 48, 52)
    if len(header) < size or int.from_bytes(header[ehsize_at:ehsize_at + 2], "little") != size:
        raise ValueError(f"invalid ELF header size: {path}")
    machine = int.from_bytes(header[18:20], "little")
    host = {(2, 62): "linux-x86_64", (1, 3): "linux-i686", (2, 183): "linux-aarch64"}.get((bits, machine))
    if host:
        return host
    if (bits, machine) == (1, 40):
        flags = int.from_bytes(header[flags_at:flags_at + 4], "little")
        abi = flags & 0x600
        if flags >> 24 != 5 or abi == 0x600:
            raise ValueError(f"invalid ARM EABI version or contradictory float flags: {path}")
        # AAELF32: when neither float flag is present, base PCS is implied.
        host = "linux-armhf" if abi == 0x400 else "linux-arm"
        arm_interpreter(path, header, host)
        return host
    raise ValueError(f"unsupported ELF class {bits} and machine {machine}: {path}")


def arm_interpreter(path, header, host):
    offset = int.from_bytes(header[28:32], "little")
    stride = int.from_bytes(header[42:44], "little")
    count = int.from_bytes(header[44:46], "little")
    if not count:
        return
    if stride != 32 or offset < 52 or offset + count * stride > Path(path).stat().st_size:
        raise ValueError(f"invalid ARM ELF program header table: {path}")
    interpreters = {"ld-linux-armhf.so.3": "linux-armhf", "ld-musl-armhf.so.1": "linux-armhf",
                    "ld-linux.so.3": "linux-arm", "ld-musl-arm.so.1": "linux-arm"}
    with Path(path).open("rb") as stream:
        stream.seek(offset)
        table = stream.read(count * stride)
        for index in range(0, len(table), stride):
            item = table[index:index + stride]
            if int.from_bytes(item[:4], "little") != 3:  # PT_INTERP
                continue
            size = int.from_bytes(item[16:20], "little")
            if not 1 < size <= 4096:
                raise ValueError(f"invalid ARM ELF interpreter size: {path}")
            stream.seek(int.from_bytes(item[4:8], "little"))
            value = stream.read(size)
            if len(value) != size or value[-1:] != b"\0" or b"\0" in value[:-1]:
                raise ValueError(f"invalid ARM ELF interpreter path: {path}")
            loader = os.fsdecode(value[:-1]).rsplit("/", 1)[-1]
            if loader in interpreters and interpreters[loader] != host:
                raise ValueError(f"ARM ELF float flags conflict with {loader}: {path}")


ARM_HWCAP_BITS = {"vfp": 6, "neon": 12, "vfpv3": 13, "vfpv3d16": 14, "vfpv4": 16, "vfpd32": 19}


def arm_hwcap():
    """Read AT_HWCAP of this process from its runtime. QEMU supplies the guest aux vector."""
    if hasattr(os, "getauxval"):
        try:
            return os.getauxval(16)
        except (KeyError, OSError):
            pass
    import ctypes
    try:
        getauxval = ctypes.CDLL(None, use_errno=True).getauxval
    except (OSError, AttributeError) as error:
        raise ValueError("the ARM process runtime does not expose AT_HWCAP") from error
    getauxval.argtypes = [ctypes.c_ulong]
    getauxval.restype = ctypes.c_ulong
    ctypes.set_errno(0)
    value = getauxval(16)
    if not value and ctypes.get_errno():
        raise ValueError("the ARM process has no readable AT_HWCAP")
    return value


@lru_cache(maxsize=1)
def host_info():
    if sys.platform != "linux":
        return {"abi": None}
    # A 32-bit userspace on a 64-bit kernel and QEMU user-mode both need the
    # ABI of the running interpreter. The kernel machine name cannot select it.
    host = elf_host(sys.executable)
    result = {"abi": host}
    if host in ("linux-arm", "linux-armhf"):
        value = arm_hwcap()
        features = [name for name, bit in ARM_HWCAP_BITS.items() if value & (1 << bit)]
        if host == "linux-armhf" and "vfp" not in features:
            raise ValueError("ARM hard-float userspace requires VFP in the process AT_HWCAP")
        result.update(at_hwcap=value, features=features)
    return result


def current_host():
    return host_info()["abi"]


def require_cpu(metadata, host):
    required = metadata.get("required_hwcap", [])
    if (not isinstance(required, list) or any(not isinstance(name, str) or name not in ARM_HWCAP_BITS for name in required)
            or required and host not in ("linux-arm", "linux-armhf")):
        raise ValueError("invalid hardware capability requirement for " + str(host))
    missing = set(required) - set(host_info().get("features", []))
    if missing:
        raise ValueError(f"{metadata.get('member', 'package')} requires ARM AT_HWCAP {', '.join(sorted(missing))}")


def require_host(path, expected):
    actual = elf_host(path)
    if actual != expected:
        raise ValueError(f"{path} is {actual}; the selected host is {expected}")


def extra_selection_paths(tree, manifest, languages):
    selections = manifest["selections"]
    paths = {}
    objc = (languages & {"objc", "objcpp"}) - selections.keys()
    if objc and "cpp" in selections and tree.contains("src/compilers/objc/selection.json"):
        paths.update(dict.fromkeys(objc, "src/compilers/objc/selection.json"))
    java_record = f"bin/packages/{manifest['host']}/wrjava/java.json"
    if "java" in languages and "c" in selections and tree.contains(java_record):
        paths["java"] = java_record
    return paths


def host_manifest(tree, language=None):
    host = current_host()
    if host is None:
        raise ValueError("native SDK packages require Linux")
    manifest = tree.json(f"bin/packages/{host}/manifest.json")
    if manifest.get("schema") != 1 or manifest["host"] != host:
        raise ValueError("unsupported host package manifest")
    selector = extra_selection_paths(tree, manifest, {language}).get(language)
    if selector is None:
        return manifest
    record = tree.json(selector)
    if language == "java":
        if record.get("schema") != 2 or record.get("host") != host:
            raise ValueError("unexpected Java package record for " + host)
        jdk_lock = "src/compilers/jvm/openjdk/" + ("upstream.json" if host == "linux-x86_64" else "debian/upstream.json")
        if record.get("jdk_lock") != jdk_lock:
            raise ValueError("unexpected JDK input manifest for " + host)
        entry = tree.json("src/compilers/jvm/selection.json")
        entry["support_roots"].extend([selector, jdk_lock])
        manifest["packages"]["wrjava"] = record["launcher"]
        manifest["selections"]["java"] = entry
    else:
        manifest["selections"][language] = record
    return manifest


def go_release(tree, language, entry):
    records = tree.json(entry["release_record"])
    if records and set(records) != set(entry["native_outputs"]):
        raise ValueError("incomplete native release set for " + language)
    return records


def selection(args, tree):
    language = ALIASES.get(args.language, args.language)
    if language not in LANGUAGES or args.platform not in PLATFORMS:
        raise ValueError("unknown language or platform; use 'list' for available selections")
    mode = args.mode or "binary"
    if language in ("objc", "objcpp"):
        if args.platform != "generic":
            raise ValueError("this revision packages the universal GNUstep interfaces for generic")
        entry = host_manifest(tree, language)["selections"].get(language)
        if not entry:
            raise ValueError("the selected host has no C-family toolchain")
        if not entry["artifacts"] and mode == "binary":
            if args.mode == "binary":
                raise ValueError("this host has no published GNUstep binary package; select --mode source")
            mode = "source"
    if language == "rust":
        if args.no_mte:
            if args.mode not in (None, "bindings"):
                raise ValueError("--no-mte at install time selects the upstream Rust bindings mode")
            mode = "bindings"
        elif mode == "bindings":
            raise ValueError("select --mode bindings --no-mte for the upstream Rust bindings")
        elif mode == "binary" and not host_manifest(tree, language)["selections"].get("rust", {}).get("artifacts"):
            if args.mode == "binary":
                raise ValueError("this revision has no published wrrs binary; select --mode source")
            mode = "source"
    elif mode == "bindings" or args.no_mte:
        raise ValueError("the --mode bindings and --no-mte install options are specific to upstream Rust")
    if language == "java" and args.platform not in JAVA_PLATFORMS:
        raise ValueError("this revision has Java bindings for generic and abb")
    if language == "py" and args.platform not in PY_PLATFORMS:
        raise ValueError("this revision has Python bindings for generic and unitree")
    if language in GO_COMMANDS:
        if args.platform not in GO_PLATFORMS:
            raise ValueError("this revision has no " + language + " bindings for platform " + args.platform)
        if mode == "binary" and not ((entry := host_manifest(tree, language)["selections"].get(language)) and go_release(tree, language, entry)):
            raise ValueError("this revision has no published " + COMMANDS[language] + " native package; select --mode source")
    if args.bootstrap and (mode != "source" or language not in ("c", "cpp", "objc", "objcpp", "tinygo")):
        raise ValueError("--bootstrap applies to C/C++ and TinyGo source builds")
    if args.jobs and current_host() not in HOSTS and not (
            mode == "source" and language in ("c", "cpp", "objc", "objcpp", "rust", "wat", "py", *GO_COMMANDS)):
        raise ValueError("--jobs requires a native host-tool or language build")
    if args.rust_bin and (mode != "source" or language not in ("wat", "rust")):
        raise ValueError("--rust-bin applies to a native Rust or wrwat source build")
    return language, mode


def binding_roots(platform_name, language):
    roots = [f"{INCLUDE}/universal/{LANGUAGES[language]}"]
    if language in ("objc", "objcpp"):
        roots.append(f"{INCLUDE}/universal/c")
    if platform_name == "generic":
        return roots
    roots.append(f"{INCLUDE}/platform/{platform_name}/{LANGUAGES[language]}")
    reader = {"c": "reader.h", "cpp": "reader.h", "rust": "reader.rs", "as": "reader.ts", "js": "reader.mjs"}.get(language)
    if reader and platform_name != "unitree":
        roots.append(f"{INCLUDE}/platform/shared/{reader}")
    return roots


def native_packages(manifest, artifacts, command=None, prefix=""):
    packages, installed = {}, set()
    for key, targets in artifacts.items():
        package = manifest["packages"][key]
        source = safe_path(package["path"])
        require_cpu(package, manifest["host"])
        if (not source.startswith("bin/packages/" + manifest["host"] + "/")
                or package.get("host", manifest["host"]) != manifest["host"]
                or source in packages or not targets or package.get("format") != "tar.xz"
                or not re.fullmatch(r"[A-Za-z0-9_+-]+", package["member"])):
            raise ValueError("duplicate or empty binary package")
        for size_key, hash_key in (("compressed_bytes", "compressed_sha256"), ("bytes", "sha256")):
            size = package[size_key]
            if type(size) is not int or not 0 < size <= MAX_BLOB or not HEX.fullmatch(package[hash_key]):
                raise ValueError("invalid package size or digest: " + source)
        for target in targets:
            rust_library = command == "wrrs" and re.fullmatch(r"lib/lib[A-Za-z0-9_.+-]+\.so(?:\.[A-Za-z0-9_.+-]+)?", target)
            rust_linker = key == "wasm-ld" and target == "lib/rustlib/x86_64-unknown-linux-gnu/bin/rust-lld"
            if safe_path(target) in installed or not (
                    target.startswith(("bin/", "share/toolchains/")) or rust_library or rust_linker):
                raise ValueError("invalid native package destination: " + target)
            installed.add(target)
        packages[source] = (package, [prefix + t for t in targets])
    if command and "bin/" + command not in installed:
        raise ValueError("release does not contain the selected native compiler")
    return packages


def package_plan(tree, platform_name, language, mode, *, tinygo_llvm=None, rust_bin=None):
    platform_manifest = f"platform/{platform_name}/platform.json"
    roots = ["LICENSE", "src/xmake", ABI, "src/examples/" + language, platform_manifest,
             f"platform/{platform_name}/README.md", f"platform/{platform_name}/README.zh.md",
             *binding_roots(platform_name, language)]
    for guide in tree.json(platform_manifest).get("guides", []):
        if not re.fullmatch(r"[a-z0-9_-]+(?:\.zh)?\.md", guide):
            raise ValueError("invalid platform guide filename: " + str(guide))
        roots.append(f"platform/{platform_name}/{guide}")
    for locale in ("en", "zh"):
        roots.extend((f"document/{locale}/install-xmake.md", f"document/{locale}/languages/{language}.md"))
    mappings = {ABI: ABI_INSTALLED, "src/xmake": "tools/xmake", "src/examples": "examples"}
    if platform_name != "generic":
        roots.append(f"src/examples/{platform_name}/{language}")
    if platform_name == "unitree":
        roots.append("platform/unitree/go2-low-state.contract")
    packages, source_roots = {}, []
    if mode != "bindings":
        manifest = host_manifest(tree, language)
        if language not in manifest["selections"]:
            raise ValueError(f"this release has no {language} selection for {manifest['host']}")
        entry = manifest["selections"][language]
        if language in GO_COMMANDS and mode == "binary":
            published = go_release(tree, language, entry)
            manifest = dict(manifest, packages={**manifest["packages"], **published})
            entry = dict(entry, artifacts=entry["native_outputs"])
        binary_only = set(entry.get("binary_support_roots", [])) if mode == "source" else set()
        roots.extend(root for root in entry["support_roots"] if root not in binary_only)
        for origin, target in entry.get("support_map", {}).items():
            safe_path(origin)
            safe_path(target)
            if origin not in entry["support_roots"] or origin in mappings and target != mappings[origin]:
                raise ValueError("invalid source mapping: " + origin)
            mappings[origin] = target
        packages = native_packages(manifest, entry.get("host_tools", {}))
        if mode == "source":
            source_roots = list(entry["source_roots"])
            if language == "tinygo" and not tinygo_llvm:
                source_roots.extend(entry["llvm_source_roots"])
            roots.extend(source_roots)
        elif language in COMMANDS:
            packages.update(native_packages(manifest, entry["artifacts"], COMMANDS[language]))
        if "native_backend" in entry:
            if entry["native_backend"] != "c" or language not in ("js", "typescript", "py", "java"):
                raise ValueError("unexpected native script backend")
            backend = manifest["selections"]["c"]
            backend_dir = {"py": PY_BACKEND, "java": JAVA_BACKEND}.get(language, C_BACKEND)
            packages.update(native_packages(manifest, backend["artifacts"], "wrc", backend_dir + "/"))
            for root in [*backend["support_roots"], *binding_roots("generic", "c")]:
                if root == ABI:
                    continue
                if root == "share/toolchains/portable/sysroots":
                    root += "/wasm32-wasip1/core3.0-eh-mte"
                if root.startswith("lib/") and root != "lib/wasm32-wasip1/core3.0-eh-mte":
                    continue
                roots.append(root)
                mappings[root] = backend_dir + "/" + safe_path(backend["support_map"].get(root, root))
        if language == "typescript":
            for root in binding_roots(platform_name, "js"):
                roots.append(root)
                mappings[root] = JS_BACKEND + "/" + root
        roots.extend(packages)
    if current_host() in HOSTS:
        roots.extend(("src/host-tools/install_official.py", "src/host-tools/xmake/UPSTREAM.json",
                      "src/host-tools/uwvm2-ros/UPSTREAM.json", "src/compilers/official_dist.py", "install/install.py",
                      "document/en/host-tools.md", "document/zh/host-tools.md"))
    files = tree.files(roots)
    if language in ("js", "typescript", "py", "java"):
        # The private C backend prepares only wasm32-wasip1/core3.0-eh-mte.
        other_configs = ("include/sysroot/c/config/nomte/", "include/sysroot/c++/config/threads/")
        files = {path: item for path, item in files.items() if not path.startswith(other_configs)}
    if language in ("c", "cpp", "js", "typescript", "py", "java"):
        # GNUstep only contributes these two archives to the common flavor directory.
        files = {path: item for path, item in files.items()
                 if not (path.startswith("lib/") and path.rsplit("/", 1)[-1] in ("libobjc.a", "libuwrosobjc.a"))}
    if language in SCRIPT_COMMANDS:
        command = "bin/" + SCRIPT_COMMANDS[language]
        script = PY_ENTRY if language == "py" else SCRIPT_ENTRY
        if mappings.get(script) != command or files[script][1] != 0o755:
            raise ValueError("release is missing its executable script launcher: " + command)
    return files, packages, mappings, source_roots


def unpack_executable(archive, metadata, output, *, host=None):
    if not manifest_file(archive, metadata["compressed_bytes"], metadata["compressed_sha256"]):
        raise ValueError("compressed executable failed verification: " + metadata["path"])
    decoder = lzma.LZMADecompressor(format=lzma.FORMAT_XZ, memlimit=256 * CHUNK)
    size = metadata["bytes"]
    output.parent.mkdir(parents=True, exist_ok=True)
    with archive.open("rb") as src, tempfile.TemporaryFile(dir=archive.parent) as tar:
        maximum = size + 16 * 1024
        while not decoder.eof:
            block = src.read(CHUNK) if decoder.needs_input else b""
            if not block and decoder.needs_input:
                raise ValueError("truncated XZ stream: " + metadata["path"])
            plain = decoder.decompress(block, max_length=min(CHUNK, maximum + 1 - tar.tell()))
            tar.write(plain)
            if tar.tell() > maximum:
                raise ValueError("tar exceeds declared member size and padding limit: " + metadata["path"])
        if src.read(1) or decoder.unused_data or tar.tell() % tarfile.BLOCKSIZE:
            raise ValueError("invalid XZ stream or tar length")
        tar.seek(0)
        header = tar.read(tarfile.BLOCKSIZE)
        member = tarfile.TarInfo.frombuf(header, "utf-8", "strict")
        if (header[257:263] != b"ustar\0" or member.type != tarfile.REGTYPE or member.linkname
                or member.name != metadata["member"] or member.mode != 0o755 or member.size != size):
            raise ValueError("expected one named, regular 0755 USTAR executable in " + metadata["path"])
        check = hashlib.sha256()
        remaining = size
        with output.open("xb") as target:
            while remaining:
                block = tar.read(min(CHUNK, remaining))
                if not block:
                    raise ValueError("incomplete tar member")
                target.write(block)
                check.update(block)
                remaining -= len(block)
        padding = tar.read()
        if (len(padding) < (-size % 512) + 1024 or any(padding) or check.hexdigest() != metadata["sha256"]):
            raise ValueError("invalid tar padding, extra member, or unverified executable")
    require_host(output, host or current_host())
    require_cpu(metadata, host or current_host())
    output.chmod(0o755)


def go_install_command(directory, scratch, language, mode, args):
    cmd = [sys.executable, "-I", "-B", directory / "src/compilers/go/rebuild.py", "--prefix", directory,
           "--work", scratch / "go-build", "--language", language, "--mode", mode]
    if args.jobs:
        cmd.extend(["--jobs", str(args.jobs)])
    if args.bootstrap:
        cmd.extend(["--llvm-config", args.bootstrap / "bin/llvm-config"])
    return cmd


def source_build(directory, scratch, language, args):
    if language in GO_COMMANDS:
        command = go_install_command(directory, scratch, language, "source", args)
    elif language == "rust":
        command = [sys.executable, "-I", "-B", directory / "src/compilers/rust/rebuild.py",
                   "--prefix", directory, "--work", scratch / "rust-build"]
        if args.rust_bin:
            command += ["--rust-bin", args.rust_bin]
        if args.jobs:
            command += ["--jobs", str(args.jobs)]
    elif language == "wat":
        command = [sys.executable, "-I", "-B", directory / "src/compilers/wrwat/rebuild.py",
                   "--output", directory / "bin/wrwat"]
        if args.rust_bin:
            command += ["--rust-bin", args.rust_bin]
    elif language in ("objc", "objcpp"):
        if not args.bootstrap:
            raise ValueError("a GNUstep source build requires --bootstrap /path/to/host-llvm")
        command = [sys.executable, "-I", "-B", directory / "src/compilers/objc/rebuild.py",
                   "--bootstrap", args.bootstrap, "--work", scratch / "build", "--prefix", directory,
                   "--language", language, "--jobs", str(args.jobs or 4)]
    else:
        if not args.bootstrap:
            raise ValueError("a C/C++ source build requires --bootstrap /path/to/host-llvm")
        command = [sys.executable, "-I", "-B", directory / "src/compilers/cc/rebuild.py",
                   "--bootstrap", args.bootstrap, "--work", scratch / "build", "--prefix", directory,
                   "--language", language, "--matrix"]
        if args.jobs:
            command.extend(("--jobs", str(args.jobs)))
    if language in ("wat", "rust"):
        command.extend(["--download-cache", args.prefix / ".cache/sha256"])
    if language == "wat":
        command.extend(["--work", scratch, "--jobs", str(args.jobs or 4)])
    env = dict(os.environ, TMPDIR=str(scratch), CARGO_NET_OFFLINE="true", WROS_DIST_CACHE=str(args.prefix / ".cache/sha256"))
    subprocess.run(command, env=env, check=True, stdout=sys.stderr)
    program = directory / "bin" / COMMANDS[language]
    if not program.is_file() or not os.access(program, os.X_OK):
        raise ValueError("source build did not produce the selected executable")
    if language == "wat":
        lock = directory / "third-parties/wat-mte/release.json"
        release = json.loads(lock.read_bytes())
        actual = digest(program)
        if actual != release["binary_sha256"]:
            release["source_build"] = {"commit": args.commit, "published_sha256": release["binary_sha256"]}
            release.update(binary_bytes=program.stat().st_size, binary_sha256=actual)
            # The canonical source lock may share its inode with the installed copy.
            replacement = scratch / "built-release.json"
            replacement.write_text(json.dumps(release, indent=2) + "\n")
            os.replace(replacement, lock)


def check_installed(directory, expected):
    receipt = json.loads((directory / "selection.json").read_text())
    if any(receipt.get(key) != value for key, value in expected.items()):
        raise ValueError("selection directory belongs to a different installation: " + str(directory))
    for name, item in receipt["files"].items():
        target = directory / safe_path(name)
        if not manifest_file(target, item["bytes"], item["sha256"]) or target.stat().st_mode & 0o777 != item["mode"]:
            raise ValueError("installed file has changed: " + str(target))
    return receipt


def install_official_node(stage, cache, host):
    import runpy
    fetch = runpy.run_path(str(stage / "src/compilers/official_dist.py"))["fetch_archive"]
    origin = json.loads((stage / "src/compilers/node/UPSTREAM.json").read_bytes())
    package = fetch(origin["distribution"] + origin["host_archive"], origin["host_archive_sha256"], cache)
    member_name = origin["host_archive"].removesuffix(".tar.xz") + "/bin/node"
    program = stage / "share/toolchains/node/bin/node"
    program.parent.mkdir(parents=True, exist_ok=True)
    with tarfile.open(package, "r:xz") as archive:
        member = archive.getmember(member_name)
        lock = origin["host_program"]
        if not member.isfile() or member.size != lock["bytes"]:
            raise ValueError("invalid Node executable in the upstream distribution")
        with archive.extractfile(member) as source, program.open("xb") as output:
            shutil.copyfileobj(source, output)
    if digest(program) != lock["sha256"]:
        raise ValueError("Node executable failed upstream digest verification")
    require_host(program, host)
    program.chmod(0o755)


def install(tree, args):
    language, mode = selection(args, tree)
    selected, packages, mappings, source_roots = package_plan(tree, args.platform, language, mode,
        tinygo_llvm=args.bootstrap or os.getenv("WROS_LLVM_CONFIG"), rust_bin=args.rust_bin)
    host = current_host()
    identity = dict(schema=1, commit=tree.commit, host=host, platform=args.platform, language=language, mode=mode)
    prefix = args.prefix
    release_root = prefix / tree.commit
    if host and host != "linux-x86_64":
        release_root = release_root / host
    destination = release_root / args.platform / language / mode
    result = dict(**identity, host_cpu=host_info(), directory=str(destination))
    if args.action == "plan":
        executables = {n: p[1] for n, p in packages.items()}
        if language in SCRIPT_COMMANDS:
            script = PY_ENTRY if language == "py" else SCRIPT_ENTRY
            executables[script] = [mappings[script]]
        dependencies = {}
        if host in HOSTS:
            for name in ("xmake", "uwvm2-ros"):
                origin = tree.json(f"src/host-tools/{name}/UPSTREAM.json")
                dependencies[name] = {"repository": origin["repository"], "commit": origin["commit"],
                                      "installed_as": "bin/" + name}
        return dict(**result, files=sorted(selected), executables=executables, official_host_tools=dependencies)
    if destination.exists():
        receipt = check_installed(destination, identity)
        if "python_shared" in receipt:
            result["python_shared"] = receipt["python_shared"]
        return result
    scratch = prefix / ".work"
    cache = prefix / ".cache/sha256"
    scratch.mkdir(parents=True, exist_ok=True)
    cache.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="install-", dir=scratch) as temporary:
        work = Path(temporary)
        stage = work / "sdk"
        stage.mkdir()
        targets = {}
        mapping_roots = sorted(mappings, key=len, reverse=True)
        for name in selected:
            mapped = name
            for origin in mapping_roots:
                if name == origin or name.startswith(origin + "/"):
                    mapped = mappings[origin] + name[len(origin):]
                    break
            targets[name] = (work / "archives" / name) if name in packages else stage / mapped
        if len(set(targets.values())) != len(targets) or stage / "selection.json" in targets.values():
            raise ValueError("duplicate installed path in selection")
        tree.materialize(selected, targets, cache)
        # Keep editable sources at their canonical paths when a private runtime copy is also needed.
        for name, installed in targets.items():
            if installed != stage / name and any(name == root or name.startswith(root + "/") for root in source_roots):
                canonical = stage / name
                canonical.parent.mkdir(parents=True, exist_ok=True)
                os.link(installed, canonical)
        for name, (metadata, outputs) in packages.items():
            first = stage / outputs[0]
            unpack_executable(targets[name], metadata, first, host=host)
            for alias in outputs[1:]:
                target = stage / alias
                target.parent.mkdir(parents=True, exist_ok=True)
                os.link(first, target)
        if mode != "bindings" and language in ("as", "typescript"):
            install_official_node(stage, cache, host)
        if mode == "source" and language in COMMANDS and language != "java":
            source_build(stage, work, language, args)
        if mode == "binary" and language in GO_COMMANDS:
            subprocess.run(go_install_command(stage, work, language, mode, args), check=True, stdout=sys.stderr,
                           env=dict(os.environ, TMPDIR=str(work), WROS_DIST_CACHE=str(cache)))
        if language in ("js", "typescript", "py", "java"):
            backend = stage / {"py": PY_BACKEND, "java": JAVA_BACKEND}.get(language, C_BACKEND)
            backend_abi = backend / ABI_INSTALLED
            backend_abi.parent.mkdir(parents=True, exist_ok=True)
            os.link(stage / ABI_INSTALLED, backend_abi)
            subprocess.run([sys.executable, "-I", "-B", backend / "install/portable_cc.py",
                            "--language", "c", "--sdk", backend, "--target", "wasm32-wasip1"],
                           check=True, stdout=sys.stderr)
        if language == "java":
            subprocess.run([sys.executable, "-I", "-B", stage / "src/compilers/jvm/prepare.py",
                            "--sdk", stage, "--work", work, "--download-cache", cache,
                            "--mode", mode, "--platform", args.platform, "--host", host],
                           env=dict(os.environ, TMPDIR=str(work)), check=True, stdout=sys.stderr)
        if language == "py" and mode == "source":
            subprocess.run([sys.executable, "-I", "-B", stage / "src/runtimes/cpython/build_runtime.py",
                            "--sdk", stage, "--work", work, "--from-source", "--jobs", str(args.jobs or 2)],
                           env=dict(os.environ, TMPDIR=str(work)), check=True, stdout=sys.stderr)
        if language in ("c", "cpp", "objc", "objcpp"):
            # Fully validate and expand the guest sysroot before publishing a read-only installation.
            subprocess.run([sys.executable, "-I", "-B", stage / "install/portable_cc.py",
                            "--language", "c" if language == "c" else "cpp", "--sdk", stage], check=True, stdout=sys.stderr)
        if host in HOSTS:
            subprocess.run([sys.executable, "-I", "-B", stage / "src/host-tools/install_official.py",
                            "--host", host, "--cache", cache.parent, "--work", work, "--jobs", str(args.jobs or 2)],
                           check=True, stdout=sys.stderr)
        inventory = {}
        hashes = {}
        for item in sorted(stage.rglob("*")):
            if item.is_symlink():
                raise ValueError("unexpected symlink in selection: " + str(item.relative_to(stage)))
            if item.is_file():
                info = item.stat()
                inode = (info.st_dev, info.st_ino)
                if inode not in hashes:
                    hashes[inode] = digest(item)
                inventory[item.relative_to(stage).as_posix()] = dict(bytes=info.st_size, mode=info.st_mode & 0o777,
                                                                    sha256=hashes[inode])
        receipt = dict(**identity, host_cpu=host_info(), files=inventory)
        if language == "py":
            shared = stage / "shared/wasm32-wasip1/core3.0-eh-mte"
            report = subprocess.check_output([sys.executable, "-I", "-B", stage / "src/runtimes/cpython/build_runtime.py",
                                              "--sdk", stage, "--check-shared", shared])
            result["python_shared"] = receipt["python_shared"] = json.loads(report)
        (stage / "selection.json").write_text(json.dumps(receipt, indent=2) + "\n")
        destination.parent.mkdir(parents=True, exist_ok=True)
        try:
            stage.rename(destination)
        except OSError:
            if not destination.is_dir():
                raise
            installed = check_installed(destination, identity)
            if "python_shared" in installed:
                result["python_shared"] = installed["python_shared"]
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("repository", type=Path)
    parser.add_argument("commit")
    parser.add_argument("prefix", type=Path)
    parser.add_argument("action", choices=("list", "plan", "install"))
    parser.add_argument("--language")
    parser.add_argument("--platform", required=True)
    parser.add_argument("--mode", choices=("binary", "source", "bindings"))
    parser.add_argument("--no-mte", action="store_true")
    parser.add_argument("--bootstrap", type=Path)
    parser.add_argument("--rust-bin", type=Path)
    parser.add_argument("--jobs", type=int, metavar="N", help="parallel jobs for building native host tools (including the VM) and language components")
    args = parser.parse_args()
    if args.jobs is not None and args.jobs < 1:
        parser.error("--jobs must be positive")
    if args.jobs is not None and args.action == "list":
        parser.error("--jobs applies to install and plan")
    if not re.fullmatch(r"[0-9a-f]{40}", args.commit):
        parser.error("expected an immutable Git commit")
    if args.action == "list":
        result = dict(commit=args.commit, platforms=PLATFORMS, native=COMMANDS, go_platforms=GO_PLATFORMS,
                      experimental={"rust_bindings": "upstream wasm32-unknown-unknown compatibility mode, requires --no-mte",
                                    "as": "wras, pinned Node host, scalar or bounded-driver wasm32",
                                    "js": "wrjs, embedded QuickJS, wasm32",
                                    "typescript": "wrts, pinned Node host and embedded QuickJS, wasm32"})
        result["python"] = {"id": "py", "aliases": ["python"], "command": "wrpy.py",
                            "platforms": PY_PLATFORMS, "modes": ["binary", "source"],
                            "target": "wasm32-wasip1/core3.0-eh-mte"}
        result["rust_modes"] = ["bindings"]
        tree = GitTree(args.repository, args.commit)
        host = current_host()
        result.update(host=host, host_cpu=host_info(), host_selections=[])
        if host and tree.contains(f"bin/packages/{host}/manifest.json"):
            catalog = host_manifest(tree)
            extra = extra_selection_paths(tree, catalog, {"objc", "objcpp", "java"})
            result["host_selections"] = sorted(catalog["selections"].keys() | extra.keys())
            if "java" in result["host_selections"]:
                result["java"] = {"command": "wrjava", "platforms": JAVA_PLATFORMS, "modes": ["binary", "source"],
                                  "target": "wasm32-wasip1/core3.0-eh-mte"}
            result["go_modes"] = {lang: ["source"] + (["binary"] if go_release(tree, lang, catalog["selections"][lang]) else [])
                                  for lang in GO_COMMANDS if lang in catalog["selections"]}
            if "rust" in catalog["selections"]:
                result["rust_modes"].append("source")
                if catalog["selections"]["rust"]["artifacts"]:
                    result["rust_modes"].append("binary")
    else:
        result = install(GitTree(args.repository, args.commit), args)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    try:
        main()
    except (OSError, ValueError, KeyError, TypeError, lzma.LZMAError, tarfile.TarError, subprocess.CalledProcessError) as error:
        sys.exit(f"Installation failed: {error}")
