"""Generate this revision's selective installation manifests and platform declarations."""
import hashlib
import json
from pathlib import Path
import re
import runpy
import textwrap


ROOT = Path(__file__).resolve().parents[1]
HOOK = ROOT / "install/revision.py"
hook = runpy.run_path(str(HOOK))
DEVELOPMENT = hook["DEVELOPMENT"]
PROJECT_LANGUAGES = hook["PROJECT_LANGUAGES"]
COMPILER_COMMANDS = hook["COMPILER_COMMANDS"]


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
    package("migration/tf2-buffer", ["tools/migration/tf2_buffer_port.py",
                                     "tools/migration/tf2_single_executor_mutex.hpp",
                                     "document/en/tf2-buffer-port.md", "document/zh/tf2-buffer-port.md"])
    package("migration/resources", [
        "tools/migration/package_manifest.py", "tools/migration/package_resources.py",
        "include/wros/package_resources.h", "document/en/migration.md", "document/zh/migration.md",
    ])
    package("migration/policy", ["tools/migration/legacy_permissions.py", "document/en/legacy-permissions.md",
                                 "document/zh/legacy-permissions.md"])
    migration_guides = ["document/en/platform-migration-examples.md", "document/zh/platform-migration-examples.md"]
    fixture = "third-parties/migration-examples/sensor_msgs/"
    package("migration/examples/c/common", [*migration_guides, "examples/shared/migration/c/prepare.py",
            "examples/shared/migration/c/resource.c", "examples/shared/migration/c/imu.lock",
            *(fixture + name for name in ("LICENSE", "README.md", "package.xml", "msg/Imu.msg"))])
    package("migration/examples/fsharp/common", [*migration_guides, "examples/shared/migration/fsharp/GoalStatus.fs"])
    for platform in registry["platforms"]:
        for language in ("c", "fsharp"):
            directory = f"examples/platform/{platform}/migration/{language}/"
            names = ["README.md", "README.zh.md", "xmake.lua"]
            if language == "c":
                names.extend(("upstream.lock", "resource.c"))
            else:
                names.append("GoalStatus.fs")
            inputs = [directory + name for name in names]
            if language == "c" and (ROOT / directory / "vendor-package.xml").is_file():
                inputs.extend([directory + "vendor-package.xml", "examples/shared/migration/c/stage_vendor.py"])
            package(f"migration/examples/{language}/{platform}", inputs)
    for platform in registry["platforms"]:
        for language in ("csharp", "vbnet", "fsharp"):
            managed_examples = ["document/en/managed-platform-examples.md", "document/zh/managed-platform-examples.md"]
            areas = ("extension",) if language == "fsharp" else ("extension", "migration")
            for area in areas:
                folder = ROOT / "examples/platform" / platform / area / language
                managed_examples.extend(p.relative_to(ROOT).as_posix() for p in folder.iterdir() if p.is_file())
            package("examples/managed/" + platform + "/" + language, managed_examples)
    for key, source in {"c": "include/wros/scene.h", "rs": "language/rust/scene.rs",
                        "as": "language/assemblyscript/scene.ts"}.items():
        package("bindings/" + key, [source])
    package("bindings/d", ["language/d/wros_scene.d", "language/d/imports.c", "include/wros/scene.h"])
    package("bindings/nim", ["language/nim/wros_scene.nim", "include/wros/scene.h"])
    package("nim-producer-source", ["third-parties/nim/nim-2.2.4.tar.xz"])
    package("protocol", ["share/abi/ros.json", "LICENSE"])
    for name, languages in registry["platforms"].items():
        platform_adapter(name, languages)
    for name in registry["platforms"]:
        platform_examples = ROOT / "examples/platform" / name
        for language in PROJECT_LANGUAGES:
            inputs = [p.relative_to(ROOT).as_posix()
                      for case in ("common", "extension", "migration")
                      for p in sorted((platform_examples / case / language).glob("*")) if p.is_file()]
            if not inputs:
                raise ValueError(f"missing examples for {name}/{language}")
            package(f"examples/{name}/{language}", [*inputs, "document/en/platform-examples.md",
                    "document/zh/platform-examples.md", "document/source/ros-abi.dox", "document/source/Doxyfile"])
    for language in registry["languages"]:
        path = "share/language/" + language + ".json"
        metadata = {"id": language, "development_package": language in DEVELOPMENT}
        if language in COMPILER_COMMANDS:
            metadata["command_name"] = COMPILER_COMMANDS[language]
        if language in ("c", "cpp"):
            metadata["optional_components"] = ["migration"]
        if language == "go":
            metadata.update(development_scope="register-only-wasm32", optional_components=["compiler-source"])
        if language in ("java","kotlin"):
            metadata.update(development_package=True, development_scope="synchronous-wasm32-aot",
                            optional_components=["synchronous-aot"])
        if language in ("csharp", "vbnet", "fsharp"):
            metadata.update(development_package=True, development_scope="freestanding-i32-method",
                            optional_components=["numeric-aot", "migration"])
        write_json(path, metadata)
        package("metadata/" + language, [path])

    mono_aot = ["language/csharp/prepare_host.py", "language/csharp/packages.json", "install/private_exports.py", "language/csharp/numeric.py", "language/csharp/host.py",
                "language/csharp/Scene.cs", "language/csharp/driver_binding.py", "language/csharp/SceneEntry.cs", "language/csharp/scalar.py",
                "language/csharp/Admit.cs", "language/csharp/leaf.cpp", "language/csharp/inputs.sha256"]
    for language, example in (("csharp", "Robot.cs"), ("vbnet", "Robot.vb"), ("fsharp", "Robot.fs")):
        paths = [*mono_aot, "bin/" + COMPILER_COMMANDS[language], f"language/{language}/xmake/adapter.lua",
                 f"examples/{language}/scene-abi/{example}", f"examples/{language}/scene-abi/xmake.lua",
                 f"document/en/{language}.md", f"document/zh/{language}.md"]
        if language == "fsharp":
            paths.append("language/fsharp/inputs.sha256")
        if language == "csharp":
            paths.extend(["examples/csharp/numeric-aot/Filter.cs", "examples/csharp/numeric-aot/xmake.lua",
                          "tests/csharp/README.md"])
        package(language + "/numeric", paths)
    shared_jvm = [p.relative_to(ROOT).as_posix() for name in ("language/jvm", "third-parties/jvm")
                  for p in (ROOT / name).rglob("*") if p.is_file() and "__pycache__" not in p.parts]
    package("jvm/synchronous", [*shared_jvm, "install/private_exports.py", "include/wros/scene.h", "document/en/jvm.md", "document/zh/jvm.md"])
    for language in ("java", "kotlin"):
        examples = sorted((ROOT / "examples" / language / "synchronous-aot").iterdir())
        package("jvm/" + language, ["bin/" + COMPILER_COMMANDS[language], f"language/{language}/xmake/adapter.lua",
                                   f"language/{language}/host-inputs.json", *(p.relative_to(ROOT).as_posix() for p in examples)])
    policy = ["install/" + name for name in ("frontend.py", "imports.py", "guest_profile.py", "compiler.py", "artifacts.py", "qualification.py", "local_release.py")]
    package("frontend", [*policy, "share/qualification/memory-neighbors.json", "bin/wrar", "install/archiver.py", "document/en/memtag.md", "document/zh/memtag.md",
                         "document/en/memory-qualification.md", "document/zh/memory-qualification.md"])
    package("xmake/common", ["tools/xmake/site_archive.py", "tools/xmake/platform_driver_test.py", "tools/xmake/ros.lua", "tools/xmake/dispatch.lua", "tools/xmake/run_guest.py",
                             "document/en/xmake.md", "document/zh/xmake.md",
                             "document/en/xmake-api-index.md", "document/zh/xmake-api-index.md"])
    language_files = {
        "c": ["bin/wrc", "include/wros/scene.h", "examples/c/body.c", "examples/c/xmake.lua"],
        "cpp": ["bin/wrc", "bin/wrcc", "include/wros/scene.h", "document/en/cpp.md", "document/zh/cpp.md",
                "examples/cpp/herbceptions/channel.cpp", "examples/cpp/herbceptions/xmake.lua"],
        "lua": ["bin/wrlua", "bin/wrcc", "include/wros/scene.h", "language/lua/entry.cpp", "language/lua/scene.hpp",
                "third-parties/lua/lua-5.4.9.tar.gz", "third-parties/lua/LICENSE", "third-parties/lua/README.md",
                "examples/lua/body.lua", "examples/lua/guard.lua", "document/en/lua.md", "document/zh/lua.md"],
    }
    language_files["js"] = [
        "bin/wrjs", "bin/wrc", "include/wros/scene.h", "language/js/entry.c",
        "examples/js/body.js", "examples/js/xmake.lua", "document/en/js.md", "document/zh/js.md",
        *[p.relative_to(ROOT).as_posix() for p in (ROOT / "third-parties/quickjs").iterdir() if p.is_file()],
    ]
    language_files["typescript"] = [
        *[name for name in language_files["js"] if name.startswith(("bin/", "include/", "language/", "third-parties/"))],
        "bin/wrts", "language/typescript/compile.cjs", "examples/typescript/main.ts", "examples/typescript/filter.ts",
        "examples/typescript/xmake.lua", "document/en/typescript.md", "document/zh/typescript.md",
        *[p.relative_to(ROOT).as_posix() for p in (ROOT / "third-parties/typescript").iterdir() if p.is_file()],
    ]
    language_files["d"] = [
        "bin/wrd", "include/wros/scene.h", "examples/d/body.d", "examples/d/xmake.lua",
        "document/en/d.md", "document/zh/d.md",
        *["language/d/" + name for name in ("driver.py", "release.py", "release-inputs.json", "check_site.py", "frontend.conf",
                                             "entry.c", "imports.c", "wros_scene.d")],
    ]
    language_files["nim"] = [
        "bin/wrnim", "bin/wrc", "include/wros/scene.h", "examples/nim/body.nim", "examples/nim/xmake.lua",
        "document/en/nim.md", "document/zh/nim.md", "third-parties/nim/LICENSE", "third-parties/nim/README.md",
        "third-parties/nim/nim-2.2.4-lib.tar.xz",
        *["language/nim/" + name for name in ("build_producer.py", "check_site.py", "pack_library.py", "wrnim_lower.nim",
                                              "wros_scene.nim", "panicoverride.nim", "entry.c")],
    ]
    language_files["objectc"] = [
        "bin/wrobjc", "include/wros/scene.h", "document/en/objectc.md", "document/zh/objectc.md",
        "examples/objectc/body.m", "examples/objectc/xmake.lua",
        *["language/objectc/" + name for name in ("base_object.m", "build_frontend.py", "build_runtime.py",
                                                 "check_site.py", "frontend_objectc.py", "runtime.py")],
        *[p.relative_to(ROOT).as_posix() for p in (ROOT / "third-parties/objectc").iterdir() if p.is_file()],
    ]
    language_files["py"] = [
        "bin/wrpy", "bin/wrc", "include/wros/scene.h", "document/en/python.md", "document/zh/python.md",
        "examples/py/body.py", "examples/py/xmake.lua",
        *["language/py/" + name for name in ("entry.c", "scene.h", "isolate.py", "build_interpreter.py",
                                             "freeze_encodings.py", "runtime_paths.mk", "runtime_pack.py", "check_site.py")],
        *[p.relative_to(ROOT).as_posix() for p in (ROOT / "third-parties/cpython").iterdir() if p.is_file()],
    ]
    for width in ("wasm32", "wasm64"):
        stem = f"third-parties/cpython-runtime/{width}-wasip1-core3.0-eh-mte"
        package("python-runtime/" + width, [stem + ".json", stem + ".tar.xz"])
    language_files["fortran"] = [
        "examples/fortran/body.f90", "examples/fortran/xmake.lua",
        "examples/fortran/static/body.f90", "examples/fortran/static/kernel.f90", "examples/fortran/static/xmake.lua",
        "bin/wrf", "bin/wrc", "bin/wrcc", "include/wros/scene.h",
        "document/en/fortran.md", "document/zh/fortran.md",
        *["language/fortran/" + name for name in ("build_flang.py", "clock.c", "compute_platform.cpp", "entry.c", "flang_identity.py",
                                                   "frontend_fortran.py", "mark_mte.cpp", "prepare.py")],
        *[p.relative_to(ROOT).as_posix() for p in (ROOT / "third-parties/fortran").rglob("*") if p.is_file()],
    ]
    language_files["go"] = [
        "bin/wrgo", "language/go/check_site.py", "language/go/driver.py", "language/go/registers.py", "language/go/release.json",
        "language/go/linux-amd64/producer.xz", "language/go/LICENSE", "examples/go/controller.go", "examples/go/xmake.lua",
        "document/en/go.md", "document/zh/go.md",
        *[f"examples/shared/{kind}/go/{name}" for kind in ("common", "extension", "migration")
          for name in ("controller.go", "xmake.lua")],
    ]
    package("go-producer-source", ["third-parties/go/go1.24.2.src.tar.gz", "language/go/LICENSE",
            *["language/go/producer/" + path for path in ("build.py", "main.go", "proof.go")]])
    language_files["tinygo"] = [
        "bin/wrtg", "tools/wasm/tag_ir.cpp", "include/wros/scene.h", "document/en/tinygo.md", "document/zh/tinygo.md",
        *["language/tinygo/" + name for name in ("LICENSE-TinyGo", "toolchain-inputs.json", "check_site.py",
            "scene/go.mod", "scene/scene_wros.go", "runtime/arch_tinygowasm.go", "runtime/gc_blocks.go",
            "runtime/runtime_tinygowasm.go", "runtime/runtime_wasip1.go", "runtime/wros_gc.go", "runtime/wros_gc.c")],
    ]
    language_files["rs"] = [
        "bin/wrrs", "tools/wasm/tag_ir.cpp", "language/rust/scene.rs", "language/rust/toolchain-inputs.json", "language/rust/check_site.py",
        "document/en/rust.md", "document/zh/rust.md", "examples/rs/body.rs", "examples/rs/xmake.lua",
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
