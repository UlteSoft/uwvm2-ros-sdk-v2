"""Regression for direct inspection of the final linked core Wasm."""
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / "install"), str(ROOT / "language/csharp")]
from artifacts import MAGIC, sections, uleb
from scalar import prove_scalar


def section(kind, data):
    return bytes([kind]) + uleb(len(data)) + data


def kernel(instructions, extra=b""):
    code = b"\x00" + instructions + b"\x0b"
    return (MAGIC + section(1, bytes.fromhex("0160017f017f")) + section(3, b"\x01\x00")
            + section(5, b"\x01\x01\x01\x01") + extra + section(7, b"\x01\x08evaluate\x00\x00")
            + section(10, b"\x01" + uleb(len(code)) + code))


class RegisterOnlyKernel(unittest.TestCase):
    def test_constant_and_debug_payload_do_not_execute(self):
        source = kernel(bytes.fromhex("4128")) + section(0, b"\x05debug\x28\xfe\x00")
        result = prove_scalar(source)
        self.assertEqual([result[start] for start, _, _, _ in sections(result)], [1, 3, 7, 10, 0])
        self.assertTrue(result.endswith(b"debug\x28\xfe\x00"))

    def test_memory_and_other_effects_fail_closed(self):
        for code in ("2000280200", "0041004100360200", "3f00", "4000", "1000",
                     "2300", "fc0a0000", "fe100200", "fb0000", "ffc080840800", "0b4128"):
            with self.subTest(code=code), self.assertRaises(ValueError):
                prove_scalar(kernel(bytes.fromhex(code)))

    def test_other_executable_state_cannot_survive(self):
        for extra in (section(8, b"\x00"), section(3, b"\x01\x00"), section(11, b"\x00"),
                      section(6, bytes.fromhex("017f0041000b"))):
            with self.subTest(extra=extra), self.assertRaises(ValueError):
                prove_scalar(kernel(b"\x20\x00", extra))
