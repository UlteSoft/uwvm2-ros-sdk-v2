"""@brief Lower checked Go compiler SSA to a core module containing only scalar operations."""
import json
import re
from graphlib import TopologicalSorter

I32, I64 = 0x7f, 0x7e
TYPES = {"int32": I32, "uint32": I32, "int64": I64, "uint64": I64, "bool": I32}
OPS = {}
SHIFTS = {}
CONVERSIONS = {
    "Trunc64to32": (I64, I32, 0xa7),
    "SignExt32to64": (I32, I64, 0xac),
    "ZeroExt32to64": (I32, I64, 0xad),
}
ROTATIONS = {"RotateLeft32": (I32, 0x77), "RotateLeft64": (I64, 0x89)}
BOOL_OPS = {"EqB": 0x46, "NeqB": 0x47, "AndB": 0x71, "OrB": 0x72}
for bits, wasmtype, first in [(32, I32, 0x6a), (64, I64, 0x7c)]:
    for opname, offset in {"Add": 0, "Sub": 1, "Mul": 2, "And": 7, "Or": 8, "Xor": 9}.items():
        OPS[opname + str(bits)] = (first + offset, wasmtype, False)
    equal = 0x46 if bits == 32 else 0x51
    for opname, offset in {"Eq": 0, "Neq": 1, "Less": 2, "LessU": 3, "Leq": 6, "LeqU": 7}.items():
        spelling = opname.rstrip("U") + str(bits) + ("U" if opname.endswith("U") else "")
        OPS[spelling] = (equal + offset, wasmtype, True)
    for count_bits, count_type in ((32, I32), (64, I64)):
        for op, instruction, signed in (("Lsh", first + 10, False), ("Rsh", first + 11, True),
                                        ("RshU", first + 12, False)):
            name = op.rstrip("U") + str(bits) + ("U" if op.endswith("U") else "") + "x" + str(count_bits)
            SHIFTS[name] = (wasmtype, count_type, bits, instruction, signed)


def register_type(value):
    """@brief Read the scalar width of an SSA value without widening the guest ABI."""
    # The pinned Go Wasm frontend supplies untyped constant shift counts as
    # word-sized uint values. Keep machine-word types out of public signatures.
    if value["op"] == "Const64" and value["type"] == "uint":
        return I64
    return TYPES[value["type"]]


def same_representation(left, right):
    """@brief Allow integer signedness aliases while keeping bool distinct."""
    return left == right or ("bool" not in (left, right) and TYPES[left] == TYPES[right])


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


def control_flow(entry, rows):
    """@brief Validate a forward-only scalar control-flow graph and its edge ordinals."""
    blocks = {row["id"]: row for row in rows}
    if not 1 <= len(rows) <= 64 or len(blocks) != len(rows) or entry not in blocks:
        raise ValueError("invalid Go block count, duplicate block or missing entry")
    predecessors = {}
    for ident, block in blocks.items():
        count = block["predecessors"]
        if not 0 <= count <= 128 or (ident == entry) != (count == 0):
            raise ValueError("invalid Go block entry or predecessor count")
        predecessors[ident] = [None] * count
    for ident, block in blocks.items():
        edges = block.get("succs", [])
        kind = block["kind"]
        if len(edges) != {"Ret": 0, "Plain": 1, "If": 2}.get(kind, -1):
            raise ValueError("invalid Go block terminator")
        if ("control" in block) != (kind != "Plain"):
            raise ValueError("invalid Go block control")
        for edge in edges:
            pred = predecessors[edge["block"]]
            index = edge["index"]
            if not 0 <= index < len(pred) or pred[index] is not None:
                raise ValueError("invalid or duplicate Go predecessor edge")
            pred[index] = ident
    if any(None in pred for pred in predecessors.values()):
        raise ValueError("missing Go predecessor edge")
    # Every nonentry block has a predecessor. A DAG with only one such root
    # has no disconnected components, and every edge targets a later block.
    return blocks, predecessors, list(TopologicalSorter(predecessors).static_order())


