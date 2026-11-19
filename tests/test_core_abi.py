"""The SDK admits core guests and P1 by exact signature. Component inputs fail at every build boundary."""
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "install"))
import artifacts
from frontend import audit
from guest_profile import Profile
from imports import inspect
sys.path.insert(0, str(ROOT / "tools/xmake"))
from run_guest import require_test_entry, resolve_test_queries

CORE = artifacts.MAGIC
COMPONENT = b"\0asm\x0d\x00\x01\x00"
PROFILE = Profile(32)
DIGEST = "a" * 64


def name(s):
    data = s.encode()
    return artifacts.uleb(len(data)) + data


def section(number, body):
    return bytes([number]) + artifacts.uleb(len(body)) + body


def fn_import(module, field, params=b"", results=b"\x7f"):
    signature = b"\x60" + bytes([len(params)]) + params + bytes([len(results)]) + results
    return CORE + section(1, b"\1" + signature) + section(2, b"\1" + name(module) + name(field) + b"\0\0")


def fn_export(field):
    return (CORE + section(1, b"\1\x60\0\0") + section(3, b"\1\0")
            + section(7, b"\1" + name(field) + b"\0\0") + section(10, b"\1\2\0\x0b"))


class CoreAbi(unittest.TestCase):
    def test_kinds_and_component_metadata(self):
        for module in (COMPONENT, COMPONENT + section(1, CORE),
                       CORE + section(0, name("component-type:example") + COMPONENT),
                       CORE + section(0, name("component-type") + b"metadata"),
                       CORE + section(0, name("component-name"))):
            with self.subTest(module=module), self.assertRaisesRegex(ValueError, "Component Model"):
                inspect(module)

    def test_imports_and_exports(self):
        for module, field in [("wasi:io/streams@0.2.3", "read"), ("wasi:sockets/tcp@0.3.0", "connect"),
                              ("example:robot/sensors@1.2.0", "read"), ("cm32p2", "foo"), ("cm32p3", "bar"), ("env", "wasi:io/streams@0.2.0#read"),
                              ("wasi_snapshot_preview2", "x"), ("wasip3", "x")]:
            with self.subTest(module=module, field=field), self.assertRaisesRegex(ValueError, "prohibited"):
                inspect(fn_import(module, field))
        for symbol in ("cabi_realloc", "[resource-drop]sensor", "example:robot/sensors#read", "cm32p2|wasi:cli/run|run", "wasi:cli/run@0.3.0#run"):
            with self.subTest(symbol=symbol), self.assertRaisesRegex(ValueError, "prohibited"):
                audit(fn_export(symbol), PROFILE)

    def test_relocatable_and_archive(self):
        linking = section(0, name("linking") + b"\2")
        clean = artifacts.seal_object(CORE + linking, PROFILE.to_dict(), DIGEST, DIGEST)
        artifacts.check_object(clean)
        bad = fn_import("wasi:io/streams@0.2.0", "read") + linking
        with self.assertRaisesRegex(ValueError, "prohibited"):
            artifacts.seal_object(bad, PROFILE.to_dict(), DIGEST, DIGEST)
        # Assemble a legacy, correctly digested note; the independent consumer must reject it.
        import hashlib
        note = dict(schema=artifacts.NOTE, profile=PROFILE.to_dict(), compiler_sha256=DIGEST,
                    closure_sha256=DIGEST, object_sha256=hashlib.sha256(bad).hexdigest())
        bad += section(0, name(artifacts.NOTE) + json.dumps(note).encode())
        with self.assertRaisesRegex(ValueError, "prohibited"):
            artifacts.check_object(bad)
        def member(label, data):
            header = f"{label+'/':<16}{0:<12}{0:<6}{0:<6}{'644':<8}{len(data):<10}".encode() + b"`\n"
            return header + data + (b"\n" if len(data) % 2 else b"")
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "combined.a"
            path.write_bytes(b"!<arch>\n" + member("ok.o", clean) + member("unused.o", bad))
            with self.assertRaisesRegex(ValueError, "prohibited"):
                artifacts.stage_inputs([path], Path(td), PROFILE.to_dict(), DIGEST, DIGEST, Path(td))

    def test_operator_can_narrow_project_queries(self):
        """@brief Verify default, explicit denial and disjoint operator permissions."""
        self.assertEqual(resolve_test_queries("abi", None), ["abi"])
        self.assertEqual(resolve_test_queries("abi", ""), [])
        self.assertEqual(resolve_test_queries("abi", "monotonic-clock"), [])
        self.assertEqual(resolve_test_queries("abi", "abi,realtime-clock"), ["abi"])
        self.assertEqual(resolve_test_queries(None, "monotonic-clock"), ["monotonic-clock"])
        with self.assertRaises(ValueError):
            resolve_test_queries("abi", "misspelling")

    def test_execution_requires_guest_code(self):
        """@brief Count only modules with local executable test entry points."""
        typ = section(1, bytes.fromhex("01 60 00 00"))
        funcs = section(3, bytes.fromhex("01 00"))
        code = section(10, bytes.fromhex("01 02 00 0b"))
        export = section(7, b"\x01" + name("_start") + b"\x00\x00")
        imported = section(2, b"\x01" + name("uwvm_ros_v2") + name("abi") + b"\x00\x00")
        require_test_entry(CORE + typ + funcs + export + code)
        require_test_entry(CORE + typ + funcs + section(8, b"\x00") + code)
        for module in (CORE, CORE + typ + funcs + code, CORE + typ + imported + export,
                       CORE + typ + imported + funcs + section(8, b"\x00") + code):
            with self.assertRaisesRegex(ValueError, "module-defined"):
                require_test_entry(module)

    def test_core_remains_usable(self):
        audit(fn_import("uwvm_ros_v2", "abi"), PROFILE)
        audit(fn_import("wasi_snapshot_preview1", "clock_time_get", b"\x7f\x7e\x7f"), PROFILE)
        audit(fn_import("wasi_snapshot_preview1", "clock_time_get_wasm64", b"\x7f\x7e\x7e"), Profile(64))
        audit(fn_import("wasi", "thread-spawn", b"\x7f"), Profile(32, threads=True))
        audit(fn_export("_start") + section(0, name("debug") + b"wasi: component-type cabi_realloc"), PROFILE)

    def test_xmake_runner(self):
        with tempfile.TemporaryDirectory() as td:
            base = Path(td)
            spy = base / "vm"
            spy.write_text('#!/bin/sh\nfor arg do last="$arg"; done\ncat "$last"\n')
            spy.chmod(0o700)
            for content, ok in [(COMPONENT, False), (fn_export("cabi_realloc"), False), (fn_export("_start"), True)]:
                guest = base / "guest.wasm"
                guest.write_bytes(content)
                result = subprocess.run([sys.executable, ROOT / "tools/xmake/run_guest.py", guest, "wasm32", "3.0", "single"],
                                        env={**os.environ, "WROS_VM": str(spy)}, capture_output=True)
                self.assertEqual(result.returncode == 0, ok, result.stderr)
                self.assertEqual(result.stdout, content if ok else b"")


if __name__ == "__main__":
    unittest.main()
