# Mono for WASI

[简体中文](README.zh.md)

The native sources come from .NET Runtime v10.0.15, commit `a3788b71495457354b64ca8040b6ded5ff6ca4f9`. They include the Mono AOT compiler and runtime sources, SGen collector, Mono-specific CoreLib sources, WASI platform code and shared native headers. The source index gives the original Git blob for each selected file. [Upstream release](https://github.com/dotnet/runtime/tree/a3788b71495457354b64ca8040b6ded5ff6ca4f9) · [Source and license metadata](upstream.json) · [File index](upstream.git-blobs)

On a wasm32 WASI build the retained SGen change delegates sorting to wasi-libc. This bounds the temporary storage used while the collector holds the heap lock. The original file matched the historical patch base byte for byte. The SDK still needs the managed compiler distributions, the matching Mono WASI build and the installed C#, F# and Visual Basic guest projects. Their qualification is pending.
