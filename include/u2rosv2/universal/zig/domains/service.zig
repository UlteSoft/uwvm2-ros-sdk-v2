//! ROSv2 service imports generated from src/abi/contract.json.

const raw = struct {
    extern "uwvm_ros_v2" fn @"service.abandon"(cap: u64, memory: u32, request: u64, size: u64, output: u64, capacity: u64, length_output: u64) u32;
    extern "uwvm_ros_v2" fn @"service.acknowledge"(cap: u64, memory: u32, request: u64, size: u64, output: u64, capacity: u64, length_output: u64) u32;
    extern "uwvm_ros_v2" fn @"service.available"(cap: u64, memory: u32, request: u64, size: u64, output: u64, capacity: u64, length_output: u64) u32;
    extern "uwvm_ros_v2" fn @"service.describe"(cap: u64, memory: u32, request: u64, size: u64, output: u64, capacity: u64, length_output: u64) u32;
    extern "uwvm_ros_v2" fn @"service.open"(cap: u64, memory: u32, request: u64, size: u64, output: u64, capacity: u64, length_output: u64) u32;
    extern "uwvm_ros_v2" fn @"service.release"(cap: u64, memory: u32, request: u64, size: u64, output: u64, capacity: u64, length_output: u64) u32;
    extern "uwvm_ros_v2" fn @"service.reserve"(cap: u64, memory: u32, request: u64, size: u64, output: u64, capacity: u64, length_output: u64) u32;
    extern "uwvm_ros_v2" fn @"service.respond"(cap: u64, memory: u32, request: u64, size: u64, output: u64, capacity: u64, length_output: u64) u32;
    extern "uwvm_ros_v2" fn @"service.submit"(cap: u64, memory: u32, request: u64, size: u64, output: u64, capacity: u64, length_output: u64) u32;
    extern "uwvm_ros_v2" fn @"service.take"(cap: u64, memory: u32, request: u64, size: u64, output: u64, capacity: u64, length_output: u64) u32;
};

/// service.abandon. Retire local wait/response interest; never claim remote cancellation.
/// The caller must belong to the capability's environment. The deployment must expose service.abandon
/// and the grant must authorize service.abandon. Applicable grant purposes include service.
/// Keep the request readable, the full reply capacity writable and the eight-byte length slot writable
/// through the call. Preserve WasmMTE tags on all addresses. Request and reply may overlap because the
/// VM copies the request before delivery. The length slot must be disjoint from both ranges after
/// address normalization. An overlap with the slot returns INVALID (22).
/// `cap` — Capability handle for the service.abandon action in the caller's environment.
/// `memory` — Index of the caller's linear memory containing all three spans.
/// `request` — Guest address of the encoded request. Wire order is `client` (`u64`), `request` (`u64`).
/// `size` — Exact request length, 16 bytes.
/// `output` — Guest address of the writable result. Wire order is `receipt` (`receipt`).
/// `capacity` — Byte capacity of the full writable reply range, at most 4194304.
/// `length_output` — Guest address of the writable little-endian u64 byte count. On delivery it records
/// the number of bytes written to the reply.
/// Result. Zero on success, otherwise a scene status. A short reply returns TOO_LARGE (90) with the
/// required capacity or minimum in the length slot. Other limits may return 90 before a useful size is
/// available. Inspect the delivered receipt for the operation's outcome.
pub const abandon = raw.@"service.abandon";

/// service.acknowledge. Consume exactly the previously reserved record after guest processing. Exact
/// replay is idempotent; stale generation, wrong consumer, altered nonce or expired reservation is
/// refused. Lost native ACK is outcome_unknown and never triggers blind re-consumption. Bounded receipt
/// survives failed guest delivery.
/// The caller must belong to the capability's environment. The deployment must expose
/// service.acknowledge and the grant must authorize service.acknowledge. Applicable grant purposes
/// include service.
/// Keep the request readable, the full reply capacity writable and the eight-byte length slot writable
/// through the call. Preserve WasmMTE tags on all addresses. Request and reply may overlap because the
/// VM copies the request before delivery. The length slot must be disjoint from both ranges after
/// address normalization. An overlap with the slot returns INVALID (22).
/// `cap` — Capability handle for the service.acknowledge action in the caller's environment.
/// `memory` — Index of the caller's linear memory containing all three spans.
/// `request` — Guest address of the encoded request. Wire order is `key` (`request_key`), `reservation`
/// (`reservation_ref`).
/// `size` — Byte length of the complete encoded request. The carrier accepts at most 4194304 bytes.
/// `output` — Guest address of the writable result. Wire order is `receipt` (`receipt`).
/// `capacity` — Byte capacity of the full writable reply range, at most 4194304.
/// `length_output` — Guest address of the writable little-endian u64 byte count. On delivery it records
/// the number of bytes written to the reply.
/// Result. Zero on success, otherwise a scene status. A short reply returns TOO_LARGE (90) with the
/// required capacity or minimum in the length slot. Other limits may return 90 before a useful size is
/// available. Inspect the delivered receipt for the operation's outcome.
pub const acknowledge = raw.@"service.acknowledge";

