/** @file
 *  @brief Compare the installed AssemblyScript artifact with native ECMAScript.
 */
const fs = require("node:fs");

const f64 = {
  MAX_VALUE: Number.MAX_VALUE, MAX_SAFE_INTEGER: Number.MAX_SAFE_INTEGER,
  MIN_VALUE: Number.MIN_VALUE, EPSILON: Number.EPSILON
};
const buffer = new DataView(new ArrayBuffer(8));
let seed = 0x8ba1f436;

function next() {
  seed ^= seed << 13;
  seed ^= seed >>> 17;
  seed ^= seed << 5;
  return seed >>> 0;
}

function sample() {
  buffer.setUint32(0, next());
  buffer.setUint32(4, next());
  return buffer.getFloat64(0);
}

async function main() {
  let assertions = 0;
  function assert(condition) {
    if (!condition) throw new Error("upstream assertion failed");
    assertions++;
  }
  checkOriginal(Math, f64, assert);
  if (assertions !== 28) throw new Error("native original checks did not all run");

  const { instance } = await WebAssembly.instantiate(fs.readFileSync(process.argv[2]));
  const { imul, clz32, _start } = instance.exports;
  _start();
  assertions = 0;
  checkOriginal({ imul, clz32 }, f64, assert);
  if (assertions !== 28) throw new Error("Wasm original checks did not all run");

  function differential(left, right) {
    const product = imul(left, right);
    const zeros = clz32(left);
    if (product !== Math.imul(left, right) || zeros !== Math.clz32(left)) {
      throw new Error("native/Wasm integer conversion disagreement at " + [left, right, product, zeros]);
    }
  }
  differential(-0.5, 1);
  differential(-1.5, 1);
  for (let index = 0; index < 2048; ++index) {
    differential(sample(), sample());
  }
  console.log(JSON.stringify({ upstream_assertions: assertions, differential_checks: 4100 }));
}

main().catch(error => { console.error(error); process.exitCode = 1; });
