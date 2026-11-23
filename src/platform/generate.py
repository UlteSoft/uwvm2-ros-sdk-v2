"""Regenerate the public observation bindings and their installed Xmake projects."""
import json
from pathlib import Path
from bindings import c_example, c_header, rust_example, rust_header
from model import Record
from script_bindings import as_example, as_module, es_example, es_module
from wat import wat_module

ROOT = Path(__file__).resolve().parents[2]
LANGUAGES = {"c": "c", "cpp": "cpp", "rust": "rs", "wat": "wat", "as": "ts", "js": "mjs", "typescript": "ts"}
FORMAT_LABEL = {
    "ros1": ("a compact ROS 1 message body, starting at its first field",
             "从第一个字段开始的 ROS 1 紧凑序列化消息正文"),
    "cdr": ("an encapsulated ROS 2 CDR1 message, with big- or little-endian representation",
            "含封装头的 ROS 2 CDR1 消息，支持大端和小端"),
    "quaternion": ("a 32-byte ROS 1 quaternion or a CDR1-encapsulated ROS 2 quaternion",
                   "32 字节的 ROS 1 四元数或含 CDR1 封装头的 ROS 2 四元数"),
    "packed": ("the field or record described above, in little-endian byte order", "上述字段或记录的小端字节序列"),
    "lcm": ("the big-endian LCM message body, starting at the eight-byte type fingerprint",
            "从 8 字节类型指纹开始的大端 LCM 消息正文"),
}


def write(relative, text):
    path = ROOT / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    if not path.exists() or path.read_text() != text:
        path.write_text(text)


def xmake(platform, language, ext):
    lines = [f'set_project("{platform}-observation")',
             'includes(path.join(os.getenv("UWVM_ROS_SDK_ROOT"), "tools/xmake/ros.lua"))', "",
             f'target("{platform}-observation")', '    set_kind("binary")',
             f'    set_language("{language}")', f'    set_ros_platform("{platform}")']
    if language == "as":
        lines.append("    set_wros_profile({as_driver = true})")
    elif language in ("js", "typescript"):
        lines.append('    set_wros_test_queries("realtime-clock")')
    lines += [f'    add_files("main.{ext}")', '    add_wros_tests("int", "aot")', "target_end()", ""]
    return "\n".join(lines)


def wire_guides(record, zh):
    """Wire modules may ship separate guides alongside the generated observation page."""
    suffix = ".zh.md" if zh else ".md"
    return [module + suffix for module in record.spec.get("wire_modules", [])
            if (ROOT / "platform" / record.platform / (module + suffix)).is_file()]


def manifest(record):
    spec = record.spec
    entries = []
    for r in record.readings:
        entry = {"name": "read_" + r.name, "field": r.field.name, "type": r.field.type, "indexed": r.indexed}
        if r.step != 1:
            entry.update(element_stride=r.step, component=r.base)
        entries.append(entry)
    data = {"id": record.platform, "module": "uwvm_ros_v2", "abi_major": 2, "capabilities": [],
            "observation": {"type": spec["type"], "format": spec["format"], "fields": entries,
                            "sources": spec["sources"]}}
    guides = wire_guides(record, False) + wire_guides(record, True)
    if guides:
        data["guides"] = guides
    return json.dumps(data, ensure_ascii=False, indent=2) + "\n"


