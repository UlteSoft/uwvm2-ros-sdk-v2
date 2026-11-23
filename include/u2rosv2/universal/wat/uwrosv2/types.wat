;; Generated from src/abi/contract.json. Copy the required imports into the calling
;; guest and declare each one with wrwat --ros-operation. Guest addresses refer to
;; the immediate caller's linear memory.
(module

  ;; type.describe. Bounded immutable approved schema dependency closure; type names never load code.
  ;;
  ;; The caller must belong to the capability's environment. The deployment must expose type.describe
  ;; and the grant must authorize type.describe. Applicable grant purposes include type.
  ;;
  ;; Use the ordered wire record. Scalars are little-endian. Text and byte strings carry a u64
  ;; byte-length prefix.
  ;;
  ;; Keep the request readable, the full reply capacity writable and the eight-byte length slot
  ;; writable through the call. Preserve WasmMTE tags on all addresses. Request and reply may overlap
  ;; because the VM copies the request before delivery. The length slot must be disjoint from both
  ;; ranges after address normalization. An overlap with the slot returns INVALID (22).
  ;;
  ;; @param $cap - (i64) Capability handle for the type.describe action in the caller's environment.
  ;; @param $memory - (i32) Index of the caller's linear memory containing all three spans.
  ;; @param $request - (i64) Guest address of the encoded request. Wire order is `identity` (`text`),
  ;;   `cursor` (`optional<u64>`), `limit` (`u64`).
  ;; @param $size - (i64) Byte length of the complete encoded request. The carrier accepts at most
  ;;   4194304 bytes.
  ;; @param $output - (i64) Guest address of the writable result. Wire order is `schema` (`message`),
  ;;   `page` (`page`).
  ;; @param $capacity - (i64) Byte capacity of the full writable reply range, at most 4194304.
  ;; @param $length_output - (i64) Guest address of the writable little-endian u64 byte count. On
  ;;   delivery it records the number of bytes written to the reply.
  ;; @returns Zero on success, otherwise a scene status. A short reply returns TOO_LARGE (90) with
  ;;   the required capacity or minimum in the length slot. Other limits may return 90 before a
  ;;   useful size is available.
  (import "uwvm_ros_v2" "type.describe" (func $wr_type_describe (param $cap i64) (param $memory i32) (param $request i64) (param $size i64) (param $output i64) (param $capacity i64) (param $length_output i64) (result i32)))

  (export "type.describe" (func $wr_type_describe))
)
