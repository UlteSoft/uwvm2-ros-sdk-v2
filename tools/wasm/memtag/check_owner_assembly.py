"""Verify the address type and wire encoding of every managed-allocation instruction."""
import re
import subprocess


OWNER_OPERATIONS = ("claim", "claimz", "reserve", "activate", "release")


def assembly(bits):
    """Use real parameters and results so each instruction has a typed operand stack."""
    return "\n".join(
        f".globl test_{name}\n.type test_{name},@function\ntest_{name}:\n"
        f".functype test_{name} (i{bits}, i{bits}) -> (i{bits})\n"
        f"local.get 0\nlocal.get 1\nmemtag.{name} 0\nend_function\n"
        for name in OWNER_OPERATIONS
    )


def check(tool, work):
    """Check positive and wrong-width input for both targets with the supplied assembler."""
    work.mkdir(parents=True, exist_ok=True)
    cases = []
    for bits, other in ((32, 64), (64, 32)):
        command = [str(tool), f"-triple=wasm{bits}-unknown-unknown", "-mattr=+memtag", "--show-encoding"]
        for operand_bits in (bits, other):
            stem = f"wasm{bits}-owners-i{operand_bits}"
            source = work / (stem + ".s")
            source.write_text(assembly(operand_bits), encoding="ascii")
            args = [*command, str(source)]
            process = subprocess.run(args, capture_output=True, text=True, timeout=60)
            (work / (stem + ".stdout")).write_text(process.stdout)
            (work / (stem + ".stderr")).write_text(process.stderr)
            if operand_bits == bits:
                if process.returncode:
                    raise RuntimeError(f"{stem} assembly failed: {process.stderr}")
                for index, name in enumerate(OWNER_OPERATIONS):
                    # Prefix, packed opcode in unsigned LEB128, and memory index zero.
                    encoding = rf"\[0xff,0x{0xc0 + index:x},0x80,0x84,0x08,0x00\]"
                    line = rf"^\s*memtag\.{name}\s+0\s+# encoding: {encoding}\s*$"
                    if not re.search(line, process.stdout, re.MULTILINE):
                        raise RuntimeError(f"{stem} has incorrect encoding for memtag.{name}")
            else:
                diagnostic = f"expected [i{bits}, i{bits}] but got [i{other}, i{other}]"
                if process.returncode == 0 or process.stderr.count(diagnostic) != len(OWNER_OPERATIONS):
                    raise RuntimeError(f"{stem} did not reject each wrong-width instruction: {process.stderr}")
            cases.append(dict(name=stem, producer=args, producer_exit=process.returncode, passed=True))
    return cases
