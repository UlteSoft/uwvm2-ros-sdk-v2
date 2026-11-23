"""Resolve language bindings in the checkout or a single installed platform selection."""
import json
import os
from pathlib import Path
import re
import sys

COMPILERS = Path(__file__).resolve().parent
ROOT = COMPILERS.parents[1]
SDK = Path(os.environ.get("UWVM_ROS_SDK_ROOT", ROOT)).resolve()
INCLUDE = ROOT / "include/u2rosv2"
C_BACKEND = ROOT / "libexec/quickjs-c"
JS_BACKEND = ROOT / "libexec/quickjs-modules"
CONTRACT = ROOT / "src/abi/contract.json"
if not CONTRACT.is_file():
    CONTRACT = ROOT / "share/abi/ros.json"

policy = COMPILERS / "cc/policy"
if not policy.is_dir():
    policy = C_BACKEND / "install" if C_BACKEND.is_dir() else SDK / "install"
sys.path.insert(0, str(policy))


def selected_platform(requested=None):
    """An installed tool sees exactly its selected platform. A checkout can select one explicitly."""
    receipt = ROOT / "selection.json"
    if receipt.is_file():
        installed = json.loads(receipt.read_bytes())["platform"]
        if requested is not None and requested != installed:
            raise ValueError("platform differs from the installed selection")
        requested = installed
    name = "generic" if requested is None else requested
    if not re.fullmatch(r"[a-z0-9][a-z0-9_-]*", name) or not (ROOT / "platform" / name / "platform.json").is_file():
        raise ValueError("unknown SDK platform: " + name)
    return name


def include_root(language):
    """TypeScript embeds JS modules and QuickJS compiles C headers as private dependencies."""
    if language == "js" and JS_BACKEND.is_dir():
        return JS_BACKEND / "include/u2rosv2"
    if language == "c" and C_BACKEND.is_dir():
        return C_BACKEND / "include/u2rosv2"
    return INCLUDE


def native(name):
    """The installed ECMAScript tools carry their own wasm32 C backend."""
    path = (C_BACKEND if C_BACKEND.is_dir() else SDK) / "bin" / name
    if not path.is_file() or not os.access(path, os.X_OK):
        raise ValueError(f"{name} requires a native WROS installation; set UWVM_ROS_SDK_ROOT")
    return path
