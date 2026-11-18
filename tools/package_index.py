"""Generate this revision's selective installation manifests and platform declarations."""
import hashlib
import json
from pathlib import Path
import re
import runpy
import textwrap


ROOT = Path(__file__).resolve().parents[1]
HOOK = ROOT / "install/revision.py"
DEVELOPMENT = runpy.run_path(str(HOOK))["DEVELOPMENT"]


def write(path, text):
    file = ROOT / path
    file.parent.mkdir(parents=True, exist_ok=True)
    file.write_text(text, encoding="utf-8")


def write_json(path, value):
    write(path, json.dumps(value, indent=2) + "\n")


def package(name, paths):
    entries = []
    for path in sorted(set(paths)):
        file = ROOT / path
        if not file.is_file() or file.is_symlink():
            raise ValueError("missing package input: " + path)
        with file.open("rb") as stream:
            digest = hashlib.file_digest(stream, "sha256").hexdigest()
        entries.append(dict(path=path, bytes=file.stat().st_size,
                            mode=0o755 if path.startswith("bin/") else 0o644, sha256=digest))
    write_json("install/packages/" + name + ".json", {"files": entries})


def render_inventory(registry):
    """The bootstrap runs revision.py alone. Embed only IDs in that small file."""
    languages = registry["languages"]
    for platform, declared in registry["platforms"].items():
        if not set(declared) <= set(languages):
            raise ValueError("unknown language in platform " + platform)
    def words(values):
        if any(not re.fullmatch(r"[a-z0-9][a-z0-9_-]*", entry) for entry in values):
            raise ValueError("invalid target identifier")
        return json.dumps(" ".join(values))
    header = "# BEGIN generated target inventory (tools/package_index.py)\n"
    footer = "# END generated target inventory"
    block = [f"LANGUAGES = {words(languages)}.split()",
             f"PLATFORMS = {words(registry['platforms'])}.split()"]
    before, section = HOOK.read_text().split(header)
    _, after = section.split(footer)
    write(HOOK, before + header + "\n".join(block) + "\n" + footer + after)


def platform_adapter(platform, languages):
    source = f"platform/{platform}/sources.json"
    data = json.loads((ROOT / source).read_text())
    if data["platform"] != platform or not re.fullmatch(r"[a-z][a-z0-9_-]*", data["admission"]):
        raise ValueError("unexpected platform admission for " + platform)
    path = f"platform/{platform}/xmake/platform.lua"
    ids = ", ".join(json.dumps(language) for language in languages)
    rows = textwrap.wrap(ids, width=89, break_long_words=False, break_on_hyphens=False)
    code = ["-- Generated from this platform's inventory by tools/package_index.py.",
            "function describe()", "    return {", "        id = " + json.dumps(platform) + ",",
            "        admission = " + json.dumps(data["admission"]) + ",", "        languages = {"]
    code.extend("            " + row for row in rows)
    code.extend(("        }", "    }", "end", ""))
    write(path, "\n".join(code))
    package("platforms/" + platform, [source])
    package("xmake/platforms/" + platform, [path])


