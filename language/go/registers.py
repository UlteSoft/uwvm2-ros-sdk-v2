"""@brief Lower checked Go compiler SSA to a core module containing only scalar operations."""
import re
from graphlib import TopologicalSorter

I32, I64 = 0x7f, 0x7e
TYPES = {"int32": I32, "uint32": I32, "int64": I64, "uint64": I64, "bool": I32}
OPS = {}
for bits, wasmtype, first in [(32, I32, 0x6a), (64, I64, 0x7c)]:
    for opname, offset in {"Add": 0, "Sub": 1, "Mul": 2, "And": 7, "Or": 8, "Xor": 9}.items():
        OPS[opname + str(bits)] = (first + offset, wasmtype, wasmtype)
    equal = 0x46 if bits == 32 else 0x51
    for opname, offset in {"Eq": 0, "Neq": 1, "Less": 2, "LessU": 3, "Leq": 6, "LeqU": 7}.items():
        spelling = opname.rstrip("U") + str(bits) + ("U" if opname.endswith("U") else "")
        OPS[spelling] = (equal + offset, wasmtype, I32)


def uleb(n):
    """@brief Encode one bounded unsigned core-Wasm field."""
    if not isinstance(n, int) or not 0 <= n <= 0xffffffff:
        raise ValueError("invalid unsigned Wasm field")
    out = bytearray()
    while n >= 128:
        out.append((n & 127) | 128)
        n >>= 7
    out.append(n)
    return bytes(out)


def sleb(n, bits):
    """@brief Encode a signed constant using Go fixed-width wraparound."""
    n &= (1 << bits) - 1
    if n >= 1 << (bits - 1):
        n -= 1 << bits
    out = bytearray()
    while True:
        byte = n & 127
        n >>= 7
        done = n == (-1 if byte & 64 else 0)
        out.append(byte if done else byte | 128)
        if done:
            return bytes(out)


def vector(entries):
    """@brief Encode a counted vector of core-Wasm values."""
    return uleb(len(entries)) + b"".join(entries)


def field(b):
    """@brief Encode a length-delimited Wasm payload."""
    return uleb(len(b)) + b


def function_type(params, result):
    """@brief Encode the exact scalar signature of a guest or approved host function."""
    return b"\x60" + vector([bytes([t]) for t in params]) + vector([bytes([result])] if result else [])