def lower(f, locations=None):
    """@brief Check one optimized Go function and encode its Wasm locals and operations.
    @param f A scalar function exported by the pinned standard Go compiler.
    @param locations Optional list receiving source rows relative to the encoded body.
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
    entry = f["entry"]
    blocks, predecessors, order = control_flow(entry, f["blocks"])
    values = [v for block in blocks.values() for v in block["values"]]
    ids = {v["id"]: v for v in values}
    if len(params) > 32 or not 1 <= len(values) <= 1024 or len(ids) != len(values):
        raise ValueError("invalid Go SSA size or duplicate value")
    memory = [v["id"] for v in values if v["op"] == "InitMem"]
    if (len(memory) != 1 or ids[memory[0]]["type"] != "mem"
            or ids[memory[0]].get("args") or ids[memory[0]] not in blocks[entry]["values"]):
        raise ValueError("expected one immutable Go memory token in the entry")

    local_ids = {}
    locals_ = []
    code = bytearray()
    points = {}
    live_out = {}
    positions = {ident: index for index, ident in enumerate(order)}
    phis = {ident: [v for v in block["values"] if v["op"] == "Phi"]
            for ident, block in blocks.items()}

    def get(v):
        code.extend(b"\x20" + uleb(local_ids[v]))

    def const(t, n):
        code.extend((b"\x41" if t == I32 else b"\x42") + sleb(n, 32 if t == I32 else 64))

    def mark(position=None):
        """@brief Attribute emitted bytes to an original Go position or a generated gap."""
        if locations is not None:
            points[len(code)] = position

    def reserve(v, t):
        local_ids[v["id"]] = len(params) + len(locals_)
        locals_.append(bytes([1, t]))

    def emit_shift(v, t, args):
        """@brief Lower shifts without dropping the unmasked Go count."""
        operand, count, width, instruction, signed = SHIFTS[v["op"]]
        base, amount = args
        if (t != operand or ids[base]["type"] == "bool" or v["type"] == "bool"
                or register_type(ids[base]) != operand or register_type(ids[amount]) != count
                or ids[amount]["type"] == "bool"
                or v.get("literal", 0) not in (0, 1)):
            raise ValueError("incorrect Go SSA shift signature")
        literal = ids[amount].get("literal", 0)
        bounded = ids[amount]["op"] in ("Const32", "Const64") and 0 <= literal < width
        get(base)
        get(amount)
        if count != operand:
            code.append(0xa7 if operand == I32 else 0xad)  # wrap or zero extend
        if bounded:
            code.append(instruction)
            return
        if not signed:
            code.append(instruction)
        const(operand, width - 1 if signed else 0)
        get(amount)
        const(count, width)
        # A sign-only cast can leave its original SSA type on the count. The
        # Go frontend emits a distinct control path for negative-count panics,
        # which the register-only profile does not admit. The pure shift here
        # uses the count bits as unsigned, including bits a Wasm shift masks.
        code.extend(bytes([0x49 if count == I32 else 0x54, 0x1b]))
        if signed:
            code.append(instruction)

    def emit_scalar(v, t):
        """@brief Lower one validated scalar value using Wasm locals and numeric ops."""
        op, args = v["op"], v.get("args", [])
        if op == "Arg":
            index = v.get("index", 0)
            if args or v.get("literal", 0) or not 0 <= index < len(params) or f["params"][index] != v["type"]:
                raise ValueError("invalid compiler parameter binding")
            if v["type"] != "bool":
                local_ids[v["id"]] = index
                return
            # The Wasm ABI admits arbitrary i32 arguments for Go bool parameters.
            # Normalize nonzero values before further use at internal SSA sites.
            code.extend(b"\x20" + uleb(index) + b"\x45\x45")
        elif v["type"] != "bool" and op == ("Const32" if t == I32 else "Const64") and not args:
            const(t, v.get("literal", 0))
        elif op == "ConstBool" and v["type"] == "bool" and not args and v.get("literal", 0) in (0, 1):
            const(I32, v.get("literal", 0))
        elif op in BOOL_OPS and len(args) == 2 and v["type"] == "bool" and all(
                ids[a]["type"] == "bool" for a in args):
            get(args[0])
            get(args[1])
            code.append(BOOL_OPS[op])
        elif op in OPS and len(args) == 2:
            instruction, operand, comparison = OPS[op]
            if (t != (I32 if comparison else operand) or comparison != (v["type"] == "bool")
                    or any(ids[a]["type"] == "bool" or register_type(ids[a]) != operand for a in args)):
                raise ValueError("incorrect Go SSA operation signature")
            get(args[0])
            get(args[1])
            code.append(instruction)
        elif op in SHIFTS and len(args) == 2:
            emit_shift(v, t, args)
        elif op in ROTATIONS and len(args) == 2:
            operand, instruction = ROTATIONS[op]
            amount = register_type(ids[args[1]])
            if (t != operand or register_type(ids[args[0]]) != operand or v["type"] == "bool"
                    or any(ids[a]["type"] == "bool" for a in args) or v.get("literal", 0)):
                raise ValueError("incorrect Go SSA rotation signature")
            get(args[0])
            get(args[1])
            if amount != t:
                code.append(0xa7 if t == I32 else 0xad)
            code.append(instruction)
        elif op in CONVERSIONS and len(args) == 1:
            operand, result, instruction = CONVERSIONS[op]
            if (t != result or register_type(ids[args[0]]) != operand or v["type"] == "bool"
                    or ids[args[0]]["type"] == "bool" or v.get("literal", 0)):
                raise ValueError("incorrect Go SSA integer conversion signature")
            get(args[0])
            code.append(instruction)
        elif op in ("Neg32", "Neg64", "Com32", "Com64") and len(args) == 1:
            if (v["type"] == "bool" or ids[args[0]]["type"] == "bool"
                    or TYPES[ids[args[0]]["type"]] != t or op[-2:] != ("32" if t == I32 else "64")):
                raise ValueError("incorrect Go SSA unary signature")
            negate = op.startswith("Neg")
            const(t, 0 if negate else -1)
            get(args[0])
            code.append((0x6b if t == I32 else 0x7d) if negate else (0x73 if t == I32 else 0x85))
        elif op in ("Copy", "Not") and len(args) == 1 and same_representation(ids[args[0]]["type"], v["type"]):
            get(args[0])
            if op == "Not":
                if v["type"] != "bool":
                    raise ValueError("Go logical negation requires bool")
                code.append(0x45)  # i32.eqz
        else:
            raise ValueError(f"{name}: {op} is outside the verified Go scalar instruction set")
        reserve(v, t)
        code.extend(b"\x21" + uleb(local_ids[v["id"]]))

    for ident, rows in phis.items():
        for value in rows:
            args = value.get("args", [])
            if (not args or len(args) != len(predecessors[ident]) or any(
                    not same_representation(ids[arg]["type"], value["type"]) for arg in args)):
                raise ValueError("Go phi operands must match its predecessor edges and scalar type")
            reserve(value, TYPES[value["type"]])

    def jump(edge, here, conditional):
        """@brief Apply exactly the selected edge's phi assignments before branching."""
        for value in phis[edge["block"]]:
            operand = value["args"][edge["index"]]
            if operand not in live_out[order[here]]:
                raise ValueError("Go phi operand is unavailable on its predecessor edge")
            get(operand)
            code.extend(b"\x21" + uleb(local_ids[value["id"]]))
        depth = positions[edge["block"]] - here - 1
        if conditional or depth:
            code.extend(b"\x0c" + uleb(depth + conditional))

    # Every enclosing Wasm block ends where its forward target begins. An
    # immediate unconditional successor uses fallthrough as the fast path.
    code.extend(b"\x02\x40" * (len(order) - 1))
    for here, ident in enumerate(order):
        if here:
            mark()
            code.append(0x0b)  # end the block targeting this position
        block = blocks[ident]
        kind = block["kind"]
        pred = predecessors[ident]
        live = set.intersection(*(live_out[p] for p in pred)) if pred else set()
        live.update(phi["id"] for phi in phis[ident])
        rows = {v["id"]: v for v in block["values"] if v["op"] != "Phi"}
        local_order = TopologicalSorter({i: [a for a in v.get("args", []) if a in rows]
                                        for i, v in rows.items()}).static_order()
        terminator = block.get("control")
        ret = None
        for value_id in local_order:
            v = rows[value_id]
            op, args = v["op"], v.get("args", [])
            if op == "InitMem" or (op == "InlMark" and args == memory and v["type"] == "void"):
                continue
            if op == "MakeResult":
                if (kind != "Ret" or value_id != terminator or len(args) != 2 or args[1] != memory[0]
                        or args[0] not in live or not same_representation(ids[args[0]]["type"], f["result"])
                        or v["type"] != f["result"] + ",mem"):
                    raise ValueError("Go return changes the memory token or uses an unavailable scalar")
                ret = args[0]
                continue
            if any(a not in live for a in args):
                raise ValueError("Go scalar operand does not dominate its use")
            begin = len(code)
            emit_scalar(v, register_type(v))
            if locations is not None and begin < len(code):
                # An existing argument is an SSA alias with no emitted code.
                points[begin] = v.get("source")
            live.add(value_id)
        live_out[ident] = live
        if kind == "Ret":
            if ret is None:
                raise ValueError("Go return lacks a scalar and its original memory token")
            mark(block.get("source"))
            get(ret)
            if here < len(order) - 1:
                code.append(0x0f)  # return
        elif kind == "Plain":
            mark()
            jump(block["succs"][0], here, False)
        else:
            if terminator not in live or ids[terminator]["type"] != "bool":
                raise ValueError("Go branch requires an available boolean")
            mark(block.get("source"))
            get(terminator)
            code.extend(b"\x04\x40")
            mark()
            jump(block["succs"][0], here, True)
            code.append(0x05)
            jump(block["succs"][1], here, True)
            code.append(0x0b)
    mark()
    local_prefix = vector(locals_)
    payload = local_prefix + code + b"\x0b"
    if locations is not None:
        expression = len(uleb(len(payload))) + len(local_prefix)
        locations.extend((expression + offset, origin) for offset, origin in points.items())
    return function_type(params, result), field(payload)