def main():
    registry = json.loads((ROOT / "share/targets.json").read_text())
    render_inventory(registry)
    package("license", ["LICENSE"])
    for key, source in {"c": "include/wros/scene.h", "rs": "language/rust/scene.rs",
                        "as": "language/assemblyscript/scene.ts"}.items():
        package("bindings/" + key, [source])
    package("bindings/nim", ["language/nim/wros_scene.nim", "include/wros/scene.h"])
    package("nim-producer-source", ["third-parties/nim/nim-2.2.4.tar.xz"])
    package("protocol", ["share/abi/ros.json", "LICENSE"])
    for name, languages in registry["platforms"].items():
        platform_adapter(name, languages)
    for language in registry["languages"]:
        path = "share/language/" + language + ".json"
        write_json(path, {"id": language, "development_package": language in DEVELOPMENT})
        package("metadata/" + language, [path])

    policy = ["install/" + name for name in ("frontend.py", "imports.py", "guest_profile.py", "compiler.py", "artifacts.py", "qualification.py", "local_release.py")]
    package("frontend", [*policy, "share/qualification/memory-neighbors.json", "bin/wrar", "install/archiver.py", "document/en/memtag.md", "document/zh/memtag.md",
                         "document/en/memory-qualification.md", "document/zh/memory-qualification.md"])
    package("xmake/common", ["tools/xmake/ros.lua", "tools/xmake/dispatch.lua", "tools/xmake/run_guest.py",
                             "document/en/xmake.md", "document/zh/xmake.md",
                             "document/en/xmake-api-index.md", "document/zh/xmake-api-index.md"])
    language_files = {
        "c": ["bin/wrc", "include/wros/scene.h", "examples/c/body.c", "examples/c/xmake.lua"],
        "cpp": ["bin/wrc", "bin/wrcc", "include/wros/scene.h"],
        "lua": ["bin/wrlua", "bin/wrcc", "include/wros/scene.h", "language/lua/entry.cpp",
                "third-parties/lua/lua-5.4.9.tar.gz", "third-parties/lua/LICENSE", "third-parties/lua/README.md",
                "examples/lua/body.lua", "document/en/lua.md", "document/zh/lua.md"],
    }
    language_files["nim"] = [
        "bin/wrnim", "bin/wrc", "include/wros/scene.h", "examples/nim/body.nim", "examples/nim/xmake.lua",
        "document/en/nim.md", "document/zh/nim.md", "third-parties/nim/LICENSE", "third-parties/nim/README.md",
        "third-parties/nim/nim-2.2.4-lib.tar.xz",
        *["language/nim/" + name for name in ("build_producer.py", "pack_library.py", "wrnim_lower.nim",
                                              "wros_scene.nim", "panicoverride.nim", "entry.c")],
    ]
    language_files["fortran"] = [
        "bin/wrfortran", "bin/wrc", "bin/wrcc", "include/wros/scene.h",
        "document/en/fortran.md", "document/zh/fortran.md",
        *["language/fortran/" + name for name in ("build_flang.py", "entry.c", "flang_identity.py",
                                                   "frontend_fortran.py", "mark_mte.cpp", "prepare.py")],
        *[p.relative_to(ROOT).as_posix() for p in (ROOT / "third-parties/fortran").rglob("*") if p.is_file()],
    ]
    language_files["tinygo"] = [
        "bin/wrtinygo", "tools/wasm/tag_ir.cpp", "include/wros/scene.h", "document/en/tinygo.md", "document/zh/tinygo.md",
        *["language/tinygo/" + name for name in ("LICENSE-TinyGo", "toolchain-inputs.json",
            "scene/go.mod", "scene/scene_wros.go", "runtime/arch_tinygowasm.go", "runtime/gc_blocks.go",
            "runtime/runtime_tinygowasm.go", "runtime/runtime_wasip1.go", "runtime/wros_gc.go", "runtime/wros_gc.c")],
    ]
    language_files["rs"] = [
        "bin/wrrust", "tools/wasm/tag_ir.cpp", "language/rust/scene.rs", "language/rust/toolchain-inputs.json",
        "document/en/rust.md", "document/zh/rust.md",
        *["third-parties/rust/" + name for name in ("rust-src-1.98.0.tar.xz", "COPYRIGHT", "LICENSE-APACHE", "LICENSE-MIT")],
    ]
    if set(language_files) != set(DEVELOPMENT):
        raise ValueError("developer payloads must match the revision hook")
    for language, files in language_files.items():
        package("languages/" + language, [*files, f"language/{language}/xmake/adapter.lua"])
    inputs = (file.relative_to(ROOT).as_posix() for directory in ("tools/wasm/memtag", "third-parties/sources")
              for file in (ROOT / directory).rglob("*") if file.is_file() and "__pycache__" not in file.parts)
    package("compiler-source", inputs)


if __name__ == "__main__":
    main()
