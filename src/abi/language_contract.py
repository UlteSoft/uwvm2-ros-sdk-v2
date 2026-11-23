"""Document individual raw imports from the registered VM carrier and wire record."""
from collections import defaultdict
from textwrap import wrap

SPECIAL = {"abi", "capability.open", "capability.close"}
OBSERVATION = {"invoke_permission_report", "invoke_module_permission_report", "invoke_module_observation"}
REPORTS = {"permission.report", "module.permission.report"}
EXCHANGE = "invoke_module_call"

# Outer extent checks in imported/scene/host.h. A grant, codec or provider can
# impose a smaller limit. Fixed request and result sizes come from the VM tuple.
TRANSFER = 4 * 1024 * 1024
BOUNDS = {
    "invoke": (40, TRANSFER),
    "invoke_artifact": (40, TRANSFER),
    "invoke_bridge": (4096, 1024),
    "invoke_buffer": (TRANSFER + 24, TRANSFER + 512),
    "invoke_communication": (TRANSFER, TRANSFER),
    "invoke_device": (16384, 4096),
    "invoke_driver": (65536 + 24, 65536 + 16),
    "invoke_log_diagnostic": (TRANSFER, TRANSFER),
    "invoke_managed": (40, TRANSFER),
    "invoke_media": (4096, 1024),
    "invoke_model": (TRANSFER + 12288, TRANSFER + 512),
    "invoke_module_call": (TRANSFER + 16, TRANSFER + 16),
    "invoke_module_observation": (271, 65536),
    "invoke_module_permission_report": (263 + 295, 65536),
    "invoke_output": (TRANSFER + 24, TRANSFER),
    "invoke_parameter": (TRANSFER, TRANSFER),
    "invoke_permission_report": (295, 65536),
    "invoke_proposal": (16384, 8192),
    "invoke_recording": (24 + 96 * 63, TRANSFER),
    "invoke_revocation": (16, TRANSFER),
    "invoke_sensor": (144, TRANSFER + 2048),
    "invoke_transform": (40 + 622 * 128, TRANSFER),
}


def domains(contract):
    grouped = defaultdict(list)
    names = set()
    for row in contract["operations"]:
        name, signature = row["name"], row["wasm_signature"]
        if (name in names or signature["results"] != ["i32"] or
                [arg["type"] for arg in row["parameters"]] != signature["parameters"]):
            raise ValueError("inconsistent registered import: " + name)
        names.add(name)
        grouped[row["domain"]].append(row)
    return dict(sorted(grouped.items()))


def fields(rows):
    return ", ".join(f"`{row['name']}` (`{row['type']}`)" for row in rows)


def authority(row):
    name, action = row["name"], row["action"]
    if name == "abi":
        return "The deployment must expose abi to the immediate caller."
    if name == "capability.open":
        return "The caller must belong to an environment that exposes capability.open and grants the exact, live alias."
    if name == "capability.close":
        return "The caller must be an enrolled member of the handle's environment with capability.close exposed."
    if name == "permission.report":
        return "The VM authenticates the immediate caller and applies that caller's ROSv2 membership, import exposure and observation policy."
    if row["registration"]["handler"] in OBSERVATION:
        grant = "vm/runtime/metadata" if name == "vm.describe" else "module/metadata"
        result = f"The caller's deployment must expose {name}. The request alias must select a {grant} grant with this exact action."
        if name == "module.permission.report":
            result += " The viewer's family and exact-function observation restrictions also apply."
        return result
    result = f"The caller must belong to the capability's environment. The deployment must expose {name} and the grant must authorize {action}."
    if name == "resource.close":
        result += " The resource registry checks the originating grant and provider binding."
    elif name in {"request.describe", "request.release"}:
        result += " The request's originating grant and provider binding select the ledger."
    elif row["purposes"]:
        result += " Applicable grant purposes include " + ", ".join(row["purposes"]) + "."
    if row["secondary_actions"]:
        result += " Depending on the selected inputs and plan, the VM also checks " + ", ".join(row["secondary_actions"]) + "."
    return result


