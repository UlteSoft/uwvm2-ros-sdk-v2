// WROS exports the optimized Go SSA directly from its official compiler.
package ssa

import (
	"cmd/compile/internal/ir"
	"encoding/json"
	"fmt"
	"os"
)

type wrosValue struct {
	ID      int    `json:"id"`
	Op      string `json:"op"`
	Type    string `json:"type"`
	Literal int64  `json:"literal,omitempty"`
	Index   int    `json:"index,omitempty"`
	Args    []int  `json:"args,omitempty"`
}

// @brief Export a single returning SSA block with exact parameter identities.
// @param f Function after the official Go compiler's generic optimization pass.
// @details The encoder independently checks every exported operation and the
// unchanged memory token. Unsupported effects prevent publication of the guest.
func wrosWriteRegisters(f *Func) {
	reject := func(message string) {
		fmt.Fprintf(os.Stderr, "wrgo: function %s is outside the register-only profile: %s\n", f.Name, message)
		os.Exit(2)
	}
	if len(f.Blocks) != 1 || f.Entry.Kind != BlockRet || f.Entry.NumControls() != 1 {
		reject("requires a single returning block")
	}
	params := f.Type.Params()
	results := f.Type.Results()
	if len(params) > 32 || len(results) != 1 || len(f.Entry.Values) > 1024 {
		reject("signature or instruction limit")
	}
	types := make([]string, len(params))
	for i, p := range params {
		types[i] = p.Type.String()
	}
	values := make([]wrosValue, 0, len(f.Entry.Values))
	for _, v := range f.Entry.Values {
		s := wrosValue{ID: int(v.ID), Op: v.Op.String(), Type: v.Type.String(), Literal: v.AuxInt}
		if v.Op == OpArg {
			n, ok := v.Aux.(*ir.Name)
			if !ok {
				reject("invalid parameter origin")
			}
			s.Index = -1
			for i, p := range params {
				if p.Nname == n {
					s.Index = i
					break
				}
			}
			if s.Index < 0 || v.AuxInt != 0 {
				reject("indirect parameter")
			}
		} else if v.Aux != nil {
			reject("requires a symbol, memory reference or runtime operation")
		}
		for _, a := range v.Args {
			s.Args = append(s.Args, int(a.ID))
		}
		values = append(values, s)
	}
	result := struct {
		Name   string      `json:"name"`
		Params []string    `json:"params"`
		Result string      `json:"result"`
		Ret    int         `json:"ret"`
		Values []wrosValue `json:"values"`
	}{f.Name, types, results[0].Type.String(), int(f.Entry.Controls[0].ID), values}
	out, err := os.OpenFile("compiler.jsonl", os.O_APPEND|os.O_CREATE|os.O_WRONLY, 0600)
	if err != nil {
		reject(fmt.Sprint(err))
	}
	err = json.NewEncoder(out).Encode(result)
	if closeErr := out.Close(); err == nil {
		err = closeErr
	}
	if err != nil {
		reject(fmt.Sprint(err))
	}
}
