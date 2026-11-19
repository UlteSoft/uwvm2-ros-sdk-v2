"""Check RVL depth frames from the ROS source inventory against independent wire vectors."""
from pathlib import Path, PurePosixPath

from strict_numeric import qualify

SOURCE = PurePosixPath("src/rvl_codec.cpp")


def rvl_words(depths):
    """Encode zero and nonzero run lengths and zigzag deltas in 8-nibble words."""
    digits = []

    def write(value):
        while value >= 8:
            digits.append(8 + value % 8)
            value //= 8
        digits.append(value)

    previous = 0
    cursor = 0
    while cursor < len(depths):
        start = cursor
        while cursor < len(depths) and depths[cursor] == 0:
            cursor += 1
        write(cursor - start)
        start = cursor
        while cursor < len(depths) and depths[cursor] != 0:
            cursor += 1
        write(cursor - start)
        for value in depths[start:cursor]:
            diff = value - previous
            write(2 * diff if diff >= 0 else -2 * diff - 1)
            previous = value
    digits.extend([0] * (-len(digits) % 8))
    return [int("".join(format(n, "x") for n in digits[i:i + 8]), 16)
            for i in range(0, len(digits), 8)]


def vectors():
    # Independent format anchors: one zero run, one value and both delta signs.
    assert rvl_words([0]) == [0x10000000]
    assert rvl_words([1]) == [0x01200000]
    assert rvl_words([2, 1]) == [0x02410000]
    frames = {"empty": [], "all_zero": [0] * 512, "constant": [1900] * 512,
              "delta_extremes": [1, 65535, 1, 2, 65534, 6, 0, 1],
              "nibble_boundaries": [0] * 7 + [2] * 8 + [0] * 63 + [512] * 64 + [4096] * 65,
              "depth_scan": [(0 if (i % 53 < 16) else 350 + (i * 7) % 1873) for i in range(1024)]}
    code = ["#pragma once"]
    for name, frame in frames.items():
        words = rvl_words(frame)
        code.append("static constexpr unsigned short " + name + "_pixels[] = {" +
                    ", ".join(map(str, frame or [0])) + "};")
        code.append("static constexpr unsigned int " + name + "_words[] = {" +
                    ", ".join(hex(word) + "u" for word in words or [0]) + "};")
    code.append("static constexpr Frame frames[] = {")
    for name, frame in frames.items():
        code.append(f"    {{{name}_pixels, {len(frame)}, {name}_words, {len(rvl_words(frame))}}},")
    code.append("};")
    return "\n".join(code) + "\n", list(frames)


def adapter(files, entry):
    header, = [path for path in files if path.parts[0] == "include"]
    return '#include "' + str(header.relative_to("include")) + '"\n'


if __name__ == "__main__":
    qualify("compressed_depth_image_transport", "valid locally owned RVL depth payloads",
            Path(__file__), [SOURCE], "rvl-source-absent", vectors, adapter)