def lower(f):
    """@brief Check one optimized Go function and encode its Wasm locals and operations.
    @param f A scalar function exported by the pinned standard Go compiler.
    @return A core function type and a length-prefixed body.
    @details Every operation is checked, including values unused by the return.
    The initial memory token must reach the return unchanged. No linear memory
    exists in the generated module, so every tag operation can be elided.
    """
    name = f["name"]
    if not isinstance(name, str) or not re.fullmatch(r"[A-Za-z][A-Za-z0-9_]{0,63}", name):
        raise ValueError("compiler emitted a non-scalar Go function")
    params = [TYPES[p] for p in f["params"]]
    result = TYPES[f["result"]]
    values = f["values"]
    ids = {v["id"]: v for v in values}
    if len(params) > 32 or not 1 <= len(values) <= 1024 or len(ids) != len(values):
        raise ValueError("invalid Go SSA size or duplicate value")
    memory = [v["id"] for v in values if v["op"] == "InitMem"]
    returns = [v for v in values if v["op"] == "MakeResult"]
    if len(memory) != 1 or len(returns) != 1 or returns[0]["id"] != f["ret"]:
        raise ValueError("expected one immutable memory token and one return value")
    ret = returns[0]["args"]
    if (len(ret) != 2 or ret[1] != memory[0] or ids[memory[0]]["type"] != "mem"
            or returns[0]["type"] != f["result"] + ",mem" or ids[ret[0]]["type"] != f["result"]):
        raise ValueError("Go return depends on a memory effect or has the wrong scalar type")

    local_ids = {}
    locals_ = []
    code = bytearray()

    def get(v):
        code.extend(b"\x20" + uleb(local_ids[v]))

    def const(t, n):
        code.extend((b"\x41" if t == I32 else b"\x42") + sleb(n, 32 if t == I32 else 64))

    order = TopologicalSorter({n: v.get("args", []) for n, v in ids.items()}).static_order()
    for ident in order:
        v = ids[ident]
        op, args = v["op"], v.get("args", [])
        if (op == "InitMem" and not args) or op == "MakeResult":
            continue
        if op == "InlMark" and args == memory and v["type"] == "void":
            continue
        t = TYPES.get(v["type"])
        if t is None:
            raise ValueError(f"{name}: unsupported Go SSA type {v['type']}")
        if op == "Arg":
            index = v.get("index", 0)
            if args or v.get("literal", 0) or not 0 <= index < len(params) or f["params"][index] != v["type"]:
                raise ValueError("invalid compiler parameter binding")
            local_ids[v["id"]] = index
            continue
        if op == ("Const32" if t == I32 else "Const64") and not args:
            const(t, v.get("literal", 0))
        elif op == "ConstBool" and v["type"] == "bool" and not args and v.get("literal", 0) in (0, 1):
            const(I32, v.get("literal", 0))
        elif op in OPS and len(args) == 2:
            instruction, operand, output = OPS[op]
            if t != output or any(TYPES[ids[a]["type"]] != operand for a in args):
                raise ValueError("incorrect Go SSA operation signature")
            get(args[0])
            get(args[1])
            code.append(instruction)
        elif op in ("Neg32", "Neg64", "Com32", "Com64") and len(args) == 1:
            if TYPES[ids[args[0]]["type"]] != t or op[-2:] != ("32" if t == I32 else "64"):
                raise ValueError("incorrect Go SSA unary signature")
            negate = op.startswith("Neg")
            const(t, 0 if negate else -1)
            get(args[0])
            code.append((0x6b if t == I32 else 0x7d) if negate else (0x73 if t == I32 else 0x85))
        else:
            raise ValueError(f"{name}: {op} is outside the verified Go scalar instruction set")
        local_ids[v["id"]] = len(params) + len(locals_)
        locals_.append(bytes([1, t]))
        code.extend(b"\x21" + uleb(local_ids[v["id"]]))
    get(ret[0])
    return function_type(params, result), field(vector(locals_) + code + b"\x0b")


def module(records, ros_abi):
    """@brief Encode a memory-free core Wasm module from checked Go SSA.
    @param records All compiler-emitted functions in one guest package.
    @param ros_abi Whether to import uwvm_ros_v2.abi as the sole host query.
    @return Core Wasm bytes. Start returns zero for success; other values trap.
    """
    if len(records) > 128:
        raise ValueError("too many Go functions")
    records = sorted(records, key=lambda f: f["name"])
    names = [f["name"] for f in records]
    if len(set(names)) != len(names) or "Start" not in names:
        raise ValueError("define an entry function named Start")
    start = records[names.index("Start")]
    required = ["uint32"] if ros_abi else []
    if start["params"] != required or start["result"] != "uint32":
        raise ValueError("Start must return uint32 and accept " + ("one uint32 ABI argument" if ros_abi else "zero arguments"))
    compiled = [lower(f) for f in records]
    types = [function_type([], I32)] if ros_abi else []
    types.extend(t for t, _ in compiled)
    types.append(function_type([], None))
    imports = []
    if ros_abi:
        imports.append(field(b"uwvm_ros_v2") + field(b"abi") + b"\x00\x00")
    base = len(imports)
    exports = [field(n.encode()) + b"\x00" + uleb(base + i) for i, n in enumerate(names)]
    exports.append(field(b"_start") + b"\x00" + uleb(base + len(names)))
    bodies = [body for _, body in compiled]
    entry = (b"\x10\x00" if ros_abi else b"") + b"\x10" + uleb(base + names.index("Start"))
    bodies.append(field(b"\x00" + entry + b"\x04\x40\x00\x0b\x0b"))
    sections = [(1, types)]
    if imports:
        sections.append((2, imports))
    sections.extend([(3, [uleb(base + i) for i in range(len(bodies))]), (7, exports), (10, bodies)])
    return b"\0asm\x01\0\0\0" + b"".join(bytes([s]) + field(vector(entries)) for s, entries in sections)
