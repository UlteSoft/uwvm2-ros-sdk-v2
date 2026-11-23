"""Raw modules imports from uwvm_ros_v2."""
from _uwros_runtime import raw


def wr_module_describe(cap, memory, request, size, output, capacity, length_output):
    """Return the exact registered target name and kind: main-wasm, preload-wasm or preload-dl.
    Default authority is zero: require explicit import exposure and exact module/metadata grant
    action. The trusted grant fixes the target; guests cannot supply arbitrary target names or
    wildcards. Carrier capability must be zero. Exact immediate caller identity comes from the
    runtime. Observation never freezes deployment, enrolls a caller, opens a capability,
    replenishes or consumes execution quotas, starts a provider, invokes an export, reads
    foreign memory, or changes another policy. A denial writes neither result nor length. Owned
    temporary buffers are securely overwritten.

    The caller's deployment must expose module.describe. The request alias must select a
    module/metadata grant with this exact action.

    Keep the request readable, the full reply capacity writable and the eight-byte length slot
    writable through the call. Preserve WasmMTE tags on all addresses. The request, full reply
    range and length slot must be pairwise disjoint in linear memory. The VM compares normalized
    addresses and returns INVALID (22) for any overlap.

    cap (i64, unsigned bit pattern). Pass zero. The VM authenticates the immediate caller and
    resolves observation authority separately.

    memory (i32, unsigned bit pattern). Index of the caller's linear memory containing all three
    spans.

    request (i64, unsigned bit pattern). Guest address of the encoded request. Wire order is
    `grant_alias` (`text`), `first` (`u64`). The cursor first is a zero-based row index, at most
    65536.

    size (i64, unsigned bit pattern). Byte length of the complete encoded request. The carrier
    accepts at most 271 bytes.

    output (i64, unsigned bit pattern). Guest address of the writable result. Wire order is
    `page` (`permission_page`). The 40-byte header holds supported, enabled, first, total and
    row count as little-endian u64 values. Each of up to 32 rows contains scope, key, annotation
    (length-prefixed UTF-8) and value (u64).

    capacity (i64, unsigned bit pattern). Byte capacity of the full writable reply range, at
    most 65536.

    length_output (i64, unsigned bit pattern). Guest address of the writable little-endian u64
    byte count. On delivery it records the number of bytes written to the reply.

    Returns an i32 as a Python int. Zero delivers a page and its byte count. When a completed
    page exceeds capacity, TOO_LARGE (90) writes the required page length and leaves the reply
    untouched. A scan or page-construction limit can return 90 before either output is written.
    DENIED (13) leaves both outputs untouched. An unsupported observation returns UNSUPPORTED
    (95) before writing either output."""
    return raw('module.describe', cap, memory, request, size, output, capacity, length_output)


def wr_module_exports(cap, memory, request, size, output, capacity, length_output):
    """Return only export names already recorded in the module registry. Do not resolve or call a
    symbol. Default authority is zero: require explicit import exposure and exact
    module/metadata grant action. The trusted grant fixes the target; guests cannot supply
    arbitrary target names or wildcards. Carrier capability must be zero. Exact immediate caller
    identity comes from the runtime. Observation never freezes deployment, enrolls a caller,
    opens a capability, replenishes or consumes execution quotas, starts a provider, invokes an
    export, reads foreign memory, or changes another policy. A denial writes neither result nor
    length. Owned temporary buffers are securely overwritten.

    The caller's deployment must expose module.exports. The request alias must select a
    module/metadata grant with this exact action.

    Keep the request readable, the full reply capacity writable and the eight-byte length slot
    writable through the call. Preserve WasmMTE tags on all addresses. The request, full reply
    range and length slot must be pairwise disjoint in linear memory. The VM compares normalized
    addresses and returns INVALID (22) for any overlap.

    cap (i64, unsigned bit pattern). Pass zero. The VM authenticates the immediate caller and
    resolves observation authority separately.

    memory (i32, unsigned bit pattern). Index of the caller's linear memory containing all three
    spans.

    request (i64, unsigned bit pattern). Guest address of the encoded request. Wire order is
    `grant_alias` (`text`), `first` (`u64`). The cursor first is a zero-based row index, at most
    65536.

    size (i64, unsigned bit pattern). Byte length of the complete encoded request. The carrier
    accepts at most 271 bytes.

    output (i64, unsigned bit pattern). Guest address of the writable result. Wire order is
    `page` (`permission_page`). The 40-byte header holds supported, enabled, first, total and
    row count as little-endian u64 values. Each of up to 32 rows contains scope, key, annotation
    (length-prefixed UTF-8) and value (u64).

    capacity (i64, unsigned bit pattern). Byte capacity of the full writable reply range, at
    most 65536.

    length_output (i64, unsigned bit pattern). Guest address of the writable little-endian u64
    byte count. On delivery it records the number of bytes written to the reply.

    Returns an i32 as a Python int. Zero delivers a page and its byte count. When a completed
    page exceeds capacity, TOO_LARGE (90) writes the required page length and leaves the reply
    untouched. A scan or page-construction limit can return 90 before either output is written.
    DENIED (13) leaves both outputs untouched. An unsupported observation returns UNSUPPORTED
    (95) before writing either output."""
    return raw('module.exports', cap, memory, request, size, output, capacity, length_output)


