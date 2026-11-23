"""Fetch immutable upstream distribution inputs into a content-addressed cache."""
import hashlib
import os
from pathlib import Path
import re
import tempfile
import urllib.request


def fetch_archive(url, sha256, cache, *, size=None):
    """Return the verified archive, reusing an earlier download with the same digest."""
    origins = ("https://static.rust-lang.org/dist/", "https://github.com/xmake-io/xmake/releases/download/",
               "https://go.dev/dl/", "https://github.com/tinygo-org/tinygo/releases/download/",
               "https://ziglang.org/download/", "https://nodejs.org/dist/", "https://repo.maven.apache.org/maven2/",
               "https://github.com/adoptium/temurin21-binaries/releases/download/", "https://snapshot.debian.org/archive/")
    if not url.startswith(origins):
        raise ValueError("unexpected distribution URL: " + url)
    if not re.fullmatch("[0-9a-f]{64}", sha256):
        raise ValueError("invalid upstream digest")
    cache = Path(cache)
    cache.mkdir(parents=True, exist_ok=True)
    dest = cache / sha256
    if dest.is_file() and not dest.is_symlink() and (size is None or dest.stat().st_size == size):
        with dest.open("rb") as stream:
            if hashlib.file_digest(stream, "sha256").hexdigest() == sha256:
                return dest
    limit = size if size is not None else 512 << 20
    with tempfile.NamedTemporaryFile(dir=cache, delete=False) as out:
        partial = Path(out.name)
    try:
        check = hashlib.sha256()
        with urllib.request.urlopen(url, timeout=120) as response, partial.open("wb") as out:
            while block := response.read(1 << 20):
                out.write(block)
                check.update(block)
                if out.tell() > limit:
                    raise ValueError("oversized upstream download: " + url)
            if check.hexdigest() != sha256 or (size is not None and out.tell() != size):
                raise ValueError("upstream download failed verification: " + url)
        os.replace(partial, dest)
    finally:
        partial.unlink(missing_ok=True)
    return dest
