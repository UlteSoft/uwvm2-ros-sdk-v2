"""Qualify the ROS sensor_msgs image encoding helpers on recorded package sources."""
from pathlib import Path, PurePosixPath

from strict_numeric import qualify


def vectors():
    # Each entry describes its pixel layout from the public encoding name.
    cases = []
    for bits in (8, 16):
        cases.append((f"mono{bits}", 1, bits, "mono"))
        for name in ("rgb", "bgr", "rgba", "bgra"):
            cases.append((f"{name}{bits}", len(name), bits, "alpha" if len(name) == 4 else "color"))
        for mosaic in ("rggb", "bggr", "gbrg", "grbg"):
            cases.append((f"bayer_{mosaic}{bits}", 1, bits, "bayer"))
    for storage in ("8U", "8S", "16U", "16S", "32S", "32F", "64F"):
        for channels in (1, 4, 12):
            cases.append((f"{storage}C{channels}", channels, int(storage[:-1]), "generic"))
    lines = ["static constexpr Encoding cases[] = {"]
    for name, channels, bits, kind in cases:
        lines.append(f'    {{"{name}", {channels}, {bits}, Kind::{kind}}},')
    lines.append("};")
    return "\n".join(lines) + "\n", [row[0] for row in cases]


def adapter(files, header):
    # Hydro's headers explicitly enumerate the first four OpenCV channel counts.
    # Later headers parse a decimal channel count. Both behaviours are public.
    enumerated = b"CHECK_CHANNELS(" in files[header]
    return (f"#define FOUR_CHANNEL_LAYOUTS_ONLY {int(enumerated)}\n" +
            '#include "' + str(header.relative_to("include")) + '"\n')


if __name__ == "__main__":
    headers = [PurePosixPath("include/sensor_msgs/image_encodings." + ext) for ext in ("hpp", "h")]
    # Some libc++ regex versions reference these functions during linking.
    # A numerical image classification cannot acquire their runtime rights.
    denied = {
        "environ_get": (["i32", "i32"], ["i32"]),
        "environ_sizes_get": (["i32", "i32"], ["i32"]),
        "clock_time_get": (["i32", "i64", "i32"], ["i32"]),
        "proc_exit": (["i32"], []),
    }
    qualify("sensor_msgs", "Image encoding classification, channels, depth and rejection of unknown formats",
            Path(__file__), headers, "image-encoding-header-absent", vectors, adapter, denied_imports=denied)
