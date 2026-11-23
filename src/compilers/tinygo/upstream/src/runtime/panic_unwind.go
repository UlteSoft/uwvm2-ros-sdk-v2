//go:build !tinygo.wasm

package runtime

import (
	"internal/task"
	"runtime/interrupt"
)

// Restore the saved stack pointer and jump to the deferred call's landing pad.
//
//export tinygo_longjmp
func tinygo_longjmp(frame *deferFrame)

func dispatchPanicOrGoexit(message interface{}, panicking panicState) {
	if supportsRecover() && !interrupt.In() {
		frame := (*deferFrame)(task.Current().DeferFrame)
		if frame != nil {
			frame.PanicValue = message
			frame.Panicking = panicking
			tinygo_longjmp(frame)
		}
	}
	terminalPanicOrGoexit(message, panicking)
}
