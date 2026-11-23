//! ROSv2 parameter imports generated from src/abi/contract.json.

const raw = struct {
    extern "uwvm_ros_v2" fn @"parameter.declare"(cap: u64, memory: u32, request: u64, size: u64, output: u64, capacity: u64, length_output: u64) u32;
    extern "uwvm_ros_v2" fn @"parameter.describe"(cap: u64, memory: u32, request: u64, size: u64, output: u64, capacity: u64, length_output: u64) u32;
    extern "uwvm_ros_v2" fn @"parameter.exists"(cap: u64, memory: u32, request: u64, size: u64, output: u64, capacity: u64, length_output: u64) u32;
    extern "uwvm_ros_v2" fn @"parameter.get"(cap: u64, memory: u32, request: u64, size: u64, output: u64, capacity: u64, length_output: u64) u32;
    extern "uwvm_ros_v2" fn @"parameter.list"(cap: u64, memory: u32, request: u64, size: u64, output: u64, capacity: u64, length_output: u64) u32;
    extern "uwvm_ros_v2" fn @"parameter.open"(cap: u64, memory: u32, request: u64, size: u64, output: u64, capacity: u64, length_output: u64) u32;
    extern "uwvm_ros_v2" fn @"parameter.respond"(cap: u64, memory: u32, request: u64, size: u64, output: u64, capacity: u64, length_output: u64) u32;
    extern "uwvm_ros_v2" fn @"parameter.search"(cap: u64, memory: u32, request: u64, size: u64, output: u64, capacity: u64, length_output: u64) u32;
    extern "uwvm_ros_v2" fn @"parameter.set"(cap: u64, memory: u32, request: u64, size: u64, output: u64, capacity: u64, length_output: u64) u32;
    extern "uwvm_ros_v2" fn @"parameter.set.atomic"(cap: u64, memory: u32, request: u64, size: u64, output: u64, capacity: u64, length_output: u64) u32;
    extern "uwvm_ros_v2" fn @"parameter.take"(cap: u64, memory: u32, request: u64, size: u64, output: u64, capacity: u64, length_output: u64) u32;
    extern "uwvm_ros_v2" fn @"parameter.undeclare"(cap: u64, memory: u32, request: u64, size: u64, output: u64, capacity: u64, length_output: u64) u32;
};

/// parameter.declare. Declaration respects override/dynamic/read-only policy without ambient YAML
/// access.
/// The caller must belong to the capability's environment. The deployment must expose parameter.declare
/// and the grant must authorize parameter.declare. Applicable grant purposes include parameter.
/// Keep the request readable, the full reply capacity writable and the eight-byte length slot writable
/// through the call. Preserve WasmMTE tags on all addresses. Request and reply may overlap because the
/// VM copies the request before delivery. The length slot must be disjoint from both ranges after
/// address normalization. An overlap with the slot returns INVALID (22).
/// `cap` — Capability handle for the parameter.declare action in the caller's environment.
/// `memory` — Index of the caller's linear memory containing all three spans.
/// `request` — Guest address of the encoded request. Wire order is `key` (`request_key`), `scope`
/// (`u64`), `descriptor` (`parameter_descriptor`), `initial` (`parameter_value`).
/// `size` — Byte length of the complete encoded request. The carrier accepts at most 4194304 bytes.
/// `output` — Guest address of the writable result. Wire order is `receipt` (`receipt`).
/// `capacity` — Byte capacity of the full writable reply range, at most 4194304.
/// `length_output` — Guest address of the writable little-endian u64 byte count. On delivery it records
/// the number of bytes written to the reply.
/// Result. Zero on success, otherwise a scene status. A short reply returns TOO_LARGE (90) with the
/// required capacity or minimum in the length slot. Other limits may return 90 before a useful size is
/// available. Inspect the delivered receipt for the operation's outcome.
pub const declare = raw.@"parameter.declare";

