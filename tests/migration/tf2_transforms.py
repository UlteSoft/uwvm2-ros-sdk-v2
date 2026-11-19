"""Qualify package-local tf2 rigid transforms using an independent axis-angle reference."""
import math
from pathlib import Path, PurePosixPath

from strict_numeric import qualify


def pose(axis, angle, translation, magnitude):
    # The guest receives xyzw. The oracle computes rotation directly from
    # axis-angle with Rodrigues' formula and never multiplies quaternions.
    x, y, z = (v / math.hypot(*axis) for v in axis)
    c, s = math.cos(angle), math.sin(angle)
    k = 1 - c
    rotation = ((c+x*x*k, x*y*k-z*s, x*z*k+y*s),
                (y*x*k+z*s, c+y*y*k, y*z*k-x*s),
                (z*x*k-y*s, z*y*k+x*s, c+z*z*k))
    q = [magnitude * math.sin(angle / 2) * u for u in (x, y, z)]
    return rotation, translation, [*q, magnitude * math.cos(angle / 2)]


def apply(pose, point, inverse=False):
    matrix, t, _ = pose
    if inverse:
        return [sum(matrix[j][i] * (point[j] - t[j]) for j in range(3)) for i in range(3)]
    return [t[i] + sum(a*b for a, b in zip(row, point)) for i, row in enumerate(matrix)]


def vectors():
    # Child-to-parent mappings. Angles are radians and translations are metres.
    identity = ((1, 0, 0), 0, (0, 0, 0), 1)
    anchor = pose((0, 0, 1), math.pi / 2, (2, 3, 0), 1)
    assert math.dist(apply(anchor, [1, 0, 0]), [2, 4, 0]) < 1e-12
    cases = [
        ("identity", identity, identity, (1, -2, 3)),
        ("translation", ((0, 0, 1), 0, (8, 9, -3), 1), identity, (0, 0, 0)),
        ("noncommuting", ((0, 0, 1), math.pi/2, (2, 3, 0), 1),
         ((1, 0, 0), -math.pi/2, (1, 0, 4), 1), (0, 1, 0)),
        ("mixed_axes", ((1, 2, -3), 1.7, (2, -0.5, 4), 1),
         ((-2, 1, 0), -0.8, (0, 3, -1), 1), (0.2, -1.6, 3.1)),
        ("near_half_turn", ((1, -2, 1), math.pi-3e-5, (-7, 5, 4), 1),
         ((0, 1, 1), math.pi+1e-5, (2, 0, -3), 1), (-2, 1, 5)),
        ("tiny_rotation", ((1, 0, 0), 1e-5, (0, 0, 0), 1),
         ((0, 1, 0), -2e-5, (0, 0, 0), 1), (7, -5, 11)),
        ("scaled_quaternions", ((1, 2, 1), 1.2, (1, 4, 5), 2.5),
         ((3, -4, -1), -1.3, (-1, 4, 7), -0.4), (5, -8, -2)),
        ("optical_frame", ((0, 0, 1), -math.pi/2, (0.4, 0.03, 1.4), 1),
         ((1, 0, 0), -math.pi/2, (0.1, 0.02, 0.3), 1), (0, 0, 2)),
    ]

    def numbers(values):
        return "{" + ", ".join(float(x).hex() for x in values) + "}"

    lines = ["static const volatile Scenario scenarios[] = {"]
    for _, outer, inner, point in cases:
        a, b = pose(*outer), pose(*inner)
        b_point = apply(b, point)
        world = apply(a, b_point)
        relative = apply(a, b_point, inverse=True)
        # Transforming the origin discriminates translation from direction.
        origin = apply(a, b[1])
        values = [a[2], a[1], b[2], b[1], point, world, relative, origin]
        lines.append("    {" + ", ".join(numbers(v) for v in values) + "},")
    lines.append("};")
    return "\n".join(lines) + "\n", [name for name, *_ in cases]


def adapter(files, entry):
    legacy = entry.name.startswith("bt")
    prefix = "bt" if legacy else "tf2::"
    return ('#include "' + str(entry.relative_to("include")) + '"\n' +
            "".join(f"using {cls} = {prefix}{cls};\n" for cls in ("Quaternion", "Vector3", "Transform")))


if __name__ == "__main__":
    directory = PurePosixPath("include/tf2/LinearMath")
    entries = [directory / name for name in ("Transform.hpp", "Transform.h", "btTransform.h")]
    qualify("tf2", "rigid transform arithmetic for validated in-memory poses", Path(__file__),
            entries, "transform-header-absent", vectors, adapter,
            dependencies={"ros/macros.h": ("cpp_common", "35e08e35aed10833c3cf82d2")})
