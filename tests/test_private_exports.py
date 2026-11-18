"""Check the component export transformation independently of the compiler fixture."""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "install"))
from artifacts import MAGIC, uleb
from private_exports import keep_private_memory


def section(kind, data):
    return bytes([kind]) + uleb(len(data)) + data


def name(text):
    raw = text.encode()
    return uleb(len(raw)) + raw


def exports(*items):
    return section(7, uleb(len(items)) + b"".join(name(key) + bytes([kind]) + uleb(index)
                                                  for key, kind, index in items))


class PrivateExports(unittest.TestCase):
    def setUp(self):
        self.entry = ("evaluate", 0, 0)
        self.heap = ("memory", 2, 0)
        self.memory = section(5, bytes([1, 1, 1, 1]))
        self.prefix = MAGIC + section(1, bytes([1, 0x60, 1, 0x7f, 1, 0x7f])) + section(3, bytes([1, 0]))
        self.tail = section(10, bytes([1, 4, 0, 0x20, 0, 0xb])) + section(0, name("debug") + b"memory")
        self.visible = exports(self.entry)

    def rewrite(self, middle):
        return keep_private_memory(self.prefix + middle + self.tail, {"evaluate"}, max_pages=1)

    def test_preserves_sections_and_private_result(self):
        original = self.prefix + self.memory + self.visible + self.tail
        for entries in ((self.entry,), (self.entry, self.heap), (self.heap, self.entry)):
            with self.subTest(entries=entries):
                self.assertEqual(self.rewrite(self.memory + exports(*entries)), original)

    def test_rejects_non_profile_memory_and_exports(self):
        cases = {
            "missing-memory": self.visible,
            "duplicate-memory-section": self.memory * 2 + self.visible,
            "second-memory": section(5, bytes([2, 1, 1, 1, 1, 1, 1])) + self.visible,
            "unbounded": section(5, bytes([1, 0, 1])) + self.visible,
            "shared": section(5, bytes([1, 3, 1, 1])) + self.visible,
            "wide": section(5, bytes([1, 5, 1, 1])) + self.visible,
            "excess": section(5, bytes([1, 1, 1, 2])) + self.visible,
            "invalid-range": section(5, bytes([1, 1, 2, 1])) + self.visible,
            "imported": section(2, bytes([1]) + name("peer") + name("x") + bytes([2, 1, 1, 1])) + self.memory + self.visible,
            "missing-entry": self.memory + exports(self.heap),
            "wrong-entry-kind": self.memory + exports(("evaluate", 3, 0)),
            "extra-function": self.memory + exports(self.entry, ("other", 0, 0)),
            "named-memory": self.memory + exports(self.entry, ("exchange", 2, 0)),
            "wrong-memory-index": self.memory + exports(self.entry, ("memory", 2, 1)),
            "duplicate-name": self.memory + exports(self.entry, self.entry),
            "duplicate-heap": self.memory + exports(self.heap, self.heap, self.entry),
            "duplicate-exports": self.memory + self.visible * 2,
        }
        for label, value in cases.items():
            with self.subTest(label=label), self.assertRaises(ValueError):
                self.rewrite(value)


if __name__ == "__main__":
    unittest.main()
