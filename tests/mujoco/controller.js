// The harness prepends the bounded request, control offset, mode and step count.
function check(condition) { if (!condition) throw Error("unexpected driver result"); }
const joint = wros.open("joint");
check(typeof joint === "object");
const empty = new ArrayBuffer(0);
function poll(op, request) {
    for (let i = 0; i < 100000; ++i) {
        const result = wros[op](joint, request, 512);
        if (result.status !== 11) return result;
    }
    throw Error("driver deadline");
}
check(poll("driver.connect", empty).status === 0);
for (let i = 1; i <= steps; ++i) {
    const word = new DataView(new ArrayBuffer(8));
    word.setBigUint64(0, BigInt(i), true);
    const message = new DataView(new Uint8Array(template).buffer);
    message.setBigUint64(0, BigInt(i), true);
    message.setBigUint64(32, BigInt(i), true);
    if (mode === "success") message.setFloat64(targetOffset, i % 2 ? 0.5 : -0.5, true);
    check(poll("driver.submit", message.buffer).status === 0);
    let reply = poll("driver.result", word.buffer);
    if (mode === "crash") {
        check(reply.status === 5 || reply.status === 13);
        reply = wros["driver.describe"](joint, empty, 512);
        check(reply.status === 0 && reply.written >= 32n);
        const snapshot = new DataView(reply.data);
        check(snapshot.getBigUint64(0, true) === 6n && snapshot.getBigUint64(24, true) === 1n);
    } else {
        check(reply.status === 0 && reply.written >= 24n);
        const result = new DataView(reply.data);
        check(result.getBigUint64(0, true) === (mode === "success" ? 0n : 13n));
        check(result.getBigUint64(16, true) === BigInt(i));
    }
}
check(wros["driver.disconnect"](joint, empty, 512).status === 0);