def wr_module_group(cap, memory, request, size, output, capacity, length_output):
    """Return the target ROSv2 group name and its members only under this independent action.
    Default authority is zero: require explicit import exposure and exact module/metadata grant
    action. The trusted grant fixes the target; guests cannot supply arbitrary target names or
    wildcards. Carrier capability must be zero. Exact immediate caller identity comes from the
    runtime. Observation never freezes deployment, enrolls a caller, opens a capability,
    replenishes or consumes execution quotas, starts a provider, invokes an export, reads
    foreign memory, or changes another policy. A denial writes neither result nor length. Owned
    temporary buffers are securely overwritten.

    The caller's deployment must expose module.group. The request alias must select a
    module/metadata grant with this exact action.

    Keep the request readable, the full reply capacity writable and the eight-byte length slot
    writable through the call. Preserve WasmMTE tags on all addresses. The request, full reply
    range and length slot must be pairwise disjoint in linear memory. The VM compares normalized
    addresses and returns INVALID (22) for any overlap.

    cap (i64, unsigned bit pattern). Pass zero. The VM authenticates the immediate caller and
    resolves observation authority separately.

    memory (i32, unsigned bit pattern). Index of the caller's linear memory containing all three
    spans.

    request (i64, unsigned bit pattern). Guest address of the encoded request. Wire order is
    `grant_alias` (`text`), `first` (`u64`). The cursor first is a zero-based row index, at most
    65536.

    size (i64, unsigned bit pattern). Byte length of the complete encoded request. The carrier
    accepts at most 271 bytes.

    output (i64, unsigned bit pattern). Guest address of the writable result. Wire order is
    `page` (`permission_page`). The 40-byte header holds supported, enabled, first, total and
    row count as little-endian u64 values. Each of up to 32 rows contains scope, key, annotation
    (length-prefixed UTF-8) and value (u64).

    capacity (i64, unsigned bit pattern). Byte capacity of the full writable reply range, at
    most 65536.

    length_output (i64, unsigned bit pattern). Guest address of the writable little-endian u64
    byte count. On delivery it records the number of bytes written to the reply.

    Returns an i32 as a Python int. Zero delivers a page and its byte count. When a completed
    page exceeds capacity, TOO_LARGE (90) writes the required page length and leaves the reply
    untouched. A scan or page-construction limit can return 90 before either output is written.
    DENIED (13) leaves both outputs untouched. An unsupported observation returns UNSUPPORTED
    (95) before writing either output. A target without a ROSv2 group yields a supported page
    with enabled=false."""
    return raw('module.group', cap, memory, request, size, output, capacity, length_output)


