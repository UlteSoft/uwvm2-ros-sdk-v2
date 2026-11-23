"""Run a Python package on the guest VM and read the explicitly exposed ABI."""
import sys
from collections import Counter
from uwrosv2.capability import wr_abi
from samples import averages

assert sys.implementation.name == "cpython" and sys.version_info[:3] == (3, 14, 8)
assert wr_abi() == 2
assert Counter(averages([[2, 4], [3, 3], [8]])) == {3.0: 2, 8.0: 1}
print("CPython 3.14.8 guest: package and ABI verified")
