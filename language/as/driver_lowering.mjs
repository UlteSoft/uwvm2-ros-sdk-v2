/** @file driver_lowering.mjs
 *  @brief Replace scalar SDK declarations with bounded Wasm staging functions.
 */
import binaryen from "binaryen";

export const claimExport = "__wros_as_claimz";
const intrinsicModule = "wros_as_driver";
const host = "uwvm_ros_v2";
const capacity = 512;
const objects = [
  ["request", 16, capacity],
  ["reply", 16 + capacity, capacity],
  ["length", 16 + 2 * capacity, 16],
  ["handle", 32 + 2 * capacity, 16],
];
const i32 = binaryen.i32;
const i64 = binaryen.i64;
const none = binaryen.none;
const abi = [i64, i32, i64, i64, i64, i64, i64];
const prefix = "__wros_as_internal_";

/** @brief Hide SDK declarations that the compiler exports from auxiliary sources. */
export function hideDriverDeclarations(module) {
  for (let i = module.getNumExports() - 1; i >= 0; --i) {
    const out = binaryen.getExportInfo(module.getExportByIndex(i));
    if (out.kind === binaryen.ExternalFunction &&
        binaryen.getFunctionInfo(module.getFunction(out.value)).module === intrinsicModule) {
      module.removeExport(out.name);
    }
  }
}

/** @brief Add the approved private objects after validating the scalar application. */
export function lowerDriver(module, tagged) {
  const imports = new Map();
  for (let i = 0; i < module.getNumFunctions(); ++i) {
    const info = binaryen.getFunctionInfo(module.getFunctionByIndex(i));
    if (info.module === intrinsicModule) {
      if (imports.has(info.base)) throw new Error("Duplicate driver intrinsic " + info.base);
      imports.set(info.base, info);
    } else if (info.module) {
      throw new Error("The driver profile requires only the SDK driver declarations");
    }
    if (info.name.startsWith(prefix)) throw new Error("Reserved driver function name");
  }
  if (!imports.size) throw new Error("Import the driver bindings from ./wros");
  if (module.getExport(claimExport)) throw new Error("Reserved driver export name");

  const c = n => module.i32.const(n);
  const word = n => module.i64.const(BigInt(n));
  const z = () => word(0);
  const at = name => module.global.get(prefix + name, i32);
  const assign = (name, value) => module.global.set(prefix + name, value);
  const slot = (index, type = i32) => module.local.get(index, type);
  const pointer = name => module.i64.extend_u(at(name));
  const address = (name, offset) => module.i32.add(at(name), offset);
  const width = types => types.length ? binaryen.createType(types) : none;
  const block = (body, type = none) => module.block(null, body, type);
  const assert = condition => module.if(condition, module.unreachable());
  const store = (name, value) => module.i64.store(0, 8, at(name), value);
  const load = name => module.i64.load(0, 8, at(name));

  module.setMemory(1, 1, null, [], false, false);
  for (const [name, base] of objects) module.addGlobal(prefix + name, i32, true, c(base));
  module.addGlobal(prefix + "ready", i32, true, c(0));
  if (tagged) {
    // The final byte emitter replaces this exact stub after Binaryen validation.
    module.addFunction(prefix + "claim", width([i32, i32]), i32, [], slot(0));
    module.addFunctionExport(prefix + "claim", claimExport);
  }
  if (tagged) {
    const init = [
      ...objects.map(([name, base, bytes]) => assign(name, module.call(prefix + "claim", [c(base), c(bytes)], i32))),
      assign("ready", c(1)),
    ];
    module.addFunction(prefix + "initialize", none, none, [],
                       module.if(module.i32.eqz(at("ready")), block(init)));
  }

  function bind(name, params, result, body, locals = []) {
    const info = imports.get(name);
    if (!info) return;
    if (info.params !== width(params) || info.results !== result) throw new Error("Invalid driver intrinsic signature");
    const entry = tagged ? [module.call(prefix + "initialize", [], none)] : [];
    module.removeFunction(info.name);
    module.addFunction(info.name, width(params), result, locals, block([...entry, ...body()], result));
    imports.delete(name);
  }

  function call(name, params, args) {
    const field = prefix + name;
    if (!module.getFunction(field)) module.addFunctionImport(field, host, name, width(params), i32);
    return module.call(field, args, i32);
  }

  bind("writeByte", [i32, i32], none, () => [
    assert(module.i32.or(module.i32.ge_u(slot(0), c(capacity)), module.i32.gt_u(slot(1), c(255)))),
    module.i32.store8(0, 1, address("request", slot(0)), slot(1)),
  ]);
  bind("writeWord", [i32, i64], none, () => [
    assert(module.i32.gt_u(slot(0), c(capacity - 8))),
    module.i64.store(0, 1, address("request", slot(0)), slot(1, i64)),
  ]);
  bind("open", [i32], i32, () => [
    assert(module.i32.or(module.i32.eqz(slot(0)), module.i32.gt_u(slot(0), c(capacity)))),
    store("handle", z()),
    call("capability.open", [i32, i64, i64, i64], [c(0), pointer("request"), module.i64.extend_u(slot(0)), pointer("handle")]),
  ]);
  bind("opened", [], i64, () => [load("handle")]);
  bind("close", [i64], i32, () => [
    call("capability.close", [i64], [slot(0, i64)]),
  ]);
  for (const name of ["connect", "submit", "result", "describe", "disconnect"]) {
    const submit = name === "submit";
    const params = submit ? [i64, i32] : [i64];
    const status = params.length;
    bind(name, params, i32, () => [
      ...(submit ? [assert(module.i32.gt_u(slot(1), c(capacity)))] : []),
      store("length", z()),
      module.local.set(status, call("driver." + name, abi, [
        slot(0, i64), c(0), pointer("request"),
        submit ? module.i64.extend_u(slot(1)) : word(name === "result" ? 8 : 0),
        pointer("reply"), word(capacity), pointer("length"),
      ])),
      module.if(slot(status), store("length", z())),
      slot(status),
    ], [i32]);
  }
  bind("replySize", [], i32, () => [
    assert(module.i64.gt_u(load("length"), word(capacity))),
    module.i32.wrap(load("length")),
  ]);
  bind("readWord", [i32], i64, () => [
    assert(module.i64.gt_u(load("length"), word(capacity))),
    assert(module.i64.gt_u(module.i64.add(module.i64.extend_u(slot(0)), word(8)), load("length"))),
    module.i64.load(0, 1, address("reply", slot(0))),
  ]);
  if (imports.size) throw new Error("Unknown driver intrinsic " + imports.keys().next().value);
}
