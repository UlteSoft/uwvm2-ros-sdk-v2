"""Bounded, profile-consistent relocatable Wasm objects and static archives.

The build note is a consistency check, not a signature or proof of safe code.
The selected local compiler prefix is trusted. Final imports and runtime
permissions remain independent checks. Native ELF, LLVM bitcode, thin archives
and unmarked objects are refused rather than guessing their guest profile.
"""
import hashlib
import json
import re
import subprocess
from pathlib import Path
from imports import Reader, require_core, inspect

MAGIC = b"\0asm\1\0\0\0"
NOTE = "wros.sdk.object"
MAX_BYTES = 128 * 1024 * 1024
MAX_TOTAL = 256 * 1024 * 1024
MAX_MEMBERS = 1024
MAX_SECTIONS = 4096


def read_bounded(path):
    """Limit bytes actually read, including files growing during the read."""
    with path.open("rb") as stream:
        data = stream.read(MAX_BYTES + 1)
    if len(data) > MAX_BYTES:
        raise ValueError("build artifact exceeds 128 MiB")
    return data


def sections(data):
    """Walk section envelopes without interpreting or executing guest code."""
    if len(data) > MAX_BYTES:
        raise ValueError("build artifact exceeds 128 MiB")
    reader = Reader(data)
    require_core(reader)
    count = 0
    while reader.position < len(data):
        count += 1
        if count > MAX_SECTIONS:
            raise ValueError("too many Wasm sections")
        start = reader.position
        kind = reader.byte()
        if kind > 13:
            raise ValueError("unknown Wasm section")
        body = Reader(reader.take(reader.uint()))
        name = body.name() if kind == 0 else None
        yield start, reader.position, name, body


def uleb(value):
    result = bytearray()
    while value >= 128:
        result.append((value & 127) | 128)
        value >>= 7
    result.append(value)
    return bytes(result)


def strip_notes(data):
    """Remove build-only notes after linking; leave relocations/debug untouched."""
    result = [MAGIC]
    for start, end, name, _ in sections(data):
        if name != NOTE:
            result.append(data[start:end])
    return b"".join(result)


def validate_profile(value):
    from guest_profile import Profile
    if not isinstance(value, dict):
        raise ValueError("invalid object profile")
    profile = Profile(**{key: value[key] for key in Profile.__dataclass_fields__})
    if value != profile.to_dict():
        raise ValueError("inconsistent object profile")
    return value


def seal_object(data, profile, compiler_sha256, closure_sha256):
    """Append one digest-bound note to a compiler-produced relocatable object."""
    validate_profile(profile)
    if not re.fullmatch(r"[0-9a-f]{64}", compiler_sha256):
        raise ValueError("invalid compiler digest")
    if not re.fullmatch(r"[0-9a-f]{64}", closure_sha256):
        raise ValueError("invalid sysroot closure digest")
    inspect(data)
    linking = 0
    for _, _, name, body in sections(data):
        if name == NOTE:
            raise ValueError("object already has a WROS build note")
        if name == "linking":
            linking += 1
            if body.uint() != 2:
                raise ValueError("unsupported Wasm linking metadata")
    if linking != 1:
        raise ValueError("expected one relocatable Wasm linking section")
    note = dict(schema=NOTE, profile=profile, compiler_sha256=compiler_sha256, closure_sha256=closure_sha256,
                object_sha256=hashlib.sha256(data).hexdigest())
    payload = NOTE.encode()
    payload = uleb(len(payload)) + payload + json.dumps(note, sort_keys=True, separators=(",", ":")).encode()
    result = data + b"\0" + uleb(len(payload)) + payload
    if len(result) > MAX_BYTES:
        raise ValueError("object plus build note exceeds size bound")
    return result


def unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("duplicate build note field")
        result[key] = value
    return result


