;; Generated from src/abi/contract.json. Copy the required imports into the calling
;; guest and declare each one with wrwat --ros-operation. Guest addresses refer to
;; the immediate caller's linear memory.
(module

  ;; vm.describe. Return only closed VM build-support flags, selected compiler, compile-thread
  ;; ceiling and counts of registered declaration kinds. These are not live thread counts or
  ;; per-module execution permissions. Require independent vm/runtime/metadata authority and exact
  ;; exposure. Self permission.report and module grants cannot authorize VM observation. No module
  ;; names, paths, process IDs, addresses, source bytes or credentials are returned. Carrier
  ;; capability must be zero. Exact immediate caller identity comes from the runtime. Observation
  ;; never freezes deployment, enrolls a caller, opens a capability, replenishes or consumes
  ;; execution quotas, starts a provider, invokes an export, reads foreign memory, or changes another
  ;; policy. A denial writes neither result nor length. Owned temporary buffers are securely
  ;; overwritten.
  ;;
  ;; The caller's deployment must expose vm.describe. The request alias must select a
  ;; vm/runtime/metadata grant with this exact action.
  ;;
  ;; Use the ordered wire record. Scalars are little-endian. Text and byte strings carry a u64
  ;; byte-length prefix.
  ;;
  ;; Keep the request readable, the full reply capacity writable and the eight-byte length slot
  ;; writable through the call. Preserve WasmMTE tags on all addresses. The request, full reply range
  ;; and length slot must be pairwise disjoint in linear memory. The VM compares normalized addresses
  ;; and returns INVALID (22) for any overlap.
  ;;
  ;; @param $cap - (i64) Pass zero. The VM authenticates the immediate caller and resolves
  ;;   observation authority separately.
  ;; @param $memory - (i32) Index of the caller's linear memory containing all three spans.
  ;; @param $request - (i64) Guest address of the encoded request. Wire order is `grant_alias`
  ;;   (`text`), `first` (`u64`). The cursor first is a zero-based row index, at most 65536.
  ;; @param $size - (i64) Byte length of the complete encoded request. The carrier accepts at most
  ;;   271 bytes.
  ;; @param $output - (i64) Guest address of the writable result. Wire order is `page`
  ;;   (`permission_page`). The 40-byte header holds supported, enabled, first, total and row count
  ;;   as little-endian u64 values. Each of up to 32 rows contains scope, key, annotation
  ;;   (length-prefixed UTF-8) and value (u64).
  ;; @param $capacity - (i64) Byte capacity of the full writable reply range, at most 65536.
  ;; @param $length_output - (i64) Guest address of the writable little-endian u64 byte count. On
  ;;   delivery it records the number of bytes written to the reply.
  ;; @returns Zero delivers a page and its byte count. When a completed page exceeds capacity,
  ;;   TOO_LARGE (90) writes the required page length and leaves the reply untouched. A scan or
  ;;   page-construction limit can return 90 before either output is written. DENIED (13) leaves both
  ;;   outputs untouched. An unsupported observation returns UNSUPPORTED (95) before writing either
  ;;   output.
  (import "uwvm_ros_v2" "vm.describe" (func $wr_vm_describe (param $cap i64) (param $memory i32) (param $request i64) (param $size i64) (param $output i64) (param $capacity i64) (param $length_output i64) (result i32)))

  (export "vm.describe" (func $wr_vm_describe))
)