def wr_module_importers(cap, memory, request, size, output, capacity, length_output):
    """Return direct registered Wasm importers of the exact target, as importer module/symbol rows.
    Require an independent module/metadata grant and exact exposure even when the target is the
    caller. Count all visited modules and imports, including nonmatches, against the finite scan
    budget. Reexports are not expanded and native dynamic-linker dependencies are not inspected.
    An explicit grant may also name a registered builtin module. No unrelated peers or their
    remaining imports are disclosed. Carrier capability must be zero. Exact immediate caller
    identity comes from the runtime. Observation never freezes deployment, enrolls a caller,
    opens a capability, replenishes or consumes execution quotas, starts a provider, invokes an
    export, reads foreign memory, or changes another policy. A denial writes neither result nor
    length. Owned temporary buffers are securely overwritten.

    The caller's deployment must expose module.importers. The request alias must select a
    module/metadata grant with this exact action.

    Keep the request readable, the full reply capacity writable and the eight-byte length slot
    writable through the call. Preserve WasmMTE tags on all addresses. The request, full reply
    range and length slot must be pairwise disjoint in linear memory. The VM compares normalized
    addresses and returns INVALID (22) for any overlap.

    cap (i64, unsigned bit pattern). Pass zero. The VM authenticates the immediate caller and
    resolves observation authority separately.

    memory (i32, unsigned bit pattern). Index of the caller's linear memory containing all three
    spans.

    request (i64, unsigned bit pattern). Guest address of the encoded request. Wire order is
    `grant_alias` (`text`), `first` (`u64`). The cursor first is a zero-based row index, at most
    65536.

    size (i64, unsigned bit pattern). Byte length of the complete encoded request. The carrier
    accepts at most 271 bytes.

    output (i64, unsigned bit pattern). Guest address of the writable result. Wire order is
    `page` (`permission_page`). The 40-byte header holds supported, enabled, first, total and
    row count as little-endian u64 values. Each of up to 32 rows contains scope, key, annotation
    (length-prefixed UTF-8) and value (u64).

    capacity (i64, unsigned bit pattern). Byte capacity of the full writable reply range, at
    most 65536.

    length_output (i64, unsigned bit pattern). Guest address of the writable little-endian u64
    byte count. On delivery it records the number of bytes written to the reply.

    Returns an i32 as a Python int. Zero delivers a page and its byte count. When a completed
    page exceeds capacity, TOO_LARGE (90) writes the required page length and leaves the reply
    untouched. A scan or page-construction limit can return 90 before either output is written.
    DENIED (13) leaves both outputs untouched. An unsupported observation returns UNSUPPORTED
    (95) before writing either output. The scan budget counts all visited modules and import
    declarations, including nonmatches."""
    return raw('module.importers', cap, memory, request, size, output, capacity, length_output)


def wr_module_imports(cap, memory, request, size, output, capacity, length_output):
    """Return the exact Wasm import module/name pairs; native preloaddl platform imports are
    unsupported. Default authority is zero: require explicit import exposure and exact
    module/metadata grant action. The trusted grant fixes the target; guests cannot supply
    arbitrary target names or wildcards. Carrier capability must be zero. Exact immediate caller
    identity comes from the runtime. Observation never freezes deployment, enrolls a caller,
    opens a capability, replenishes or consumes execution quotas, starts a provider, invokes an
    export, reads foreign memory, or changes another policy. A denial writes neither result nor
    length. Owned temporary buffers are securely overwritten.

    The caller's deployment must expose module.imports. The request alias must select a
    module/metadata grant with this exact action.

    Keep the request readable, the full reply capacity writable and the eight-byte length slot
    writable through the call. Preserve WasmMTE tags on all addresses. The request, full reply
    range and length slot must be pairwise disjoint in linear memory. The VM compares normalized
    addresses and returns INVALID (22) for any overlap.

    cap (i64, unsigned bit pattern). Pass zero. The VM authenticates the immediate caller and
    resolves observation authority separately.

    memory (i32, unsigned bit pattern). Index of the caller's linear memory containing all three
    spans.

    request (i64, unsigned bit pattern). Guest address of the encoded request. Wire order is
    `grant_alias` (`text`), `first` (`u64`). The cursor first is a zero-based row index, at most
    65536.

    size (i64, unsigned bit pattern). Byte length of the complete encoded request. The carrier
    accepts at most 271 bytes.

    output (i64, unsigned bit pattern). Guest address of the writable result. Wire order is
    `page` (`permission_page`). The 40-byte header holds supported, enabled, first, total and
    row count as little-endian u64 values. Each of up to 32 rows contains scope, key, annotation
    (length-prefixed UTF-8) and value (u64).

    capacity (i64, unsigned bit pattern). Byte capacity of the full writable reply range, at
    most 65536.

    length_output (i64, unsigned bit pattern). Guest address of the writable little-endian u64
    byte count. On delivery it records the number of bytes written to the reply.

    Returns an i32 as a Python int. Zero delivers a page and its byte count. When a completed
    page exceeds capacity, TOO_LARGE (90) writes the required page length and leaves the reply
    untouched. A scan or page-construction limit can return 90 before either output is written.
    DENIED (13) leaves both outputs untouched. An unsupported observation returns UNSUPPORTED
    (95) before writing either output. Native modules have no registered Wasm import list."""
    return raw('module.imports', cap, memory, request, size, output, capacity, length_output)


