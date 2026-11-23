#!/usr/bin/env python3
"""Run the source frontend selected by the installed command name."""
from pathlib import Path
import runpy
import sys

command = Path(__file__).resolve()
language = {"wras": "as", "wrjs": "js", "wrts": "typescript"}[command.name]
sys.dont_write_bytecode = True
runpy.run_path(str(command.parents[1] / "src/compilers" / language / "driver.py"), run_name="__main__")
