"""Allocation-free typed facades for capability handles and VM scheduling resources."""


def scoped_enum(name, underlying, values):
    """Keep the scoped spellings on C++98, which has no enum class."""
    fields = ",\n".join(f"    {key} = {value}" for key, value in values.items())
    return f"""#if __cplusplus >= 201103L
enum class {name} : {underlying} {{
#else
class {name} {{
    {underlying} value_;
public:
    enum code {{
#endif
{fields}
#if __cplusplus >= 201103L
}};
#else
    }};
    {name}(code v = {next(iter(values))}) throw() : value_(v) {{}}
    explicit {name}({underlying} v) throw() : value_(v) {{}}
    operator {underlying}() const throw() {{ return value_; }}
}};
#endif"""


CAP_C = """/**
 * Open an exact deployed alias in memory zero. The VM publishes the capability
 * only after successful delivery. Close the capability explicitly after use.
 */
static inline uint32_t uwrosv2_capability_open(uwrosv2_text alias, uwrosv2_capability *out) UWROSV2_C_NOEXCEPT {
    uint8_t id[8] = {0};
    if (!out || !alias.data || !alias.size || alias.size > 255) return 22;
    uint32_t code = uwrosv2_raw_capability_open(0, uwrosv2_address(alias.data), alias.size, uwrosv2_address(id));
    if (code) return code;
    uint64_t handle = uwrosv2_read_le64(id);
    if (!handle) return 22;
    out->id = handle;
    return 0;
}
/** Retire the environment capability; keep its id on failure for recovery. */
static inline uint32_t uwrosv2_capability_close(uwrosv2_capability *cap) UWROSV2_C_NOEXCEPT {
    if (!cap || !cap->id) return 9;
    uint32_t code = uwrosv2_raw_capability_close(cap->id);
    if (!code) cap->id = 0;
    return code;
}
/** A return value of 2 identifies this ABI. Exposure or resource errors share the i32 result. */
static inline uint32_t uwrosv2_abi(void) UWROSV2_C_NOEXCEPT { return uwrosv2_raw_abi(); }"""

CAP_CPP = """namespace uwrosv2 { namespace capability {
/** Open the exact deployed alias. Adopt the result in a capability_owner or retire it with close. */
UWROSV2_CPP_NODISCARD inline result<capability_handle> open(text_view alias) UWROSV2_CPP_NOEXCEPT {
    if (!alias.data || !alias.size || alias.size > 255) return detail::failure<capability_handle>(22);
    uint8_t bytes[8] = {0};
    const uint32_t code = raw::uwrosv2_raw_capability_open(0, detail::address(alias.data), alias.size, detail::address(bytes));
    if (code) return detail::failure<capability_handle>(code);
    const capability_handle cap = {detail::read_word(bytes)};
    if (!cap.id) return detail::failure<capability_handle>(22);
    return detail::with_value(detail::finish(0, 8, sizeof bytes), cap);
}
/** Retire an environment capability. Failed closure preserves the handle. */
UWROSV2_CPP_NODISCARD inline uint32_t close(capability_handle& cap) UWROSV2_CPP_NOEXCEPT {
    if (!cap.id) return 9;
    const uint32_t code = raw::uwrosv2_raw_capability_close(cap.id);
    if (!code) cap.id = 0;
    return code;
}
}
/** Returns major 2 on success. Exposure or resource errors share the i32 result. */
UWROSV2_CPP_NODISCARD inline uint32_t abi() UWROSV2_CPP_NOEXCEPT { return capability::raw::uwrosv2_raw_abi(); }
}"""

CAP_RS = """/// Returns major 2 on success. Exposure or resource errors share the i32 result.
pub fn abi() -> u32 { unsafe { ffi::abi() } }
/// Open the exact deployed alias in memory zero. Only this VM instance can use the returned capability.
pub fn open(alias: &str) -> crate::Result<crate::Capability> {
    use crate::base::{address, invalid};
    if alias.is_empty() || alias.len() > 255 { return Err(invalid()); }
    let mut bytes = [0; 8];
    let code = unsafe { ffi::open(0, address(alias.as_ptr()), alias.len() as u64, address(bytes.as_mut_ptr())) };
    if code != 0 { return Err(crate::Error { status: code, reported: 0 }); }
    crate::Capability::from_id(u64::from_le_bytes(bytes)).ok_or_else(invalid)
}
/// Explicitly retire the capability. The handle remains available if the VM refuses closure.
pub fn close(cap: &mut crate::Capability) -> crate::Result<()> {
    if cap.id() == 0 { return Err(crate::Error { status: 9, reported: 0 }); }
    let code = unsafe { ffi::close(cap.id()) };
    if code != 0 { return Err(crate::Error { status: code, reported: 0 }); }
    cap.clear();
    Ok(())
}"""