def wr_module_permission_report(cap, memory, request, size, output, capacity, length_output):
    """Return permissions of the exact registered target for the requested family. The viewer
    observation policy also applies, including exact-function and aggregate denials. Default
    authority is zero: require explicit import exposure and exact module/metadata grant action.
    The trusted grant fixes the target; guests cannot supply arbitrary target names or
    wildcards. Carrier capability must be zero. Exact immediate caller identity comes from the
    runtime. Observation never freezes deployment, enrolls a caller, opens a capability,
    replenishes or consumes execution quotas, starts a provider, invokes an export, reads
    foreign memory, or changes another policy. A denial writes neither result nor length. Owned
    temporary buffers are securely overwritten.

    The caller's deployment must expose module.permission.report. The request alias must select
    a module/metadata grant with this exact action. The viewer's family and exact-function
    observation restrictions also apply.

    Keep the request readable, the full reply capacity writable and the eight-byte length slot
    writable through the call. Preserve WasmMTE tags on all addresses. The request, full reply
    range and length slot must be pairwise disjoint in linear memory. The VM compares normalized
    addresses and returns INVALID (22) for any overlap.

    cap (i64, unsigned bit pattern). Pass zero. The VM authenticates the immediate caller and
    resolves observation authority separately.

    memory (i32, unsigned bit pattern). Index of the caller's linear memory containing all three
    spans.

    request (i64, unsigned bit pattern). Guest address of the encoded request. Wire order is
    `grant_alias` (`text`), `family` (`text`), `function` (`text`), `first` (`u64`). The cursor
    first is a zero-based row index, at most 65536. Select preloaddl, preloadwasm, wasip1,
    ros1v1, ros2v1 or rosv2. An empty function selects the whole family.

    size (i64, unsigned bit pattern). Byte length of the complete encoded request. The carrier
    accepts at most 558 bytes.

    output (i64, unsigned bit pattern). Guest address of the writable result. Wire order is
    `page` (`permission_page`). The 40-byte header holds supported, enabled, first, total and
    row count as little-endian u64 values. Each of up to 32 rows contains scope, key, annotation
    (length-prefixed UTF-8) and value (u64).

    capacity (i64, unsigned bit pattern). Byte capacity of the full writable reply range, at
    most 65536.

    length_output (i64, unsigned bit pattern). Guest address of the writable little-endian u64
    byte count. On delivery it records the number of bytes written to the reply. Initialize this
    slot to zero to distinguish a delivered status-95 page from a refusal that writes nothing.

    Returns an i32 as a Python int. Zero delivers a page and its byte count. When a completed
    page exceeds capacity, TOO_LARGE (90) writes the required page length and leaves the reply
    untouched. A scan or page-construction limit can return 90 before either output is written.
    DENIED (13) leaves both outputs untouched. For an authorized whole-family query with a valid
    cursor, an unbuilt family returns UNSUPPORTED (95) with a supported=false, enabled=false
    page when it fits. An unsupported exact-function query returns 95 without writing the page
    or length. A built but disabled family can return zero with enabled=false. An unsupported
    target identity can also return 95 before either output is written."""
    return raw('module.permission.report', cap, memory, request, size, output, capacity, length_output)
