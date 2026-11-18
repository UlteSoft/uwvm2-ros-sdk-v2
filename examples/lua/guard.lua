local status, signal = wros.open("signal")
assert(status == 0)
local create, trigger, take = wros["guard.create"], wros["guard.trigger"], wros["guard.take"]
local code, guard, size = create(signal, "", 8)
assert(code == 0 and size == 8)
assert(trigger(signal, guard, 0) == 0)
local available, bytes = take(signal, guard, 8)
assert(available == 0 and string.unpack("<I8", bytes) == 1)
assert(wros.close(signal) == 0)