CLOCK_TYPES = {
    "c": """typedef enum { UWROSV2_CLOCK_STEADY = 0, UWROSV2_CLOCK_SYSTEM = 1, UWROSV2_CLOCK_ROS = 2 } uwrosv2_clock_kind;
typedef struct { int64_t now; uint64_t epoch; int started; uwrosv2_clock_kind kind; } uwrosv2_clock_sample;""",
    "cpp": scoped_enum("kind", "uint64_t", {"steady": 0, "system": 1, "ros": 2})
           + "\nstruct sample { int64_t now; uint64_t epoch; bool started; kind source; };",
    "rs": """#[repr(u64)]
#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub enum ClockKind { Steady = 0, System = 1, Ros = 2 }
#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub struct Sample { pub now: i64, pub epoch: u64, pub started: bool, pub kind: ClockKind }""",
}
TIMER_TYPES = {
    "c": "typedef struct { int64_t expected, actual; uint64_t occurrences, clock_epoch; } uwrosv2_timer_sample;",
    "cpp": "struct sample { int64_t expected, actual; uint64_t occurrences, clock_epoch; };",
    "rs": "#[derive(Clone, Copy, Debug, PartialEq, Eq)]\npub struct Sample { pub expected: i64, pub actual: i64, pub occurrences: u64, pub clock_epoch: u64 }",
}
WAIT_TYPES = {
    "c": """enum uwrosv2_interest { UWROSV2_READABLE = 1, UWROSV2_CHANGED = 2, UWROSV2_EXPIRED = 4, UWROSV2_CLOSED = 8 };
typedef struct { uwrosv2_resource source; uint64_t token, events, sequence; } uwrosv2_ready_record;
/** Decode a 32-byte readiness record. Pass only the extent returned by wait.poll. */
static inline int uwrosv2_wait_ready_at(uwrosv2_input records, size_t index, uwrosv2_ready_record *out) UWROSV2_C_NOEXCEPT {
    if (!out || !records.data || records.size % 32 || index >= records.size / 32) return 0;
    const uint8_t *p = records.data + 32 * index;
    out->source.id = uwrosv2_read_le64(p); out->token = uwrosv2_read_le64(p + 8);
    out->events = uwrosv2_read_le64(p + 16); out->sequence = uwrosv2_read_le64(p + 24); return 1;
}""",
    "cpp": """enum interest
#if __cplusplus >= 201103L
    : uint64_t
#endif
{ readable = 1, changed = 2, expired = 4, closed = 8 };
struct ready_record { resource_handle source; uint64_t token, events, sequence; };
/** Decode a readiness record from the delivered prefix of wait.poll. */
UWROSV2_CPP_NODISCARD inline result<ready_record> ready_at(input records, size_t index) UWROSV2_CPP_NOEXCEPT {
    if (!records.data || records.size % 32 || index >= records.size / 32) return detail::failure<ready_record>(22);
    const uint8_t* p = records.data + index * 32;
    const ready_record ready = {{detail::read_word(p)}, detail::read_word(p + 8), detail::read_word(p + 16), detail::read_word(p + 24)};
    return detail::with_value(detail::finish(0, 32, 32), ready);
}""",
    "rs": """pub const READABLE: u64 = 1;
pub const CHANGED: u64 = 2;
pub const EXPIRED: u64 = 4;
pub const CLOSED: u64 = 8;
#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub struct Ready { pub source: u64, pub token: u64, pub events: u64, pub sequence: u64 }
/// Decode one 32-byte readiness record from the delivered poll prefix.
pub fn ready_at(records: &[u8], index: usize) -> crate::Result<Ready> {
    if records.len() % 32 != 0 { return Err(crate::base::invalid()); }
    let bytes = records.chunks_exact(32).nth(index).ok_or_else(crate::base::invalid)?;
    let mut r = crate::wire::Reader::new(bytes);
    Ok(Ready { source: r.word()?, token: r.word()?, events: r.word()?, sequence: r.word()? })
}"""
}


def local_arg(name, kind):
    if name in {"clock", "guard", "timer", "source", "waitset", "resource"}:
        return "resource"
    if name.endswith("_capability"):
        return "capability"
    return "kind" if name == "kind" else kind


TYPES = {
    "c": {"resource": "uwrosv2_resource", "capability": "uwrosv2_capability", "kind": "uwrosv2_clock_kind",
          "i64": "int64_t", "u64": "uint64_t", "bool": "int"},
    "cpp": {"resource": "resource_handle", "capability": "capability_handle", "kind": "kind",
            "i64": "int64_t", "u64": "uint64_t", "bool": "bool"},
    "rs": {"resource": "&crate::Resource", "capability": "&crate::Capability", "kind": "ClockKind",
           "i64": "i64", "u64": "u64", "bool": "bool"},
}


