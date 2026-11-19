# @file controller.rb
# @brief Exercise the approved simulated joint over typed ROSv2 calls.

# @brief Encode one nonnegative integer as a little-endian wire word.
def wire_u64(value)
  bytes = "\x00" * 8
  8.times do |index|
    bytes.setbyte(index, value & 255)
    value >>= 8
  end
  bytes
end

# @brief Decode one little-endian wire word from a checked reply.
def read_u64(bytes, offset)
  raise "short ROS reply" if bytes.bytesize < offset + 8
  value = 0
  8.times { |index| value |= bytes.getbyte(offset + index) << (index * 8) }
  value
end

# @brief Replace one field in the harness-provided request.
def replace(bytes, offset, field)
  tail = offset + field.bytesize
  bytes.byteslice(0, offset) + field + bytes.byteslice(tail, bytes.bytesize - tail)
end

# @brief Wait within the fixture budget for one driver operation.
def poll(operation, joint, request)
  remaining = 100_000
  while remaining > 0
    status, reply, length = WROS.call(operation, joint, request, 512)
    return [status, reply, length] if status != 11
    remaining -= 1
  end
  raise "driver response exceeded the polling budget"
end

status, joint = WROS.open("joint")
raise "missing simulated joint" unless status == 0
status, steady = WROS.open("steady")
raise "missing steady clock" unless status == 0
status, clock, length = WROS.call("clock.create", steady, wire_u64(0), 8)
raise "clock creation failed" unless status == 0 && length == 8
raise "driver connection refused" unless poll("driver.connect", joint, "")[0] == 0

(1..STEPS).each do |sequence|
  status, sample, length = WROS.call("clock.read", steady, clock, 32)
  raise "clock sample failed" unless status == 0 && length == 32
  expiry = wire_u64(read_u64(sample, 0) + 5 * 1_000_000_000)
  word = wire_u64(sequence)
  request = replace(replace(TEMPLATE, 0, word + expiry), 32, word)
  request = replace(request, request.bytesize - 8, expiry)
  if MODE == "success"
    # Adjacent commands alternate +0.5 and -0.5 in binary64.
    target = sequence % 2 == 1 ? "\x00\x00\x00\x00\x00\x00\xe0\x3f" : "\x00\x00\x00\x00\x00\x00\xe0\xbf"
    request = replace(request, TARGET_OFFSET, target)
  end
  raise "driver submission rejected" unless poll("driver.submit", joint, request)[0] == 0
  status, reply, length = poll("driver.result", joint, word)
  if MODE == "crash"
    raise "missing receiver failure" unless status == 5 || status == 13
    status, reply, length = WROS.call("driver.describe", joint, "", 512)
    raise "missing unresolved effect" unless status == 0 && length >= 32 &&
      read_u64(reply, 0) == 6 && read_u64(reply, 24) == 1
  else
    outcome = MODE == "success" ? 0 : 13
    raise "unexpected driver outcome" unless status == 0 && length >= 24 &&
      read_u64(reply, 0) == outcome && read_u64(reply, 16) == sequence
  end
end

raise "driver disconnect failed" unless WROS.call("driver.disconnect", joint, "", 512)[0] == 0
