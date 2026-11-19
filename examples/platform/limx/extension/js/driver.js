/** @brief Test that the platform child and the parent capability must both authorize driver connection. */
const handle = wros.open("arm");
if (typeof handle === "number") throw Error("driver handle unavailable");
const reply = wros["driver.connect"](handle, new ArrayBuffer(0), 8);
if (reply.status !== 13 || reply.data !== null || wros.close(handle) !== 0)
    throw Error("unexpected driver access or reply");
