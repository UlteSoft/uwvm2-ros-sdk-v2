const signal = wros.open("signal");
if (typeof signal !== "object") throw Error("capability.open returned " + signal);
const guard = wros["guard.create"](signal, new ArrayBuffer(0), 8);
if (guard.status !== 0 || guard.written !== 8n) throw Error("guard creation failed");
if (wros["guard.trigger"](signal, guard.data, 0).status !== 0) throw Error("guard trigger failed");
const taken = wros["guard.take"](signal, guard.data, 8);
if (taken.status !== 0 || new DataView(taken.data).getBigUint64(0, true) !== 1n) throw Error("guard not set");
if (wros.close(signal) !== 0) throw Error("capability close failed");
