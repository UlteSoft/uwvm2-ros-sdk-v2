"""Build the static target error domains and bind a sysroot to the reviewed producer."""
import hashlib
import json
from pathlib import Path
import re
import shutil
import shlex
import subprocess

from compiler import digest

TOOLS = ("clang", "clang++", "llvm-ar", "llvm-ranlib", "llvm-nm", "llvm-config", "wasm-ld")
DOMAINS = ("cmath", "http", "parse", "posix", "tls")


def verify_exception_bridge(prefix, triple, toolchain, expected):
    """Require one implementation of each legacy exception entry point in an EH profile."""
    archive = prefix / "lib" / triple / "libc++abi.a"
    nm = toolchain / "bin/llvm-nm"
    symbols = subprocess.check_output([nm, "--extern-only", "--defined-only", archive], text=True)
    counts = {name:len(re.findall(r"(?m)^\s*(?:[0-9A-Fa-f]+\s+)?[TW]\s+" + name + "$", symbols))
              for name in ("__cxa_error_domain_itanium_exception_ptr", "__cxa_error_code_itanium_exception_ptr_cast")}
    if any(count != int(expected) for count in counts.values()):
        raise ValueError("Itanium exception bridge definitions differ from the selected EH profile: " + str(counts))
    return {"enabled":expected, "archive":str(archive.relative_to(prefix)), "sha256":digest(archive),
            "definitions":counts}


def definitions(prefix, flags, common_target):
    """Compile domain data in freestanding target mode against this exact libc++."""
    return {**common_target, "CMAKE_SYSROOT":str(prefix),
            "CMAKE_CXX_FLAGS":flags + " -nostdinc++ -isystem" + shlex.quote(str(prefix / "include/c++/v1")),
            "LIBHERBCEPTIONS_BUILD_SHARED":"OFF", "LIBHERBCEPTIONS_BUILD_STATIC":"ON",
            "LIBHERBCEPTIONS_FREESTANDING":"ON", "LIBHERBCEPTIONS_ENABLE_RTTI":"OFF",
            "LIBHERBCEPTIONS_ENABLE_EXCEPTIONS":"OFF", "LIBHERBCEPTIONS_ENABLE_ITANIUM_EXCEPTION_PTR_DOMAIN":"OFF",
            "LIBHERBCEPTIONS_BUILD_TESTS":"OFF", "LIBHERBCEPTIONS_BUILD_FUZZERS":"OFF"}


def install_domains(stage, prefix, triple, toolchain):
    """Only publish the upstream headers and target archive after checking their contents."""
    from artifacts import sections
    archive = stage / "lib/libherbceptions.a"
    headers = stage / "include/herbceptions"
    if not (headers / "error").is_file():
        raise ValueError("the Herbceptions target header is missing")
    ar = str(toolchain / "bin/llvm-ar")
    members = subprocess.check_output([ar, "t", archive], text=True).splitlines()
    if not members or len(members) != len(set(members)) or not all(re.fullmatch(r"[A-Za-z_0-9.]+\.(?:o|obj)", n) for n in members):
        raise ValueError("unexpected Herbceptions archive member list")
    for member in members:
        data = subprocess.check_output([ar, "p", archive, member])
        if sum(name == "linking" for _, _, name, _ in sections(data)) != 1:
            raise ValueError("Herbceptions archive member is not a relocatable core Wasm object: " + member)
    symbols = subprocess.check_output([str(toolchain / "bin/llvm-nm"), "--defined-only", archive], text=True)
    defined = {line.split()[-1] for line in symbols.splitlines() if line.split()}
    if any("__cxa_error_domain_" + domain not in defined for domain in DOMAINS):
        raise ValueError("missing a portable error-domain runtime entry")
    archive_name = "lib/" + triple + "/libherbceptions.a"
    (prefix / archive_name).parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(archive, prefix / archive_name)
    destination = prefix / "include/herbceptions"
    shutil.copytree(headers, destination, dirs_exist_ok=True)
    inputs = {}
    for path in sorted(destination.rglob("*")):
        if path.is_symlink():
            raise ValueError("unexpected symlink in Herbceptions target headers")
        if path.is_file():
            inputs[str(path.relative_to(destination))] = digest(path)
    return {"archive":archive_name, "archive_sha256":digest(archive), "members":members,
            "headers_sha256":hashlib.sha256(json.dumps(inputs,sort_keys=True,separators=(",",":")).encode()).hexdigest(),
            "domains":list(DOMAINS)}
