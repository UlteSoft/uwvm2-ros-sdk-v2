//go:build wasip1 && wasm && u2ros_eh

#include "textflag.h"

TEXT runtime·wasmThrowPanic(SB), NOSPLIT|NOFRAME, $0
	GoPanicThrow
	UNDEF
