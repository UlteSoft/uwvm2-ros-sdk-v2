"""@file platform_projects.py
@brief Materialize editable language projects for every registered platform.
@details Shared guest sources implement common behavior, source migration or a
real platform permission check. Each generated xmake project fixes its own
platform selection and builds only the sources stored in its directory.
"""
import argparse
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SHARED = ROOT / "examples/shared"
INDEX = ROOT / "examples/platform"
LANGUAGES = set("c cpp csharp d fortran fsharp go java js kotlin lua nim objectc py rs ruby tinygo typescript vbnet".split())
# The .NET and C migration projects use independently maintained, platform-selected ROS fixtures.
SEPARATE = ({("migration", lang) for lang in ("c", "fsharp", "csharp", "vbnet")} |
            {("extension", lang) for lang in ("fsharp", "csharp", "vbnet", "go")})
DRIVER = ("capability.open", "driver.connect", "capability.close")
C_OPTIONS = {"c", "cpp", "objectc", "d", "fortran", "js", "lua", "nim", "py", "ruby", "tinygo", "typescript", "java", "kotlin"}


def strings(names):
    """@brief Render JSON-escaped string arguments accepted by Lua."""
    return ", ".join(json.dumps(n) for n in names)


def target(area, lang, platform, name, source_names, *, sensor=False):
    """@brief Describe one real guest and its per-engine assertions."""
    extended = area == "extension"
    use_abi = (area == "common" and not sensor and lang != "go") or lang in ("csharp", "fsharp", "vbnet")
    operations = DRIVER if extended else ("abi",) if use_abi else ()
    lines = [f'target("{name}")', '    set_kind("binary")', f'    set_language("{lang}")',
             f'    set_ros_platform("{platform}")']
    if lang not in ("csharp", "fsharp", "vbnet"):
        eh = "false" if lang == "rs" else "true"
        lines.append('    set_wros_profile({core = "3.0", eh = ' + eh + ', mte = true})')
    if lang in C_OPTIONS or lang in ("csharp", "fsharp", "vbnet"):
        lines.extend(['    set_optimize("fastest")', '    set_symbols("debug")'])
    if lang in ("java", "kotlin"):
        lines.append('    set_wros_jvm_main("example.Main")')
    if lang in ("csharp", "fsharp", "vbnet"):
        lines.append('    add_wros_exports("Robot.Start")')
    if lang in ("js", "typescript", "java", "kotlin", "csharp", "fsharp", "vbnet", "lua", "py", "ruby") and operations:
        lines.append("    add_wros_operations(" + strings(operations) + ")")
    if lang == "typescript" and len(source_names) > 1:
        lines.append('    set_wros_typescript_entry("main.ts")')
    queries = ["abi"] if use_abi else []
    if lang in ("js", "typescript"):
        queries.append("realtime-clock")
    if lang == "py":
        queries.extend(["realtime-clock", "monotonic-clock", "realtime-resolution", "monotonic-resolution"])
    if queries:
        lines.append("    set_wros_test_queries(" + strings(queries) + ")")
    if extended:
        lines.append('    set_wros_test_policy("platform-driver-denial")')
    if lang == "tinygo":
        source_names = ["go.mod"]
    lines.extend(["    add_files(" + strings(source_names) + ")", '    add_wros_tests("int", "aot")', "target_end()"])
    return lines


def materialize(platform, area, folder):
    """@brief Return all bytes of one independently editable project."""
    lang = folder.name
    files = {p.name: p.read_bytes() for p in sorted(folder.iterdir())
             if p.is_file() and p.name != "xmake.lua" and (lang != "py" or p.suffix == ".py")}
    sensor = [n for n in files if n.startswith("sensor.")]
    body = [n for n in files if n not in sensor]
    if not body:
        raise ValueError("missing guest source: " + str(folder))
    lines = ["-- @file xmake.lua", "-- @brief Build and test this platform's guest modules.",
             f'set_project("{platform}-{area}-{lang}")',
             'includes(path.join(os.getenv("UWVM_ROS_SDK_ROOT"), "tools/xmake/ros.lua"))', "",
             *target(area, lang, platform, area, body)]
    if sensor:
        lines.extend(["", *target(area, lang, platform, "sensor", sensor, sensor=True)])
    return {**files, "xmake.lua": ("\n".join(lines) + "\n").encode()}


def output(path, data, check):
    """@brief Write the project, or fail if the checkout differs from its source."""
    if path.is_file() and path.read_bytes() == data:
        return
    if check:
        raise ValueError("outdated or missing example: " + str(path))
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data)



def navigation(platform, languages, chinese):
    """@brief Link each installed source project and identify gaps in the registry."""
    base = INDEX / platform
    areas = ("common", "extension", "migration")
    if chinese:
        lines = [f"# {platform} 平台示例", "", "[English](README.en.md)", "",
                 "每个项目链接都指向含源码和 xmake.lua 的目录。横线表示该语言尚无此类示例。", "",
                 "安装对应平台和语言后，在项目目录执行 xmake build 生成 Wasm，再执行 xmake test -j1 运行注册的测试。", "",
                 "[安装与测试说明](../../../document/zh/platform-examples.md) · [平台来源和固定版本](../../../platform/" + platform + "/sources.json)", "",
                 "| 语言 | 通用 | 平台权限扩展 | ROS 源码移植 |"]
    else:
        lines = [f"# {platform} platform examples", "", "[中文](README.zh.md)", "",
                 "Each project link opens editable guest sources and an xmake.lua file. A dash marks a category with no example for that language.", "",
                 "Install the platform and language, run xmake build inside the project to emit Wasm, then use xmake test -j1 to execute its registered tests.", "",
                 "[Installation and testing](../../../document/en/platform-examples.md) · [Platform sources and pinned revisions](../../../platform/" + platform + "/sources.json)", "",
                 "| Language | Common | Platform permissions | ROS source migration |"]
    lines.append("| --- | --- | --- | --- |")
    for lang in sorted(languages):
        cells = [f"[{area}/{lang}]({area}/{lang}/)" if (base / area / lang / "xmake.lua").is_file()
                 else "—" for area in areas]
        lines.append("| " + " | ".join([lang, *cells]) + " |")
    return ("\n".join(lines) + "\n").encode()


def main():
    """@brief Generate only categories with authored source for this language."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    registry = json.loads((ROOT / "share/targets.json").read_bytes())
    platforms = registry["platforms"]
    for platform in sorted(platforms):
        for area in ("common", "extension", "migration"):
            for folder in sorted((SHARED / area).iterdir()):
                if not folder.is_dir() or folder.name not in LANGUAGES or (area, folder.name) in SEPARATE:
                    continue
                for name, data in materialize(platform, area, folder).items():
                    output(INDEX / platform / area / folder.name / name, data, args.check)
        for locale in ("en", "zh"):
            output(INDEX / platform / f"README.{locale}.md",
                   navigation(platform, registry["languages"], locale == "zh"), args.check)


if __name__ == "__main__":
    main()
