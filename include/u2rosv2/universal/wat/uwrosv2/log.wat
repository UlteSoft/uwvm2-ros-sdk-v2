;; Generated from src/abi/contract.json. Copy the required imports into the calling
;; guest and declare each one with wrwat --ros-operation. Guest addresses refer to
;; the immediate caller's linear memory.
(module

  ;; log.emit. Independent log grant, bounded private content and declared attenuation; no
  ;; format-string execution.
  ;;
  ;; The caller must belong to the capability's environment. The deployment must expose log.emit and
  ;; the grant must authorize log.emit. Applicable grant purposes include log.
  ;;
  ;; Use the ordered wire record. Scalars are little-endian. Text and byte strings carry a u64
  ;; byte-length prefix.
  ;;
  ;; Keep the request readable, the full reply capacity writable and the eight-byte length slot
  ;; writable through the call. Preserve WasmMTE tags on all addresses. Request and reply may overlap
  ;; because the VM copies the request before delivery. The length slot must be disjoint from both
  ;; ranges after address normalization. An overlap with the slot returns INVALID (22).
  ;;
  ;; @param $cap - (i64) Capability handle for the log.emit action in the caller's environment.
  ;; @param $memory - (i32) Index of the caller's linear memory containing all three spans.
  ;; @param $request - (i64) Guest address of the encoded request. Wire order is `session` (`u64`),
  ;;   `sequence` (`u64`), `severity` (`text`), `logger` (`text`), `stamp` (`optional<log_stamp>`),
  ;;   `message` (`text`), `location` (`optional<log_location>`).
  ;; @param $size - (i64) Byte length of the complete encoded request. The carrier accepts at most
  ;;   4194304 bytes.
  ;; @param $output - (i64) Guest address of the writable result. Wire order is `receipt`
  ;;   (`log_receipt`).
  ;; @param $capacity - (i64) Byte capacity of the full writable reply range, at most 4194304. The
  ;;   fixed result occupies 48 bytes.
  ;; @param $length_output - (i64) Guest address of the writable little-endian u64 byte count. On
  ;;   delivery it records the number of bytes written to the reply.
  ;; @returns Zero on success, otherwise a scene status. A short reply returns TOO_LARGE (90) with
  ;;   the required capacity or minimum in the length slot. Other limits may return 90 before a
  ;;   useful size is available. Inspect the delivered receipt for the operation's outcome.
  (import "uwvm_ros_v2" "log.emit" (func $wr_log_emit (param $cap i64) (param $memory i32) (param $request i64) (param $size i64) (param $output i64) (param $capacity i64) (param $length_output i64) (result i32)))

  (export "log.emit" (func $wr_log_emit))
)
