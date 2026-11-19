"""@brief Check per-guest Xmake receipt admission with positive and incomplete reports."""
from pathlib import Path
import unittest

from platform_projects import engine_results, passed_engines


class PlatformResults(unittest.TestCase):
    """@brief Require final evidence for each guest and each selected engine."""

    def test_passing_multi_guest(self):
        log = ("running.test extra/int\nreport of tests:\n"
               "\x1b[0m[ 25%]: body/aot passed 0.1s\n[ 50%]: body/int passed 0.1s\n"
               "[ 75%]: sensor/aot passed 0.1s\n[100%]: sensor/int passed 0.1s\n")
        self.assertEqual(passed_engines(log, [Path("body.wasm"), Path("sensor.wasm")]),
                         ["body/aot", "body/int", "sensor/aot", "sensor/int"])

    def test_both_engines_report_the_expected_trap(self):
        """@brief Reject a passing or missing engine in a deliberately failing guest test."""
        log = "report of tests:\n[ 50%]: sensor/aot failed\n[100%]: sensor/int failed"
        modules = [Path("sensor.wasm")]
        self.assertEqual(engine_results(log, modules, "failed"), ["sensor/aot", "sensor/int"])
        for mixed in (log.replace("int failed", "int passed"), log.splitlines()[0]):
            with self.assertRaises(ValueError):
                engine_results(mixed, modules, "failed")

    def test_running_skipped_duplicate_and_missing_do_not_pass(self):
        name = [Path("body.wasm")]
        for log in (
            "running.test body/int\nrunning.test body/aot",
            "report of tests:\n[ 0%]: body/int passed\n[100%]: body/aot skipped",
            "report of tests:\n[ 0%]: body/int passed\n[100%]: body/int passed",
            "running.test body/aot\nreport of tests:\n[100%]: body/int passed",
        ):
            with self.subTest(log=log):
                with self.assertRaises(ValueError):
                    passed_engines(log, name)


if __name__ == "__main__":
    unittest.main()