/// parameter.describe. Only granted descriptor metadata.
/// The caller must belong to the capability's environment. The deployment must expose
/// parameter.describe and the grant must authorize parameter.describe. Applicable grant purposes
/// include parameter.
/// Keep the request readable, the full reply capacity writable and the eight-byte length slot writable
/// through the call. Preserve WasmMTE tags on all addresses. Request and reply may overlap because the
/// VM copies the request before delivery. The length slot must be disjoint from both ranges after
/// address normalization. An overlap with the slot returns INVALID (22).
/// `cap` — Capability handle for the parameter.describe action in the caller's environment.
/// `memory` — Index of the caller's linear memory containing all three spans.
/// `request` — Guest address of the encoded request. Wire order is `scope` (`u64`), `names`
/// (`array<text>`).
/// `size` — Byte length of the complete encoded request. The carrier accepts at most 4194304 bytes.
/// `output` — Guest address of the writable result. Wire order is `descriptors`
/// (`array<parameter_descriptor>`).
/// `capacity` — Byte capacity of the full writable reply range, at most 4194304.
/// `length_output` — Guest address of the writable little-endian u64 byte count. On delivery it records
/// the number of bytes written to the reply.
/// Result. Zero on success, otherwise a scene status. A short reply returns TOO_LARGE (90) with the
/// required capacity or minimum in the length slot. Other limits may return 90 before a useful size is
/// available.
pub const describe = raw.@"parameter.describe";

/// parameter.exists. Authorize the exact resolved key before existence lookup. Read-only existence
/// authority reveals neither value nor descriptor and is independent of get/list. Missing,
/// uninitialized and denied are distinct; denied never returns false as if absent.
/// The caller must belong to the capability's environment. The deployment must expose parameter.exists
/// and the grant must authorize parameter.exists. Applicable grant purposes include parameter.
/// Keep the request readable, the full reply capacity writable and the eight-byte length slot writable
/// through the call. Preserve WasmMTE tags on all addresses. Request and reply may overlap because the
/// VM copies the request before delivery. The length slot must be disjoint from both ranges after
/// address normalization. An overlap with the slot returns INVALID (22).
/// `cap` — Capability handle for the parameter.exists action in the caller's environment.
/// `memory` — Index of the caller's linear memory containing all three spans.
/// `request` — Guest address of the encoded request. Wire order is `scope` (`u64`), `name` (`text`).
/// `size` — Byte length of the complete encoded request. The carrier accepts at most 4194304 bytes.
/// `output` — Guest address of the writable result. Wire order is `exists` (`bool`), `initialized`
/// (`bool`), `snapshot_revision` (`u64`).
/// `capacity` — Byte capacity of the full writable reply range, at most 4194304. The fixed result
/// occupies 24 bytes.
/// `length_output` — Guest address of the writable little-endian u64 byte count. On delivery it records
/// the number of bytes written to the reply.
/// Result. Zero on success, otherwise a scene status. A short reply returns TOO_LARGE (90) with the
/// required capacity or minimum in the length slot. Other limits may return 90 before a useful size is
/// available.
pub const exists = raw.@"parameter.exists";

/// parameter.get. Bounded batch; missing/uninitialized/denied are not silently conflated.
/// The caller must belong to the capability's environment. The deployment must expose parameter.get and
/// the grant must authorize parameter.get. Applicable grant purposes include parameter.
/// Keep the request readable, the full reply capacity writable and the eight-byte length slot writable
/// through the call. Preserve WasmMTE tags on all addresses. Request and reply may overlap because the
/// VM copies the request before delivery. The length slot must be disjoint from both ranges after
/// address normalization. An overlap with the slot returns INVALID (22).
/// `cap` — Capability handle for the parameter.get action in the caller's environment.
/// `memory` — Index of the caller's linear memory containing all three spans.
/// `request` — Guest address of the encoded request. Wire order is `scope` (`u64`), `names`
/// (`array<text>`).
/// `size` — Byte length of the complete encoded request. The carrier accepts at most 4194304 bytes.
/// `output` — Guest address of the writable result. Wire order is `values` (`array<parameter_item>`),
/// `revision` (`optional<u64>`).
/// `capacity` — Byte capacity of the full writable reply range, at most 4194304.
/// `length_output` — Guest address of the writable little-endian u64 byte count. On delivery it records
/// the number of bytes written to the reply.
/// Result. Zero on success, otherwise a scene status. A short reply returns TOO_LARGE (90) with the
/// required capacity or minimum in the length slot. Other limits may return 90 before a useful size is
/// available.
pub const get = raw.@"parameter.get";