def memory_contract(row):
    name, handler = row["name"], row["registration"]["handler"]
    if name in {"abi", "capability.close"}:
        return "Call from the guest bound to this import. This signature has no guest memory operands."
    if name == "capability.open":
        return ("Keep the alias readable and the handle slot writable through the call. Their ranges may overlap. "
                "The VM copies the alias before writing the handle. Preserve WasmMTE tags on both addresses.")
    spans = "Keep the request readable, the full reply capacity writable and the eight-byte length slot writable through the call. Preserve WasmMTE tags on all addresses."
    if handler in OBSERVATION or handler == EXCHANGE:
        spans += (" The request, full reply range and length slot must be pairwise disjoint in linear memory. "
                  "The VM compares normalized addresses and returns INVALID (22) for any overlap.")
    else:
        spans += (" Request and reply may overlap because the VM copies the request before delivery. "
                  "The length slot must be disjoint from both ranges after address normalization. An overlap with the slot returns INVALID (22).")
    if handler == EXCHANGE:
        spans += (" Use caller-defined shared memory in a module with no memory exports. Give the VM writable access to the "
                  "entire input when the route erases it after copying (the default). A span that intersects an outstanding "
                  "delivery returns CONFLICT (17). Coordinate concurrent access to all exchange storage.")
        if name in {"module.call.take", "module.call.result"}:
            until = "the server responds" if name == "module.call.take" else "the client acknowledges"
            spans += (f" On successful delivery reserve the full reply capacity and length slot until {until} or confirmed "
                      "cleanup erases the registered region. Cancellation, observed expiry, revocation and retirement can erase it.")
    return spans


def observation_result(name):
    result = ("Zero delivers a page and its byte count. When a completed page exceeds capacity, TOO_LARGE (90) writes the "
              "required page length and leaves the reply untouched. A scan or page-construction limit can return 90 before "
              "either output is written. DENIED (13) leaves both outputs untouched.")
    if name in REPORTS:
        result += (" For an authorized whole-family query with a valid cursor, an unbuilt family returns UNSUPPORTED (95) "
                   "with a supported=false, enabled=false page when it fits. An unsupported exact-function query returns "
                   "95 without writing the page or length. A built but disabled family can return zero with enabled=false.")
        if name == "module.permission.report":
            result += " An unsupported target identity can also return 95 before either output is written."
    else:
        result += " An unsupported observation returns UNSUPPORTED (95) before writing either output."
        if name == "module.imports":
            result += " Native modules have no registered Wasm import list."
        elif name == "module.group":
            result += " A target without a ROSv2 group yields a supported page with enabled=false."
        elif name == "module.importers":
            result += " The scan budget counts all visited modules and import declarations, including nonmatches."
    return result


EXCHANGE_RESULTS = {
    "module.call.submit": "Zero delivers a 16-byte receipt with a new nonzero token and an empty payload. AGAIN (11) can mean the server has not registered or the route has no free slot.",
    "module.call.take": "Zero delivers the token and queued request. An empty queue returns AGAIN (11). If the frame exceeds capacity, TOO_LARGE (90) leaves the request queued and supplies no required length.",
    "module.call.respond": "Zero delivers a 16-byte receipt with the request token and an empty payload. Exceeding the route's response limit returns TOO_LARGE (90) without a required length. A failed receipt copy after commit leaves the response available to the client.",
    "module.call.result": "Zero delivers the token and committed response. A pending response returns AGAIN (11). If the frame exceeds capacity, TOO_LARGE (90) preserves the response and supplies no required length. Repeating a completed delivery returns CONFLICT (17).",
    "module.call.acknowledge": "Zero writes zero to the length slot after releasing the registered delivery. The same token can be acknowledged again while its freed slot still carries that token.",
    "module.call.cancel": "Zero writes zero to the length slot after erasing the exchange for this token. Failed erasure returns IO (5) and quarantines the slot.",
}