def check_object(data, profile=None, compiler_sha256=None, closure_sha256=None):
    """Check the entire object against its final note and optional expected ABI."""
    inspect(data)
    notes, linking = [], 0
    for start, end, name, body in sections(data):
        if name == "linking":
            linking += 1
            if body.uint() != 2:
                raise ValueError("unsupported Wasm linking metadata")
        if name == NOTE:
            remaining = len(body.data) - body.position
            if remaining > 4096 or end != len(data):
                raise ValueError("build note must be bounded and final")
            try:
                note = json.loads(bytes(body.take(remaining)), object_pairs_hook=unique_object)
            except (UnicodeError, RecursionError, json.JSONDecodeError) as error:
                raise ValueError("invalid object build note") from error
            if not isinstance(note, dict) or set(note) != {"schema", "profile", "compiler_sha256", "closure_sha256", "object_sha256"}:
                raise ValueError("invalid build note fields")
            if note["schema"] != NOTE or note["object_sha256"] != hashlib.sha256(data[:start]).hexdigest():
                raise ValueError("object digest mismatch")
            validate_profile(note["profile"])
            if not isinstance(note["compiler_sha256"], str) or not re.fullmatch(r"[0-9a-f]{64}", note["compiler_sha256"]):
                raise ValueError("invalid compiler digest")
            if not isinstance(note["closure_sha256"], str) or not re.fullmatch(r"[0-9a-f]{64}", note["closure_sha256"]):
                raise ValueError("invalid sysroot closure digest")
            notes.append(note)
    if linking != 1 or len(notes) != 1:
        raise ValueError("expected one relocatable linking section and WROS build note")
    note = notes[0]
    if profile is not None and note["profile"] != profile:
        raise ValueError("object guest profile mismatch")
    if compiler_sha256 is not None and note["compiler_sha256"] != compiler_sha256:
        raise ValueError("object compiler digest mismatch")
    if closure_sha256 is not None and note["closure_sha256"] != closure_sha256:
        raise ValueError("object sysroot closure mismatch")
    return note


def archive_members(data):
    """Read a bounded ordinary GNU archive; no extraction paths or thin links.

    The symbol index is never handed to the linker. After checking every member
    (including unused ones), rebuild it from the copied objects using llvm-ar.
    This prevents attacker-supplied index offsets from bypassing member checks.
    """
    if len(data) > MAX_BYTES or not data.startswith(b"!<arch>\n"):
        raise ValueError("expected a bounded ordinary GNU archive")
    pos, names, members, index_seen = 8, set(), [], False
    while pos < len(data):
        header = data[pos:pos + 60]
        if len(header) != 60 or header[58:] != b"`\n":
            raise ValueError("invalid archive header")
        raw_size = header[48:58].rstrip(b" ")
        if not raw_size or not raw_size.isdigit():
            raise ValueError("invalid archive member size")
        size = int(raw_size)
        pos += 60
        if size > len(data) - pos:
            raise ValueError("truncated archive member")
        payload = data[pos:pos + size]
        pos += size
        if size & 1:
            if data[pos:pos + 1] != b"\n":
                raise ValueError("invalid archive padding")
            pos += 1
        name = header[:16].rstrip(b" ")
        if name in (b"/", b"/SYM64/"):
            if index_seen or members:
                raise ValueError("duplicate or misplaced archive symbol table")
            index_seen = True
            continue
        if not re.fullmatch(rb"[A-Za-z0-9_][A-Za-z0-9_.-]{0,11}\.o/", name) or name in names:
            raise ValueError("unsupported or duplicate archive member name")
        names.add(name)
        members.append(payload)
        if len(members) > MAX_MEMBERS:
            raise ValueError("too many archive members")
    if not members:
        raise ValueError("empty object archive")
    return members


def archive(toolchain, output, members, work):
    """Build a deterministic indexed GNU archive from already checked bytes."""
    archiver = toolchain.resolve() / "bin/llvm-ar"
    if not archiver.is_file():
        raise ValueError("explicit compiler prefix lacks llvm-ar")
    work.mkdir()
    paths = []
    for index, data in enumerate(members):
        path = work / f"u{index:06d}.o"
        path.write_bytes(data)
        paths.append(path)
    subprocess.run([str(archiver), "--format=gnu", "rcsD", str(output), *map(str, paths)], check=True)


def stage_inputs(sources, work, profile, compiler_sha256, closure_sha256, toolchain):
    """Snapshot every object/archive; refuse ABI mixtures before linking."""
    result, total, count = [], 0, 0
    for index, source in enumerate(sources):
        if source.suffix not in (".o", ".a"):
            result.append(source)
            continue
        data = read_bounded(source)
        total += len(data)
        if total > MAX_TOTAL:
            raise ValueError("combined build artifacts exceed 256 MiB")
        members = archive_members(data) if source.suffix == ".a" else [data]
        count += len(members)
        if count > MAX_MEMBERS:
            raise ValueError("too many input object members")
        for member in members:
            check_object(member, profile, compiler_sha256, closure_sha256)
        path = work / (f"input{index}" + source.suffix)
        if source.suffix == ".a":
            archive(toolchain, path, members, work / f"archive{index}")
        else:
            path.write_bytes(data)
        result.append(path)
    return result
