"""Apply digest-pinned compatibility edits to a staged Jazzy BufferCore tree."""
import argparse
import hashlib
import json
import tempfile
from pathlib import Path

CORE = "35b12cd9f26ee24b7f22752697adc52ceabfabe1ad70c446122a6499dfa7b9c2"
HEADER = "228833cb8d85c7d3a6c2232a5e51a7ddb4e03735d7a4416075dce375ec3cf8db"
TRAITS = "a33e6b6dbed6b8102d85da4bf00f6a779fe99357e6b68206138a88276ff54d6c"


def digest(data):
    return hashlib.sha256(data).hexdigest()


def apply_port(tree, prefix, output, single_executor):
    # Read the three small, pinned inputs before creating any output files.
    products = {}
    sources = {}

    def edit(source, relative, expected, substitutions):
        with source.open("rb") as stream:
            data = stream.read(256 * 1024 + 1)
        if len(data) > 256 * 1024:
            raise ValueError(f"input exceeds the Jazzy source size bound: {source}")
        if digest(data) != expected:
            raise ValueError(f"unexpected Jazzy source digest: {source}")
        sources[str(relative)] = expected
        if not substitutions:
            return
        value = data.decode("utf-8")
        for old, new, count in substitutions:
            if value.count(old) != count:
                raise ValueError(f"unexpected source occurrences in {source}")
            value = value.replace(old, new)
        products[relative] = value.encode("utf-8")

    traits = Path("rosidl_runtime_cpp/traits.hpp")
    # The original branch converts only ASCII. Preserve ostream handling of a
    # C string, including a leading NUL, and leave all other code units alone.
    edit(prefix / "include/rosidl_runtime_cpp" / traits, Path("include") / traits, TRAITS, [
        ("#include <codecvt>\n", "", 1),
        ("  std::wstring_convert<std::codecvt_utf8_utf16<char16_t>, char16_t> convert;\n", "", 1),
        ("std::string character_as_string = convert.to_bytes(character);",
         "const char ascii[2] = {static_cast<char>(character), 0};", 1),
        ("character_as_string.c_str()", "ascii", 1)])
    header = Path("include/tf2/buffer_core.hpp")
    unit = Path("src/buffer_core.cpp")
    edit(tree / header, header, HEADER, [
        ("#include <mutex>", '#include "tf2_single_executor_mutex.hpp"', 1),
        ("std::mutex", "wros_tf2::single_executor_mutex", 4)] if single_executor else [])
    edit(tree / unit, unit, CORE, [
        ("std::mutex", "wros_tf2::single_executor_mutex", 17)] if single_executor else [])
    if single_executor:
        mutex = Path(__file__).with_name("tf2_single_executor_mutex.hpp")
        products[Path("include") / mutex.name] = mutex.read_bytes()

    manifest = {
        "execution": "single-executor" if single_executor else "threaded",
        "inputs": sources,
        "outputs": {str(rel): digest(data) for rel, data in products.items()},
        "buffer_source": str((output if single_executor else tree) / unit),
    }
    with tempfile.TemporaryDirectory(dir=output.parent) as temp:
        staged = Path(temp) / "overlay"
        staged.mkdir(mode=0o700)
        for relative, data in products.items():
            path = staged / relative
            path.parent.mkdir(exist_ok=True, parents=True)
            path.write_bytes(data)
        (staged / "port.json").write_text(json.dumps(manifest, indent=2) + "\n")
        # Reserve the name exclusively. Replacing our empty directory publishes
        # all files together and concurrent invocations cannot share the output.
        output.mkdir(mode=0o700)
        try:
            staged.replace(output)
        except OSError:
            output.rmdir()
            raise


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("tf2-source", "ros-prefix", "output"):
        parser.add_argument("--" + name, required=True, type=lambda x: Path(x).resolve())
    parser.add_argument("--execution", required=True, choices=("single-executor", "threaded"))
    args = parser.parse_args()
    try:
        apply_port(args.tf2_source, args.ros_prefix, args.output, args.execution == "single-executor")
    except (ValueError, OSError) as error:
        parser.exit(1, f"tf2_buffer_port: {error}\n")


if __name__ == "__main__":
    main()