def docs(record, zh):
    spec, p = record.spec, record.platform
    en_fmt, zh_fmt = FORMAT_LABEL[spec["format"]]
    names = ("、" if zh else ", ").join("`read_" + r.name + "`" for r in record.readings)
    sources = [f"- [{s['path']}]({s['url']})" for s in spec["sources"]]
    if zh:
        lines = [f"# {p} 只读观测", "", f"`{spec['type']}`。{spec['description_zh']}", "",
                 f"输入为{zh_fmt}。可读取的字段函数为 {names}。", "",
                 f"C 包含 `<uwrosv2/{record.ident}/observation.h>`，函数带 `uwrosv2_{record.ident}_` 前缀。",
                 f"C++98 及后续标准包含 `<uwrosv2/{record.ident}/observation.hpp>`，使用 `uwrosv2::{record.ident}` 命名空间。",
                 "C 函数接受输出指针，C++ 函数接受输出引用。解码成功时才写入输出。Rust 的 `wros_observation` crate 返回 `Option<T>`。",
                 f'JS 和 TypeScript 从 `uwrosv2/platform/{p}/observation` 导入函数，传入 `Uint8Array`。64 位整数返回 `bigint`，无效记录返回 `undefined`。',
                 "AssemblyScript 在有界驱动模式下读取请求暂存区，传入最后一个参数 true 可读取上一次成功回复。读取成功时返回 true，并更新同名字段值。",
                 f"WAT 库 `include/u2rosv2/platform/{p}/wat/observation.wat` 导出线性内存和上述函数。传入输入地址、长度、数组索引（如适用）和输出地址。成功返回 1，并将字段按原宽度以小端序写入。", "",
                 "## 在本地运行", "",
                 f"安装时指定 `--platform {p}` 和语言，将 `examples/{p}/<language>` 复制到用户工程，设置 `UWVM_ROS_SDK_ROOT`、`WROS_VM`。",
                 "执行 `xmake build` 和 `xmake test -j1`。示例使用按原始定义构造的离线样本，校验字段值并拒绝截断数据。", "",
                 "## 上游定义", "", *sources, "",
                 "platform.json 记录各定义文件的 SHA-256 和源码版本。"]
    else:
        lines = [f"# {p} read-only observations", "", f"`{spec['type']}`. {spec['description']}", "",
                 f"Supply {en_fmt}. The accessors are {names}.", "",
                 f"C applications include `<uwrosv2/{record.ident}/observation.h>` and use the `uwrosv2_{record.ident}_` function prefix.",
                 f"C++98 and later include `<uwrosv2/{record.ident}/observation.hpp>` and use namespace `uwrosv2::{record.ident}`.",
                 "C takes an output pointer and C++ takes an output reference. Both write the value on success. The Rust crate `wros_observation` returns `Option<T>`.",
                 f"JS and TypeScript import the accessors from `uwrosv2/platform/{p}/observation` and pass a Uint8Array. Invalid records return undefined. The 64-bit integer fields return bigint.",
                 "In the AssemblyScript bounded-driver profile, pass a staged request length or set the final argument to true to read the last successful driver reply. Each successful accessor returns true and sets the exported field value.",
                 f"The standalone WAT library at `include/u2rosv2/platform/{p}/wat/observation.wat` exports its memory and the named functions. Supply the input address, length, optional array index and output address. A return value of 1 stores the field at its original width in little-endian order.", "",
                 "## Run the example", "",
                 f"Install `--platform {p}` and the selected language. Copy `examples/{p}/<language>` into a user project and set `UWVM_ROS_SDK_ROOT` and `WROS_VM`.",
                 "Run `xmake build` and `xmake test -j1`. The guest reads constructed offline samples and checks field values and truncated input.", "",
                 "## Upstream definitions", "", *sources, "",
                 "The platform.json manifest records each source revision and file SHA-256."]
    guides = wire_guides(record, zh)
    if guides:
        summary = spec["wire_summary_zh" if zh else "wire_summary"]
        links = []
        for guide in guides:
            module = guide.split(".")[0]
            label = f"{module.upper()} 消息与服务记录" if zh else f"{module.upper()} message and service records"
            if module in spec.get("wire_guide_labels", {}):
                label = spec["wire_guide_labels"][module]["zh" if zh else "en"]
            links.append(f"[{label}]({guide})")
        title = spec.get("display_name", p.upper() if p == "abb" else p.capitalize())
        heading = "只读观测接口" if zh else "Read-only observation API"
        lines[:1] = [f"# {title}", "", summary + " " + " · ".join(links), "", "## " + heading]
    return "\n".join([*lines, ""])