/// parameter.list. Bounded filtered key listing; counts and cursors obey same visibility. Name entries
/// use fixed message type_identity ros.parameter.name and encoding canonical.text; each body is exactly
/// one canonical wire text.
/// The caller must belong to the capability's environment. The deployment must expose parameter.list
/// and the grant must authorize parameter.list. Applicable grant purposes include parameter.
/// Keep the request readable, the full reply capacity writable and the eight-byte length slot writable
/// through the call. Preserve WasmMTE tags on all addresses. Request and reply may overlap because the
/// VM copies the request before delivery. The length slot must be disjoint from both ranges after
/// address normalization. An overlap with the slot returns INVALID (22).
/// `cap` — Capability handle for the parameter.list action in the caller's environment.
/// `memory` — Index of the caller's linear memory containing all three spans.
/// `request` — Guest address of the encoded request. Wire order is `scope` (`u64`), `prefixes`
/// (`array<text>`), `depth` (`u64`), `cursor` (`optional<u64>`), `limit` (`u64`).
/// `size` — Byte length of the complete encoded request. The carrier accepts at most 4194304 bytes.
/// `output` — Guest address of the writable result. Wire order is `page` (`page`).
/// `capacity` — Byte capacity of the full writable reply range, at most 4194304.
/// `length_output` — Guest address of the writable little-endian u64 byte count. On delivery it records
/// the number of bytes written to the reply.
/// Result. Zero on success, otherwise a scene status. A short reply returns TOO_LARGE (90) with the
/// required capacity or minimum in the length slot. Other limits may return 90 before a useful size is
/// available.
pub const list = raw.@"parameter.list";

/// parameter.open. Bind exact parameter keys, value algebra, descriptors and role.
/// The caller must belong to the capability's environment. The deployment must expose parameter.open
/// and the grant must authorize parameter.open. Applicable grant purposes include parameter. Depending
/// on the selected inputs and plan, the VM also checks node.open.
/// Keep the request readable, the full reply capacity writable and the eight-byte length slot writable
/// through the call. Preserve WasmMTE tags on all addresses. Request and reply may overlap because the
/// VM copies the request before delivery. The length slot must be disjoint from both ranges after
/// address normalization. An overlap with the slot returns INVALID (22).
/// `cap` — Capability handle for the parameter.open action in the caller's environment.
/// `memory` — Index of the caller's linear memory containing all three spans.
/// `request` — Guest address of the encoded request. Wire order is `node_capability` (`u64`), `node`
/// (`u64`), `profile` (`profile`).
/// `size` — Byte length of the complete encoded request. The carrier accepts at most 4194304 bytes.
/// `output` — Guest address of the writable result. Wire order is `handle` (`u64`).
/// `capacity` — Byte capacity of the full writable reply range, at most 4194304. The fixed result
/// occupies 8 bytes.
/// `length_output` — Guest address of the writable little-endian u64 byte count. On delivery it records
/// the number of bytes written to the reply.
/// Result. Zero on success, otherwise a scene status. A short reply returns TOO_LARGE (90) with the
/// required capacity or minimum in the length slot. Other limits may return 90 before a useful size is
/// available.
pub const open = raw.@"parameter.open";

/// parameter.respond. Current validator generation/deadline; transformed keys and values revalidated;
/// no recursive mutation.
/// The caller must belong to the capability's environment. The deployment must expose parameter.respond
/// and the grant must authorize parameter.respond. Applicable grant purposes include parameter.
/// Keep the request readable, the full reply capacity writable and the eight-byte length slot writable
/// through the call. Preserve WasmMTE tags on all addresses. Request and reply may overlap because the
/// VM copies the request before delivery. The length slot must be disjoint from both ranges after
/// address normalization. An overlap with the slot returns INVALID (22).
/// `cap` — Capability handle for the parameter.respond action in the caller's environment.
/// `memory` — Index of the caller's linear memory containing all three spans.
/// `request` — Guest address of the encoded request. Wire order is `scope` (`u64`), `request` (`u64`),
/// `accepted` (`bool`), `replacement` (`optional<array<parameter_item>>`), `reason` (`text`).
/// `size` — Byte length of the complete encoded request. The carrier accepts at most 4194304 bytes.
/// `output` — Guest address of the writable result. Wire order is `receipt` (`receipt`).
/// `capacity` — Byte capacity of the full writable reply range, at most 4194304.
/// `length_output` — Guest address of the writable little-endian u64 byte count. On delivery it records
/// the number of bytes written to the reply.
/// Result. Zero on success, otherwise a scene status. A short reply returns TOO_LARGE (90) with the
/// required capacity or minimum in the length slot. Other limits may return 90 before a useful size is
/// available. Inspect the delivered receipt for the operation's outcome.
pub const respond = raw.@"parameter.respond";

