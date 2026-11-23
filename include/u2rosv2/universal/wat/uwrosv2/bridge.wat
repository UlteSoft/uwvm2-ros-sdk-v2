;; Generated from src/abi/contract.json. Copy the required imports into the calling
;; guest and declare each one with wrwat --ros-operation. Guest addresses refer to
;; the immediate caller's linear memory.
(module

  ;; bridge.create. Both endpoint directions/types/conversion/QoS preflight independently.
  ;;
  ;; The caller must belong to the capability's environment. The deployment must expose bridge.create
  ;; and the grant must authorize bridge.create. Applicable grant purposes include bridge. Depending
  ;; on the selected inputs and plan, the VM also checks topic.reserve, topic.acknowledge,
  ;; topic.release, topic.describe, data.export, topic.publish.
  ;;
  ;; Use the ordered wire record. Scalars are little-endian. Text and byte strings carry a u64
  ;; byte-length prefix.
  ;;
  ;; Keep the request readable, the full reply capacity writable and the eight-byte length slot
  ;; writable through the call. Preserve WasmMTE tags on all addresses. Request and reply may overlap
  ;; because the VM copies the request before delivery. The length slot must be disjoint from both
  ;; ranges after address normalization. An overlap with the slot returns INVALID (22).
  ;;
  ;; @param $cap - (i64) Capability handle for the bridge.create action in the caller's environment.
  ;; @param $memory - (i32) Index of the caller's linear memory containing all three spans.
  ;; @param $request - (i64) Guest address of the encoded request. Wire order is `bridge`
  ;;   (`bridge_request`).
  ;; @param $size - (i64) Byte length of the complete encoded request. The carrier accepts at most
  ;;   4096 bytes.
  ;; @param $output - (i64) Guest address of the writable result. Wire order is `handle` (`u64`).
  ;; @param $capacity - (i64) Byte capacity of the full writable reply range, at most 1024. The fixed
  ;;   result occupies 8 bytes.
  ;; @param $length_output - (i64) Guest address of the writable little-endian u64 byte count. On
  ;;   delivery it records the number of bytes written to the reply.
  ;; @returns Zero on success, otherwise a scene status. A short reply returns TOO_LARGE (90) with
  ;;   the required capacity or minimum in the length slot. Other limits may return 90 before a
  ;;   useful size is available.
  (import "uwvm_ros_v2" "bridge.create" (func $wr_bridge_create (param $cap i64) (param $memory i32) (param $request i64) (param $size i64) (param $output i64) (param $capacity i64) (param $length_output i64) (result i32)))

  ;; bridge.describe. Conversion/loss/QoS degradation/loop/correlation state only within scope.
  ;;
  ;; The caller must belong to the capability's environment. The deployment must expose
  ;; bridge.describe and the grant must authorize bridge.describe. Applicable grant purposes include
  ;; bridge.
  ;;
  ;; Use the ordered wire record. Scalars are little-endian. Text and byte strings carry a u64
  ;; byte-length prefix.
  ;;
  ;; Keep the request readable, the full reply capacity writable and the eight-byte length slot
  ;; writable through the call. Preserve WasmMTE tags on all addresses. Request and reply may overlap
  ;; because the VM copies the request before delivery. The length slot must be disjoint from both
  ;; ranges after address normalization. An overlap with the slot returns INVALID (22).
  ;;
  ;; @param $cap - (i64) Capability handle for the bridge.describe action in the caller's
  ;;   environment.
  ;; @param $memory - (i32) Index of the caller's linear memory containing all three spans.
  ;; @param $request - (i64) Guest address of the encoded request. Wire order is `bridge` (`u64`).
  ;; @param $size - (i64) Exact request length, 8 bytes.
  ;; @param $output - (i64) Guest address of the writable result. Wire order is `description`
  ;;   (`bridge_description`).
  ;; @param $capacity - (i64) Byte capacity of the full writable reply range, at most 1024.
  ;; @param $length_output - (i64) Guest address of the writable little-endian u64 byte count. On
  ;;   delivery it records the number of bytes written to the reply.
  ;; @returns Zero on success, otherwise a scene status. A short reply returns TOO_LARGE (90) with
  ;;   the required capacity or minimum in the length slot. Other limits may return 90 before a
  ;;   useful size is available.
  (import "uwvm_ros_v2" "bridge.describe" (func $wr_bridge_describe (param $cap i64) (param $memory i32) (param $request i64) (param $size i64) (param $output i64) (param $capacity i64) (param $length_output i64) (result i32)))

  ;; bridge.start. Revalidate both grants and generation; no unchecked forwarding thread.
  ;;
  ;; The caller must belong to the capability's environment. The deployment must expose bridge.start
  ;; and the grant must authorize bridge.start. Applicable grant purposes include bridge. Depending
  ;; on the selected inputs and plan, the VM also checks topic.reserve, topic.acknowledge,
  ;; topic.release, topic.describe, data.export, topic.publish.
  ;;
  ;; Use the ordered wire record. Scalars are little-endian. Text and byte strings carry a u64
  ;; byte-length prefix.
  ;;
  ;; Keep the request readable, the full reply capacity writable and the eight-byte length slot
  ;; writable through the call. Preserve WasmMTE tags on all addresses. Request and reply may overlap
  ;; because the VM copies the request before delivery. The length slot must be disjoint from both
  ;; ranges after address normalization. An overlap with the slot returns INVALID (22).
  ;;
  ;; @param $cap - (i64) Capability handle for the bridge.start action in the caller's environment.
  ;; @param $memory - (i32) Index of the caller's linear memory containing all three spans.
  ;; @param $request - (i64) Guest address of the encoded request. Wire order is `key`
  ;;   (`request_key`), `bridge` (`u64`), `deadline` (`u64`).
  ;; @param $size - (i64) Byte length of the complete encoded request. The carrier accepts at most
  ;;   4096 bytes.
  ;; @param $output - (i64) Guest address of the writable result. Wire order is `receipt`
  ;;   (`receipt`).
  ;; @param $capacity - (i64) Byte capacity of the full writable reply range, at most 1024.
  ;; @param $length_output - (i64) Guest address of the writable little-endian u64 byte count. On
  ;;   delivery it records the number of bytes written to the reply.
  ;; @returns Zero on success, otherwise a scene status. A short reply returns TOO_LARGE (90) with
  ;;   the required capacity or minimum in the length slot. Other limits may return 90 before a
  ;;   useful size is available. Inspect the delivered receipt for the operation's outcome.
  (import "uwvm_ros_v2" "bridge.start" (func $wr_bridge_start (param $cap i64) (param $memory i32) (param $request i64) (param $size i64) (param $output i64) (param $capacity i64) (param $length_output i64) (result i32)))

  ;; bridge.stop. Stop admitted direction, drain/cancel declared in profile.
  ;;
  ;; The caller must belong to the capability's environment. The deployment must expose bridge.stop
  ;; and the grant must authorize bridge.stop. Applicable grant purposes include bridge.
  ;;
  ;; Use the ordered wire record. Scalars are little-endian. Text and byte strings carry a u64
  ;; byte-length prefix.
  ;;
  ;; Keep the request readable, the full reply capacity writable and the eight-byte length slot
  ;; writable through the call. Preserve WasmMTE tags on all addresses. Request and reply may overlap
  ;; because the VM copies the request before delivery. The length slot must be disjoint from both
  ;; ranges after address normalization. An overlap with the slot returns INVALID (22).
  ;;
  ;; @param $cap - (i64) Capability handle for the bridge.stop action in the caller's environment.
  ;; @param $memory - (i32) Index of the caller's linear memory containing all three spans.
  ;; @param $request - (i64) Guest address of the encoded request. Wire order is `key`
  ;;   (`request_key`), `bridge` (`u64`), `profile` (`profile`), `deadline` (`u64`).
  ;; @param $size - (i64) Byte length of the complete encoded request. The carrier accepts at most
  ;;   4096 bytes.
  ;; @param $output - (i64) Guest address of the writable result. Wire order is `receipt`
  ;;   (`receipt`).
  ;; @param $capacity - (i64) Byte capacity of the full writable reply range, at most 1024.
  ;; @param $length_output - (i64) Guest address of the writable little-endian u64 byte count. On
  ;;   delivery it records the number of bytes written to the reply.
  ;; @returns Zero on success, otherwise a scene status. A short reply returns TOO_LARGE (90) with
  ;;   the required capacity or minimum in the length slot. Other limits may return 90 before a
  ;;   useful size is available. Inspect the delivered receipt for the operation's outcome.
  (import "uwvm_ros_v2" "bridge.stop" (func $wr_bridge_stop (param $cap i64) (param $memory i32) (param $request i64) (param $size i64) (param $output i64) (param $capacity i64) (param $length_output i64) (result i32)))

  (export "bridge.create" (func $wr_bridge_create))
  (export "bridge.describe" (func $wr_bridge_describe))
  (export "bridge.start" (func $wr_bridge_start))
  (export "bridge.stop" (func $wr_bridge_stop))
)