def result_text(row):
    name, handler = row["name"], row["registration"]["handler"]
    if name == "abi":
        return "The major ABI number (2) on success. The same i32 carries a scene status on failure."
    if name == "capability.open":
        return ("Zero after writing the handle. Invalid alias bytes, invalid memory or failed handle delivery return INVALID (22). "
                "Failed delivery rolls back the unpublished handle. An absent or revoked alias returns DENIED (13).")
    if name == "capability.close":
        return "Zero retires the handle. BAD_HANDLE (9) identifies an unknown or already closed handle in the authorized environment."
    if handler in OBSERVATION:
        return observation_result(name)
    if handler == EXCHANGE:
        return EXCHANGE_RESULTS[name] + " UNSUPPORTED (95) can indicate failure to capture an eligible tagged exchange span."
    result = "Zero on success, otherwise a scene status."
    if row["result"]:
        result += (" A short reply returns TOO_LARGE (90) with the required capacity or minimum in the length slot. "
                   "Other limits may return 90 before a useful size is available.")
    else:
        result += " The VM writes a zero length before the mutation. A later refusal can therefore also leave zero in the slot."
    if any(f["name"] in {"receipt", "effect_status", "creation"} for f in row["result"]):
        result += " Inspect the delivered receipt for the operation's outcome."
    elif name == "driver.result":
        result += " The response record contains the driver's status and payload."
    elif row["behavior"] == "receive_reservation":
        result += " The reservation remains owned until acknowledgement or release."
    return result


def request_size(row, maximum):
    name, words = row["name"], row["request_words"]
    if words >= 0:
        return f"Exact request length, {8 * words} bytes."
    if all(f["type"] in {"u64", "i64", "bool"} for f in row["request"]):
        return f"Exact request length, {8 * len(row['request'])} bytes."
    if row["registration"]["handler"] == EXCHANGE:
        if name in {"module.call.submit", "module.call.respond"}:
            return f"16 bytes of token and payload length plus payload bytes, at most {maximum} bytes. The route also bounds the payload."
        return "Exactly 16 bytes for the token and zero payload length."
    if name == "artifact.append":
        return f"24 bytes of header plus the raw data byte count, at most {maximum} bytes in total. The data has no length prefix."
    if name == "artifact.publish":
        return f"16 bytes of header plus the declared number of raw data bytes. The header check bounds the whole span at {maximum} bytes and the grant additionally bounds the payload."
    return f"Byte length of the complete encoded request. The carrier accepts at most {maximum} bytes."


def parameters(row):
    name, handler = row["name"], row["registration"]["handler"]
    if name == "abi":
        return {}
    if name == "capability.close":
        return {"id": "Handle issued by capability.open in the caller's environment."}
    if name == "capability.open":
        return {"memory": "Index of the caller's linear memory containing both spans.",
                "offset": "Guest address of the raw ASCII grant alias. Letters, digits, underscore, hyphen and period are allowed. The exact names `.` and `..` are invalid.",
                "size": "Alias length from 1 through 255 bytes, excluding any terminator or wire prefix.",
                "output": "Guest address of the writable eight-byte little-endian handle slot."}
    maximum, capacity_limit = BOUNDS[handler]
    if name == "diagnostic.read":
        maximum = 40
    result_bytes = row["result_bytes"]
    cap = f"Capability handle for the {row['action']} action in the caller's environment."
    if handler in OBSERVATION:
        cap = "Pass zero. The VM authenticates the immediate caller and resolves observation authority separately."
    request = ("Guest address of the encoded request. Wire order is " + fields(row["request"]) + "." if row["request"] else
               "Guest address of the checked zero-length request range.")
    output = ("Guest address of the writable result. Wire order is " + fields(row["result"]) + "." if row["result"] else
              "Guest address of the checked reply range. This operation has an empty reply body.")
    length = "Guest address of the writable little-endian u64 byte count. On delivery it records the number of bytes written to the reply."
    capacity = f"Byte capacity of the full writable reply range, at most {capacity_limit}."
    if result_bytes >= 0:
        capacity += f" The fixed result occupies {result_bytes} bytes."
    if handler in OBSERVATION:
        request += " The cursor first is a zero-based row index, at most 65536."
        output += " The 40-byte header holds supported, enabled, first, total and row count as little-endian u64 values. Each of up to 32 rows contains scope, key, annotation (length-prefixed UTF-8) and value (u64)."
        if name in REPORTS:
            request += " Select preloaddl, preloadwasm, wasip1, ros1v1, ros2v1 or rosv2. An empty function selects the whole family."
            length += " Initialize this slot to zero to distinguish a delivered status-95 page from a refusal that writes nothing."
    if handler == EXCHANGE:
        request += " The frame starts with the little-endian u64 token and payload byte count."
        limit = "Zero capacity is allowed for this empty reply." if not row["result"] else "At least 16 bytes are required for the frame header."
        capacity += " " + limit
        length += " This carrier does not publish a required size on TOO_LARGE (90)."
    if name == "driver.result":
        capacity += " Reserve 16 bytes plus the route's configured maximum response payload even when the pending response is shorter."
    if name == "wait.poll":
        output += " Each 32-byte record contains source, token, events and sequence, with no array length prefix."
    if name == "artifact.open":
        request += " The SHA-256 digest occupies 32 raw bytes immediately after the generation."
    if name == "artifact.describe":
        output += " The last 32 bytes are the raw SHA-256 digest."
    if name == "artifact.read":
        output += " The result contains raw data without a length prefix."
    return {
        "cap": cap,
        "memory": ("Index of the caller's owned shared exchange memory." if handler == EXCHANGE else
                   "Index of the caller's linear memory containing all three spans."),
        "request": request, "size": request_size(row, maximum), "output": output,
        "capacity": capacity, "length_output": length,
    }


