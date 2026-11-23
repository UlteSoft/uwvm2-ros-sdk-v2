;; Generated from src/abi/contract.json. Copy the required imports into the calling
;; guest and declare each one with wrwat --ros-operation. Guest addresses refer to
;; the immediate caller's linear memory.
(module

  ;; communication.open.cancel. Independent exact origin action and complete caller/incarnation
  ;; checks. Take publishes a typed endpoint only after fresh origin admission; cancelled/unknown
  ;; work retains native cleanup debt and never refunds creation work.
  ;;
  ;; The caller must belong to the capability's environment. The deployment must expose
  ;; communication.open.cancel and the grant must authorize communication.open.cancel. Applicable
  ;; grant purposes include node, topic, service, action. Depending on the selected inputs and plan,
  ;; the VM also checks node.open.
  ;;
  ;; Use the ordered wire record. Scalars are little-endian. Text and byte strings carry a u64
  ;; byte-length prefix.
  ;;
  ;; Keep the request readable, the full reply capacity writable and the eight-byte length slot
  ;; writable through the call. Preserve WasmMTE tags on all addresses. Request and reply may overlap
  ;; because the VM copies the request before delivery. The length slot must be disjoint from both
  ;; ranges after address normalization. An overlap with the slot returns INVALID (22).
  ;;
  ;; @param $cap - (i64) Capability handle for the communication.open.cancel action in the caller's
  ;;   environment.
  ;; @param $memory - (i32) Index of the caller's linear memory containing all three spans.
  ;; @param $request - (i64) Guest address of the encoded request. Wire order is `request` (`u64`).
  ;; @param $size - (i64) Exact request length, 8 bytes.
  ;; @param $output - (i64) Guest address of the writable result. Wire order is `creation`
  ;;   (`communication_creation_receipt`).
  ;; @param $capacity - (i64) Byte capacity of the full writable reply range, at most 4194304. The
  ;;   fixed result occupies 48 bytes.
  ;; @param $length_output - (i64) Guest address of the writable little-endian u64 byte count. On
  ;;   delivery it records the number of bytes written to the reply.
  ;; @returns Zero on success, otherwise a scene status. A short reply returns TOO_LARGE (90) with
  ;;   the required capacity or minimum in the length slot. Other limits may return 90 before a
  ;;   useful size is available. Inspect the delivered receipt for the operation's outcome.
  (import "uwvm_ros_v2" "communication.open.cancel" (func $wr_communication_open_cancel (param $cap i64) (param $memory i32) (param $request i64) (param $size i64) (param $output i64) (param $capacity i64) (param $length_output i64) (result i32)))

  ;; communication.open.take. Independent exact origin action and complete caller/incarnation checks.
  ;; Take publishes a typed endpoint only after fresh origin admission; cancelled/unknown work
  ;; retains native cleanup debt and never refunds creation work.
  ;;
  ;; The caller must belong to the capability's environment. The deployment must expose
  ;; communication.open.take and the grant must authorize communication.open.take. Applicable grant
  ;; purposes include node, topic, service, action. Depending on the selected inputs and plan, the VM
  ;; also checks node.open.
  ;;
  ;; Use the ordered wire record. Scalars are little-endian. Text and byte strings carry a u64
  ;; byte-length prefix.
  ;;
  ;; Keep the request readable, the full reply capacity writable and the eight-byte length slot
  ;; writable through the call. Preserve WasmMTE tags on all addresses. Request and reply may overlap
  ;; because the VM copies the request before delivery. The length slot must be disjoint from both
  ;; ranges after address normalization. An overlap with the slot returns INVALID (22).
  ;;
  ;; @param $cap - (i64) Capability handle for the communication.open.take action in the caller's
  ;;   environment.
  ;; @param $memory - (i32) Index of the caller's linear memory containing all three spans.
  ;; @param $request - (i64) Guest address of the encoded request. Wire order is `request` (`u64`).
  ;; @param $size - (i64) Exact request length, 8 bytes.
  ;; @param $output - (i64) Guest address of the writable result. Wire order is `creation`
  ;;   (`communication_creation_receipt`), `kind` (`u64`), `handle` (`u64`).
  ;; @param $capacity - (i64) Byte capacity of the full writable reply range, at most 4194304. The
  ;;   fixed result occupies 64 bytes.
  ;; @param $length_output - (i64) Guest address of the writable little-endian u64 byte count. On
  ;;   delivery it records the number of bytes written to the reply.
  ;; @returns Zero on success, otherwise a scene status. A short reply returns TOO_LARGE (90) with
  ;;   the required capacity or minimum in the length slot. Other limits may return 90 before a
  ;;   useful size is available. Inspect the delivered receipt for the operation's outcome.
  (import "uwvm_ros_v2" "communication.open.take" (func $wr_communication_open_take (param $cap i64) (param $memory i32) (param $request i64) (param $size i64) (param $output i64) (param $capacity i64) (param $length_output i64) (result i32)))

  (export "communication.open.cancel" (func $wr_communication_open_cancel))
  (export "communication.open.take" (func $wr_communication_open_take))
)