/// parameter.search. ROS1 ancestor search within a deployment-fixed canonical namespace root and finite
/// candidate-count bound, including the starting namespace. Authorize each exact candidate key before
/// existence lookup; return denied at the first unauthorized candidate. Exhaustion returns too_large;
/// only reaching the root with no match returns not-found. One coherent local store snapshot supplies a
/// revision even for negative results. No ambient namespace, filesystem path or unrestricted discovery.
/// This local provider does not impersonate a native parameter server.
/// The caller must belong to the capability's environment. The deployment must expose parameter.search
/// and the grant must authorize parameter.search. Applicable grant purposes include parameter.
/// Keep the request readable, the full reply capacity writable and the eight-byte length slot writable
/// through the call. Preserve WasmMTE tags on all addresses. Request and reply may overlap because the
/// VM copies the request before delivery. The length slot must be disjoint from both ranges after
/// address normalization. An overlap with the slot returns INVALID (22).
/// `cap` — Capability handle for the parameter.search action in the caller's environment.
/// `memory` — Index of the caller's linear memory containing all three spans.
/// `request` — Guest address of the encoded request. Wire order is `scope` (`u64`), `name` (`text`),
/// `start_namespace` (`text`).
/// `size` — Byte length of the complete encoded request. The carrier accepts at most 4194304 bytes.
/// `output` — Guest address of the writable result. Wire order is `resolved_name` (`optional<text>`),
/// `snapshot_revision` (`u64`).
/// `capacity` — Byte capacity of the full writable reply range, at most 4194304.
/// `length_output` — Guest address of the writable little-endian u64 byte count. On delivery it records
/// the number of bytes written to the reply.
/// Result. Zero on success, otherwise a scene status. A short reply returns TOO_LARGE (90) with the
/// required capacity or minimum in the length slot. Other limits may return 90 before a useful size is
/// available.
pub const search = raw.@"parameter.search";

/// parameter.set. Per-item writes; report every committed/rejected/unknown decision.
/// The caller must belong to the capability's environment. The deployment must expose parameter.set and
/// the grant must authorize parameter.set. Applicable grant purposes include parameter.
/// Keep the request readable, the full reply capacity writable and the eight-byte length slot writable
/// through the call. Preserve WasmMTE tags on all addresses. Request and reply may overlap because the
/// VM copies the request before delivery. The length slot must be disjoint from both ranges after
/// address normalization. An overlap with the slot returns INVALID (22).
/// `cap` — Capability handle for the parameter.set action in the caller's environment.
/// `memory` — Index of the caller's linear memory containing all three spans.
/// `request` — Guest address of the encoded request. Wire order is `transaction`
/// (`parameter_transaction`).
/// `size` — Byte length of the complete encoded request. The carrier accepts at most 4194304 bytes.
/// `output` — Guest address of the writable result. Wire order is `receipt` (`receipt`), `decisions`
/// (`array<parameter_decision>`).
/// `capacity` — Byte capacity of the full writable reply range, at most 4194304.
/// `length_output` — Guest address of the writable little-endian u64 byte count. On delivery it records
/// the number of bytes written to the reply.
/// Result. Zero on success, otherwise a scene status. A short reply returns TOO_LARGE (90) with the
/// required capacity or minimum in the length slot. Other limits may return 90 before a useful size is
/// available. Inspect the delivered receipt for the operation's outcome.
pub const set = raw.@"parameter.set";

