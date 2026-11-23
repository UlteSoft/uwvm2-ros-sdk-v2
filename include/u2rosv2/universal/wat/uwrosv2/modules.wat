;; Generated from src/abi/contract.json. Copy the required imports into the calling
;; guest and declare each one with wrwat --ros-operation. Guest addresses refer to
;; the immediate caller's linear memory.
(module

  ;; module.describe. Return the exact registered target name and kind: main-wasm, preload-wasm or
  ;; preload-dl. Default authority is zero: require explicit import exposure and exact
  ;; module/metadata grant action. The trusted grant fixes the target; guests cannot supply arbitrary
  ;; target names or wildcards. Carrier capability must be zero. Exact immediate caller identity
  ;; comes from the runtime. Observation never freezes deployment, enrolls a caller, opens a
  ;; capability, replenishes or consumes execution quotas, starts a provider, invokes an export,
  ;; reads foreign memory, or changes another policy. A denial writes neither result nor length.
  ;; Owned temporary buffers are securely overwritten.
  ;;
  ;; The caller's deployment must expose module.describe. The request alias must select a
  ;; module/metadata grant with this exact action.
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
  (import "uwvm_ros_v2" "module.describe" (func $wr_module_describe (param $cap i64) (param $memory i32) (param $request i64) (param $size i64) (param $output i64) (param $capacity i64) (param $length_output i64) (result i32)))

  ;; module.exports. Return only export names already recorded in the module registry. Do not resolve
  ;; or call a symbol. Default authority is zero: require explicit import exposure and exact
  ;; module/metadata grant action. The trusted grant fixes the target; guests cannot supply arbitrary
  ;; target names or wildcards. Carrier capability must be zero. Exact immediate caller identity
  ;; comes from the runtime. Observation never freezes deployment, enrolls a caller, opens a
  ;; capability, replenishes or consumes execution quotas, starts a provider, invokes an export,
  ;; reads foreign memory, or changes another policy. A denial writes neither result nor length.
  ;; Owned temporary buffers are securely overwritten.
  ;;
  ;; The caller's deployment must expose module.exports. The request alias must select a
  ;; module/metadata grant with this exact action.
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
  (import "uwvm_ros_v2" "module.exports" (func $wr_module_exports (param $cap i64) (param $memory i32) (param $request i64) (param $size i64) (param $output i64) (param $capacity i64) (param $length_output i64) (result i32)))

  ;; module.group. Return the target ROSv2 group name and its members only under this independent
  ;; action. Default authority is zero: require explicit import exposure and exact module/metadata
  ;; grant action. The trusted grant fixes the target; guests cannot supply arbitrary target names or
  ;; wildcards. Carrier capability must be zero. Exact immediate caller identity comes from the
  ;; runtime. Observation never freezes deployment, enrolls a caller, opens a capability, replenishes
  ;; or consumes execution quotas, starts a provider, invokes an export, reads foreign memory, or
  ;; changes another policy. A denial writes neither result nor length. Owned temporary buffers are
  ;; securely overwritten.
  ;;
  ;; The caller's deployment must expose module.group. The request alias must select a
  ;; module/metadata grant with this exact action.
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
  ;;   output. A target without a ROSv2 group yields a supported page with enabled=false.
  (import "uwvm_ros_v2" "module.group" (func $wr_module_group (param $cap i64) (param $memory i32) (param $request i64) (param $size i64) (param $output i64) (param $capacity i64) (param $length_output i64) (result i32)))

  ;; module.importers. Return direct registered Wasm importers of the exact target, as importer
  ;; module/symbol rows. Require an independent module/metadata grant and exact exposure even when
  ;; the target is the caller. Count all visited modules and imports, including nonmatches, against
  ;; the finite scan budget. Reexports are not expanded and native dynamic-linker dependencies are
  ;; not inspected. An explicit grant may also name a registered builtin module. No unrelated peers
  ;; or their remaining imports are disclosed. Carrier capability must be zero. Exact immediate
  ;; caller identity comes from the runtime. Observation never freezes deployment, enrolls a caller,
  ;; opens a capability, replenishes or consumes execution quotas, starts a provider, invokes an
  ;; export, reads foreign memory, or changes another policy. A denial writes neither result nor
  ;; length. Owned temporary buffers are securely overwritten.
  ;;
  ;; The caller's deployment must expose module.importers. The request alias must select a
  ;; module/metadata grant with this exact action.
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
  ;;   output. The scan budget counts all visited modules and import declarations, including
  ;;   nonmatches.
  (import "uwvm_ros_v2" "module.importers" (func $wr_module_importers (param $cap i64) (param $memory i32) (param $request i64) (param $size i64) (param $output i64) (param $capacity i64) (param $length_output i64) (result i32)))

  ;; module.imports. Return the exact Wasm import module/name pairs; native preloaddl platform
  ;; imports are unsupported. Default authority is zero: require explicit import exposure and exact
  ;; module/metadata grant action. The trusted grant fixes the target; guests cannot supply arbitrary
  ;; target names or wildcards. Carrier capability must be zero. Exact immediate caller identity
  ;; comes from the runtime. Observation never freezes deployment, enrolls a caller, opens a
  ;; capability, replenishes or consumes execution quotas, starts a provider, invokes an export,
  ;; reads foreign memory, or changes another policy. A denial writes neither result nor length.
  ;; Owned temporary buffers are securely overwritten.
  ;;
  ;; The caller's deployment must expose module.imports. The request alias must select a
  ;; module/metadata grant with this exact action.
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
  ;;   output. Native modules have no registered Wasm import list.
  (import "uwvm_ros_v2" "module.imports" (func $wr_module_imports (param $cap i64) (param $memory i32) (param $request i64) (param $size i64) (param $output i64) (param $capacity i64) (param $length_output i64) (result i32)))

  ;; module.permission.report. Return permissions of the exact registered target for the requested
  ;; family. The viewer observation policy also applies, including exact-function and aggregate
  ;; denials. Default authority is zero: require explicit import exposure and exact module/metadata
  ;; grant action. The trusted grant fixes the target; guests cannot supply arbitrary target names or
  ;; wildcards. Carrier capability must be zero. Exact immediate caller identity comes from the
  ;; runtime. Observation never freezes deployment, enrolls a caller, opens a capability, replenishes
  ;; or consumes execution quotas, starts a provider, invokes an export, reads foreign memory, or
  ;; changes another policy. A denial writes neither result nor length. Owned temporary buffers are
  ;; securely overwritten.
  ;;
  ;; The caller's deployment must expose module.permission.report. The request alias must select a
  ;; module/metadata grant with this exact action. The viewer's family and exact-function observation
  ;; restrictions also apply.
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
  ;;   (`text`), `family` (`text`), `function` (`text`), `first` (`u64`). The cursor first is a
  ;;   zero-based row index, at most 65536. Select preloaddl, preloadwasm, wasip1, ros1v1, ros2v1 or
  ;;   rosv2. An empty function selects the whole family.
  ;; @param $size - (i64) Byte length of the complete encoded request. The carrier accepts at most
  ;;   558 bytes.
  ;; @param $output - (i64) Guest address of the writable result. Wire order is `page`
  ;;   (`permission_page`). The 40-byte header holds supported, enabled, first, total and row count
  ;;   as little-endian u64 values. Each of up to 32 rows contains scope, key, annotation
  ;;   (length-prefixed UTF-8) and value (u64).
  ;; @param $capacity - (i64) Byte capacity of the full writable reply range, at most 65536.
  ;; @param $length_output - (i64) Guest address of the writable little-endian u64 byte count. On
  ;;   delivery it records the number of bytes written to the reply. Initialize this slot to zero to
  ;;   distinguish a delivered status-95 page from a refusal that writes nothing.
  ;; @returns Zero delivers a page and its byte count. When a completed page exceeds capacity,
  ;;   TOO_LARGE (90) writes the required page length and leaves the reply untouched. A scan or
  ;;   page-construction limit can return 90 before either output is written. DENIED (13) leaves both
  ;;   outputs untouched. For an authorized whole-family query with a valid cursor, an unbuilt family
  ;;   returns UNSUPPORTED (95) with a supported=false, enabled=false page when it fits. An
  ;;   unsupported exact-function query returns 95 without writing the page or length. A built but
  ;;   disabled family can return zero with enabled=false. An unsupported target identity can also
  ;;   return 95 before either output is written.
  (import "uwvm_ros_v2" "module.permission.report" (func $wr_module_permission_report (param $cap i64) (param $memory i32) (param $request i64) (param $size i64) (param $output i64) (param $capacity i64) (param $length_output i64) (result i32)))

  (export "module.describe" (func $wr_module_describe))
  (export "module.exports" (func $wr_module_exports))
  (export "module.group" (func $wr_module_group))
  (export "module.importers" (func $wr_module_importers))
  (export "module.imports" (func $wr_module_imports))
  (export "module.permission.report" (func $wr_module_permission_report))
)