/// service.available. Observe native readiness on the exact live client. Direct client grants supply
/// source_capability zero. A service-observer grant requires its separately authorized registered
/// source service.submit capability. Only the observer is charged. Either authorization may prevent
/// result delivery.
/// The caller must belong to the capability's environment. The deployment must expose service.available
/// and the grant must authorize service.available. Applicable grant purposes include service.
/// Keep the request readable, the full reply capacity writable and the eight-byte length slot writable
/// through the call. Preserve WasmMTE tags on all addresses. Request and reply may overlap because the
/// VM copies the request before delivery. The length slot must be disjoint from both ranges after
/// address normalization. An overlap with the slot returns INVALID (22).
/// `cap` — Capability handle for the service.available action in the caller's environment.
/// `memory` — Index of the caller's linear memory containing all three spans.
/// `request` — Guest address of the encoded request. Wire order is `client` (`u64`),
/// `source_capability` (`u64`).
/// `size` — Exact request length, 16 bytes.
/// `output` — Guest address of the writable result. Wire order is `available` (`bool`), `observed`
/// (`stamp`).
/// `capacity` — Byte capacity of the full writable reply range, at most 4194304. The fixed result
/// occupies 32 bytes.
/// `length_output` — Guest address of the writable little-endian u64 byte count. On delivery it records
/// the number of bytes written to the reply.
/// Result. Zero on success, otherwise a scene status. A short reply returns TOO_LARGE (90) with the
/// required capacity or minimum in the length slot. Other limits may return 90 before a useful size is
/// available.
pub const available = raw.@"service.available";

/// service.describe. Inspect the exact retained native client/server endpoint and each request/response
/// QoS leg. Support/absence is explicit; profile configuration never stands in for actual getter
/// evidence. Observation grants no submission, response, borrow or discovery authority.
/// The caller must belong to the capability's environment. The deployment must expose service.describe
/// and the grant must authorize service.describe. Applicable grant purposes include service.
/// Keep the request readable, the full reply capacity writable and the eight-byte length slot writable
/// through the call. Preserve WasmMTE tags on all addresses. Request and reply may overlap because the
/// VM copies the request before delivery. The length slot must be disjoint from both ranges after
/// address normalization. An overlap with the slot returns INVALID (22).
/// `cap` — Capability handle for the service.describe action in the caller's environment.
/// `memory` — Index of the caller's linear memory containing all three spans.
/// `request` — Guest address of the encoded request. Wire order is `endpoint` (`u64`).
/// `size` — Exact request length, 8 bytes.
/// `output` — Guest address of the writable result. Wire order is `endpoint` (`endpoint_info`),
/// `channels` (`array<endpoint_qos_profile>`).
/// `capacity` — Byte capacity of the full writable reply range, at most 4194304.
/// `length_output` — Guest address of the writable little-endian u64 byte count. On delivery it records
/// the number of bytes written to the reply.
/// Result. Zero on success, otherwise a scene status. A short reply returns TOO_LARGE (90) with the
/// required capacity or minimum in the length slot. Other limits may return 90 before a useful size is
/// available.
pub const describe = raw.@"service.describe";

