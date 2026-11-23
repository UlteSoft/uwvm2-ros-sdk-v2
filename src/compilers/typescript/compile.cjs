/** Check the supplied project and emit ES modules consumed by the guest's QuickJS loader. */
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
for (const [name, contents] of Object.entries(request.sdkModules)) {
    files.set("/sdk/" + name + ".d.ts", contents);
}
for (const name of fs.readdirSync(lib)) {
    if (/^lib\.[a-z0-9.]+\.d\.ts$/.test(name)) files.set("/lib/" + name, fs.readFileSync(lib + "/" + name, "utf8"));
}
const edges = new Map(Array.from(sources.keys(), name => [name, new Map()]));
const emitted = {};
const options = {
    strict: true, noEmitOnError: true, target: ts.ScriptTarget.ES2022,
    module: ts.ModuleKind.ES2022, moduleDetection: ts.ModuleDetectionKind.Force,
    types: [], lib: ["lib.es2022.d.ts"], rootDir: "/app", outDir: "/out",
    noUncheckedSideEffectImports: true, newLine: ts.NewLineKind.LineFeed,
};

function resolveModule(name, from) {
    if (Object.hasOwn(request.sdkModules, name)) {
        return {resolvedFileName: "/sdk/" + name + ".d.ts", extension: ts.Extension.Dts, isExternalLibraryImport: true};
    }
    if (!(name.startsWith("./") || name.startsWith("../")) || name.includes("\\")) {
        throw Error("unregistered guest module: " + name);
    }
    const id = path.resolve(path.dirname(from), name);
    const candidates = name.endsWith(".js") ? [id.slice(0, -3) + ".ts"] : [id + ".ts", id + "/index.ts"];
    const target = candidates.find(candidate => sources.has(candidate));
    if (!target) throw Error("module is outside the supplied source set: " + name);
    let relative = path.relative(path.dirname(from), target).replace(/\.ts$/, ".js");
    if (!relative.startsWith(".")) relative = "./" + relative;
    edges.get(from).set(name, relative);
    return {resolvedFileName: target, extension: ts.Extension.Ts, isExternalLibraryImport: false};
}

const host = {
    getDefaultLibFileName: () => "/lib/lib.es2022.d.ts", getDefaultLibLocation: () => "/lib",
    getCurrentDirectory: () => "/app", getCanonicalFileName: name => name, useCaseSensitiveFileNames: () => true,
    getNewLine: () => "\n", fileExists: name => files.has(name), readFile: name => files.get(name),
    getSourceFile(name, languageVersion) {
        if (!files.has(name)) return undefined;
        const file = ts.createSourceFile(name, files.get(name), languageVersion, true);
        if (sources.has(name)) {
            if (file.hasNoDefaultLib || file.referencedFiles.length || file.libReferenceDirectives.length ||
                file.typeReferenceDirectives.length || file.amdDependencies.length || file.moduleName)
                throw Error("compiler reference directives are outside the project profile: " + name);
            function visit(node) {
                if (ts.isCallExpression(node) && node.expression.kind === ts.SyntaxKind.ImportKeyword)
                    throw Error("dynamic import is outside the static TypeScript project profile: " + name);
                ts.forEachChild(node, visit);
            }
            visit(file);
        }
        return file;
    },
    resolveModuleNames: (names, from) => names.map(name => resolveModule(name, from)),
    writeFile(name, contents, bom, error, originals) {
        if (!name.startsWith("/out/") || !name.endsWith(".js") || originals?.length !== 1 ||
            !sources.has(originals[0].fileName)) throw Error("unexpected compiler output");
        emitted[name.slice("/out/".length)] = contents;
    },
};

// Preserve each dependency's canonical identity in QuickJS, including cycles and index imports.
const rewrite = ctx => file => {
    const resolved = edges.get(file.fileName);
    function visit(node) {
        const name = node.moduleSpecifier && resolved?.get(node.moduleSpecifier.text);
        if (name && ts.isImportDeclaration(node)) {
            return ts.factory.updateImportDeclaration(node, node.modifiers, node.importClause, ts.factory.createStringLiteral(name), node.attributes);
        }
        if (name && ts.isExportDeclaration(node)) {
            return ts.factory.updateExportDeclaration(node, node.modifiers, node.isTypeOnly, node.exportClause,
                ts.factory.createStringLiteral(name), node.attributes);
        }
        return ts.visitEachChild(node, visit, ctx);
    }
    return ts.visitNode(file, visit);
};

const program = ts.createProgram([...sources.keys(), "/sdk/wros.d.ts"], options, host);
const diagnostics = ts.getPreEmitDiagnostics(program);
if (diagnostics.length) {
    process.stderr.write(ts.formatDiagnostics(diagnostics.slice(0, 20), host));
    process.exitCode = 1;
} else {
    const result = program.emit(undefined, undefined, undefined, false, {after: [rewrite]});
    if (result.emitSkipped || result.diagnostics.length || Object.keys(emitted).length !== sources.size)
        throw Error("incomplete TypeScript output");
    fs.writeFileSync(outputPath, JSON.stringify({entry: request.entry.replace(/\.ts$/, ".js"), modules: emitted}));
}
