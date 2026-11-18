## Private source producer. Only its generated C is consumed by the guest compiler.
import std/os
import options, commands, condsyms, modulegraphs, idents, lineinfos, pathutils,
       pipelines, cgen, extccomp, msgs

proc lower() =
  if paramCount() != 6 or paramStr(1) notin ["wasm32", "wasm64"]:
    quit("usage: wrnim-lower wasm32|wasm64 LIBRARY SDK_MODULES PROJECT_DIR CACHE ENTRY.nim", 2)
  for index in 2..6:
    if not paramStr(index).isAbsolute:
      quit("lowering paths must be absolute", 2)
  let conf = newConfigRef()
  initDefines(conf.symbols)
  conf.setCmd(cmdCompileToC)
  conf.setFromProjectName(paramStr(6))
  conf.outDir = AbsoluteDir(paramStr(5))
  conf.outFile = RelativeFile("wros_entry")
  for pass in [passCmd1, passCmd2]:
    for item in [("os", "standalone"), ("cpu", paramStr(1)), ("cc", "clang"),
                 ("lib", paramStr(2)), ("path", paramStr(3)), ("path", paramStr(4)),
                 ("nimcache", paramStr(5)), ("threads", "off"), ("mm", "arc"),
                 ("exceptions", "goto"), ("stackTrace", "off"), ("lineTrace", "off"),
                 ("define", "useMalloc"), ("noMain", "on"), ("compileOnly", "on")]:
      processSwitch(item[0], item[1], pass, unknownLineInfo, conf)
  conf.searchPaths.add(conf.libpath)
  defineSymbol(conf.symbols, "c")
  extccomp.initVars(conf)
  if not extccomp.ccHasSaneOverflow(conf):
    defineSymbol(conf.symbols, "nimEmulateOverflowChecks")
  let graph = newModuleGraph(newIdentCache(), conf)
  setPipeLinePass(graph, CgenPass)
  compilePipelineProject(graph)
  if conf.errorCounter != 0 or graph.backend == nil: quit(1)
  cgenWriteModules(graph.backend, conf)
  extccomp.writeJsonBuildInstructions(conf, graph.cachedFiles)
  if conf.errorCounter != 0: quit(1)

lower()
