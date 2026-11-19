#!/usr/bin/python3
"""@brief Record only the selected engine and platform before executing the SDK VM test runner."""
import json
import os
import sys

args = sys.argv[1:]
if args and args[0].endswith("/tools/xmake/run_guest.py") and "--driver-denial" in args and "--engine" in args:
    row = [args[args.index("--engine") + 1], args[args.index("--driver-denial") + 1]]
    with open(os.environ["WROS_TEST_DRIVER_TRACE"], "a", encoding="utf-8") as stream:
        stream.write(json.dumps(row) + "\n")
os.execv(sys.executable, [sys.executable, *args])
