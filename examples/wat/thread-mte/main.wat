;; @brief Transfer a live tagged address to an actual Wasm child and share data.
;; @details The first atomic word signals completion. Two neighboring managed
;; extents begin at addresses 128 and 144.
(module
  (import "env" "memory" (memory $heap 1 1 shared))
  (import "wasi" "thread-spawn" (func $spawn (param i32) (result i32)))
  (tag $signal (param i32))

  (func $worker (export "wasi_thread_start") (param $tid i32) (param $address i32)
    (if (i32.ne (i32.atomic.load $heap (local.get $address)) (i32.const 7))
      (then unreachable))
    (i32.atomic.store $heap (local.get $address) (i32.const 19))
    (i32.atomic.store $heap (i32.const 0) (i32.const 1))
    (drop (memory.atomic.notify $heap (i32.const 0) (i32.const 1))))

  (func $main (export "_start")
    (local $address i32) (local $neighbor i32)
    (if (i32.ne
          (block $handled (result i32)
            (try_table (catch $signal $handled) (throw $signal (i32.const 73)))
            unreachable)
          (i32.const 73))
      (then unreachable))
    (local.set $address (memtag.claim $heap (i32.const 128) (i32.const 16)))
    (local.set $neighbor (memtag.claim $heap (i32.const 144) (i32.const 16)))
    (if (memtag.status $heap)
      (then
        (if (i32.eq (memtag.extract $heap (local.get $address))
                    (memtag.extract $heap (local.get $neighbor)))
          (then unreachable))))
    (i32.atomic.store $heap (local.get $address) (i32.const 7))
    (if (i32.le_s (call $spawn (local.get $address)) (i32.const 0)) (then unreachable))
    (drop (memory.atomic.wait32 $heap (i32.const 0) (i32.const 0) (i64.const 1000000000)))
    (if (i32.ne (i32.atomic.load $heap (i32.const 0)) (i32.const 1)) (then unreachable))
    (if (i32.ne (i32.atomic.load $heap (local.get $address)) (i32.const 19))
      (then unreachable))
    (drop (memtag.release $heap (local.get $address) (i32.const 16)))
    (drop (memtag.release $heap (local.get $neighbor) (i32.const 16)))))