def source_map(path, source, points):
    """@brief Encode genuine Go frontend positions with absolute Wasm byte offsets."""
    lines = source.split(b"\n")
    alphabet = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/"

    def vlq(delta):
        word = abs(delta) * 2 + int(delta < 0)
        digits = []
        while word >= 32:
            digits.append(alphabet[(word & 31) | 32])
            word >>= 5
        digits.append(alphabet[word])
        return "".join(digits)

    mapped = []
    previous = 0
    line = column = 0
    active = None
    for offset, origin in points:
        if origin is None:
            if active is None:
                continue
            mapped.append(vlq(offset - previous))
            active = None
        else:
            row, byte_column = origin["line"] - 1, origin["column"] - 1
            if not 0 <= row < len(lines) or not 0 <= byte_column <= len(lines[row]):
                raise ValueError("Go debug position outside the source snapshot")
            left_text = lines[row][:byte_column].decode("utf-8")
            col = len(left_text.encode("utf-16-le")) // 2
            if active == (row, col):
                continue
            mapped.append(vlq(offset - previous) + "A" + vlq(row - line) + vlq(col - column))
            line, column = row, col
            active = (row, col)
        previous = offset
    if not mapped:
        raise ValueError("Go frontend emitted no usable source positions")
    return json.dumps({"version": 3, "sources": [path], "names": [], "mappings": ",".join(mapped)},
                      ensure_ascii=False, separators=(",", ":")).encode("utf-8")


