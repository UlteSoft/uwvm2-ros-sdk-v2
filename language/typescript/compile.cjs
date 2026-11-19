/** @file compile.cjs
 * @brief Compile a closed set of user modules. Only the build host reads these SDK
 * files. Application code executes later, inside the embedded Wasm interpreter. */
"use strict";
const fs = require("node:fs");
const path = require("node:path").posix;
const [lib, requestPath, outputPath] = process.argv.slice(2);
const ts = require(lib + "/typescript.js");
if (ts.version !== "5.9.3") throw Error("unexpected TypeScript compiler version");

const request = JSON.parse(fs.readFileSync(requestPath, "utf8"));
const sources = new Map(request.sources.map(row => ["/app/" + row.name, row.source]));
const entry = "/app/" + request.entry;
const files = new Map(sources);
files.set("/sdk/wros.d.ts", request.declarations);
for (const name of fs.readdirSync(lib)) {
    if (/^lib\.[a-z0-9.]+\.d\.ts$/.test(name))
        files.set("/lib/" + name, fs.readFileSync(lib + "/" + name, "utf8"));
}
const dependencies = new Map(Array.from(sources.keys(), name => [name, new Map()]));
const emitted = new Map();
const options = {
    strict: true, noEmitOnError: true, target: ts.ScriptTarget.ES2022,
    module: ts.ModuleKind.CommonJS, moduleDetection: ts.ModuleDetectionKind.Force,
    types: [], lib: ["lib.es2022.d.ts"], rootDir: "/app", outDir: "/out",
    noUncheckedSideEffectImports: true, newLine: ts.NewLineKind.LineFeed,
};
/** @brief Resolve an import exclusively against explicitly supplied project modules. */
function resolveModule(name, from) {
    if (!(name.startsWith("./") || name.startsWith("../")) || name.includes("\\"))
        throw Error("only relative project imports are supported: " + name);
    const id = path.resolve(path.dirname(from), name);
    const candidates = name.endsWith(".js") ? [id.slice(0, -3) + ".ts"] : [id + ".ts", id + "/index.ts"];
    const target = candidates.find(candidate => sources.has(candidate));
    if (!target) throw Error("module is outside the supplied source set: " + name);
    dependencies.get(from).set(name, target);
    return {resolvedFileName: target, extension: ts.Extension.Ts, isExternalLibraryImport: false};
}
const host = {
    getDefaultLibFileName: () => "/lib/lib.es2022.d.ts",
    getDefaultLibLocation: () => "/lib",
    getCurrentDirectory: () => "/app",
    getCanonicalFileName: name => name,
    useCaseSensitiveFileNames: () => true,
    getNewLine: () => "\n",
    fileExists: name => files.has(name),
    readFile: name => files.get(name),
    getSourceFile(name, languageVersion) {
        if (!files.has(name)) return undefined;
        const file = ts.createSourceFile(name, files.get(name), languageVersion, true);
        if (sources.has(name)) {
            if (file.hasNoDefaultLib || file.referencedFiles.length || file.libReferenceDirectives.length ||
                file.typeReferenceDirectives.length || file.amdDependencies.length || file.moduleName)
                throw Error("compiler reference directives are outside the project profile: " + name);
            function visit(node) {
                if (ts.isCallExpression(node) && node.expression.kind === ts.SyntaxKind.ImportKeyword)
                    throw Error("dynamic import is outside the static guest module profile: " + name);
                ts.forEachChild(node, visit);
            }
            visit(file);
        }
        return file;
    },
    resolveModuleNames: (names, from) => names.map(name => resolveModule(name, from)),
    writeFile(name, contents, bom, error, originals) {
        if (!name.endsWith(".js") || originals?.length !== 1 || !sources.has(originals[0].fileName))
            throw Error("unexpected compiler output");
        emitted.set(originals[0].fileName, contents);
    },
};
const program = ts.createProgram([...sources.keys(), "/sdk/wros.d.ts"], options, host);
const diagnostics = ts.getPreEmitDiagnostics(program);
if (diagnostics.length) {
    process.stderr.write(ts.formatDiagnostics(diagnostics.slice(0, 20), host));
    process.exitCode = 1;
} else {
    const result = program.emit();
    if (result.emitSkipped || result.diagnostics.length || emitted.size !== sources.size)
        throw Error("incomplete TypeScript output");
    // Node-style CommonJS initialization order, including partial exports in a cycle.
    // The guest loader can resolve only edges already resolved by the real compiler.
    const ids = new Map(Array.from(sources.keys()).sort().map((key, index) => [key, index]));
    const modules = Array.from(ids.keys(), name => {
        const cases = Array.from(dependencies.get(name), ([key, target]) =>
            "case " + JSON.stringify(key) + ": return load(" + ids.get(target) + ");").join("\n");
        return "[function(module, exports, require){\n" + emitted.get(name) +
            "\n}, function(name, load){switch(name){\n" + cases +
            "\n}throw Error('unregistered guest module');}]";
    });
    const bundle = "(function(units){'use strict';const cache=Object.create(null);\n" +
        "function load(i){if(cache[i])return cache[i].exports;const m={exports:{}};cache[i]=m;\n" +
        "const u=units[i];u[0](m,m.exports,n=>u[1](n,load));return m.exports;}\n" +
        "load(" + ids.get(entry) + ");})([\n" + modules.join(",\n") + "\n]);\n";
    fs.writeFileSync(outputPath, bundle);
}
