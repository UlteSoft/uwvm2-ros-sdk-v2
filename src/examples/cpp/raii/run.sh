#!/bin/sh
# Run the guard example under the requested engine with its exact scene grant.
set -eu
module=${1:?usage: sh run.sh GUEST.wasm [int|aot]}
engine=${2:-int}
: "${WROS_VM:?set WROS_VM to the uwvm2-ros executable}"
case "$engine" in int|aot) ;; *) echo 'expected int or aot' >&2; exit 2 ;; esac
set -- "--runtime-$engine" --wasm-feature-wasm3 --wasm-feature-enable-exceptions \
    --runtime-compile-threads 0 --runtime-memtag-mode sync --debug-fault-action exit \
    --wasm-set-main-module-name main --ros-scene-create robot --ros-scene-bind robot main
if [ "$engine" = aot ]; then
    set -- "$@" --runtime-llvm-jit-cache-path disable --runtime-llvm-jit-policy fast-compile
fi
for op in capability.open capability.close guard.create guard.trigger guard.take resource.close; do
    set -- "$@" --ros-scene-interface robot "$op" allow
done
exec "$WROS_VM" "$@" --ros-scene-grant robot signal guard signal local \
    guard.create,guard.trigger,guard.take,resource.close --run "$module"
