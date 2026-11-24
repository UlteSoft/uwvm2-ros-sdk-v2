# Measure the WasmMTE linear-access kernel

Build the four guest modules once with an installed C binary SDK. Run the same bundle with a VM for each host ABI. The published run used x86_64 and i686 on x86 hardware, and AArch64, ARM EABI and ARM hard-float under system QEMU TCG. The receipt gives the VM and compiler revisions, module hashes, iteration count for each cell and its paired timings. [Five-host measurements](../qualification/cfamily-mte-performance.json) · [Kernel and native reference](../../src/qualification/cfamily/mte_performance_sources) · [简体中文](../zh/cfamily-mte-performance.md)

From this SDK checkout, supply the installed C prefix and the VM executable. Each command creates a new directory on the checkout volume. Linux requires Python 3.11+, Bubblewrap with user namespaces, systemd user scopes and cgroup v2. The build phase also needs native GCC at `/usr/bin/gcc`. The qualification parent slice `wrosvendor.slice` must have `MemoryMax=64G`, `MemorySwapMax=0` and `memory.oom.group=0`. The launcher creates a child scope with the same memory and swap limits and group OOM killing, then verifies the limits, private namespaces, read-only temporary mounts and project scratch before starting either workload. [Shared isolation launcher](../../src/qualification/isolated.py)

```sh
runner=src/qualification/cfamily/mte_performance.py
python3 -I -B "$runner" build --cc-sdk /path/to/installed/c --work .tmp/mte-build
python3 -I -B "$runner" run --programs .tmp/mte-build/fixtures \
  --vm /path/to/uwvm2-ros --work .tmp/mte-run
```

Copy the whole `fixtures` directory to measure another host. The published i686 VM requires the 32-bit ELF loader `/lib/ld-linux.so.2` and 32-bit shared libraries, including `libatomic.so.1`, in the system library paths. Use a native i386 system or an x86_64 system with 32-bit execution support and those libraries (on Debian, `libc6:i386` and `libatomic1:i386` supply the loader and libatomic).

For one published x86_64 cell, add `--width 32 --engine int --iterations 8388608`. By default both widths and engines run five repeats, pinned to the first permitted CPU. Use `--cpu N` to choose another. Automatic calibration targets 320 ms of software checking and selects a power of two. Add `--emulated` inside a system-QEMU guest to use its shorter calibration probe. On an MTE-capable AArch64 Linux system add `--hardware` to time the synchronous hardware backend alongside software checking. An untimed control must show both a tagged mapping and successful synchronous tag control on the VM under `strace`. Supply `--strace /path/to/strace` for a separately installed tracer. Each control saves its trace beside `summary.json`. The cell’s `hardware_probe` records the filename and SHA-256.

The guest clocks initialization and a loop that reads and writes one indexed 32-bit word in a 4 KiB array. Each sample must match the independently compiled native checksum and report the expected zero or nonzero allocation tag. In `summary.json`, each ratio divides long-kernel times from the same repetition. The denominators are the ordinary module and the same tagged module with runtime checking disabled. Triples give inclusive Q1, median and Q3. The paired samples also include quarter-length and zero-loop controls, guest nanoseconds and host process nanoseconds. The summary identifies the supplied VM and module hashes that match the publication. [Runner](../../src/qualification/cfamily/mte_performance.py)
