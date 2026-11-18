local status, joint = wros.open("joint")
assert(status == 0)
local function poll(operation, body)
    for i = 1, 10000000 do
        local code, reply = wros[operation](joint, body, 512)
        if code ~= 11 then return code, reply end
    end
    error("receiver timeout")
end
local function replace(bytes, offset, value)
    return bytes:sub(1, offset) .. value .. bytes:sub(offset + #value + 1)
end

assert(poll("driver.connect", "") == 0)
for sequence = 1, steps do
    local word = string.pack("<I8", sequence)
    local request = replace(replace(template, 0, word), 32, word)
    if mode == "success" then
        request = replace(request, target_offset, string.pack("<d", sequence % 2 == 1 and 0.5 or -0.5))
    end
    assert(poll("driver.submit", request) == 0)
    local code, result = poll("driver.result", word)
    if mode == "crash" then
        assert(code == 5 or code == 13)
        local described, snapshot = wros["driver.describe"](joint, "", 512)
        assert(described == 0 and #snapshot >= 32)
        assert(string.unpack("<I8", snapshot) == 6 and string.unpack("<I8", snapshot, 25) == 1)
    else
        assert(code == 0 and #result >= 24)
        local outcome, _, reported = string.unpack("<I8I8I8", result)
        assert(outcome == (mode == "success" and 0 or 13) and reported == sequence)
    end
end
assert(wros["driver.disconnect"](joint, "", 512) == 0)
