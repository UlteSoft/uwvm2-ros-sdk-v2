/** @file compile.mjs
 *  @brief Compile one AssemblyScript application and certify its memory-free output.
 */
import {readFile, writeFile} from "node:fs/promises";
import asc from "assemblyscript/asc";
import binaryen from "binaryen";

const source = await readFile("input.ts", "utf8");
const compile = await asc.compileString({"input.ts": source}, {
  runtime: "stub",
  noExportMemory: true,
  optimizeLevel: 3,
  shrinkLevel: 1,
  debug: process.argv.includes("--debug"),
});
const diagnostics = compile.stderr.toString();
if (diagnostics) process.stderr.write(diagnostics);
if (compile.error || !compile.binary) {
  throw new Error("AssemblyScript compilation failed");
}

const module = binaryen.readBinary(compile.binary);
try {
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
  await writeFile("result.wasm", module.emitBinary(), {flag: "wx"});
} finally {
  module.dispose();
}
