"""Exercise the installed-style CLI against scoped legacy observation grants."""
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

REVIEWER = Path(os.environ.get("WROS_TEST_LEGACY_PERMISSION_REVIEWER",
                              Path(__file__).resolve().parents[2] / "tools/migration/legacy_permissions.py"))
spec = importlib.util.spec_from_file_location("legacy_permissions", REVIEWER)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


def grants(backend="ros1", scope="global", target="robots", observation="service.available",
           source="service.call", ref="call", declared_resource="/solver"):
    prefix = "--" + backend + "-" + scope + "-"
    who = [] if scope == "global" else [target]
    args = [prefix + "grant", *who, "call", source, declared_resource, "example/Solve", "type-hash",
            prefix + "grant", *who, "observe", observation, "/solver", "example/Solve", "type-hash"]
    def put(alias, field, value):
        args.extend([prefix + "set", *who, alias, field, value])
    if ref:
        put("observe", module.PAIRS[observation], ref)
    if observation == "service.available" and backend == "ros2":
        # Effective RMW values used by the old native_graph_availability test.
        qos = {"qos.reliability":"reliable", "qos.durability":"volatile", "qos.history":"keep-last",
               "qos.depth":"4", "qos.deadline":"infinite", "qos.lifespan":"infinite",
               "qos.liveliness":"automatic", "qos.liveliness-lease-duration":"infinite"}
        for alias in ("call", "observe"):
            for field, value in qos.items():
                put(alias, field, value)
    if observation == "event.observe":
        put("observe", "event-kinds", "service-response,resource-closed")
    return args


class Policy(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        default = Path(__file__).resolve().parents[2] / ".tmp"
        configured = Path(os.environ.get("TMPDIR", default)).resolve()
        cls.scratch = configured if ".tmp" in configured.parts else default
        cls.scratch.mkdir(parents=True, exist_ok=True)

    def run_cli(self, raw, exit_code):
        with tempfile.TemporaryDirectory(dir=self.scratch) as name:
            policy = Path(name) / "args.json"
            policy.write_bytes(raw)
            result = subprocess.run([sys.executable, "-I", "-B", REVIEWER, policy], capture_output=True)
        self.assertEqual(result.returncode, exit_code, result.stderr)
        return result

    def test_scoped_pairs(self):
        for backend in ("ros1", "ros2"):
            for target in ("global", "single", "group"):
                for op in module.PAIRS:
                    with self.subTest(backend=backend, target=target, op=op):
                        args = grants(backend=backend, scope=target, observation=op)
                        row, = json.loads(self.run_cli(json.dumps(args).encode(), 2).stdout)["findings"]
                        self.assertEqual((row["backend"], row["scope"], row["field"], row["source"]),
                                         (backend, target, module.PAIRS[op], "call"))
                        expected = (["review-service-observer-client-binding-and-native-wait",
                                     "independent-service-query-and-call-authority-required"] if op == "service.available"
                                    else ["independent-event-observer-and-source-authority-required"])
                        self.assertEqual(row["reasons"], expected)

    def test_no_cross_target_binding(self):
        for prefix in ("--ros2-group-grant", "--ros1-single-grant", "--ros1-group-grant"):
            setup = grants(scope="group")
            setup[0] = prefix
            if prefix == "--ros1-group-grant":
                setup[1] = "another"
            row, = module.review(setup)["findings"]
            self.assertIn("missing-source-in-same-backend-and-target", row["reasons"])

    def test_specific_findings(self):
        for args, issue in (
            (grants(ref=None), "missing-source-alias"), (grants(ref="observe"), "source-is-observer"),
            (grants(declared_resource="/other"), "resource-mismatch"), (grants(source="topic.publish"), "source-is-not-service-call"),
            (grants(observation="event.observe", source="topic.publish"), "event-payload-exceeds-source-operation"),
        ):
            with self.subTest(issue=issue):
                self.assertIn(issue, module.review(args)["findings"][0]["reasons"])
        for before, after, code in (("type-hash", "wrong-hash", "service-type-or-identity-mismatch"),
                                     ("service-response,resource-closed", "resource-closed,service-response",
                                      "missing-or-invalid-ordered-event-kinds")):
            args = grants(observation="event.observe" if "," in before else "service.available")
            args[args.index(before)] = after
            self.assertIn(code, module.review(args)["findings"][0]["reasons"])
        args = grants() + ["--ros1-global-set", "call", "adapter-codec-identity", "my-codec"]
        self.assertIn("codec-identity-mismatch", module.review(args)["findings"][0]["reasons"])
        args = grants(backend="ros2")
        args[args.index("qos.depth") + 1] = "other"
        self.assertIn("missing-or-mismatched-qos.depth", module.review(args)["findings"][0]["reasons"])
        args = ["keep-all" if v == "keep-last" else v for v in args]
        self.assertNotIn("missing-or-mismatched-qos.depth", module.review(args)["findings"][0]["reasons"])

    def test_no_grant_emission(self):
        result = self.run_cli(b'["--ros2-global-grant","telemetry","topic.subscribe","/a","pkg/A","hash"]', 0)
        self.assertEqual(json.loads(result.stdout)["result"], "no-paired-observer-declarations")
        self.assertNotIn("grants", json.loads(result.stdout))
        self.assertEqual(module.review([])["findings"], [])

    @unittest.skipUnless(hasattr(os, "mkfifo"), "FIFO test requires POSIX")
    def test_nonregular_input(self):
        with tempfile.TemporaryDirectory(dir=self.scratch) as name:
            path = Path(name) / "input"
            os.mkfifo(path)
            result = subprocess.run([sys.executable, "-I", "-B", REVIEWER, path], capture_output=True, timeout=3)
            self.assertEqual(result.returncode, 3)
            self.assertFalse(result.stdout)

    def test_refusal(self):
        for raw in [b"{}", b"not-json", b"\xff", b" " * (1024*1024+1), b'["--not-a-ros-option"]',
                    b'["--ros1-global-set","a","service-source-alias","b"]',
                    b'["--ros2-group-create"]', b'["--ros2-global-add-module","x"]',
                    json.dumps(grants()+["--ros1-global-set","observe","service-source-alias","call"]).encode()]:
            with self.subTest(length=len(raw)):
                self.assertEqual(self.run_cli(raw, 3).stdout, b"")


if __name__ == "__main__":
    unittest.main()
