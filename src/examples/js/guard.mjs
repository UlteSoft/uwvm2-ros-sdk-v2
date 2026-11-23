import { wr_capability_open, wr_capability_close } from "uwrosv2/capability";
import { wr_guard_create } from "uwrosv2/guard";
import { addressOf } from "uwrosv2/memory";
const alias = new Uint8Array([115, 105, 103, 110, 97, 108]); // "signal"
const handle = new ArrayBuffer(8);
if (wr_capability_open(0, addressOf(alias.buffer), 6n, addressOf(handle)) !== 0) throw Error("open");
const capability = new DataView(handle).getBigUint64(0, true);
const reply = new ArrayBuffer(8);
const written = new ArrayBuffer(8);
try {
  if (wr_guard_create(capability, 0, 0n, 0n, addressOf(reply), 8n, addressOf(written)) !== 0)
    throw Error("create");
  if (new DataView(written).getBigUint64(0, true) !== 8n) throw Error("length");
} finally {
  if (wr_capability_close(capability) !== 0) throw Error("close");
}
