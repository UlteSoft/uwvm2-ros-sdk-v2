"""Verify C# source locations and the boundary between method-level and statement-level DWARF."""
import argparse
import os
from pathlib import Path
import re
import subprocess
import sys

from separate_compilation import cgroup_record

ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for option in ("dotnet", "mono-compiler", "toolchain", "dwarfdump", "output"):
        parser.add_argument("--" + option, type=Path, required=True)
    args = parser.parse_args()
    cgroup_record()
    out = args.output.resolve()
    out.mkdir(parents=True, exist_ok=False)
    dwarf = args.dwarfdump.resolve()
    libs = [dwarf.parents[1] / "lib/x86_64-unknown-linux-gnu", dwarf.parents[1] / "lib"]
    env = dict(os.environ, LD_LIBRARY_PATH=os.pathsep.join(map(str, libs)))
    source = out / "Sensor.cs"
    cases = (
        ("single", "        return k * 11 - 1;", True, 5),
        ("loop", "        int x = k;\n        for (int i=0;i<6;i++) x ^= i;\n        return x;", False, 5),
        ("unmatched", '#line 700 "virtual.cs"\n        return k + 2;\n#line default', False, 0),
    )
    for tag, body, instructions, line in cases:
        source.write_text("public static class Sensor\n{\n    public static int Read(int k)\n    {\n" + body + "\n    }\n}\n")
        module = out / (tag + ".wasm")
        subprocess.run([sys.executable, "-B", ROOT / "bin/wrcs", "--dotnet", args.dotnet.resolve(),
            "--mono-compiler", args.mono_compiler.resolve(), "--toolchain", args.toolchain.resolve(),
            "--legacy-mte", "--entry", "Sensor.Read", source, "-o", module], check=True, timeout=180)
        code = subprocess.check_output([dwarf, "--debug-info", "--debug-line", module], env=env, text=True, timeout=30)
        (out / (tag + ".dwarf.txt")).write_text(code)
        # Ignore source paths in llvm-dwarfdump's banner for the module itself.
        if str(out) in code.partition("\n")[2] or "virtual.cs" in code:
            raise ValueError("unmatched or absolute source path leaked into DWARF")
        actual = [int(n) for n in re.findall(r"^0x[0-9a-f]+\s+(\d+)\s+\d+\s+\d+\s+", code, re.M)]
        if line:
            for evidence in ('("Sensor.Read")', '("evaluate")', '"Sensor.cs"', f'DW_AT_decl_line\t({line})'):
                if evidence not in code:
                    raise ValueError("missing C# source identity: " + evidence)
        if instructions and (not actual or set(actual) != {line}):
            raise ValueError("unexpected numerical instruction mapping")
        if not instructions and any(n for n in actual):
            raise ValueError("multiple or unmatched method statements received guessed instruction lines")
        print(tag, "passed", flush=True)


if __name__ == "__main__":
    main()
