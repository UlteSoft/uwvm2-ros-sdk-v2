"""Fixed upstream observation layouts shared by the native, Rust and WAT emitters."""
from dataclasses import dataclass
from hashlib import sha256
import json
from pathlib import Path
import re
import struct

# ROS 1 uses compact little endian. CDR1 aligns from the start of its body.
FORMATS = {"ros1": 0, "packed": 0, "cdr": 1, "lcm": 2, "quaternion": 3}
PACK = {"bool": "B", "i8": "b", "u8": "B", "i16": "h", "u16": "H", "i32": "i", "u32": "I",
        "i64": "q", "u64": "Q", "f32": "f", "f64": "d"}
WIDTH = {t: struct.calcsize("<" + fmt) for t, fmt in PACK.items()} | {"str": 0}
C_TYPE = {k: (k.replace("i", "int", 1) if k.startswith("i") else k.replace("u", "uint", 1)) + "_t"
          for k in PACK if k.startswith(("i", "u"))} | {"f32": "float", "f64": "double", "bool": "uint8_t"}


@dataclass(frozen=True)
class Field:
    type: str
    name: str
    repeat: int
    kind: int

    @property
    def width(self):
        return WIDTH[self.type]

    @classmethod
    def parse(cls, declaration, fmt):
        spelling, name = declaration.split()
        match = re.fullmatch(r"([a-z0-9]+)(?:\[(\d*|saved|rest\d+)\])?", spelling)
        kind, size = match.groups()
        if size == "saved":
            repeat = -1
        elif size and size.startswith("rest"):
            repeat = -1 - int(size[4:])
        else:
            repeat = 1 if size is None else int(size or 0)
        return cls(kind, name, repeat, 2 if fmt == "lcm" and name == "motor_num" else int(kind == "bool"))


@dataclass(frozen=True)
class Reading:
    name: str
    field: Field
    number: int
    step: int
    base: int
    sample: int | float

    @property
    def indexed(self):
        return self.field.repeat != 1

    @property
    def example_index(self):
        return 1 if self.indexed else 0


class Record:
    def __init__(self, platform, spec):
        self.platform = platform
        self.ident = platform.replace("-", "_")
        self.spec = spec
        self.mode = FORMATS[spec["format"]]
        self.fields = [Field.parse(line, spec["format"]) for line in spec["layout"]]
        self.readings = []
        for name, entry in spec["read"].items():
            args = entry if isinstance(entry, dict) else {"value": entry}
            target = args.get("field", name)
            i = next(i for i, f in enumerate(self.fields) if f.name == target)
            self.readings.append(Reading(name, self.fields[i], i, args.get("step", 1),
                                         args.get("base", 0), args["value"]))

    def example(self, *, big_cdr=False):
        """Use an independently frozen frame when provided, or construct a sample from the layout."""
        cdr = self.mode in (1, 3)
        if "example_frames" in self.spec:
            root = Path(__file__).resolve().parent
            path = (root / self.spec["example_frames"]).resolve()
            if not path.is_relative_to(root):
                raise ValueError("example_frames must be inside src/platform")
            key = "be" if big_cdr else "le"
            frame = json.loads(path.read_bytes())[key]
            data = bytes.fromhex(frame["hex"])
            if (not cdr or len(data) < 4 or data[:2] != bytes((0, int(not big_cdr))) or
                    len(data) != frame["size"] or sha256(data).hexdigest() != frame["sha256"]):
                raise ValueError(f"Invalid {key} CDR fixture for {self.platform}")
            return data
        big = self.mode == 2 or cdr and big_cdr
        endian = ">" if big else "<"
        body = bytearray()

        def scalar(kind, value):
            width = WIDTH[kind]
            if cdr:
                body.extend(b"\0" * (-len(body) % width))
            body.extend(struct.pack(endian + PACK[kind], value))

        for f in self.fields:
            count = f.repeat if f.repeat > 0 else (2 if f.repeat >= -1 else 2 * (-1 - f.repeat))
            if f.repeat == 0:
                scalar("u32", count)
            examples = {r.example_index * r.step + r.base: r.sample for r in self.readings if r.field == f}
            for index in range(count):
                if f.type == "str":
                    data = (("joint" + str(index)) if f.repeat != 1 else "frame").encode()
                    if cdr:
                        data += b"\0"
                    scalar("u32", len(data))
                    body.extend(data)
                else:
                    scalar(f.type, 2 if f.kind == 2 else examples.get(index, 0))
        prefix = b"\x00\x00\x00\x00" if cdr and big else b"\x00\x01\x00\x00" if cdr else b""
        if self.mode == 2:
            prefix = bytes.fromhex("4a be c5 2f 17 ed d1 1f")
        return prefix + body


def octets(data, indent="    "):
    return ",\n".join(indent + ", ".join(f"0x{x:02x}" for x in data[i:i+12]) for i in range(0, len(data), 12))
