//go:build wasip1 && wasm && u2ros_mte

#include "textflag.h"

TEXT runtime·wasmStackClaim(SB), NOSPLIT|NOFRAME, $0-24
	MOVD base+0(FP), R0
	MOVD size+8(FP), R1
	Get R0
	I32WrapI64
	Get R1
	I32WrapI64
	MemtagClaimZ
	I64ExtendI32U
	Set R0
	MOVD R0, ret+16(FP)
	RET

TEXT runtime·wasmStackRelease(SB), NOSPLIT|NOFRAME, $0-24
	MOVD base+0(FP), R0
	MOVD size+8(FP), R1
	Get R0
	I32WrapI64
	Get R1
	I32WrapI64
	MemtagRelease
	I64ExtendI32U
	Set R0
	MOVD R0, ret+16(FP)
	RET
