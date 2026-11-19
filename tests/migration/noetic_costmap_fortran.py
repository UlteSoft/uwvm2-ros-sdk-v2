"""@file noetic_costmap_fortran.py
@brief Compare the shipped Fortran cell index with the original ROS Noetic method.
@details The native reference embeds the exact inline getIndex method from the
pinned navigation header. Grid coordinates are tested as unsigned 32-bit bit
patterns. The probe exercises arithmetic only, without a ROS node or device.
"""
import argparse
import hashlib
import itertools
import json
from pathlib import Path
import random
import subprocess
import tempfile

HEADER_SHA256 = "ce28d5b873fe9f09aa63c46769bba28dd3014fc55d59382c74e49c769ea1f158"
ROOT = Path(__file__).resolve().parents[2]
FORTRAN = ROOT / "examples/shared/migration/fortran/grid.f90"
MASK = (1 << 32) - 1


def digest(data):
    """@brief Return the SHA-256 digest of the exact recorded bytes."""
    return hashlib.sha256(data).hexdigest()


def write_reference(header, directory):
    """@brief Write the pinned inline method with its real unsigned width member.
    @param header Original costmap_2d.h bytes from the Noetic navigation source.
    @param directory Fresh test directory.
    @return C++ source path for the native reference.
    """
    if digest(header) != HEADER_SHA256:
        raise ValueError("unexpected Noetic costmap header")
    text = header.decode("utf-8")
    start = text.index("  inline unsigned int getIndex(")
    end = text.index("\n  }", start) + len("\n  }")
    reference = directory / "reference.cpp"
    reference.write_text(
        "#include <cstdio>\n#include <limits>\n"
        "static_assert(std::numeric_limits<unsigned int>::digits == 32);\n"
        "struct Grid { unsigned int size_x_;\n" + text[start:end] + "\n};\n"
        "int main() { unsigned int w, x, y;\n"
        "while (std::scanf(\"%u%u%u\", &w, &x, &y) == 3) "
        "std::printf(\"%u\\n\", Grid{w}.getIndex(x, y));\n}\n"
    )
    return reference


def write_probe(grid, directory):
    """@brief Embed the shipped Fortran contained procedure in a vector reader."""
    source = grid.decode("utf-8")
    before, contains, body = source.partition("\ncontains\n")
    if not before or not contains or "function cell(width,x,y)" not in body:
        raise ValueError("cannot locate the Fortran index procedure")
    probe = directory / "probe.f90"
    probe.write_text(
        "program vectors\n"
        "use iso_c_binding, only: c_int32_t, c_int64_t\n"
        "implicit none\ninteger(c_int32_t) :: w,x,y\ninteger :: status\n"
        "do\n read(*,*,iostat=status) w,x,y\n if (status /= 0) exit\n"
        " write(*,*) cell(w,x,y)\nend do" + contains + body
    )
    return probe


def inputs():
    """@brief Return signed 32-bit edge triples and reproducible random patterns."""
    bounds = [-2**31, -2**31 + 1, -1, 0, 1, 2**31 - 2, 2**31 - 1]
    values = list(itertools.product(bounds, repeat=3))
    rng = random.Random(2026)
    for _ in range(4096):
        values.append(tuple(rng.randrange(-2**31, 2**31) for _ in range(3)))
    return values


def main():
    """@brief Compile both implementations and require equality for every result."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--noetic-header", type=Path, required=True)
    parser.add_argument("--cxx", type=Path, required=True)
    parser.add_argument("--gfortran", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=False)
    header = args.noetic_header.read_bytes()
    grid = FORTRAN.read_bytes()
    vectors = inputs()
    signed = "".join(f"{w} {x} {y}\n" for w, x, y in vectors).encode()
    unsigned = "".join(f"{w & MASK} {x & MASK} {y & MASK}\n" for w, x, y in vectors).encode()
    with tempfile.TemporaryDirectory(dir=args.output) as scratch:
        directory = Path(scratch).resolve()
        reference, probe = directory / "noetic", directory / "fortran"
        subprocess.run([args.cxx.resolve(), "-std=c++17", "-O3", "-g",
                        write_reference(header, directory), "-o", reference], check=True)
        subprocess.run([args.gfortran.resolve(), "-O3", "-g", "-ftrapv", "-fcheck=all",
                        write_probe(grid, directory), "-o", probe], check=True)
        cpp = subprocess.run([reference], check=True, input=unsigned, stdout=subprocess.PIPE, timeout=30)
        f90 = subprocess.run([probe], check=True, input=signed, stdout=subprocess.PIPE, timeout=30)
    expected = [int(x) for x in cpp.stdout.split()]
    actual = [int(x) & MASK for x in f90.stdout.split()]
    if len(expected) != len(vectors) or actual != expected:
        raise ValueError("the Fortran indices differ from the compiled Noetic method")
    receipt = {"complete": True, "cases": len(vectors), "header_sha256": digest(header),
               "fortran_sha256": digest(grid), "vectors_sha256": digest(signed),
               "reference_outputs_sha256": digest(cpp.stdout), "fortran_outputs_sha256": digest(f90.stdout)}
    (args.output / "results.json").write_text(json.dumps(receipt, indent=2) + "\n")


if __name__ == "__main__":
    main()