def generate(record):
    p = record.platform
    write(f"platform/{p}/platform.json", manifest(record))
    write(f"platform/{p}/README.md", docs(record, False))
    write(f"platform/{p}/README.zh.md", docs(record, True))
    for lang, extension in LANGUAGES.items():
        project = f"src/examples/{p}/{lang}"
        directory = "c++" if lang == "cpp" else lang
        public = f"include/u2rosv2/platform/{p}/{directory}"
        if lang in ("c", "cpp"):
            cpp = lang == "cpp"
            name = f"uwrosv2/{record.ident}/observation." + ("hpp" if cpp else "h")
            header, main = c_header(record, cpp), c_example(record, cpp)
        elif lang == "rust":
            name, header, main = "lib.rs", rust_header(record), rust_example(record)
        elif lang == "as":
            name, header, main = "observation.ts", as_module(record), as_example(record)
        elif lang in ("js", "typescript"):
            typed = lang == "typescript"
            name = "observation.d.ts" if typed else "observation.mjs"
            header, main = es_module(record, declarations=typed), es_example(record, typed=typed)
        else:
            name, header, main = "observation.wat", wat_module(record, example=False), wat_module(record, example=True)
        write(f"{public}/{name}", header)
        write(f"{project}/main.{extension}", main)
        write(f"{project}/xmake.lua", xmake(p, lang, extension))


def index(specs, zh):
    page = "README.zh.md" if zh else "README.md"
    if zh:
        lines = ["# 平台接口", "", "安装时用下列平台 ID 和语言选择接口。每个平台提供 C、C++98 至 C++26、WAT、Rust、AssemblyScript、JavaScript 和 TypeScript 的 Xmake 工程。",
                 "每页给出读取字段、输入编码和固定版本的上游文件。各厂商示例在 guest 内存中读取离线数据。", "",
                 "单个平台的开发流程和完整上游验收要求见[平台验收](../document/zh/platform-qualification.md)。", "",
                 f"- 通用场景 ABI。[generic](generic/{page})",
                 f"- Go 支持 43 种 Unitree ROS 2 消息类型，Go2 与 HG LowState 有双端序编解码器。[unitree](unitree/{page})"]
    else:
        lines = ["# Platform interfaces", "", "Select the platform ID and language when installing. Each selection has Xmake projects for C, C++98 through C++26, WAT, Rust, AssemblyScript, JavaScript and TypeScript.",
                 "Each guide identifies the input encoding, fields and pinned upstream files. Vendor examples read offline data in guest memory.", "",
                 "The per-platform development and full upstream acceptance requirements are in the [platform qualification guide](../document/en/platform-qualification.md).", "",
                 f"- Common scene ABI. [generic](generic/{page})",
                 f"- Go provides 43 Unitree ROS 2 message types and both-endian Go2 and HG LowState codecs. [unitree](unitree/{page})"]
    for name, spec in specs.items():
        summary = spec.get("wire_summary_zh" if zh else "wire_summary", spec["type"] + ".")
        lines.append(f"- {summary} [{name}]({name}/{page})")
    return "\n".join([*lines, ""])


if __name__ == "__main__":
    specs = json.loads((ROOT / "src/platform/observations.json").read_bytes())
    for platform, spec in specs.items():
        generate(Record(platform, spec))
    for lang in ("as", "js", "typescript"):
        write(f"src/examples/unitree/{lang}/xmake.lua", xmake("unitree", lang, LANGUAGES[lang]))
    library = (ROOT / "include/u2rosv2/platform/unitree/wat/go2_low_state.wat").read_text()
    fixture = (ROOT / "src/platform/unitree_example.inc").read_text()
    write("src/examples/unitree/wat/main.wat", library.rstrip().removesuffix(")") + fixture + ")\n")
    for zh in (False, True):
        write("platform/README.zh.md" if zh else "platform/README.md", index(specs, zh))
