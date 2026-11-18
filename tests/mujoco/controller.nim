import wros_scene, simulation

var handle, used: uint64
var response: array[64, uint64]

template invoke(operation: untyped, data: pointer, size: uint64): uint32 =
  operation(handle, 0'u32, wrAddress(data), size, wrAddress(addr response[0]), uint64(sizeof(response)), wrAddress(addr used))

template poll(operation: untyped, data: pointer, size: uint64): uint32 =
  block:
    var status = 11'u32
    var tries = 0
    while status == 11 and tries < 10000000:
      status = invoke(operation, data, size)
      inc tries
    doAssert status != 11
    status

let alias = "joint"
doAssert wr_capability_open(0, wrAddress(unsafeAddr alias[0]), 5, wrAddress(addr handle)) == 0
doAssert poll(wr_driver_connect, nil, 0) == 0
for index in 1..steps:
  var sequence = uint64(index)
  copyMem(addr request[0], addr sequence, sizeof(sequence))
  copyMem(addr request[32], addr sequence, sizeof(sequence))
  when success:
    var target = if index mod 2 == 1: 0.5 else: -0.5
    copyMem(addr request[targetOffset], addr target, sizeof(target))
  doAssert poll(wr_driver_submit, addr request[0], uint64(request.len)) == 0
  let status = poll(wr_driver_result, addr sequence, 8)
  when crash:
    doAssert status == 5 or status == 13
    doAssert invoke(wr_driver_describe, nil, 0) == 0
    doAssert used >= 32 and response[0] == 6 and response[3] == 1
  else:
    doAssert status == 0 and used >= 24 and response[0] == (if success: 0'u64 else: 13'u64)
    doAssert response[2] == sequence
doAssert invoke(wr_driver_disconnect, nil, 0) == 0