def module(records, ros_abi, *, debug_source=None):
    """@brief Encode a memory-free core Wasm module from checked Go SSA.
    @param records All compiler-emitted functions in one guest package.
    @param ros_abi Whether to import uwvm_ros_v2.abi as the sole host query.
    @param debug_source Original path and source bytes for an optional source map.
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
    locations = [[] for _ in records] if debug_source is not None else [None] * len(records)
    compiled = [lower(f, positions) for f, positions in zip(records, locations)]
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
    sections.extend([(3, [uleb(base + i) for i in range(len(bodies))]), (7, exports)])
    function_names = (["uwvm_ros_v2.abi"] if ros_abi else []) + names + ["_start"]
    symbols = vector([uleb(i) + field(name.encode("ascii")) for i, name in enumerate(function_names)])
    prefix = b"\0asm\x01\0\0\0" + b"".join(bytes([s]) + field(vector(entries)) for s, entries in sections)
    code = vector(bodies)
    result = prefix + b"\x0a" + field(code) + b"\0" + field(field(b"name") + b"\x01" + field(symbols))
    if debug_source is not None:
        first_body = len(prefix) + 1 + len(uleb(len(code))) + len(uleb(len(bodies)))
        points = []
        for body, function_locations in zip(bodies, locations):
            points.extend((first_body + pc, origin) for pc, origin in function_locations)
            first_body += len(body)
        mapping = source_map(*debug_source, points)
        result += b"\0" + field(field(b".debug_source_map") + mapping)
    return result
