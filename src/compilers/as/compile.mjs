/** @file compile.mjs
 *  @brief Compile one AssemblyScript application and certify its memory-free output.
 */
import {readdir, readFile, writeFile} from "node:fs/promises";
import asc from "assemblyscript/asc";
import {Transform} from "assemblyscript/transform";
import binaryen from "binaryen";

const source = await readFile("input.ts", "utf8");
const sources = new Map([["input.ts", source], ["scene.ts", 'export * from "./uwrosv2/scene";']]);
async function loadBindings(directory) {
  for (const item of await readdir(directory, {withFileTypes: true})) {
    const name = directory + "/" + item.name;
    if (item.isDirectory()) await loadBindings(name);
    else if (item.isFile() && name.endsWith(".ts")) sources.set(name, await readFile(name, "utf8"));
  }
}
await loadBindings("uwrosv2");
const driver = process.argv.includes("--driver");
if (driver) sources.set("wros.ts", await readFile("wros.ts", "utf8"));
const debug = process.argv.includes("--debug");
const options = {
  runtime: "stub",
  noExportMemory: true,
  optimizeLevel: 3,
  // Select the upstream full dtoi32 algorithm for NativeMath integer conversion.
  shrinkLevel: 0,
  debug,
};

/** Check the final scalar core before emitting it. */
function checkScalarModule(module) {
  module.runPasses(["remove-unused-module-elements"]);
  if (module.hasMemory() || !module.validate()) {
    throw new Error("The scalar AssemblyScript profile requires validated Wasm without linear memory");
  }
  const entry = module.getExport("_start");
  if (entry === 0) throw new Error("Export _start() as the application entry");
  const exported = binaryen.getExportInfo(entry);
  if (exported.kind !== binaryen.ExternalFunction) throw new Error("_start must be a function");
  const fn = binaryen.getFunctionInfo(module.getFunction(exported.value));
  if (fn.params !== binaryen.none || fn.results !== binaryen.none) {
    throw new Error("_start must have signature () -> ()");
  }
}

/** Validate and emit on the module that still owns the original source locations. */
class ScalarSourceMap extends Transform {
  afterCompile(module) {
    module.setFeatures(module.getFeatures() | binaryen.Features.NontrappingFPToInt);
    checkScalarModule(module);
  }
}

/** Report diagnostics from the pinned compiler before publishing any output. */
function checkCompiler(result) {
  const diagnostics = result.stderr.toString();
  if (diagnostics) process.stderr.write(diagnostics);
  if (result.error) throw new Error("AssemblyScript compilation failed");
}

const locations = debug && !driver;
const output = new Map();
const args = ["input.ts", "--runtime", options.runtime, "--noExportMemory",
  "--optimizeLevel", String(options.optimizeLevel), "--shrinkLevel", String(options.shrinkLevel),
  "--outFile", "result.wasm"];
if (debug) args.push("--debug");
if (locations) args.push("--sourceMap");
const compile = await asc.main(args, {
  readFile: name => sources.get(name) ?? null,
  listFiles: () => [],
  writeFile: (name, data) => output.set(name, data),
  transforms: locations ? [new ScalarSourceMap()] : [],
});
checkCompiler(compile);
if (!output.has("result.wasm")) throw new Error("Missing AssemblyScript compiler output");
if (locations) {
  for (const name of ["result.wasm", "result.wasm.map"]) {
    if (!output.has(name)) throw new Error("Missing AssemblyScript compiler output: " + name);
    await writeFile(name, output.get(name), {flag: "wx"});
  }
} else {
  const module = binaryen.readBinary(output.get("result.wasm"));
  try {
    // Preserve saturating scalar float-to-int conversions when validating Core Wasm.
    module.setFeatures(module.getFeatures() | binaryen.Features.NontrappingFPToInt);
    const lowering = driver ? await import("./driver_lowering.mjs") : null;
    if (lowering) lowering.hideDriverDeclarations(module);
    checkScalarModule(module);
    if (lowering) {
      lowering.lowerDriver(module, !process.argv.includes("--plain"));
      if (!module.validate()) throw new Error("Invalid generated driver staging module");
    }
    await writeFile("result.wasm", module.emitBinary(), {flag: "wx"});
  } finally {
    module.dispose();
  }
}