def comment(row, *, style="assemblyscript"):
    """Document the same authority, memory and result rules in each binding."""
    args = parameters(row)
    if set(args) != {p["name"] for p in row["parameters"]}:
        raise ValueError("undocumented parameter on " + row["name"])
    notes = [row["name"] + ". " + row["contract"].strip(), authority(row)]
    if row["wire"] in {"fixed_words", "local_lifecycle", "volatile_cache", "immutable_input"}:
        notes.append("Encode and decode scalar words as little-endian u64. Signed values use their two's-complement bit pattern.")
    elif row["wire"] == "canonical_record":
        notes.append("Use the ordered wire record. Scalars are little-endian. Text and byte strings carry a u64 byte-length prefix.")
    safety = memory_contract(row)
    returns = result_text(row)
    lines = []

    def paragraph(content, *, indent=""):
        lines.extend(wrap(content.replace("*/", "* /"), 96, subsequent_indent=indent,
                          break_long_words=False, break_on_hyphens=False))

    for note in notes:
        paragraph(note)
        lines.append("")
    if style == "rustdoc":
        lines.extend(["# Safety", ""])
        paragraph(safety)
        if row["name"] not in {"abi", "capability.close"}:
            paragraph("Maintain storage validity and Rust aliasing and synchronization requirements for every byte the VM may read, write or erase, for the full access lifetime.")
        if args:
            lines.extend(["", "# Arguments", ""])
            for name, description in args.items():
                paragraph(f"- `{name}` — {description}", indent="  ")
        lines.extend(["", "# Returns", ""])
        paragraph(returns)
        return "\n".join("/// " + line if line else "///" for line in lines)

    paragraph(safety)
    lines.append("")
    is_script = style in {"javascript", "typescript"}
    if is_script and args:
        paragraph("Supply i64 operands as bigint. The Wasm boundary uses the low 64 bits and rejects JavaScript number for these operands.")
        lines.append("")
    for param in row["parameters"]:
        name = param["name"]
        tag = ""
        description = args[name]
        if style == "wat":
            tag = "$"
            description = f"({param['type']}) " + description
        if is_script:
            if style == "javascript":
                tag = "{bigint} " if param["type"] == "i64" else "{number} "
            if param["type"] == "i32":
                description += " Use an integer from 0 through 4294967295."
        separator = " " if style == "doxygen" else " - "
        paragraph(f"@param {tag}{name}{separator}{description}", indent="  ")
    paragraph(("@return " if style == "doxygen" else "@returns {number} " if style == "javascript" else "@returns ") + returns,
              indent="  ")
    if style == "wat":
        return "\n".join("  ;; " + line if line else "  ;;" for line in lines)
    return "/**\n" + "\n".join(" * " + line if line else " *" for line in lines) + "\n */"
