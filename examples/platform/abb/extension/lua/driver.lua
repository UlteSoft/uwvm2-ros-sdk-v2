--- @brief Check both deployment gates before the driver can receive a request.
local opened, arm = wros.open("arm")
assert(opened == 0)
local status, data = wros["driver.connect"](arm, "", 8)
assert(status == 13 and data == nil)
assert(wros.close(arm) == 0)
