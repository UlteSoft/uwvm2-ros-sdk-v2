//! ROSv2 permission imports generated from src/abi/contract.json.

const raw = struct {
    extern "uwvm_ros_v2" fn @"permission.report"(cap: u64, memory: u32, request: u64, size: u64, output: u64, capacity: u64, length_output: u64) u32;
};

/// permission.report. Self observation defaults to allowed only after explicit ROSv2 binding. Family
/// and exact function denials can only reduce observation; any exact denial refuses the full aggregate
/// to prevent bypass. Explicit hidden removes the import. Returns own identity, exact import exposure,
/// configured/live ROSv2 permissions and own group name without other members. WASI descriptor rows are
/// initial approved rights; ROSv1 rows are configured policy, not a complete live handle snapshot.
/// Carrier capability must be zero. Exact immediate caller identity comes from the runtime. Observation
/// never freezes deployment, enrolls a caller, opens a capability, replenishes or consumes execution
/// quotas, starts a provider, invokes an export, reads foreign memory, or changes another policy. A
/// denial writes neither result nor length. Owned temporary buffers are securely overwritten.
/// The VM authenticates the immediate caller and applies that caller's ROSv2 membership, import
/// exposure and observation policy.
/// Keep the request readable, the full reply capacity writable and the eight-byte length slot writable
/// through the call. Preserve WasmMTE tags on all addresses. The request, full reply range and length
/// slot must be pairwise disjoint in linear memory. The VM compares normalized addresses and returns
/// INVALID (22) for any overlap.
/// `cap` — Pass zero. The VM authenticates the immediate caller and resolves observation authority
/// separately.
/// `memory` — Index of the caller's linear memory containing all three spans.
/// `request` — Guest address of the encoded request. Wire order is `family` (`text`), `function`
/// (`text`), `first` (`u64`). The cursor first is a zero-based row index, at most 65536. Select
/// preloaddl, preloadwasm, wasip1, ros1v1, ros2v1 or rosv2. An empty function selects the whole family.
/// `size` — Byte length of the complete encoded request. The carrier accepts at most 295 bytes.
/// `output` — Guest address of the writable result. Wire order is `page` (`permission_page`). The
/// 40-byte header holds supported, enabled, first, total and row count as little-endian u64 values.
/// Each of up to 32 rows contains scope, key, annotation (length-prefixed UTF-8) and value (u64).
/// `capacity` — Byte capacity of the full writable reply range, at most 65536.
/// `length_output` — Guest address of the writable little-endian u64 byte count. On delivery it records
/// the number of bytes written to the reply. Initialize this slot to zero to distinguish a delivered
/// status-95 page from a refusal that writes nothing.
/// Result. Zero delivers a page and its byte count. When a completed page exceeds capacity, TOO_LARGE
/// (90) writes the required page length and leaves the reply untouched. A scan or page-construction
/// limit can return 90 before either output is written. DENIED (13) leaves both outputs untouched. For
/// an authorized whole-family query with a valid cursor, an unbuilt family returns UNSUPPORTED (95)
/// with a supported=false, enabled=false page when it fits. An unsupported exact-function query returns
/// 95 without writing the page or length. A built but disabled family can return zero with
/// enabled=false.
pub const report = raw.@"permission.report";
