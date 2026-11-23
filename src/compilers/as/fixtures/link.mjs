/** Link the SDK's forwarding functions with the pinned upstream AssemblyScript compiler. */
import asc from "assemblyscript/asc";

const result = await asc.main(["all_imports.ts", "--runtime", "stub", "--noExportMemory",
  "--optimizeLevel", "2", "--outFile", "all_imports.wasm"]);
const diagnostics = result.stderr.toString();
if (diagnostics) process.stderr.write(diagnostics);
if (result.error) process.exitCode = 1;
