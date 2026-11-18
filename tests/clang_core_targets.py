#!/usr/bin/env python3
"""Verify the WROS Clang refuses component targets at each executable entry point."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import resource
import subprocess

from separate_compilation import cgroup_record


def sha(path):
    with path.open('rb') as f:
        return hashlib.file_digest(f, 'sha256').hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--clang', required=True, type=Path)
    parser.add_argument('--vm', required=True, type=Path)
    parser.add_argument('--output', required=True, type=Path)
    options = parser.parse_args()
    cgroup = cgroup_record()
    assert int(cgroup['memory_max']) == 68719476736 and int(cgroup['swap_max']) == 0
    resource.setrlimit(resource.RLIMIT_CORE, (0, 0))
    clang, vm = options.clang.resolve(), options.vm.resolve()
    out = options.output.resolve()
    out.mkdir(parents=True, exist_ok=False)
    os.environ.update(TMPDIR=str(out), LC_ALL='C')
    program = out/'main.c'
    program.write_text('void _start(void) {}\n')
    assembly = out/'entry.s'
    assembly.write_text('.text\n.globl entry\n.type entry,@function\nentry:\n.functype entry () -> ()\nend_function\n')
    recorder = out/'wasm-component-ld'
    recorder.write_text('#!/bin/sh\n: > "$WROS_FORBIDDEN_LINKER_MARKER"\nexit 61\n')
    recorder.chmod(0o700)
    marker = out/'forbidden-linker-called'
    os.environ['WROS_FORBIDDEN_LINKER_MARKER'] = str(marker)
    paths = [Path(__file__), clang, clang.parent/'wasm-ld', vm, program, assembly]
    report = {'complete': False, 'cgroup': cgroup, 'cases': [], 'inputs': {str(p): sha(p) for p in paths}}
    def run(label, command, *, product=None, deny=False, diagnostics=()):
        before = product.read_bytes() if product and product.exists() else None
        argv = list(map(str, command))
        state = subprocess.run(argv, cwd=out, timeout=30, capture_output=True)
        msg = state.stdout + state.stderr
        (out/(label+'.log')).write_bytes(msg)
        ok = (state.returncode != 0 and any(d.encode() in msg for d in diagnostics)) if deny else state.returncode == 0
        if product and deny:
            ok = ok and ((not product.exists()) if before is None else product.read_bytes() == before)
        if product and not deny:
            ok = ok and product.is_file() and product.read_bytes()[:8] == bytes.fromhex('0061736d01000000')
        ok = ok and not marker.exists()
        report['cases'].append({'name': label, 'argv': argv, 'exit': state.returncode, 'passed': ok})
        print(label, state.returncode, 'pass' if ok else msg[-300:].decode(errors='replace'), flush=True)
        return msg
    try:
        targets = run('compiler-targets', [clang, '--print-targets'])
        assert {s.split()[0] for s in targets.splitlines() if b' - ' in s} == {b'wasm32', b'wasm64'}
        for bits in (32, 64):
            prefix = 'wasm'+str(bits)
            good = out/('core'+str(bits)+'.o')
            run(prefix+'-core-obj', [clang, '--target='+prefix+'-unknown-unknown', '-O3', '-g', '-c', program, '-o', good], product=good)
            for suffix in ('unknown-unknown', 'wasip1', 'unknown-wasip1-threads'):
                triple = prefix+'-'+suffix
                obj = out/(triple+'.o')
                run(triple+'-cc1', [clang, '-cc1', '-triple', triple, '-emit-obj', program, '-o', obj], product=obj)
                asm = out/(triple+'.asm.o')
                run(triple+'-cc1as', [clang, '-cc1as', '-triple', triple, '-filetype', 'obj', assembly, '-o', asm], product=asm)
                guest = out/(triple+'.wasm')
                run(triple+'-driver-link', [clang, '--target='+triple, '-O3', '-g', '-nostdlib',
                                           '-Wl,--no-entry,--export=_start', program, '-o', guest], product=guest)
                for engine in ('int', 'aot'):
                    run(triple+'-'+engine, [vm, '--runtime-'+engine, '--runtime-compile-threads','0',
                                           '--runtime-llvm-jit-cache-path','disable','--run', guest])
            for phase in (2, 3):
                for suffix in ('wasip'+str(phase), 'unknown-wasip'+str(phase), 'unknown-wasip'+str(phase)+'-threads'):
                    triple = prefix+'-'+suffix
                    normalized = prefix+'-unknown-wasip'+str(phase)+('-threads' if suffix.endswith('-threads') else '')
                    args = [clang, '--target='+triple]
                    cases = {
                        'driver-c': [*args,'-c',program],
                        'driver-ir': [*args,'-S','-emit-llvm',program],
                        'driver-asm': [*args,'-c',assembly],
                        'driver-link': [*args,'-nostdlib',good],
                        'driver-lld': [*args,'-fuse-ld=lld','-nostdlib',good],
                        'driver-syntax': [*args,'-fsyntax-only',program],
                        'driver-recipe': [*args,'-###','-nostdlib',good],
                        'cc1': [clang,'-cc1','-triple',normalized,'-emit-obj',program],
                        'cc1as': [clang,'-cc1as','-triple',normalized,'-filetype','obj',assembly]}
                    for name, cmd in cases.items():
                        case = triple+'-'+name
                        dst = out/(case+'.rejected')
                        diagnostic = run(case, [*cmd,'-o',dst], product=dst, deny=True,
                                         diagnostics=('unknown target triple', 'unknown target'))
                        if name == 'driver-recipe':
                            assert b'wasm-component-ld' not in diagnostic
            for selection in (str(recorder), 'wasm-component-ld'):
                case=prefix+'-linker-'+('absolute' if selection.startswith('/') else 'named')
                dst = out/(case+'.rejected')
                run(case, [clang, '--target='+prefix+'-wasip1','-B',str(out),'-fuse-ld='+selection,
                           '-nostdlib',good,'-o',dst], product=dst, deny=True, diagnostics=('invalid linker name',))
        report['complete'] = (all(c['passed'] for c in report['cases']) and
                              all(sha(Path(p))==v for p,v in report['inputs'].items()) and not marker.exists())
    finally:
        (out/'results.json').write_text(json.dumps(report,indent=2)+'\n')
    return int(not report['complete'])


if __name__ == '__main__':
    raise SystemExit(main())
