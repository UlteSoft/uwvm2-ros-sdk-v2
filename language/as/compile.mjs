/** @file compile.mjs
 *  @brief Compile one AssemblyScript application and certify its memory-free output.
 */
import {readFile, writeFile} from "node:fs/promises";
import asc from "assemblyscript/asc";
import binaryen from "binaryen";

const source = await readFile("input.ts", "utf8");
const sources = {"input.ts": source};
const driver = process.argv.includes("--driver");
if (driver) sources["wros.ts"] = await readFile("wros.ts", "utf8");
const compile = await asc.compileString(sources, {
  runtime: "stub",
  noExportMemory: true,
  optimizeLevel: 3,
  // Select the upstream full dtoi32 algorithm for NativeMath integer conversion.
  shrinkLevel: 0,
  debug: process.argv.includes("--debug"),
});
const diagnostics = compile.stderr.toString();
if (diagnostics) process.stderr.write(diagnostics);
if (compile.error || !compile.binary) {
  throw new Error("AssemblyScript compilation failed");
}

const module = binaryen.readBinary(compile.binary);
try {
  // Preserve saturating scalar float-to-int conversions when validating Core Wasm.
  module.setFeatures(module.getFeatures() | binaryen.Features.NontrappingFPToInt);
  const lowering = driver ? await import("./driver_lowering.mjs") : null;
  if (lowering) lowering.hideDriverDeclarations(module);
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
  if (lowering) {
    lowering.lowerDriver(module, !process.argv.includes("--plain"));
    if (!module.validate()) throw new Error("Invalid generated driver staging module");
  }
  await writeFile("result.wasm", module.emitBinary(), {flag: "wx"});
} finally {
  module.dispose();
}
