;; Generated from src/abi/contract.json. Copy the required imports into the calling
;; guest and declare each one with wrwat --ros-operation. Guest addresses refer to
;; the immediate caller's linear memory.
(module

  ;; device.describe. Actual provider/firmware support, state and watchdog contract.
  ;;
  ;; The caller must belong to the capability's environment. The deployment must expose
  ;; device.describe and the grant must authorize device.describe. Applicable grant purposes include
  ;; device.
  ;;
  ;; Use the ordered wire record. Scalars are little-endian. Text and byte strings carry a u64
  ;; byte-length prefix.
  ;;
  ;; Keep the request readable, the full reply capacity writable and the eight-byte length slot
  ;; writable through the call. Preserve WasmMTE tags on all addresses. Request and reply may overlap
  ;; because the VM copies the request before delivery. The length slot must be disjoint from both
  ;; ranges after address normalization. An overlap with the slot returns INVALID (22).
  ;;
  ;; @param $cap - (i64) Capability handle for the device.describe action in the caller's
  ;;   environment.
  ;; @param $memory - (i32) Index of the caller's linear memory containing all three spans.
  ;; @param $request - (i64) Guest address of the encoded request. Wire order is `device` (`u64`).
  ;; @param $size - (i64) Exact request length, 8 bytes.
  ;; @param $output - (i64) Guest address of the writable result. Wire order is `description`
  ;;   (`device_description`).
  ;; @param $capacity - (i64) Byte capacity of the full writable reply range, at most 4096.
  ;; @param $length_output - (i64) Guest address of the writable little-endian u64 byte count. On
  ;;   delivery it records the number of bytes written to the reply.
  ;; @returns Zero on success, otherwise a scene status. A short reply returns TOO_LARGE (90) with
  ;;   the required capacity or minimum in the length slot. Other limits may return 90 before a
  ;;   useful size is available.
  (import "uwvm_ros_v2" "device.describe" (func $wr_device_describe (param $cap i64) (param $memory i32) (param $request i64) (param $size i64) (param $output i64) (param $capacity i64) (param $length_output i64) (result i32)))

  ;; device.open. Approved bus/protocol/command envelope, independent watchdog and finite capacity.
  ;;
  ;; The caller must belong to the capability's environment. The deployment must expose device.open
  ;; and the grant must authorize device.open. Applicable grant purposes include device.
  ;;
  ;; Use the ordered wire record. Scalars are little-endian. Text and byte strings carry a u64
  ;; byte-length prefix.
  ;;
  ;; Keep the request readable, the full reply capacity writable and the eight-byte length slot
  ;; writable through the call. Preserve WasmMTE tags on all addresses. Request and reply may overlap
  ;; because the VM copies the request before delivery. The length slot must be disjoint from both
  ;; ranges after address normalization. An overlap with the slot returns INVALID (22).
  ;;
  ;; @param $cap - (i64) Capability handle for the device.open action in the caller's environment.
  ;; @param $memory - (i32) Index of the caller's linear memory containing all three spans.
  ;; @param $request - (i64) Guest address of the encoded request. Wire order is `profile`
  ;;   (`profile`).
  ;; @param $size - (i64) Byte length of the complete encoded request. The carrier accepts at most
  ;;   16384 bytes.
  ;; @param $output - (i64) Guest address of the writable result. Wire order is `handle` (`u64`).
  ;; @param $capacity - (i64) Byte capacity of the full writable reply range, at most 4096. The fixed
  ;;   result occupies 8 bytes.
  ;; @param $length_output - (i64) Guest address of the writable little-endian u64 byte count. On
  ;;   delivery it records the number of bytes written to the reply.
  ;; @returns Zero on success, otherwise a scene status. A short reply returns TOO_LARGE (90) with
  ;;   the required capacity or minimum in the length slot. Other limits may return 90 before a
  ;;   useful size is available.
  (import "uwvm_ros_v2" "device.open" (func $wr_device_open (param $cap i64) (param $memory i32) (param $request i64) (param $size i64) (param $output i64) (param $capacity i64) (param $length_output i64) (result i32)))

  ;; device.result. Distinguish accepted, observed execution, partial and unknown effect.
  ;;
  ;; The caller must belong to the capability's environment. The deployment must expose device.result
  ;; and the grant must authorize device.result. Applicable grant purposes include device.
  ;;
  ;; Use the ordered wire record. Scalars are little-endian. Text and byte strings carry a u64
  ;; byte-length prefix.
  ;;
  ;; Keep the request readable, the full reply capacity writable and the eight-byte length slot
  ;; writable through the call. Preserve WasmMTE tags on all addresses. Request and reply may overlap
  ;; because the VM copies the request before delivery. The length slot must be disjoint from both
  ;; ranges after address normalization. An overlap with the slot returns INVALID (22).
  ;;
  ;; @param $cap - (i64) Capability handle for the device.result action in the caller's environment.
  ;; @param $memory - (i32) Index of the caller's linear memory containing all three spans.
  ;; @param $request - (i64) Guest address of the encoded request. Wire order is `device` (`u64`),
  ;;   `request` (`u64`).
  ;; @param $size - (i64) Exact request length, 16 bytes.
  ;; @param $output - (i64) Guest address of the writable result. Wire order is `receipt`
  ;;   (`receipt`), `evidence` (`optional<execution_evidence>`).
  ;; @param $capacity - (i64) Byte capacity of the full writable reply range, at most 4096.
  ;; @param $length_output - (i64) Guest address of the writable little-endian u64 byte count. On
  ;;   delivery it records the number of bytes written to the reply.
  ;; @returns Zero on success, otherwise a scene status. A short reply returns TOO_LARGE (90) with
  ;;   the required capacity or minimum in the length slot. Other limits may return 90 before a
  ;;   useful size is available. Inspect the delivered receipt for the operation's outcome.
  (import "uwvm_ros_v2" "device.result" (func $wr_device_result (param $cap i64) (param $memory i32) (param $request i64) (param $size i64) (param $output i64) (param $capacity i64) (param $length_output i64) (result i32)))

  ;; device.stop. Requires explicit stop authority; trusted watchdog independent.
  ;;
  ;; The caller must belong to the capability's environment. The deployment must expose device.stop
  ;; and the grant must authorize device.stop. Applicable grant purposes include device.
  ;;
  ;; Use the ordered wire record. Scalars are little-endian. Text and byte strings carry a u64
  ;; byte-length prefix.
  ;;
  ;; Keep the request readable, the full reply capacity writable and the eight-byte length slot
  ;; writable through the call. Preserve WasmMTE tags on all addresses. Request and reply may overlap
  ;; because the VM copies the request before delivery. The length slot must be disjoint from both
  ;; ranges after address normalization. An overlap with the slot returns INVALID (22).
  ;;
  ;; @param $cap - (i64) Capability handle for the device.stop action in the caller's environment.
  ;; @param $memory - (i32) Index of the caller's linear memory containing all three spans.
  ;; @param $request - (i64) Guest address of the encoded request. Wire order is `key`
  ;;   (`request_key`), `device` (`u64`), `profile` (`profile`).
  ;; @param $size - (i64) Byte length of the complete encoded request. The carrier accepts at most
  ;;   16384 bytes.
  ;; @param $output - (i64) Guest address of the writable result. Wire order is `receipt`
  ;;   (`receipt`).
  ;; @param $capacity - (i64) Byte capacity of the full writable reply range, at most 4096.
  ;; @param $length_output - (i64) Guest address of the writable little-endian u64 byte count. On
  ;;   delivery it records the number of bytes written to the reply.
  ;; @returns Zero on success, otherwise a scene status. A short reply returns TOO_LARGE (90) with
  ;;   the required capacity or minimum in the length slot. Other limits may return 90 before a
  ;;   useful size is available. Inspect the delivered receipt for the operation's outcome.
  (import "uwvm_ros_v2" "device.stop" (func $wr_device_stop (param $cap i64) (param $memory i32) (param $request i64) (param $size i64) (param $output i64) (param $capacity i64) (param $length_output i64) (result i32)))

  ;; device.submit. Full command bounds/freshness/units/frame before hardware effect.
  ;;
  ;; The caller must belong to the capability's environment. The deployment must expose device.submit
  ;; and the grant must authorize device.submit. Applicable grant purposes include device. Depending
  ;; on the selected inputs and plan, the VM also checks device.stop, control.submit,
  ;; resource.observe, buffer.read, data.export.
  ;;
  ;; Use the ordered wire record. Scalars are little-endian. Text and byte strings carry a u64
  ;; byte-length prefix.
  ;;
  ;; Keep the request readable, the full reply capacity writable and the eight-byte length slot
  ;; writable through the call. Preserve WasmMTE tags on all addresses. Request and reply may overlap
  ;; because the VM copies the request before delivery. The length slot must be disjoint from both
  ;; ranges after address normalization. An overlap with the slot returns INVALID (22).
  ;;
  ;; @param $cap - (i64) Capability handle for the device.submit action in the caller's environment.
  ;; @param $memory - (i32) Index of the caller's linear memory containing all three spans.
  ;; @param $request - (i64) Guest address of the encoded request. Wire order is `command`
  ;;   (`command`).
  ;; @param $size - (i64) Byte length of the complete encoded request. The carrier accepts at most
  ;;   16384 bytes.
  ;; @param $output - (i64) Guest address of the writable result. Wire order is `receipt`
  ;;   (`receipt`).
  ;; @param $capacity - (i64) Byte capacity of the full writable reply range, at most 4096.
  ;; @param $length_output - (i64) Guest address of the writable little-endian u64 byte count. On
  ;;   delivery it records the number of bytes written to the reply.
  ;; @returns Zero on success, otherwise a scene status. A short reply returns TOO_LARGE (90) with
  ;;   the required capacity or minimum in the length slot. Other limits may return 90 before a
  ;;   useful size is available. Inspect the delivered receipt for the operation's outcome.
  (import "uwvm_ros_v2" "device.submit" (func $wr_device_submit (param $cap i64) (param $memory i32) (param $request i64) (param $size i64) (param $output i64) (param $capacity i64) (param $length_output i64) (result i32)))

  (export "device.describe" (func $wr_device_describe))
  (export "device.open" (func $wr_device_open))
  (export "device.result" (func $wr_device_result))
  (export "device.stop" (func $wr_device_stop))
  (export "device.submit" (func $wr_device_submit))
)
