# Compiler and interpreter source releases

From a complete SDK checkout run the following command to inspect all language selections. Use
`--language js --require` to require a verified source baseline for one selection. The check
works offline. It matches upstream release identities to the source locks, retained archives
and language-specific host inventories that the SDK reads.

```sh
python3 tools/qualification/language_sources.py
```

| Selection | Release evidence |
| --- | --- |
| C, C++, Fortran | The common source lock identifies the LLVM 23.1.5 release commit. WASI SDK 34 pins wasi-libc through its source submodule. An approved compiler build still needs its derivation and binary receipt, including the stable-release Herbceptions backport for C++. |
| Java, Kotlin | TeaVM 0.13.1 matches the upstream release commit. Kotlin uses the official 2.1.20 compiler. Both host inventories bind the Ubuntu OpenJDK 21.0.10+7 package. The review compared the SHA-256 of 36 distinct Maven artifacts with Maven Central. |
| JavaScript, Lua | JavaScript uses the official QuickJS 2026-06-04 distribution. Replay its complete source adaptation with `python3 third-parties/quickjs/verify_release.py`. The Lua 5.4.9 archive matches Lua's published digest. |
| Nim, Rust | The retained Nim 2.2.4 source matches the official source distribution. The Rust 1.98.0 source archive matches the upstream stable channel manifest. |
| TinyGo | The reviewed host inventory refers to TinyGo 0.38.0 and Go 1.24.2. The independent Go frontend has its own registry entry. |
| D | The Ubuntu build of LDC 1.41.0 supplies the pinned compiler and 723 BetterC import files. The signed site checks both before compilation. |
| Objective-C | GNUstep published libobjc2 2.3 at e877e782. The earlier SDK port used an untagged runtime, a21ae931. Those histories diverged. The checker expects the official source archive. |
| C#, Visual Basic | Both use the Microsoft .NET 10.0.404 SDK and 10.0.15 WASI Mono AOT and runtime packs. The package digests and extracted host-file inventory bind the installed tools to those releases. |

A registry entry without a developer package is reported as such. New compiler or interpreter
versions need source provenance and fresh build qualification. The result covers the base inputs
only. Execution profiles, MTE behavior, release signatures, simulator coverage and platform
qualification each have separate tests. The machine-readable review contains the primary release
references. [Release evidence](../../share/qualification/language-source-releases.json)