/// service.open. Fix client/server role and finite request/response capacities. Creation is
/// asynchronous: explicit monotonically increasing key and finite absolute steady deadline; response is
/// a request receipt, not an endpoint. communication.open.take retrieves a separately published typed
/// handle.
/// The caller must belong to the capability's environment. The deployment must expose service.open and
/// the grant must authorize service.open. Applicable grant purposes include service. Depending on the
/// selected inputs and plan, the VM also checks node.open, type.describe.
/// Keep the request readable, the full reply capacity writable and the eight-byte length slot writable
/// through the call. Preserve WasmMTE tags on all addresses. Request and reply may overlap because the
/// VM copies the request before delivery. The length slot must be disjoint from both ranges after
/// address normalization. An overlap with the slot returns INVALID (22).
/// `cap` — Capability handle for the service.open action in the caller's environment.
/// `memory` — Index of the caller's linear memory containing all three spans.
/// `request` — Guest address of the encoded request. Wire order is `endpoint` (`endpoint_request`),
/// `creation_key` (`u64`), `deadline` (`u64`).
/// `size` — Byte length of the complete encoded request. The carrier accepts at most 4194304 bytes.
/// `output` — Guest address of the writable result. Wire order is `creation`
/// (`communication_creation_receipt`).
/// `capacity` — Byte capacity of the full writable reply range, at most 4194304. The fixed result
/// occupies 48 bytes.
/// `length_output` — Guest address of the writable little-endian u64 byte count. On delivery it records
/// the number of bytes written to the reply.
/// Result. Zero on success, otherwise a scene status. A short reply returns TOO_LARGE (90) with the
/// required capacity or minimum in the length slot. Other limits may return 90 before a useful size is
/// available. Inspect the delivered receipt for the operation's outcome.
pub const open = raw.@"service.open";

/// service.release. Cancel exactly the owned borrow while retaining the original record. This is not
/// service-request cancellation or endpoint close. Cleanup uses pre-reserved capacity and is not
/// throttled by creation/traffic quotas; uncertain native cancellation retains debt until trusted
/// reconciliation.
/// The caller must belong to the capability's environment. The deployment must expose service.release
/// and the grant must authorize service.release. Applicable grant purposes include service.
/// Keep the request readable, the full reply capacity writable and the eight-byte length slot writable
/// through the call. Preserve WasmMTE tags on all addresses. Request and reply may overlap because the
/// VM copies the request before delivery. The length slot must be disjoint from both ranges after
/// address normalization. An overlap with the slot returns INVALID (22).
/// `cap` — Capability handle for the service.release action in the caller's environment.
/// `memory` — Index of the caller's linear memory containing all three spans.
/// `request` — Guest address of the encoded request. Wire order is `key` (`request_key`), `reservation`
/// (`reservation_ref`).
/// `size` — Byte length of the complete encoded request. The carrier accepts at most 4194304 bytes.
/// `output` — Guest address of the writable result. Wire order is `receipt` (`receipt`).
/// `capacity` — Byte capacity of the full writable reply range, at most 4194304.
/// `length_output` — Guest address of the writable little-endian u64 byte count. On delivery it records
/// the number of bytes written to the reply.
/// Result. Zero on success, otherwise a scene status. A short reply returns TOO_LARGE (90) with the
/// required capacity or minimum in the length slot. Other limits may return 90 before a useful size is
/// available. Inspect the delivered receipt for the operation's outcome.
pub const release = raw.@"service.release";

/// service.reserve. Explicit two-phase receive: independently authorize the exact consumer endpoint,
/// retain the original native record and deliver a bounded detached copy without acknowledgement.
/// Same-consumer retry returns the retained record/nonce; concurrent consumers cannot steal it. Both
/// node/context/schema origins and native metadata remain attached.
/// The caller must belong to the capability's environment. The deployment must expose service.reserve
/// and the grant must authorize service.reserve. Applicable grant purposes include service.
/// Keep the request readable, the full reply capacity writable and the eight-byte length slot writable
/// through the call. Preserve WasmMTE tags on all addresses. Request and reply may overlap because the
/// VM copies the request before delivery. The length slot must be disjoint from both ranges after
/// address normalization. An overlap with the slot returns INVALID (22).
/// `cap` — Capability handle for the service.reserve action in the caller's environment.
/// `memory` — Index of the caller's linear memory containing all three spans.
/// `request` — Guest address of the encoded request. Wire order is `endpoint` (`u64`), `deadline`
/// (`u64`).
/// `size` — Exact request length, 16 bytes.
/// `output` — Guest address of the writable result. Wire order is `reservation`
/// (`delivery_reservation`).
/// `capacity` — Byte capacity of the full writable reply range, at most 4194304.
/// `length_output` — Guest address of the writable little-endian u64 byte count. On delivery it records
/// the number of bytes written to the reply.
/// Result. Zero on success, otherwise a scene status. A short reply returns TOO_LARGE (90) with the
/// required capacity or minimum in the length slot. Other limits may return 90 before a useful size is
/// available. The reservation remains owned until acknowledgement or release.
pub const reserve = raw.@"service.reserve";

