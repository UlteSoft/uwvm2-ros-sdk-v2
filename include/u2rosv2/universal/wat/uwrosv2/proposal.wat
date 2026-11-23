;; Generated from src/abi/contract.json. Copy the required imports into the calling
;; guest and declare each one with wrwat --ros-operation. Guest addresses refer to
;; the immediate caller's linear memory.
(module

  ;; proposal.accept. Independent arbiter and exact current target action/argument constraints;
  ;; cannot broaden rights.
  ;;
  ;; The caller must belong to the capability's environment. The deployment must expose
  ;; proposal.accept and the grant must authorize proposal.accept. Applicable grant purposes include
  ;; arbiter. Depending on the selected inputs and plan, the VM also checks proposal.read.
  ;;
  ;; Use the ordered wire record. Scalars are little-endian. Text and byte strings carry a u64
  ;; byte-length prefix.
  ;;
  ;; Keep the request readable, the full reply capacity writable and the eight-byte length slot
  ;; writable through the call. Preserve WasmMTE tags on all addresses. Request and reply may overlap
  ;; because the VM copies the request before delivery. The length slot must be disjoint from both
  ;; ranges after address normalization. An overlap with the slot returns INVALID (22).
  ;;
  ;; @param $cap - (i64) Capability handle for the proposal.accept action in the caller's
  ;;   environment.
  ;; @param $memory - (i32) Index of the caller's linear memory containing all three spans.
  ;; @param $request - (i64) Guest address of the encoded request. Wire order is `key`
  ;;   (`request_key`), `proposal_capability` (`u64`), `proposal` (`u64`), `target_capability`
  ;;   (`u64`), `target` (`u64`), `deadline` (`u64`).
  ;; @param $size - (i64) Byte length of the complete encoded request. The carrier accepts at most
  ;;   16384 bytes.
  ;; @param $output - (i64) Guest address of the writable result. Wire order is `receipt`
  ;;   (`receipt`).
  ;; @param $capacity - (i64) Byte capacity of the full writable reply range, at most 8192.
  ;; @param $length_output - (i64) Guest address of the writable little-endian u64 byte count. On
  ;;   delivery it records the number of bytes written to the reply.
  ;; @returns Zero on success, otherwise a scene status. A short reply returns TOO_LARGE (90) with
  ;;   the required capacity or minimum in the length slot. Other limits may return 90 before a
  ;;   useful size is available. Inspect the delivered receipt for the operation's outcome.
  (import "uwvm_ros_v2" "proposal.accept" (func $wr_proposal_accept (param $cap i64) (param $memory i32) (param $request i64) (param $size i64) (param $output i64) (param $capacity i64) (param $length_output i64) (result i32)))

  ;; proposal.capture. Explicit finite capture of actual typed source observations and ordered sealed
  ;; buffers; exact per-capability key replay. Closing capture releases only its own pins. No model
  ;; execution or target effect.
  ;;
  ;; The caller must belong to the capability's environment. The deployment must expose
  ;; proposal.capture and the grant must authorize proposal.capture. Applicable grant purposes
  ;; include proposal. Depending on the selected inputs and plan, the VM also checks
  ;; resource.observe, buffer.read.
  ;;
  ;; Use the ordered wire record. Scalars are little-endian. Text and byte strings carry a u64
  ;; byte-length prefix.
  ;;
  ;; Keep the request readable, the full reply capacity writable and the eight-byte length slot
  ;; writable through the call. Preserve WasmMTE tags on all addresses. Request and reply may overlap
  ;; because the VM copies the request before delivery. The length slot must be disjoint from both
  ;; ranges after address normalization. An overlap with the slot returns INVALID (22).
  ;;
  ;; @param $cap - (i64) Capability handle for the proposal.capture action in the caller's
  ;;   environment.
  ;; @param $memory - (i32) Index of the caller's linear memory containing all three spans.
  ;; @param $request - (i64) Guest address of the encoded request. Wire order is `key`
  ;;   (`request_key`), `profile` (`profile`), `sources` (`array<proposal_capture_source>`), `expiry`
  ;;   (`u64`).
  ;; @param $size - (i64) Byte length of the complete encoded request. The carrier accepts at most
  ;;   16384 bytes.
  ;; @param $output - (i64) Guest address of the writable result. Wire order is `capture` (`u64`),
  ;;   `inputs` (`array<proposal_captured_buffer>`).
  ;; @param $capacity - (i64) Byte capacity of the full writable reply range, at most 8192.
  ;; @param $length_output - (i64) Guest address of the writable little-endian u64 byte count. On
  ;;   delivery it records the number of bytes written to the reply.
  ;; @returns Zero on success, otherwise a scene status. A short reply returns TOO_LARGE (90) with
  ;;   the required capacity or minimum in the length slot. Other limits may return 90 before a
  ;;   useful size is available.
  (import "uwvm_ros_v2" "proposal.capture" (func $wr_proposal_capture (param $cap i64) (param $memory i32) (param $request i64) (param $size i64) (param $output i64) (param $capacity i64) (param $length_output i64) (result i32)))

  ;; proposal.publish. Authenticate complete successful terminal output from the actual model request
  ;; against original captured input IDs, SHA and order. Independently authorize publication; model
  ;; bytes cannot issue grants or execute tools.
  ;;
  ;; The caller must belong to the capability's environment. The deployment must expose
  ;; proposal.publish and the grant must authorize proposal.publish. Applicable grant purposes
  ;; include proposal. Depending on the selected inputs and plan, the VM also checks model.take.
  ;;
  ;; Use the ordered wire record. Scalars are little-endian. Text and byte strings carry a u64
  ;; byte-length prefix.
  ;;
  ;; Keep the request readable, the full reply capacity writable and the eight-byte length slot
  ;; writable through the call. Preserve WasmMTE tags on all addresses. Request and reply may overlap
  ;; because the VM copies the request before delivery. The length slot must be disjoint from both
  ;; ranges after address normalization. An overlap with the slot returns INVALID (22).
  ;;
  ;; @param $cap - (i64) Capability handle for the proposal.publish action in the caller's
  ;;   environment.
  ;; @param $memory - (i32) Index of the caller's linear memory containing all three spans.
  ;; @param $request - (i64) Guest address of the encoded request. Wire order is `key`
  ;;   (`request_key`), `capture` (`u64`), `model_request` (`u64`), `envelope` (`bytes`), `expiry`
  ;;   (`u64`).
  ;; @param $size - (i64) Byte length of the complete encoded request. The carrier accepts at most
  ;;   16384 bytes.
  ;; @param $output - (i64) Guest address of the writable result. Wire order is `proposal` (`u64`).
  ;; @param $capacity - (i64) Byte capacity of the full writable reply range, at most 8192. The fixed
  ;;   result occupies 8 bytes.
  ;; @param $length_output - (i64) Guest address of the writable little-endian u64 byte count. On
  ;;   delivery it records the number of bytes written to the reply.
  ;; @returns Zero on success, otherwise a scene status. A short reply returns TOO_LARGE (90) with
  ;;   the required capacity or minimum in the length slot. Other limits may return 90 before a
  ;;   useful size is available.
  (import "uwvm_ros_v2" "proposal.publish" (func $wr_proposal_publish (param $cap i64) (param $memory i32) (param $request i64) (param $size i64) (param $output i64) (param $capacity i64) (param $length_output i64) (result i32)))

  ;; proposal.read. Read inert validated model proposal and trusted provenance.
  ;;
  ;; The caller must belong to the capability's environment. The deployment must expose proposal.read
  ;; and the grant must authorize proposal.read. Applicable grant purposes include proposal.
  ;;
  ;; Use the ordered wire record. Scalars are little-endian. Text and byte strings carry a u64
  ;; byte-length prefix.
  ;;
  ;; Keep the request readable, the full reply capacity writable and the eight-byte length slot
  ;; writable through the call. Preserve WasmMTE tags on all addresses. Request and reply may overlap
  ;; because the VM copies the request before delivery. The length slot must be disjoint from both
  ;; ranges after address normalization. An overlap with the slot returns INVALID (22).
  ;;
  ;; @param $cap - (i64) Capability handle for the proposal.read action in the caller's environment.
  ;; @param $memory - (i32) Index of the caller's linear memory containing all three spans.
  ;; @param $request - (i64) Guest address of the encoded request. Wire order is `proposal` (`u64`).
  ;; @param $size - (i64) Exact request length, 8 bytes.
  ;; @param $output - (i64) Guest address of the writable result. Wire order is `proposal`
  ;;   (`proposal`).
  ;; @param $capacity - (i64) Byte capacity of the full writable reply range, at most 8192.
  ;; @param $length_output - (i64) Guest address of the writable little-endian u64 byte count. On
  ;;   delivery it records the number of bytes written to the reply.
  ;; @returns Zero on success, otherwise a scene status. A short reply returns TOO_LARGE (90) with
  ;;   the required capacity or minimum in the length slot. Other limits may return 90 before a
  ;;   useful size is available.
  (import "uwvm_ros_v2" "proposal.read" (func $wr_proposal_read (param $cap i64) (param $memory i32) (param $request i64) (param $size i64) (param $output i64) (param $capacity i64) (param $length_output i64) (result i32)))

  (export "proposal.accept" (func $wr_proposal_accept))
  (export "proposal.capture" (func $wr_proposal_capture))
  (export "proposal.publish" (func $wr_proposal_publish))
  (export "proposal.read" (func $wr_proposal_read))
)
