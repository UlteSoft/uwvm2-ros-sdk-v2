"""Stage exactly the reviewed .NET compiler files for Roslyn and Mono LLVMOnly."""
import hashlib
import os
from pathlib import Path
import shutil

REF_PACK = "10.0.15"
SDK_VERSION = "10.0.404"
LOCK = Path(__file__).with_name("inputs.sha256")


def sha(path):
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def stage(work, dotnet, mono):
    verified = {}
    roots = {"dotnet": dotnet, "compiler": mono}
    for line in LOCK.read_text().splitlines():
        expected, name = line.split("  ", 1)
        relative = Path(name)
        if relative.is_absolute() or ".." in relative.parts or name in verified:
            raise ValueError("unexpected compiler input path: " + name)
        base, *tail = relative.parts
        source = roots[base].joinpath(*tail)
        if sha(source) != expected:
            raise ValueError("managed compiler input differs: " + name)
        destination = work / "inputs" / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        if name == "dotnet/dotnet":
            shutil.copy2(source, destination)
        else:
            destination.symlink_to(source)
        verified[name] = expected
    return verified


def environment(work, tool):
    host = work / "inputs/dotnet"
    mono_runtime = host / "packs/Microsoft.NETCore.App.Runtime.Mono.wasi-wasm" / REF_PACK / "runtimes/wasi-wasm"
    return dict(PATH=str(tool) + ":/usr/bin:/bin", LC_ALL="C", TMPDIR=str(work), HOME=str(work),
                DOTNET_ROOT=str(host), DOTNET_CLI_HOME=str(work), DOTNET_CLI_TELEMETRY_OPTOUT="1",
                DOTNET_MULTILEVEL_LOOKUP="0", DOTNET_SKIP_FIRST_TIME_EXPERIENCE="1",
                COMPlus_EnableDiagnostics="0", DOTNET_SYSTEM_GLOBALIZATION_INVARIANT="1",
                MONO_PATH=os.pathsep.join(str(mono_runtime / x) for x in ("native", "lib/net10.0")))