def arguments(op, lang):
    result = []
    for f in op["request"]:
        name = f["name"]
        typ = local_arg(name, f["type"])
        var = "clock_kind" if name == "kind" else name
        t = TYPES[lang][typ]
        if op["name"] == "resource.close":
            t = {"c": "uwrosv2_resource *", "cpp": "resource_handle&", "rs": "&mut crate::Resource"}[lang]
        decl = f"{var}: {t}" if lang == "rs" else f"{t} {var}"
        if typ in {"resource", "capability"}:
            x = var + ("->id" if op["name"] == "resource.close" and lang == "c" else ".id()" if lang == "rs" else ".id")
        elif typ == "u64":
            x = var
        elif lang == "rs":
            x = f"{var} as u64"
        elif lang == "cpp":
            x = f"static_cast<uint64_t>({var})"
        else:
            x = f"(uint64_t){var}"
        result.append((decl, x))
    return result


def layout(op, lang):
    n = op["name"]
    if n == "clock.read":
        return {"c": "uwrosv2_clock_sample", "cpp": "sample", "rs": "Sample"}[lang]
    if n == "timer.take":
        return {"c": "uwrosv2_timer_sample", "cpp": "sample", "rs": "Sample"}[lang]
    if n.endswith(".create"):
        return {"c": "uwrosv2_resource", "cpp": "resource_handle", "rs": "crate::Resource"}[lang]
    if n == "guard.take":
        return {"c": "uint64_t", "cpp": "uint64_t", "rs": "u64"}[lang]
    return None


