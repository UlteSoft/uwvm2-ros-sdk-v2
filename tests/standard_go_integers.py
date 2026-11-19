"""@brief Compare fixed-width integer operations with an independent native Go build."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import random
import struct
import subprocess

SEED = 0x57474f5348494654


def digest(path):
    """@brief Bind the inputs and executable outputs to this comparison."""
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def patterns():
    """@brief Describe shifts, conversions and division across the integer widths."""
    for width in (32, 64):
        for count_width in (32, 64):
            for kind, unsigned, operator in (("Left", False, "<<"), ("Signed", False, ">>"),
                                              ("Unsigned", True, ">>")):
                operand = ("uint" if unsigned else "int") + str(width)
                count = f"uint{count_width}"
                yield f"{kind}{width}x{count_width}", operand, count, operand, f"x {operator} n"
    yield "Narrow", "int64", None, "uint32", "uint32(x)"
    yield "SignExtend", "int32", None, "uint64", "uint64(x)"
    yield "ZeroExtend", "uint32", None, "int64", "int64(x)"
    yield "Alias32", "int32", None, "uint32", "uint32(x)"
    yield "Alias64", "uint64", None, "int64", "int64(x)"
    yield "ConvertedCount", "uint32", "int32", "uint32", "x >> uint32(n)"
    yield "Rotate32", "uint32", None, "uint32", "x << 27 | x >> 5"
    yield "Rotate64", "uint64", None, "uint64", "x << 53 | x >> 11"
    yield "LeftConstant", "int64", None, "int64", "x << 19"
    yield "RightConstant", "uint32", None, "uint32", "x >> 17"
    for width in (32, 64):
        high_bit = 1 << (width - 1)
        for prefix, divisors in (
            ("int", (-high_bit, -37, -32, -2, -1, 1, 2, 7, 32, high_bit - 1)),
            ("uint", (1, 2, 3, 7, 32, high_bit, high_bit + 1, 2 * high_bit - 1)),
        ):
            operand = prefix + str(width)
            for ordinal, value in enumerate(divisors):
                for name, operator in (("Quotient", "/"), ("Remainder", "%")):
                    function = f"{name}{prefix.title()}{width}By{ordinal}"
                    yield function, operand, None, operand, f"x {operator} ({value})"


def main():
    """@brief Qualify exact installed SDK, interpreter and AOT inputs inside the test gate."""
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("sdk", "vm", "go", "wat2wasm", "wasm-validate"):
        parser.add_argument("--" + name, type=lambda value: Path(value).resolve(strict=True), required=True)
    parser.add_argument("--output", type=Path, required=True)
    a = parser.parse_args()
    membership = Path("/proc/self/cgroup").read_text().strip().split("0::/", 1)
    if len(membership) != 2 or membership[0]:
        raise ValueError("expected one cgroup v2 membership")
    cgroup = Path("/sys/fs/cgroup") / membership[1]
    if ((cgroup / "memory.max").read_text().strip() != "68719476736"
            or (cgroup / "memory.swap.max").read_text().strip() != "0"):
        raise ValueError("use the existing 64 GiB zero-swap cgroup")
    out = a.output.resolve()
    if ".tmp" not in out.parts:
        raise ValueError("choose a new comparison directory within .tmp")
    out.mkdir(mode=0o700)
    env = dict(os.environ, GOENV="off", GOMAXPROCS="4", CGO_ENABLED="0", GOWORK="off",
               GOPROXY="off", GOTOOLCHAIN="local", GO111MODULE="off", GOCACHE=str(out / "go-cache"),
               TMPDIR=str(out))
    report = dict(complete=False, cgroup=str(cgroup), seed=SEED, commands=[],
                  reference="https://go.dev/ref/spec#Integer_operators",
                  upstream_cases=["https://github.com/golang/go/blob/go1.24.2/test/codegen/shift.go",
                                  "https://github.com/golang/go/blob/go1.24.2/test/divmod.go"],
                  memory_events_before=(cgroup / "memory.events").read_text())
    result = out / "results.json"

    def save():
        result.write_text(json.dumps(report, indent=2) + "\n")

    def run(label, command):
        proc = subprocess.run(command, cwd=out, env=env, capture_output=True, timeout=120)
        (out / (label + ".stderr")).write_bytes(proc.stderr)
        report["commands"].append(dict(label=label, argv=list(map(str, command)), exit=proc.returncode))
        save()
        proc.check_returncode()
        return proc.stdout

    def width(kind):
        return int(kind[-2:])

    def word(value, kind):
        return f"(i{width(kind)}.const {value})"

    rng = random.Random(SEED)
    sample_count = 192
    records = []
    definitions = []
    native_rows = []
    cases = list(patterns())
    for i, (name, operand, count, returns, expression) in enumerate(cases):
        parameters = f"x {operand}" + (f", n {count}" if count else "")
        definitions.append(f"func {name}({parameters}) {returns} {{ return {expression} }}")
        bits = width(operand)
        top, middle = (1 << bits) - 1, 1 << (bits - 1)
        values = (0, 1, 3, middle - 1, middle, middle + 1, top - 1, top)
        if name.startswith(("Quotient", "Remainder")):
            values += tuple(value & top for value in (-38, -37, -36, -33, -32, -31, -8, -7, -6,
                                                       6, 7, 8, 31, 32, 33, 36, 37, 38))
        counts = (0, 1, bits - 1, bits, bits + 1, bits * 2, 0xffffffff, 1 << 32, (1 << 64) - 1)
        for sample in range(sample_count):
            x = values[sample % len(values)] if sample < 72 else rng.getrandbits(bits)
            n = 0
            if count:
                n = (counts[sample // len(values)] if sample < 72
                     else rng.choice((rng.randrange(80), rng.getrandbits(width(count)))))
                n %= 1 << width(count)
            native_rows.append(f"{{{i}, {x}, {n}}}")
            records.append((i, x, n))

    source = out / "control.go"
    source.write_text("package main\nfunc Start() uint32 { return 0 }\n" + "\n".join(definitions) + "\n")
    oracle_source = out / "oracle.go"
    dispatch = []
    for i, (name, operand, count, returns, _) in enumerate(cases):
        args = f"{operand}(item.x)" + (f", {count}(item.n)" if count else "")
        dispatch.append(f"case {i}: value = uint64(uint{width(returns)}({name}({args})))")
    oracle_source.write_text('''package main
import ("bufio"; "encoding/binary"; "os")
func main() {
    inputs := []struct { id int; x,n uint64 }{
    ''' + ",\n".join(native_rows) + ''',
    }
    writer := bufio.NewWriter(os.Stdout)
    for _, item := range inputs {
        var value uint64
        switch item.id {
        ''' + "\n".join(dispatch) + '''
        default: os.Exit(2)
        }
        if err := binary.Write(writer, binary.LittleEndian, value); err != nil { os.Exit(3) }
    }
    if writer.Flush() != nil { os.Exit(4) }
}
''')
    oracle = out / "oracle"
    report["native_go_version"] = run("go-version", [a.go, "version"]).decode().strip()
    run("native-build", [a.go, "build", "-trimpath", "-o", oracle, source, oracle_source])
    data = run("native-run", [oracle])
    if len(data) != len(records) * 8:
        raise ValueError("incomplete native results")
    (out / "oracle.bin").write_bytes(data)

    guest = out / "control.wasm"
    wrgo = a.sdk / "bin/wrgo"
    run("guest-build", [wrgo, source, "-g", "--build-receipt", "-o", guest])
    receipt = json.loads(Path(str(guest) + ".wros-go.json").read_bytes())
    if not receipt["mte_requested"] or receipt["linear_memories"] or receipt["wasm_imports"]:
        raise ValueError("the scalar module must preserve its memory and authority contract")
    imports, bodies = [], [[] for _ in cases]
    for i, (name, operand, count, returns, _) in enumerate(cases):
        signature = f"i{width(operand)}" + (f" i{width(count)}" if count else "")
        imports.append(f'(import "algorithm" "{name}" (func $f{i} (param {signature}) (result i{width(returns)})))')
    for (i, x, n), (answer,) in zip(records, struct.iter_unpack("<Q", data)):
        _, operand, count, returns, _ = cases[i]
        args = word(x, operand) + (word(n, count) if count else "")
        bodies[i].append(f"(if (i{width(returns)}.ne (call $f{i} {args}) {word(answer, returns)}) (then unreachable))")
    wat, checks = out / "checks.wat", out / "checks.wasm"
    functions = [f"(func $test{i}\n" + "\n".join(body) + ")" for i, body in enumerate(bodies)]
    wat.write_text("(module\n" + "\n".join(imports + functions) + '\n(func (export "_start") '
                   + " ".join(f"(call $test{i})" for i in range(len(cases))) + "))\n")
    run("checks-build", [a.wat2wasm, wat, "-o", checks])
    for unit in (guest, checks):
        run(unit.stem + "-validate", [a.wasm_validate, unit])
    for engine in ("int", "aot"):
        run("vm-" + engine, [a.vm, "--runtime-" + engine, "--runtime-compile-threads", "0",
                              "--runtime-llvm-jit-cache-path", "disable", "--runtime-memtag-mode", "sync",
                              "--wasm-preload-library", guest, "algorithm", "--run", checks])
    report.update(complete=True, functions=len(cases), values_per_engine=len(records),
                  memory_events_after=(cgroup / "memory.events").read_text(),
                  inputs={str(p): digest(p) for p in (a.vm, a.go, wrgo, Path(__file__).resolve(), source, oracle_source,
                                                       oracle, out / "oracle.bin", guest, wat, checks)})
    save()


if __name__ == "__main__":
    main()
