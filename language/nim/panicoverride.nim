proc wrosTrap() {.importc: "__builtin_trap", nodecl, noreturn, noSideEffect.}
proc rawoutput(s: string) = discard
proc panic(s: string) {.noreturn.} = wrosTrap()