def c_family(op, cpp):
    lang = "cpp" if cpp else "c"
    name = op["name"]
    fn = (name.split(".")[1] if cpp else "uwrosv2_" + name.replace(".", "_"))
    args = arguments(op, lang)
    decl = ["capability_handle cap" if cpp else "uwrosv2_capability cap"] + [a for a, _ in args]
    poll = name == "wait.poll"
    value_type = layout(op, lang)
    ret = "uint32_t"
    if poll:
        ret = "transfer" if cpp else "uwrosv2_transfer"
        decl.append("output records" if cpp else "uwrosv2_output records")
    elif value_type:
        if cpp:
            ret = f"result<{value_type}>"
        else:
            decl.append(f"{value_type} *out")
    end = " UWROSV2_CPP_NOEXCEPT" if cpp else " UWROSV2_C_NOEXCEPT"
    prefix = "UWROSV2_CPP_NODISCARD inline" if cpp else "static inline"
    lines = [f"/** {op['contract'].strip()} */", f"{prefix} {ret} {fn}({', '.join(decl)}){end} {{"]
    if value_type and not cpp:
        lines.append("    if (!out) return 22;")
    if name == "resource.close":
        lines.append("    if (!resource.id) return 9;" if cpp else "    if (!resource || !resource->id) return 9;")
    size = len(args) * 8
    if size:
        lines.append(f"    uint8_t request[{size}];")
        write = "detail::write_word" if cpp else "uwrosv2_write_le64"
        for i, (_, x) in enumerate(args):
            lines.append(f"    {write}(request + {8*i}, {x});")
    req = ("input(request)" if cpp else "uwrosv2_bytes(request, sizeof request)") if size else ("input()" if cpp else "uwrosv2_bytes(NULL, 0)")
    out_size = op["result_bytes"]
    reply = "records" if poll else ("output()" if cpp else "uwrosv2_mut_bytes(NULL, 0)")
    if out_size > 0:
        lines.append(f"    uint8_t reply[{out_size}] = {{0}};")
        reply = "output(reply)" if cpp else "uwrosv2_mut_bytes(reply, sizeof reply)"
    lines.append(f"    {'const transfer' if cpp else 'uwrosv2_transfer'} call = {fn}_record(cap, {req}, {reply});")
    if poll:
        invalid = "detail::finish(22, call.size, records.size)" if cpp else "uwrosv2_transfer_result(22, call.size, records.size)"
        lines.append(f"    return !call.status && call.size % 32 ? {invalid} : call;")
        return "\n".join(lines + ["}"])
    if value_type and cpp:
        lines.append(f"    if (!call || call.size != {out_size}) return detail::failure<{value_type}>(call.status ? call.status : 22u, call.size);")
    else:
        lines.extend(["    if (call.status) return call.status;", f"    if (call.size != {out_size}) return 22;"])
    read = "detail::read_word" if cpp else "uwrosv2_read_le64"
    if value_type:
        for i in range(out_size // 8):
            lines.append(f"    const uint64_t w{i} = {read}(reply + {8*i});")
        if name.endswith(".create"):
            lines.append("    if (!w0) return " + ("detail::failure<resource_handle>(22, 8);" if cpp else "22;"))
            finish = "{w0}" if cpp else "out->id = w0;"
        elif name == "clock.read":
            lines.append("    if (w2 > 1 || w3 > 2) return " + ("detail::failure<sample>(22, 32);" if cpp else "22;"))
            finish = ("{detail::signed_word(w0), w1, w2 != 0, static_cast<kind>(w3)}" if cpp else
                      "out->now = uwrosv2_signed_word(w0); out->epoch = w1; out->started = w2 != 0; out->kind = (uwrosv2_clock_kind)w3;")
        elif name == "timer.take":
            finish = ("{detail::signed_word(w0), detail::signed_word(w1), w2, w3}" if cpp else
                      "out->expected = uwrosv2_signed_word(w0); out->actual = uwrosv2_signed_word(w1); out->occurrences = w2; out->clock_epoch = w3;")
        else:
            finish = "w0" if cpp else "*out = w0;"
        if cpp:
            lines.append(f"    const {value_type} value = {finish};")
            lines.append("    return detail::with_value(call, value);")
        else:
            lines.append("    " + finish)
    if name == "resource.close":
        lines.append("    resource.id = 0;" if cpp else "    resource->id = 0;")
    if not (value_type and cpp):
        lines.append("    return 0;")
    lines.append("}")
    if cpp and name.endswith(".create"):
        values = ", ".join(arg.rsplit(" ", 1)[-1] for arg in decl)
        lines.extend([
            "",
            "/** Create directly into an empty owner. Keep cap alive until the owner closes or takes the capability. */",
            f"{prefix} uint32_t create({', '.join(decl)}, resource_owner& owner){end} {{",
            "    if (!owner.empty()) return static_cast<uint32_t>(status::conflict);",
            "    if (!cap.id) return static_cast<uint32_t>(status::bad_handle);",
            f"    result<resource_handle> made = create({values});",
            "    return made ? owner.adopt(cap, made.value) : made.call.status;",
            "}",
        ])
    return "\n".join(lines)


def rs_family(op):
    name = op["name"]
    fn = name.split(".")[1]
    args = arguments(op, "rs")
    decl = ["cap: &crate::Capability"] + [a for a, _ in args]
    poll = name == "wait.poll"
    value_type = layout(op, "rs")
    if poll:
        decl.append("records: &mut [u8]")
    ret = value_type or ("usize" if poll else "()")
    lines = [f"/// {op['contract'].strip()}", f"pub fn {fn}({', '.join(decl)}) -> crate::Result<{ret}> {{"]
    if args:
        lines.append(f"    let mut request = [0; {len(args)*8}];")
        lines.append("    let mut w = crate::wire::Writer::new(&mut request);")
        lines.extend(f"    w.word({x})?;" for _, x in args)
    if op["result_bytes"] > 0:
        lines.append(f"    let mut reply = [0; {op['result_bytes']}];")
    reply = "records" if poll else "&mut reply" if value_type else "&mut []"
    lines.append(f"    let bytes = {fn}_record(cap, {'&request' if args else '&[]'}, {reply})?;")
    if poll:
        lines.append("    if bytes % 32 != 0 { return Err(crate::base::invalid()); }\n    Ok(bytes)")
    else:
        lines.append(f"    if bytes != {op['result_bytes']} {{ return Err(crate::base::invalid()); }}")
        if value_type:
            lines.append("    let mut r = crate::wire::Reader::new(&reply);")
            if name.endswith(".create"):
                lines.append("    crate::Resource::from_id(r.word()?).ok_or_else(crate::base::invalid)")
            elif name == "clock.read":
                lines.append("""    let now = r.word()? as i64;
    let epoch = r.word()?;
    let started = match r.word()? { 0 => false, 1 => true, _ => return Err(crate::base::invalid()) };
    let kind = match r.word()? { 0 => ClockKind::Steady, 1 => ClockKind::System, 2 => ClockKind::Ros, _ => return Err(crate::base::invalid()) };
    Ok(Sample { now, epoch, started, kind })""")
            elif name == "timer.take":
                lines.append("    Ok(Sample { expected: r.word()? as i64, actual: r.word()? as i64, occurrences: r.word()?, clock_epoch: r.word()? })")
            else:
                lines.append("    r.word()")
        else:
            if name == "resource.close":
                lines.append("    resource.clear();")
            lines.append("    Ok(())")
    return "\n".join(lines + ["}"])


def facade(domain, ops, lang):
    if domain == "capability":
        return {"c": CAP_C, "cpp": CAP_CPP, "rs": CAP_RS}[lang]
    types = {"clock": CLOCK_TYPES, "timer": TIMER_TYPES, "wait": WAIT_TYPES}.get(domain, {}).get(lang, "")
    parts = [types] if types else []
    for op in ops:
        parts.append(rs_family(op) if lang == "rs" else c_family(op, lang == "cpp"))
    body = "\n\n".join(parts)
    return f"namespace uwrosv2 {{ namespace {domain} {{\n{body}\n}} }}" if lang == "cpp" else body
