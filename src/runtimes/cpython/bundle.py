"""Describe source modules for compilation by the guest CPython interpreter."""
import json
from pathlib import Path, PurePosixPath

RESERVED = {"__main__", "sys", "builtins", "_uwros_runtime", "_frozen_importlib",
            "_frozen_importlib_external", "uwrosv2", "unitree_api", "unitree_go", "unitree_hg", "unitree_cdr"}


def import_name(relative):
    path = PurePosixPath(relative)
    if path.suffix != ".py" or path.is_absolute() or str(path) != relative or "\\" in relative:
        raise ValueError("expected a project-relative .py filename")
    parts = path.with_suffix("").parts
    package = parts[-1] == "__init__"
    if package:
        parts = parts[:-1]
    if not parts or any(not p.isidentifier() or not p.isascii() for p in parts):
        raise ValueError("expected dotted ASCII Python identifiers in " + relative)
    return ".".join(parts), package


def source_rows(sdk, platform, project, entry, sources):
    rows = {}
    runtime = sdk / "src/runtimes/cpython"
    include = sdk / "include/u2rosv2"
    roots = [(runtime / "upstream/Lib", "/wros/python/Lib"), (include / "universal/py", "/wros/sdk")]
    if platform != "generic":
        roots.append((include / "platform" / platform / "py", "/wros/sdk"))
    for directory, origin in roots:
        if not directory.is_dir():
            raise ValueError("missing Python module directory: " + str(directory))
        for path in sorted(directory.rglob("*.py")):
            relative = path.relative_to(directory).as_posix()
            # Scripts outside importable packages belong to the upstream source snapshot.
            if not all((parent / "__init__.py").is_file() for parent in
                       path.parents if parent != directory and directory in parent.parents):
                continue
            name, package = import_name(relative)
            if name in rows:
                raise ValueError("duplicate installed Python module: " + name)
            rows[name] = (path, f"{origin}/{relative}", package)
    if entry is not None:
        entry = entry.resolve(strict=True)
        seen = set()
        for path in sources:
            path = path.resolve(strict=True)
            relative = path.relative_to(project).as_posix()
            name, package = import_name(relative)
            if path in seen or name.split(".")[0] in RESERVED:
                raise ValueError("reserved or repeated application module: " + relative)
            seen.add(path)
            if path == entry:
                name = "__main__"
            elif name in rows:
                raise ValueError("application shadows an SDK or standard module: " + name)
            rows[name] = (path, "/app/" + relative, package)
        if entry not in seen:
            raise ValueError("declare the Python entry in the source list")
        for name, (_, filename, _) in rows.items():
            if not filename.startswith("/app/"):
                continue
            parent = name.rpartition(".")[0]
            if parent and (parent not in rows or not rows[parent][2]):
                raise ValueError("declare the parent package __init__.py for " + name)
    return rows


def write(sdk, platform, work, project=None, entry=None, sources=()):
    rows = source_rows(sdk, platform, project, entry, sources)
    index = ["static const EmbeddedModule modules[] = {"]
    total = 0
    with (work / "sources.bin").open("wb") as stream:
        for name, (path, filename, package) in sorted(rows.items()):
            with path.open("rb") as input_file:
                data = input_file.read(4 * 1024 * 1024 + 1)
            if len(data) > 4 * 1024 * 1024 or total + len(data) > 32 * 1024 * 1024 or b"\0" in data:
                raise ValueError("Python source exceeds bundle bounds or contains a NUL: " + str(path))
            index.append("    {%s, %s, %d, %d, %d}," %
                         (json.dumps(name), json.dumps(filename), total, len(data), int(package)))
            stream.write(data)
            total += len(data)
    bootstrap = Path(__file__).with_name("bootstrap.py").read_text()
    index += ["};", "static const int embedded_main = %d;" % (entry is not None),
              "static const char bootstrap[] =", *(json.dumps(line) for line in bootstrap.splitlines(True)), ";"]
    (work / "application.inc").write_text("\n".join(index) + "\n")
    (work / "sources.S").write_text(
        '.section .rodata.wros_sources,"",@\n.globl wros_sources\n.hidden wros_sources\n'
        '.type wros_sources,@object\nwros_sources:\n.incbin "sources.bin"\n.size wros_sources, .-wros_sources\n')