/// parameter.set.atomic. All or none only within qualified provider atomic domain; do not fake
/// cross-node CAS. A ROS1 provider must separately declare atomic upsert of permitted undeclared keys
/// and subtree replacement semantics; ROS2 declaration rules remain distinct. Native bridging cannot
/// silently emulate atomic upsert with a racy get/declare/set sequence.
/// The caller must belong to the capability's environment. The deployment must expose
/// parameter.set.atomic and the grant must authorize parameter.set.atomic. Applicable grant purposes
/// include parameter.
/// Keep the request readable, the full reply capacity writable and the eight-byte length slot writable
/// through the call. Preserve WasmMTE tags on all addresses. Request and reply may overlap because the
/// VM copies the request before delivery. The length slot must be disjoint from both ranges after
/// address normalization. An overlap with the slot returns INVALID (22).
/// `cap` — Capability handle for the parameter.set.atomic action in the caller's environment.
/// `memory` — Index of the caller's linear memory containing all three spans.
/// `request` — Guest address of the encoded request. Wire order is `transaction`
/// (`parameter_transaction`).
/// `size` — Byte length of the complete encoded request. The carrier accepts at most 4194304 bytes.
/// `output` — Guest address of the writable result. Wire order is `receipt` (`receipt`), `accepted`
/// (`bool`).
/// `capacity` — Byte capacity of the full writable reply range, at most 4194304.
/// `length_output` — Guest address of the writable little-endian u64 byte count. On delivery it records
/// the number of bytes written to the reply.
/// Result. Zero on success, otherwise a scene status. A short reply returns TOO_LARGE (90) with the
/// required capacity or minimum in the length slot. Other limits may return 90 before a useful size is
/// available. Inspect the delivered receipt for the operation's outcome.
pub const set_atomic = raw.@"parameter.set.atomic";

/// parameter.take. Deliver validation or committed event; no native callback into guest.
/// The caller must belong to the capability's environment. The deployment must expose parameter.take
/// and the grant must authorize parameter.take. Applicable grant purposes include parameter.
/// Keep the request readable, the full reply capacity writable and the eight-byte length slot writable
/// through the call. Preserve WasmMTE tags on all addresses. Request and reply may overlap because the
/// VM copies the request before delivery. The length slot must be disjoint from both ranges after
/// address normalization. An overlap with the slot returns INVALID (22).
/// `cap` — Capability handle for the parameter.take action in the caller's environment.
/// `memory` — Index of the caller's linear memory containing all three spans.
/// `request` — Guest address of the encoded request. Wire order is `scope` (`u64`).
/// `size` — Exact request length, 8 bytes.
/// `output` — Guest address of the writable result. Wire order is `event` (`parameter_event`).
/// `capacity` — Byte capacity of the full writable reply range, at most 4194304.
/// `length_output` — Guest address of the writable little-endian u64 byte count. On delivery it records
/// the number of bytes written to the reply.
/// Result. Zero on success, otherwise a scene status. A short reply returns TOO_LARGE (90) with the
/// required capacity or minimum in the length slot. Other limits may return 90 before a useful size is
/// available.
pub const take = raw.@"parameter.take";

/// parameter.undeclare. Explicit deletion distinct from not-set/uninitialized value.
/// The caller must belong to the capability's environment. The deployment must expose
/// parameter.undeclare and the grant must authorize parameter.undeclare. Applicable grant purposes
/// include parameter.
/// Keep the request readable, the full reply capacity writable and the eight-byte length slot writable
/// through the call. Preserve WasmMTE tags on all addresses. Request and reply may overlap because the
/// VM copies the request before delivery. The length slot must be disjoint from both ranges after
/// address normalization. An overlap with the slot returns INVALID (22).
/// `cap` — Capability handle for the parameter.undeclare action in the caller's environment.
/// `memory` — Index of the caller's linear memory containing all three spans.
/// `request` — Guest address of the encoded request. Wire order is `key` (`request_key`), `scope`
/// (`u64`), `name` (`text`), `expected_revision` (`optional<u64>`).
/// `size` — Byte length of the complete encoded request. The carrier accepts at most 4194304 bytes.
/// `output` — Guest address of the writable result. Wire order is `receipt` (`receipt`).
/// `capacity` — Byte capacity of the full writable reply range, at most 4194304.
/// `length_output` — Guest address of the writable little-endian u64 byte count. On delivery it records
/// the number of bytes written to the reply.
/// Result. Zero on success, otherwise a scene status. A short reply returns TOO_LARGE (90) with the
/// required capacity or minimum in the length slot. Other limits may return 90 before a useful size is
/// available. Inspect the delivered receipt for the operation's outcome.
pub const undeclare = raw.@"parameter.undeclare";
