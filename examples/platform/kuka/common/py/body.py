"""@brief Verify the ROSv2 ABI from an isolated CPython guest."""
import wros

assert wros.abi() == 2
