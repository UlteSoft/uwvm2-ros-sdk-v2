# Measure the WasmMTE linear-access kernel

Build the four guest modules once with an installed C binary SDK. Run the same bundle with a VM for each host ABI. The published run used x86_64 and i686 on x86 hardware, and AArch64, ARM EABI and ARM hard-float under system QEMU TCG. The receipt gives the VM and compiler revisions, module hashes, iteration count for each cell and its paired timings. [Five-host measurements](../qualification/cfamily-mte-performance.json) · [Kernel and native reference](../../src/qualification/cfamily/mte_performance_sources) · [简体中文](../zh/cfamily-mte-performance.md)

From this SDK checkout, supply the installed C prefix and the VM executable. Each command creates a new directory on the checkout volume. Linux requires Python 3.11+ at `/usr/bin/python3`, Bubblewrap with user namespaces, systemd user scopes and cgroup v2. The build phase also needs native GCC at `/usr/bin/gcc`. The qualification parent slice `wrosvendor.slice` must have `MemoryMax=64G`, `MemorySwapMax=0` and `memory.oom.group=0`. The launcher creates a child scope with the same memory and swap limits and group OOM killing, then verifies the limits, private namespaces, read-only temporary mounts and project scratch before starting either workload. [Shared isolation launcher](../../src/qualification/isolated.py)

```sh
runner=src/qualification/cfamily/mte_performance.py
/usr/bin/python3 -I -B "$runner" build --cc-sdk /path/to/installed/c --work .tmp/mte-build
/usr/bin/python3 -I -B "$runner" run --programs .tmp/mte-build/fixtures \
  --vm /path/to/uwvm2-ros --work .tmp/mte-run
```

Copy the whole `fixtures` directory to measure another host. The published i686 VM requires the 32-bit ELF loader `/lib/ld-linux.so.2` and 32-bit shared libraries, including `libatomic.so.1`, in the system library paths. Use a native i386 system or an x86_64 system with 32-bit execution support and those libraries (on Debian, `libc6:i386` and `libatomic1:i386` supply the loader and libatomic).

On an x86_64 Linux host with native i686 execution support, one command measures both VM ABIs. It verifies the ELF class and machine, then runs x86_64 followed by i686 in separate offline namespaces on the same logical CPU. Each VM runs INT and AOT at both guest widths using the four modules from the build above.

```sh
/usr/bin/python3 -I -B "$runner" x86-matrix --programs .tmp/mte-build/fixtures \
  --vm-x86_64 /path/to/x86_64/uwvm2-ros --vm-i686 /path/to/i686/uwvm2-ros \
  --work .tmp/mte-x86
```

If the host lacks the i386 `libatomic.so.1`, append `--i686-libatomic /path/to/extracted/libatomic.so.1` to use a local copy from Debian’s `libatomic1:i386` package. The runner mounts that file read-only in the i686 namespace and sets the library search path on the i686 VM process. `--cpu`, `--repeats` and `--iterations` apply to both ABIs. Once all eight cells succeed, `.tmp/mte-x86/matrix.json` records the CPU, kernel, VM and fixture hashes, and both paired ratios per cell. It gives paths and SHA-256 hashes for `x86_64/summary.json` and `i686/summary.json`, which contain the individual samples.

For one published x86_64 cell, add `--width 32 --engine int --iterations 8388608`. By default both widths and engines run five repeats, pinned to the first permitted CPU. Use `--cpu N` to choose another. Automatic calibration targets 320 ms of software checking and selects a power of two. Add `--emulated` inside a system-QEMU guest to use its shorter calibration probe. On an MTE-capable AArch64 Linux system add `--hardware` to time the synchronous hardware backend alongside software checking. An untimed control must show both a tagged mapping and successful synchronous tag control on the VM under `strace`. Supply `--strace /path/to/strace` for a separately installed tracer. Each control saves its trace beside `summary.json`. The cell’s `hardware_probe` records the filename and SHA-256.

The guest clocks initialization and a loop that reads and writes one indexed 32-bit word in a 4 KiB array. Each sample must match the independently compiled native checksum and report the expected zero or nonzero allocation tag. In `summary.json`, each ratio divides long-kernel times from the same repetition. The denominators are the ordinary module and the same tagged module with runtime checking disabled. Triples give inclusive Q1, median and Q3. The paired samples also include quarter-length and zero-loop controls, guest nanoseconds and host process nanoseconds. The summary identifies the supplied VM and module hashes that match the publication. [Runner](../../src/qualification/cfamily/mte_performance.py)

## Native x86 timings and VTune hotspots

On the 4 KiB kernel, software checking produced a larger relative slowdown in INT than in AOT at both guest widths. In the published paired timings, x86_64 INT took 1.84× and 1.78× the time of the same tagged module with checks disabled (wasm32 and wasm64, respectively). AOT took 1.42× and 1.52×. On i686 the corresponding medians were 3.56× and 3.14× for INT, and 1.91× and 1.96× for AOT. [Paired guest timings](../qualification/cfamily-mte-performance.json)

VTune profiled all 16 combinations on one Core i9-14900HX with release VM `d46186fca2dc`. Every run matched the native checksum and reported the expected allocation tag, nonzero with software checks and zero with checks disabled. Filtering raw instruction pointers to the VM process on logical CPU 6 placed 49–52% of each checked INT run’s distributed-cycle samples in the cached scalar handlers on x86_64 or the access-policy, guest-access and dispatch handlers on i686. Interpreter load or store handlers led all four disabled profiles. In a separate x86_64 build with debug symbols (SHA-256 prefix `7fa4df1e1920`), 44 wasm32 INT samples hit the shadow-tag byte load at `shadow.h` line 207. The instruction `movzx r14d, byte ptr [r12+r13]` was at `0x1e0c0a0` in that executable. [Tag read in the profiled revision](https://github.com/UlteSoft/uwvm2-ros/blob/d46186fca2dc60eebc71fdf4bf1c78ab32b9cb91/src/uwvm2/extension/memtag/shadow.h#L207) · [VTune measurements](../qualification/cfamily-mte-vtune.json)

In AOT, MCJIT symbol ranges placed 88–91% of checked samples and 92–95% of disabled samples in the compiled guest kernel. Those shares include loop arithmetic and data accesses. In checked wasm32 INT, VTune classified 22.9% of P-core pipeline slots as front-end bound on x86_64 and 1.8% on i686. DRAM stalls accounted for 0.0–0.5% of P-core clockticks across the four wasm32 INT memory reports. CPU 6 shared its physical core with SMT sibling 7, uncore bandwidth included other system traffic, and driverless sampling lacked cache-line attribution. The reference-cycle event `CPU_CLK_UNHALTED.REF_TSC` covered only part of several runs. Physical Arm MTE performance requires measurements on Arm hardware.

The scan-only candidate `5cafd78f1897` stayed unmerged. In separate A/B timings, each of the eight software-check configurations had 16 pairs, and every 97.87% sign interval for its median change included zero.