/// service.respond. Respond once to an exact live owned received request.
/// The caller must belong to the capability's environment. The deployment must expose service.respond
/// and the grant must authorize service.respond. Applicable grant purposes include service.
/// Keep the request readable, the full reply capacity writable and the eight-byte length slot writable
/// through the call. Preserve WasmMTE tags on all addresses. Request and reply may overlap because the
/// VM copies the request before delivery. The length slot must be disjoint from both ranges after
/// address normalization. An overlap with the slot returns INVALID (22).
/// `cap` — Capability handle for the service.respond action in the caller's environment.
/// `memory` — Index of the caller's linear memory containing all three spans.
/// `request` — Guest address of the encoded request. Wire order is `key` (`request_key`), `server`
/// (`u64`), `request` (`u64`), `body` (`message`), `deadline` (`u64`).
/// `size` — Byte length of the complete encoded request. The carrier accepts at most 4194304 bytes.
/// `output` — Guest address of the writable result. Wire order is `receipt` (`receipt`).
/// `capacity` — Byte capacity of the full writable reply range, at most 4194304.
/// `length_output` — Guest address of the writable little-endian u64 byte count. On delivery it records
/// the number of bytes written to the reply.
/// Result. Zero on success, otherwise a scene status. A short reply returns TOO_LARGE (90) with the
/// required capacity or minimum in the length slot. Other limits may return 90 before a useful size is
/// available. Inspect the delivered receipt for the operation's outcome.
pub const respond = raw.@"service.respond";

/// service.submit. Owned native-correlated request; remote outcome can remain unknown after timeout.
/// The caller must belong to the capability's environment. The deployment must expose service.submit
/// and the grant must authorize service.submit. Applicable grant purposes include service.
/// Keep the request readable, the full reply capacity writable and the eight-byte length slot writable
/// through the call. Preserve WasmMTE tags on all addresses. Request and reply may overlap because the
/// VM copies the request before delivery. The length slot must be disjoint from both ranges after
/// address normalization. An overlap with the slot returns INVALID (22).
/// `cap` — Capability handle for the service.submit action in the caller's environment.
/// `memory` — Index of the caller's linear memory containing all three spans.
/// `request` — Guest address of the encoded request. Wire order is `key` (`request_key`), `client`
/// (`u64`), `body` (`message`), `deadline` (`u64`).
/// `size` — Byte length of the complete encoded request. The carrier accepts at most 4194304 bytes.
/// `output` — Guest address of the writable result. Wire order is `receipt` (`receipt`).
/// `capacity` — Byte capacity of the full writable reply range, at most 4194304.
/// `length_output` — Guest address of the writable little-endian u64 byte count. On delivery it records
/// the number of bytes written to the reply.
/// Result. Zero on success, otherwise a scene status. A short reply returns TOO_LARGE (90) with the
/// required capacity or minimum in the length slot. Other limits may return 90 before a useful size is
/// available. Inspect the delivered receipt for the operation's outcome.
pub const submit = raw.@"service.submit";

/// service.take. Role-specific request/response atomically delivered with correlation.
/// The caller must belong to the capability's environment. The deployment must expose service.take and
/// the grant must authorize service.take. Applicable grant purposes include service.
/// Keep the request readable, the full reply capacity writable and the eight-byte length slot writable
/// through the call. Preserve WasmMTE tags on all addresses. Request and reply may overlap because the
/// VM copies the request before delivery. The length slot must be disjoint from both ranges after
/// address normalization. An overlap with the slot returns INVALID (22).
/// `cap` — Capability handle for the service.take action in the caller's environment.
/// `memory` — Index of the caller's linear memory containing all three spans.
/// `request` — Guest address of the encoded request. Wire order is `endpoint` (`u64`).
/// `size` — Exact request length, 8 bytes.
/// `output` — Guest address of the writable result. Wire order is `record` (`delivery`).
/// `capacity` — Byte capacity of the full writable reply range, at most 4194304.
/// `length_output` — Guest address of the writable little-endian u64 byte count. On delivery it records
/// the number of bytes written to the reply.
/// Result. Zero on success, otherwise a scene status. A short reply returns TOO_LARGE (90) with the
/// required capacity or minimum in the length slot. Other limits may return 90 before a useful size is
/// available.
pub const take = raw.@"service.take";
